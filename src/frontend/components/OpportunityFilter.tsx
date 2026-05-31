/**
 * Filter sidebar for the Opportunities Dashboard (FE-002).
 *
 * Controls: platform select, score range slider (0.5–1.0),
 * status filter, and reset button.
 */

import React, { useCallback } from "react";

import type { OpportunitiesFilters } from "../api/opportunitiesClient";

const PLATFORMS = [
  { value: "", label: "All Platforms" },
  { value: "reddit", label: "Reddit" },
  { value: "quora", label: "Quora" },
  { value: "hackernews", label: "Hacker News" },
  { value: "twitter", label: "Twitter" },
  { value: "stackoverflow", label: "Stack Overflow" },
  { value: "dev.to", label: "Dev.to" },
];

interface OpportunityFilterProps {
  filters: OpportunitiesFilters;
  onChange: (filters: OpportunitiesFilters) => void;
}

const OpportunityFilter: React.FC<OpportunityFilterProps> = ({
  filters,
  onChange,
}) => {
  const handlePlatformChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>): void => {
      const platform = e.target.value || undefined;
      onChange({ ...filters, platform, offset: 0 });
    },
    [filters, onChange]
  );

  const handleScoreMinChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>): void => {
      const score_min = parseFloat(e.target.value);
      onChange({ ...filters, score_min, offset: 0 });
    },
    [filters, onChange]
  );

  const handleReset = useCallback((): void => {
    onChange({ limit: filters.limit });
  }, [filters.limit, onChange]);

  const scoreMinDisplay = filters.score_min !== undefined
    ? (filters.score_min * 100).toFixed(0)
    : "50";

  return (
    <aside className="opportunity-filter">
      <h3 className="filter-title">Filters</h3>

      <div className="filter-group">
        <label htmlFor="platform-select">Platform</label>
        <select
          id="platform-select"
          value={filters.platform ?? ""}
          onChange={handlePlatformChange}
        >
          {PLATFORMS.map((p) => (
            <option key={p.value} value={p.value} data-platform={p.value}>
              {p.label}
            </option>
          ))}
        </select>
        {PLATFORMS.filter((p) => p.value).map((p) => (
          <button
            key={p.value}
            className={`platform-chip ${
              filters.platform === p.value ? "active" : ""
            }`}
            data-platform={p.value}
            onClick={() =>
              onChange({
                ...filters,
                platform: filters.platform === p.value
                  ? undefined
                  : p.value,
                offset: 0,
              })
            }
            type="button"
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="filter-group">
        <label htmlFor="score-min-slider">
          Min Score: {scoreMinDisplay}%
        </label>
        <input
          id="score-min-slider"
          name="score_min"
          type="range"
          min="0.5"
          max="1.0"
          step="0.05"
          value={filters.score_min ?? 0.5}
          onChange={handleScoreMinChange}
        />
      </div>

      <button
        className="btn-reset-filters"
        onClick={handleReset}
        type="button"
      >
        Reset Filters
      </button>
    </aside>
  );
};

export default OpportunityFilter;
