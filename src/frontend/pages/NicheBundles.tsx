/**
 * Niche Bundles picker page (QUALITY-004).
 *
 * Shows available pre-configured niche bundles with descriptions,
 * keywords, platforms, tone guides, and templates. Users can select
 * a bundle to auto-populate a search profile, or customize it first.
 */

import React, { useEffect, useState } from "react";

import {
  applyBundle,
  fetchBundles,
} from "../api/nicheBundlesApi";
import type { NicheBundle } from "../api/nicheBundlesApi";
import BundleDetail from "../components/BundleDetail";

interface ApplyState {
  bundleId: string;
  profileName: string;
  keywords: string;
  platforms: string;
  editing: boolean;
}

const INITIAL_APPLY: ApplyState = {
  bundleId: "",
  profileName: "",
  keywords: "",
  platforms: "",
  editing: false,
};

const NicheBundlesPage: React.FC = () => {
  const [bundles, setBundles] = useState<NicheBundle[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [apply, setApply] = useState<ApplyState>(INITIAL_APPLY);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchBundles()
      .then(setBundles)
      .catch((e: Error) => setError(e.message));
  }, []);

  const filtered = bundles.filter(
    (b) =>
      b.name.toLowerCase().includes(search.toLowerCase()) ||
      b.description.toLowerCase().includes(search.toLowerCase())
  );

  const handleSelect = (bundle: NicheBundle): void => {
    setSelectedId(bundle.id);
    setApply({
      bundleId: bundle.id,
      profileName: bundle.name,
      keywords: bundle.keywords.join("\n"),
      platforms: bundle.platforms.join("\n"),
      editing: false,
    });
    setError(null);
    setSuccess(null);
  };

  const handleApply = (): void => {
    setError(null);
    setSuccess(null);
    const kw = apply.keywords
      .split("\n")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    const plat = apply.platforms
      .split("\n")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    if (!apply.profileName.trim()) {
      setError("Profile name is required");
      return;
    }

    const token = "";
    applyBundle(token, {
      bundle_id: apply.bundleId,
      profile_name: apply.profileName,
      keywords: apply.editing ? kw : undefined,
      platforms: apply.editing ? plat : undefined,
    })
      .then((result) => {
        setSuccess(result.message);
        setSelectedId(null);
        setApply(INITIAL_APPLY);
      })
      .catch((e: Error) => setError(e.message));
  };

  const selected = bundles.find((b) => b.id === selectedId) ?? null;

  return (
    <div className="niche-bundles-page" style={{ padding: "1rem" }}>
      <h1>Niche Bundles</h1>
      <p>
        Pre-configured profiles to get you started quickly.
        Pick a niche, customize if needed, and start finding opportunities.
      </p>

      {error && <div className="error-banner">{error}</div>}
      {success && <div className="success-banner">{success}</div>}

      <input
        type="text"
        placeholder="Search bundles..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="bundle-search"
        style={{ width: "100%", padding: "0.5rem", marginBottom: "1rem" }}
      />

      <div
        className="bundles-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: "1rem",
        }}
      >
        {filtered.map((bundle) => (
          <BundleCard
            key={bundle.id}
            bundle={bundle}
            isSelected={bundle.id === selectedId}
            onSelect={() => handleSelect(bundle)}
          />
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="empty-state">No bundles match your search.</p>
      )}

      {selected && (
        <BundleDetail
          bundle={selected}
          apply={apply}
          onApplyChange={setApply}
          onApply={handleApply}
          onClose={() => { setSelectedId(null); setApply(INITIAL_APPLY); }}
        />
      )}
    </div>
  );
};

interface BundleCardProps {
  bundle: NicheBundle;
  isSelected: boolean;
  onSelect: () => void;
}

const BundleCard: React.FC<BundleCardProps> = ({
  bundle,
  isSelected,
  onSelect,
}) => (
  <div
    className={`bundle-card ${isSelected ? "bundle-card--selected" : ""}`}
    style={{
      border: isSelected ? "2px solid #3b82f6" : "1px solid #e5e7eb",
      borderRadius: "0.5rem",
      padding: "1rem",
      cursor: "pointer",
    }}
    onClick={onSelect}
    role="button"
    tabIndex={0}
    onKeyDown={(e) => { if (e.key === "Enter") onSelect(); }}
  >
    <h3 style={{ margin: "0 0 0.5rem" }}>{bundle.name}</h3>
    <p style={{ fontSize: "0.875rem", color: "#6b7280" }}>
      {bundle.description}
    </p>
    <div style={{ fontSize: "0.75rem", marginTop: "0.5rem" }}>
      <strong>Tone:</strong> {bundle.tone}
    </div>
    <div style={{ fontSize: "0.75rem", color: "#9ca3af" }}>
      {bundle.keywords.length} keywords &middot;{" "}
      {bundle.platforms.length} platforms &middot;{" "}
      {bundle.templates.length} templates
    </div>
  </div>
);

export default NicheBundlesPage;
