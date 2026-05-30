#!/usr/bin/env python3
"""Post-L1 hook: Generate schema documentation after models are created."""
import json
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger("after_l1")

# This is a template. Real implementation would:
# 1. Parse all models in src/models/
# 2. Extract column definitions
# 3. Generate contracts/schema_columns.json
# 4. Update SCHEMA.md

def main():
    """Generate schema docs after L1 (models) complete."""
    project_root = Path(__file__).parent.parent.parent.parent
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir(exist_ok=True)

    # Template schema
    schema = {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "tables": [],
        "note": "Auto-generated after L1 models. Update via src/models/"
    }

    schema_file = contracts_dir / "schema_columns.json"
    with open(schema_file, "w") as f:
        json.dump(schema, f, indent=2)

    log.info("Generated %s", schema_file)
    print(f"✓ Schema documentation generated: {schema_file}")

if __name__ == "__main__":
    main()
