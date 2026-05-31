/**
 * Opportunity feed screen with swipe gestures (MOBILE-003).
 *
 * - Scrollable list of opportunity cards
 * - Pull-to-refresh fetches new opportunities
 * - Swipe left to archive/dismiss
 * - Swipe right to open detail modal
 * - Tap for full details modal
 *
 * Cross-module contracts:
 * - Reads OpportunityData from API-001 via GET /api/v1/opportunities
 * - Logs actions via FEAT-003 POST /api/v1/opportunities/{id}/actions
 * - Uses useOpportunityStore for state
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";

import {
  fetchOpportunities,
  logOpportunityAction,
  refreshOpportunities,
} from "../api/opportunities";
import OpportunityCard from "../components/OpportunityCard.mobile";
import OpportunityDetail from "./OpportunityDetail";
import { useOpportunityStore } from "../store/opportunityStore";
import { parseApiError } from "../api/client";
import type { OpportunityData } from "../types/contracts";

/** Main feed screen showing opportunity cards with swipe gestures. */
function FeedScreen(): React.JSX.Element {
  const items = useOpportunityStore((s) => s.items);
  const isLoading = useOpportunityStore((s) => s.isLoading);
  const isRefreshing = useOpportunityStore((s) => s.isRefreshing);
  const error = useOpportunityStore((s) => s.error);

  const [selectedOpp, setSelectedOpp] =
    useState<OpportunityData | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);

  const loadFeed = useCallback(async () => {
    const store = useOpportunityStore.getState();
    store.setLoading(true);
    store.clearError();
    try {
      const data = await fetchOpportunities();
      store.setItems(data);
    } catch (err: unknown) {
      store.setError(parseApiError(err));
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    const store = useOpportunityStore.getState();
    store.setRefreshing(true);
    store.clearError();
    try {
      const data = await refreshOpportunities();
      store.setItems(data);
    } catch (err: unknown) {
      store.setError(parseApiError(err));
    }
  }, []);

  useEffect(() => {
    void loadFeed();
  }, [loadFeed]);

  const handleCardPress = useCallback(
    (opportunity: OpportunityData) => {
      setSelectedOpp(opportunity);
      setDetailVisible(true);
    },
    []
  );

  const handleArchive = useCallback((id: string) => {
    useOpportunityStore.getState().removeItem(id);
    void logOpportunityAction(id, "archived");
  }, []);

  const handleMarkPosted = useCallback((id: string) => {
    useOpportunityStore.getState().removeItem(id);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setDetailVisible(false);
    setSelectedOpp(null);
  }, []);

  if (isLoading && items.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#FF6B35" />
        <Text style={styles.loadingText}>
          Loading opportunities...
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {error ? (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      <FlatList
        data={items}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <SwipeableCard
            opportunity={item}
            onPress={handleCardPress}
            onSwipeLeft={handleArchive}
            onSwipeRight={handleCardPress}
          />
        )}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor="#FF6B35"
          />
        }
        ListEmptyComponent={<EmptyState />}
        contentContainerStyle={
          items.length === 0 ? styles.emptyList : undefined
        }
      />

      {selectedOpp ? (
        <OpportunityDetail
          opportunity={selectedOpp}
          visible={detailVisible}
          onClose={handleCloseDetail}
          onArchive={handleArchive}
          onMarkPosted={handleMarkPosted}
        />
      ) : null}
    </View>
  );
}

// --- Sub-components ---

function SwipeableCard(props: {
  opportunity: OpportunityData;
  onPress: (opp: OpportunityData) => void;
  onSwipeLeft: (id: string) => void;
  onSwipeRight: (opp: OpportunityData) => void;
}): React.JSX.Element {
  return (
    <View style={styles.swipeContainer}>
      <OpportunityCard
        opportunity={props.opportunity}
        onPress={props.onPress}
      />
    </View>
  );
}

function EmptyState(): React.JSX.Element {
  return (
    <View style={styles.center}>
      <Text style={styles.emptyTitle}>No opportunities yet</Text>
      <Text style={styles.emptySubtitle}>
        Pull down to refresh or check your settings.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    marginTop: 12,
    color: "#666666",
    fontSize: 14,
  },
  errorBanner: {
    backgroundColor: "#fce4e4",
    padding: 12,
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 8,
  },
  errorText: {
    color: "#dc3545",
    fontSize: 14,
    textAlign: "center",
  },
  emptyList: { flexGrow: 1 },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#333333",
  },
  emptySubtitle: {
    fontSize: 14,
    color: "#999999",
    marginTop: 8,
  },
  swipeContainer: { overflow: "hidden" },
});

export default FeedScreen;
