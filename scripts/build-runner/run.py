#!/usr/bin/env python3
"""
BuzzReach Build Runner — orchestrates atom-based development with Claude Code.

Usage:
  python run.py                     # Build next ready atom
  python run.py --atom AUTH-001     # Build specific atom
  python run.py --status            # Show build progress
  python run.py --dry-run           # Show wave plan (parallel atoms)
  python run.py --health            # Infrastructure health check
  python run.py --model opus        # Model override (usually Opus 4.6 always)
  python run.py --max-atoms 5       # Stop after N atoms
  python run.py --timeout 1800      # Per-atom timeout (seconds)

Reads:
  - product.yaml (tech stack, modules, build config)
  - atoms/**/*.md (atom specifications)
  - state/build_state.json (machine state, gitignored)

Windows background: run via build.bat or pythonw.exe
"""
import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Add lib/ to path
sys.path.insert(0, str(Path(__file__).parent / "lib"))

from config import load_config, ConfigError
from state import BuildState
from claims import ClaimStore
from executor import build_atom, AtomNotFound
from health import run_preflight
from errors import categorize_result, handle_failure
from deps import find_ready_atoms, compute_waves, load_atoms
from context import detect_atom_type, load_context
from prompts import select_prompt
from cost import CostTracker
from github import create_github_client
from hooks import HookRunner

log = logging.getLogger("build-runner")


def setup_logging(config):
    """Configure structured logging to file + console."""
    log_dir = config.project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "build-runner.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    return log_file


def parse_args():
    """Parse CLI arguments."""
    p = argparse.ArgumentParser(
        description="Build runner for BuzzReach MVP (30 atoms, Opus 4.6, max effort)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--config", default="product.yaml", help="Config file (default: product.yaml)")
    p.add_argument("--atom", help="Build specific atom ID (e.g. AUTH-001)")
    p.add_argument("--module", help="Build all atoms in module (e.g. auth)")
    p.add_argument("--status", action="store_true", help="Show build progress and exit")
    p.add_argument("--dry-run", action="store_true", help="Show wave plan and exit")
    p.add_argument("--health", action="store_true", help="Run infrastructure health checks")
    p.add_argument("--model", default="claude-opus-4-6", help="Model override (default: Opus 4.6)")
    p.add_argument("--max-atoms", type=int, help="Stop after N atoms")
    p.add_argument("--timeout", type=int, default=1800, help="Per-atom timeout (seconds)")
    p.add_argument("--budget", type=float, help="Budget cap (USD)")
    return p.parse_args()


def show_status(config):
    """Print build progress summary."""
    state = BuildState(config.state_dir)
    atoms = load_atoms(config.atoms_dir)

    print("\n=== BUILD STATUS ===\n")

    status_counts = {"pending": 0, "building": 0, "complete": 0, "failed": 0, "blocked": 0}
    for atom in atoms:
        s = state.get_status(atom["id"])
        status_counts[s] = status_counts.get(s, 0) + 1

    total = len(atoms)
    complete = status_counts["complete"]
    failed = status_counts["failed"]
    blocked = status_counts["blocked"]
    remaining = total - complete - failed - blocked

    print(f"Total:      {total} atoms")
    print(f"Complete:   {complete}")
    print(f"Failed:     {failed}")
    print(f"Blocked:    {blocked}")
    print(f"Remaining:  {remaining}")
    print(f"Progress:   {complete}/{total} ({100*complete/total:.0f}%)")
    print()


def show_wave_plan(config):
    """Print parallelizable wave plan."""
    atoms = load_atoms(config.atoms_dir)
    state = BuildState(config.state_dir)

    waves = compute_waves(atoms, state)

    print("\n=== WAVE PLAN (Parallelizable builds) ===\n")
    for i, wave in enumerate(waves, 1):
        print(f"Wave {i} ({len(wave)} atoms):")
        for atom in wave:
            effort = atom.get("effort", "M")
            layer = atom.get("layer", "L?")
            deps = ", ".join(atom.get("depends_on", []))
            deps_str = f" (deps: {deps})" if deps else ""
            print(f"  - {atom['id']} [{layer}] Effort {effort}{deps_str}")
        print()

    total_atoms = sum(len(w) for w in waves)
    print(f"Total: {total_atoms} atoms in {len(waves)} waves")
    print(f"Sequential time: ~{len(waves) * 20} min (avg 20min/atom)")
    print(f"Parallel time (--parallel 4): ~{20 + len(waves) * 5} min\n")


def check_wave_complete(state, wave_atoms) -> bool:
    """Check if all atoms in a wave are complete.

    Returns:
        True if all atoms in wave are complete
    """
    return all(state.get_status(a["id"]) == "complete" for a in wave_atoms)


def check_layer_complete(state, atoms, layer: str) -> bool:
    """Check if all atoms in a layer are complete.

    Args:
        state: BuildState
        atoms: All atoms
        layer: Layer name (L1, L2, L3, L4, L5)

    Returns:
        True if all atoms in layer are complete
    """
    layer_atoms = [a for a in atoms if a.get("layer") == layer]
    if not layer_atoms:
        return False
    return all(state.get_status(a["id"]) == "complete" for a in layer_atoms)


def create_wave_pr(wave_number: int, wave_atoms, github):
    """Create a GitHub PR for completed wave.

    Args:
        wave_number: Wave number
        wave_atoms: List of atom dicts in the wave
        github: GitHubClient instance
    """
    atom_ids = [a["id"] for a in wave_atoms]
    pr_url = github.create_wave_pr(wave_number, atom_ids)
    if pr_url:
        log.info("Created PR for wave %d: %s", wave_number, pr_url)
    return pr_url


