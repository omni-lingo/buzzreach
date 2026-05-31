/**
 * Data fetching hook for the Opportunities Dashboard (FE-002).
 *
 * Manages loading state, error handling, polling (auto-refresh
 * every 5 minutes), and filter-aware refetching.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import type {
  Opportunity,
  OpportunitiesFilters,
} from "../api/opportunitiesClient";
import {
  archiveOpportunity,
  fetchOpportunities,
  markPosted,
} from "../api/opportunitiesClient";

const POLL_INTERVAL_MS = 5 * 60 * 1000;

interface UseOpportunitiesReturn {
  opportunities: Opportunity[];
  total: number;
  loading: boolean;
  error: string | null;
  refresh: () => void;
  handleMarkPosted: (id: string) => Promise<void>;
  handleArchive: (id: string) => Promise<void>;
}

function useOpportunities(
  token: string,
  filters: OpportunitiesFilters
): UseOpportunitiesReturn {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback((): void => {
    setLoading(true);
    setError(null);
    fetchOpportunities(token, filters)
      .then((res) => {
        setOpportunities(res.items);
        setTotal(res.total);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token, filters]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    timerRef.current = setInterval(load, POLL_INTERVAL_MS);
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [load]);

  const handleMarkPosted = useCallback(
    async (id: string): Promise<void> => {
      await markPosted(token, id);
      setOpportunities((prev) => prev.filter((o) => o.id !== id));
      setTotal((prev) => prev - 1);
    },
    [token]
  );

  const handleArchive = useCallback(
    async (id: string): Promise<void> => {
      await archiveOpportunity(token, id);
      setOpportunities((prev) => prev.filter((o) => o.id !== id));
      setTotal((prev) => prev - 1);
    },
    [token]
  );

  return {
    opportunities,
    total,
    loading,
    error,
    refresh: load,
    handleMarkPosted,
    handleArchive,
  };
}

export default useOpportunities;
export type { UseOpportunitiesReturn };
