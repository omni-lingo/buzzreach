/**
 * Bundle detail panel for niche bundles (QUALITY-004).
 *
 * Shows full bundle info: keywords, platforms, tone guide, templates.
 * Allows customization before applying the bundle as a search profile.
 */

import React from "react";

import type { NicheBundle } from "../api/nicheBundlesApi";

interface ApplyState {
  bundleId: string;
  profileName: string;
  keywords: string;
  platforms: string;
  editing: boolean;
}

interface BundleDetailProps {
  bundle: NicheBundle;
  apply: ApplyState;
  onApplyChange: (state: ApplyState) => void;
  onApply: () => void;
  onClose: () => void;
}

const BundleDetail: React.FC<BundleDetailProps> = ({
  bundle,
  apply,
  onApplyChange,
  onApply,
  onClose,
}) => (
  <div
    className="bundle-detail"
    style={{
      marginTop: "1.5rem",
      border: "1px solid #d1d5db",
      borderRadius: "0.5rem",
      padding: "1.5rem",
    }}
  >
    <div style={{ display: "flex", justifyContent: "space-between" }}>
      <h2 style={{ margin: 0 }}>{bundle.name}</h2>
      <button onClick={onClose} style={{ cursor: "pointer" }}>
        Close
      </button>
    </div>

    <p>{bundle.description}</p>

    <ToneGuide tone={bundle.tone} description={bundle.tone_description} />

    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
      <KeywordsSection
        keywords={apply.keywords}
        editing={apply.editing}
        onChange={(v) => onApplyChange({ ...apply, keywords: v })}
      />
      <PlatformsSection
        platforms={apply.platforms}
        editing={apply.editing}
        onChange={(v) => onApplyChange({ ...apply, platforms: v })}
      />
    </div>

    <TemplatesSection templates={bundle.templates} />

    <div style={{ marginTop: "1rem" }}>
      <label style={{ display: "block", marginBottom: "0.5rem" }}>
        Profile Name
        <input
          type="text"
          value={apply.profileName}
          onChange={(e) =>
            onApplyChange({ ...apply, profileName: e.target.value })
          }
          style={{ display: "block", width: "100%", padding: "0.375rem" }}
        />
      </label>
      <label style={{ fontSize: "0.875rem" }}>
        <input
          type="checkbox"
          checked={apply.editing}
          onChange={(e) =>
            onApplyChange({ ...apply, editing: e.target.checked })
          }
        />{" "}
        Customize keywords &amp; platforms before applying
      </label>
    </div>

    <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
      <button
        onClick={onApply}
        className="apply-btn"
        style={{
          backgroundColor: "#3b82f6",
          color: "#fff",
          padding: "0.5rem 1rem",
          borderRadius: "0.25rem",
          border: "none",
          cursor: "pointer",
        }}
      >
        Use This Niche
      </button>
      <button onClick={onClose} style={{ cursor: "pointer" }}>
        Cancel
      </button>
    </div>
  </div>
);

interface ToneGuideProps {
  tone: string;
  description: string;
}

const ToneGuide: React.FC<ToneGuideProps> = ({ tone, description }) => (
  <div
    className="tone-guide"
    style={{
      background: "#f3f4f6",
      borderRadius: "0.375rem",
      padding: "0.75rem",
      marginBottom: "1rem",
    }}
  >
    <strong>Tone: </strong>
    <span style={{ textTransform: "capitalize" }}>{tone}</span>
    <p style={{ margin: "0.25rem 0 0", fontSize: "0.875rem" }}>
      {description}
    </p>
  </div>
);

interface ListSectionProps {
  editing: boolean;
  onChange: (v: string) => void;
}

interface KeywordsSectionProps extends ListSectionProps {
  keywords: string;
}

const KeywordsSection: React.FC<KeywordsSectionProps> = ({
  keywords,
  editing,
  onChange,
}) => (
  <div>
    <h4 style={{ margin: "0 0 0.25rem" }}>Keywords</h4>
    {editing ? (
      <textarea
        value={keywords}
        onChange={(e) => onChange(e.target.value)}
        rows={4}
        style={{ width: "100%", padding: "0.375rem" }}
      />
    ) : (
      <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.875rem" }}>
        {keywords.split("\n").filter(Boolean).map((kw, i) => (
          <li key={i}>{kw}</li>
        ))}
      </ul>
    )}
  </div>
);

interface PlatformsSectionProps extends ListSectionProps {
  platforms: string;
}

const PlatformsSection: React.FC<PlatformsSectionProps> = ({
  platforms,
  editing,
  onChange,
}) => (
  <div>
    <h4 style={{ margin: "0 0 0.25rem" }}>Platforms</h4>
    {editing ? (
      <textarea
        value={platforms}
        onChange={(e) => onChange(e.target.value)}
        rows={4}
        style={{ width: "100%", padding: "0.375rem" }}
      />
    ) : (
      <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.875rem" }}>
        {platforms.split("\n").filter(Boolean).map((p, i) => (
          <li key={i}>{p}</li>
        ))}
      </ul>
    )}
  </div>
);

interface TemplatesSectionProps {
  templates: NicheBundle["templates"];
}

const TemplatesSection: React.FC<TemplatesSectionProps> = ({ templates }) => (
  <div style={{ marginTop: "1rem" }}>
    <h4 style={{ margin: "0 0 0.5rem" }}>Included Templates</h4>
    {templates.map((tpl, idx) => (
      <div
        key={idx}
        style={{
          border: "1px solid #e5e7eb",
          borderRadius: "0.375rem",
          padding: "0.75rem",
          marginBottom: "0.5rem",
        }}
      >
        <strong>{tpl.name}</strong>
        <span
          style={{
            fontSize: "0.75rem",
            background: "#e5e7eb",
            padding: "0.125rem 0.375rem",
            borderRadius: "0.25rem",
            marginLeft: "0.5rem",
          }}
        >
          {tpl.category}
        </span>
        <p style={{ fontSize: "0.875rem", margin: "0.25rem 0" }}>
          {tpl.description}
        </p>
        <pre
          style={{
            fontSize: "0.75rem",
            background: "#f9fafb",
            padding: "0.5rem",
            borderRadius: "0.25rem",
            whiteSpace: "pre-wrap",
            overflow: "auto",
          }}
        >
          {tpl.text}
        </pre>
      </div>
    ))}
  </div>
);

export default BundleDetail;
