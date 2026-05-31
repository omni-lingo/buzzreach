/**
 * Opportunities Dashboard page (FE-002, QUALITY-002).
 *
 * Live feed of discovered opportunities with filter sidebar,
 * card list, empty state, auto-refresh polling, and keyboard
 * shortcuts (j/k navigation, c/o/a/p/r actions, ? help).
 */

import React, { useCallback, useMemo, useState } from "react";

import type { Opportunity, OpportunitiesFilters } from "../api/opportunitiesClient";
import KeyboardHelp from "../components/KeyboardHelp";
import OpportunityCard from "../components/OpportunityCard";
import OpportunityFilter from "../components/OpportunityFilter";
import ThemeToggle from "../components/ThemeToggle";
import useDashboardShortcuts from "../hooks/useDashboardShortcuts";
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

  const { opportunities, total, loading, error, refresh, handleMarkPosted, handleArchive } =
    useOpportunities(token, stableFilters);

  const onMarkPosted = useCallback(
    (id: string): void => { handleMarkPosted(id).catch(() => {}); },
    [handleMarkPosted]
  );

  const onArchive = useCallback(
    (id: string): void => { handleArchive(id).catch(() => {}); },
    [handleArchive]
  );

  const { activeIndex, helpVisible, shortcuts, closeHelp } =
    useDashboardShortcuts({ opportunities, onMarkPosted, onArchive, onRefresh: refresh });

  return (
    <div className="dashboard-page">
      <DashboardHeader total={total} onRefresh={refresh} />
      <div className="dashboard-layout">
        <OpportunityFilter filters={filters} onChange={setFilters} />
        <FeedColumn
          opportunities={opportunities}
          loading={loading}
          error={error}
          activeIndex={activeIndex}
          onMarkPosted={onMarkPosted}
          onArchive={onArchive}
        />
      </div>
      <KeyboardHelp shortcuts={shortcuts} visible={helpVisible} onClose={closeHelp} />
    </div>
  );
};

// --------------- Sub-components ---------------

interface FeedColumnProps {
  opportunities: Opportunity[];
  loading: boolean;
  error: string | null;
  activeIndex: number;
  onMarkPosted: (id: string) => void;
  onArchive: (id: string) => void;
}

const FeedColumn: React.FC<FeedColumnProps> = ({
  opportunities, loading, error, activeIndex, onMarkPosted, onArchive,
}) => (
  <main className="dashboard-feed">
    {loading && opportunities.length === 0 && (
      <div className="loading-spinner">Loading opportunities...</div>
    )}
    {error && <div className="error-banner">{error}</div>}
    {!loading && opportunities.length === 0 && !error && <EmptyState />}
    {opportunities.map((opp, idx) => (
      <OpportunityCard
        key={opp.id}
        opportunity={opp}
        onMarkPosted={onMarkPosted}
        onArchive={onArchive}
        isKeyboardActive={idx === activeIndex}
      />
    ))}
  </main>
);

interface DashboardHeaderProps {
  total: number;
  onRefresh: () => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({ total, onRefresh }) => (
  <header className="dashboard-header">
    <h1>Opportunities</h1>
    <span className="dashboard-count">{total} found</span>
    <button className="btn-refresh" onClick={onRefresh} type="button">
      Refresh
    </button>
    <ThemeToggle />
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