def main():
    """Main build loop."""
    args = parse_args()

    # Load config
    try:
        config = load_config(args.config or "product.yaml")
    except ConfigError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Setup logging
    log_file = setup_logging(config)
    log.info("=" * 60)
    log.info("Build runner started: %s", datetime.now(timezone.utc).isoformat())
    log.info("Config: %s", config.config_path)
    log.info("=" * 60)

    # Health check
    if args.health:
        results = run_preflight(config)
        print("\n=== HEALTH CHECK ===\n")
        for r in results:
            status = "✓" if r.passed else "✗"
            print(f"{status} {r.name}: {r.output or 'OK'}")
        print()
        sys.exit(0 if all(r.passed for r in results) else 1)

    # Status report
    if args.status:
        show_status(config)
        sys.exit(0)

    # Dry run (wave plan)
    if args.dry_run:
        show_wave_plan(config)
        sys.exit(0)

    # ===== MAIN BUILD LOOP =====
    log.info("Starting build: max effort, Opus 4.6")

    state = BuildState(config.state_dir)
    claims = ClaimStore(config.state_dir / "claims.db")
    costs = CostTracker(config.logs_dir)
    github = create_github_client()
    hook_runner = HookRunner(config.project_root, github)

    # Check GitHub auth
    if not github.check_auth():
        log.warning("GitHub auth failed. Continuing without automatic pushes.")
        github = None

    # Startup cleanup
    claims.release_stale_claims()
    log.info("Released stale claims from prior sessions")

    atoms = load_atoms(config.atoms_dir)

    # Filter by --atom or --module
    if args.atom:
        atoms = [a for a in atoms if a["id"] == args.atom]
        if not atoms:
            log.error("Atom %s not found", args.atom)
            sys.exit(1)
    elif args.module:
        atoms = [a for a in atoms if a["module"] == args.module]
        if not atoms:
            log.error("Module %s has no atoms", args.module)
            sys.exit(1)

    atoms_built = 0
    consecutive_fails = 0
    agent_id = f"agent-{int(time.time())}"
    waves = compute_waves(atoms, state)
    completed_waves = []
    completed_layers = set()

    while True:
        # Check budget
        if args.budget and costs.total() > args.budget:
            log.warning("Budget exceeded: $%.2f > $%.2f", costs.total(), args.budget)
            break

        # Check atom limit
        if args.max_atoms and atoms_built >= args.max_atoms:
            log.info("Max atoms reached: %d/%d", atoms_built, args.max_atoms)
            break

        # Find ready atoms (topological order)
        ready = find_ready_atoms(state, atoms)
        if not ready:
            log.info("No atoms ready. Build complete or blocked.")
            break

        atom = ready[0]
        atom_id = atom["id"]

        # Try to claim
        if not claims.claim(atom_id, agent_id):
            log.warning("Atom %s already claimed by another agent", atom_id)
            continue

        log.info("Building atom: %s", atom_id)

        try:
            # Detect type and load context
            atom_type = detect_atom_type(atom)
            context = load_context(atom_type, config.project_root)

            # Build atom
            result = build_atom(
                atom=atom,
                config=config,
                state=state,
                agent_id=agent_id,
                model=args.model,
                timeout=args.timeout,
                context=context,
            )

            if result == "SUCCESS":
                atoms_built += 1
                consecutive_fails = 0
                log.info("✓ %s complete", atom_id)

                # Check if current wave is complete
                for wave_idx, wave in enumerate(waves, 1):
                    if wave_idx not in completed_waves and check_wave_complete(state, wave):
                        if github:
                            create_wave_pr(wave_idx, wave, github)
                        completed_waves.append(wave_idx)
                        log.info("Wave %d complete! PR created.", wave_idx)

                # Check if layer is complete and run post-layer hooks
                atom_layer = atom.get("layer", "L?")
                if atom_layer not in completed_layers and check_layer_complete(state, atoms, atom_layer):
                    log.info("Layer %s complete! Running post-layer hooks...", atom_layer)
                    hook_runner.run_after_layer(atom_layer)
                    completed_layers.add(atom_layer)
            elif result == "RATE_LIMITED":
                log.warning("Rate limited, waiting...")
                claims.unclaim(atom_id, agent_id)
                time.sleep(60)
            elif result == "FAILED":
                consecutive_fails += 1
                log.error("✗ %s failed (attempt %d)", atom_id, consecutive_fails)
                if consecutive_fails >= 3:
                    log.error("3 consecutive failures, stopping")
                    break
            elif result == "BLOCKED":
                log.warning("⊘ %s blocked (context overflow or missing dep)", atom_id)

        except Exception as e:
            log.exception("Unexpected error in atom %s: %s", atom_id, e)
            consecutive_fails += 1
            claims.unclaim(atom_id, agent_id)
            if consecutive_fails >= 3:
                log.error("3 consecutive errors, stopping")
                break

    claims.close()

    log.info("=" * 60)
    log.info("Build finished: %d atoms built, cost $%.2f", atoms_built, costs.total())
    log.info("GitHub: https://github.com/omni-lingo/buzzreach")
    log.info("Log: %s", log_file)
    log.info("=" * 60)

    print(f"\n✓ Build complete: {atoms_built} atoms, ${costs.total():.2f}")
    print(f"GitHub: https://github.com/omni-lingo/buzzreach")
    print(f"Log: {log_file}\n")


if __name__ == "__main__":
    main()
