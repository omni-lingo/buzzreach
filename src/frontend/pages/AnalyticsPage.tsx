/**
 * Analytics page with conversion funnel (FEAT-003).
 *
 * Shows: discovered -> viewed -> copied -> posted funnel with counts,
 * conversion rate, filter by date range, and platform breakdown.
 */

import React, { useCallback, useEffect, useState } from "react";

import type { FunnelData } from "../components/opportunityApi";
import { fetchFunnel } from "../components/opportunityApi";

const PLATFORMS = ["all", "reddit", "quora", "hackernews"] as const;

const AnalyticsPage: React.FC = () => {
  const [funnel, setFunnel] = useState<FunnelData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [platform, setPlatform] = useState<string>("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const loadFunnel = useCallback((): void => {
    setLoading(true);
    setError(null);
    const params: Record<string, string> = {};
    if (platform !== "all") params.platform = platform;
    if (dateFrom) params.dateFrom = dateFrom;
    if (dateTo) params.dateTo = dateTo;

    fetchFunnel(
      Object.keys(params).length > 0 ? params : undefined
    )
      .then(setFunnel)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [platform, dateFrom, dateTo]);

  useEffect(() => {
    loadFunnel();
  }, [loadFunnel]);

  return (
    <div className="analytics-page">
      <h1>Conversion Analytics</h1>
      <p>Track your opportunity conversion funnel.</p>

      {error && <div className="error-banner">{error}</div>}

      <FilterBar
        platform={platform}
        setPlatform={setPlatform}
        dateFrom={dateFrom}
        setDateFrom={setDateFrom}
        dateTo={dateTo}
        setDateTo={setDateTo}
        onApply={loadFunnel}
        loading={loading}
      />

      {funnel && <FunnelDisplay funnel={funnel} />}
      {funnel && <ConversionRate funnel={funnel} />}
      {!funnel && !loading && (
        <p className="empty-state">No data available yet.</p>
      )}
    </div>
  );
};

interface FilterBarProps {
  platform: string;
  setPlatform: (v: string) => void;
  dateFrom: string;
  setDateFrom: (v: string) => void;
  dateTo: string;
  setDateTo: (v: string) => void;
  onApply: () => void;
  loading: boolean;
}

const FilterBar: React.FC<FilterBarProps> = ({
  platform,
  setPlatform,
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
  onApply,
  loading,
}) => (
  <div className="analytics-filters">
    <label>
      Platform
      <select
        value={platform}
        onChange={(e) => setPlatform(e.target.value)}
      >
        {PLATFORMS.map((p) => (
          <option key={p} value={p}>
            {p === "all" ? "All Platforms" : p}
          </option>
        ))}
      </select>
    </label>
    <label>
      From
      <input
        type="date"
        value={dateFrom}
        onChange={(e) => setDateFrom(e.target.value)}
      />
    </label>
    <label>
      To
      <input
        type="date"
        value={dateTo}
        onChange={(e) => setDateTo(e.target.value)}
      />
    </label>
    <button onClick={onApply} disabled={loading}>
      {loading ? "Loading..." : "Apply Filters"}
    </button>
  </div>
);

interface FunnelDisplayProps {
  funnel: FunnelData;
}

const FUNNEL_STEPS: Array<{ key: keyof FunnelData; label: string }> = [
  { key: "discovered", label: "Discovered" },
  { key: "viewed", label: "Shown" },
  { key: "copied", label: "Copied" },
  { key: "posted", label: "Posted" },
];

const FunnelDisplay: React.FC<FunnelDisplayProps> = ({ funnel }) => {
  const maxVal = Math.max(
    ...FUNNEL_STEPS.map((s) => Number(funnel[s.key]) || 0),
    1
  );

  return (
    <div className="funnel-chart">
      <h2>Conversion Funnel</h2>
      <div className="funnel-bars">
        {FUNNEL_STEPS.map((step) => {
          const value = Number(funnel[step.key]) || 0;
          const pct = (value / maxVal) * 100;
          return (
            <div key={step.key} className="funnel-step">
              <span className="funnel-label">{step.label}</span>
              <div className="funnel-bar-bg">
                <div
                  className="funnel-bar-fill"
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="funnel-count">{value}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

interface ConversionRateProps {
  funnel: FunnelData;
}

const ConversionRate: React.FC<ConversionRateProps> = ({ funnel }) => {
  const rate = (funnel.conversion_rate * 100).toFixed(1);

  return (
    <div className="conversion-summary">
      <h2>Summary</h2>
      <table className="summary-table">
        <tbody>
          <tr>
            <td>Discovered</td>
            <td>{funnel.discovered}</td>
          </tr>
          <tr>
            <td>Shown (Viewed)</td>
            <td>{funnel.viewed}</td>
          </tr>
          <tr>
            <td>Copied</td>
            <td>{funnel.copied}</td>
          </tr>
          <tr>
            <td>Posted</td>
            <td>{funnel.posted}</td>
          </tr>
          <tr>
            <td>Archived</td>
            <td>{funnel.archived}</td>
          </tr>
          <tr className="conversion-row">
            <td>Conversion Rate (posted/viewed)</td>
            <td>{rate}%</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default AnalyticsPage;
