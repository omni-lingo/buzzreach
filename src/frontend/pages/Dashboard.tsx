/**
 * Opportunities Dashboard page (FE-002).
 *
 * Live feed of discovered opportunities with filter sidebar,
 * card list, empty state, and auto-refresh polling.
 */

import React, { useCallback, useMemo, useState } from "react";

import type { OpportunitiesFilters } from "../api/opportunitiesClient";
import OpportunityCard from "../components/OpportunityCard";
import OpportunityFilter from "../components/OpportunityFilter";
import useOpportunities from "../hooks/useOpportunities";

interface DashboardProps {
  token: string;
}

const DEFAULT_FILTERS: OpportunitiesFilters = {
  limit: 50,
  score_min: 0.5,
};

const Dashboard: React.FC<DashboardProps> = ({ token }) => {
  const [filters, setFilters] = useState<OpportunitiesFilters>(
    DEFAULT_FILTERS
  );

  const stableFilters = useMemo(() => filters, [
    filters.platform,
    filters.score_min,
    filters.score_max,
    filters.status,
    filters.limit,
    filters.offset,
  ]);

  const {
    opportunities,
    total,
    loading,
    error,
    refresh,
    handleMarkPosted,
    handleArchive,
  } = useOpportunities(token, stableFilters);

  const onMarkPosted = useCallback(
    (id: string): void => {
      handleMarkPosted(id).catch(() => {});
    },
    [handleMarkPosted]
  );

  const onArchive = useCallback(
    (id: string): void => {
      handleArchive(id).catch(() => {});
    },
    [handleArchive]
  );

  return (
    <div className="dashboard-page">
      <DashboardHeader total={total} onRefresh={refresh} />

      <div className="dashboard-layout">
        <OpportunityFilter filters={filters} onChange={setFilters} />

        <main className="dashboard-feed">
          {loading && opportunities.length === 0 && (
            <div className="loading-spinner">Loading opportunities...</div>
          )}

          {error && <div className="error-banner">{error}</div>}

          {!loading && opportunities.length === 0 && !error && (
            <EmptyState />
          )}

          {opportunities.map((opp) => (
            <OpportunityCard
              key={opp.id}
              opportunity={opp}
              onMarkPosted={onMarkPosted}
              onArchive={onArchive}
            />
          ))}
        </main>
      </div>
    </div>
  );
};

// --------------- Sub-components ---------------

interface DashboardHeaderProps {
  total: number;
  onRefresh: () => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  total,
  onRefresh,
}) => (
  <header className="dashboard-header">
    <h1>Opportunities</h1>
    <span className="dashboard-count">{total} found</span>
    <button className="btn-refresh" onClick={onRefresh} type="button">
      Refresh
    </button>
  </header>
);

const EmptyState: React.FC = () => (
  <div className="empty-state">
    <h2>No opportunities found</h2>
    <p>
      No opportunities match your current filters. Try adjusting the
      platform or score range, or wait for the next scan cycle.
    </p>
  </div>
);

export default Dashboard;
