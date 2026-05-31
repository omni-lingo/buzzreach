/**
 * Feed screen stub for BuzzReach mobile app (MOBILE-001).
 *
 * Displays a list of opportunities from the API.
 * Full implementation deferred to MOBILE-003 (Opportunity Feed).
 *
 * Cross-module contracts:
 * - Reads OpportunityData from API-001 via GET /api/v1/opportunities
 * - Uses useOpportunityStore for state
 */

import React, { useCallback, useEffect } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { apiClient, parseApiError } from "../api/client";
import { useOpportunityStore } from "../store/opportunityStore";
import type { OpportunityData } from "../types/contracts";

/** Main feed screen showing opportunity cards. */
function FeedScreen(): React.JSX.Element {
  const items = useOpportunityStore((s) => s.items);
  const isLoading = useOpportunityStore((s) => s.isLoading);
  const error = useOpportunityStore((s) => s.error);

  const fetchOpportunities = useCallback(async () => {
    const store = useOpportunityStore.getState();
    store.setLoading(true);
    store.clearError();

    try {
      const response = await apiClient.get<OpportunityData[]>(
        "/opportunities"
      );
      store.setItems(response.data);
    } catch (err: unknown) {
      store.setError(parseApiError(err));
    }
  }, []);

  useEffect(() => {
    void fetchOpportunities();
  }, [fetchOpportunities]);

  if (isLoading && items.length === 0) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#FF6B35" />
        <Text style={styles.loadingText}>Loading opportunities...</Text>
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
        renderItem={({ item }) => <OpportunityCard opportunity={item} />}
        refreshControl={
          <RefreshControl
            refreshing={isLoading}
            onRefresh={fetchOpportunities}
            tintColor="#FF6B35"
          />
        }
        ListEmptyComponent={<EmptyState />}
        contentContainerStyle={
          items.length === 0 ? styles.emptyList : undefined
        }
      />
    </View>
  );
}

// --------------- Sub-components ---------------

function OpportunityCard(props: {
  opportunity: OpportunityData;
}): React.JSX.Element {
  const { opportunity } = props;
  const scorePercent = Math.round(opportunity.relevance_score * 100);

  return (
    <Pressable style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.cardTitle} numberOfLines={2}>
          {opportunity.title}
        </Text>
        <View style={styles.scoreBadge}>
          <Text style={styles.scoreText}>{scorePercent}%</Text>
        </View>
      </View>
      <Text style={styles.cardSource}>
        {opportunity.source} / {opportunity.niche}
      </Text>
      <Text style={styles.cardReason} numberOfLines={2}>
        {opportunity.why_matched}
      </Text>
    </Pressable>
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

// --------------- Styles ---------------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  loadingText: { marginTop: 12, color: "#666", fontSize: 14 },
  errorBanner: {
    backgroundColor: "#fce4e4",
    padding: 12,
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 8,
  },
  errorText: { color: "#dc3545", fontSize: 14, textAlign: "center" },
  emptyList: { flexGrow: 1 },
  emptyTitle: { fontSize: 18, fontWeight: "600", color: "#333" },
  emptySubtitle: { fontSize: 14, color: "#999", marginTop: 8 },
  card: {
    backgroundColor: "#fff",
    marginHorizontal: 16,
    marginTop: 12,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#e9ecef",
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  cardTitle: { fontSize: 16, fontWeight: "600", color: "#333", flex: 1 },
  scoreBadge: {
    backgroundColor: "#FF6B35",
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    marginLeft: 8,
  },
  scoreText: { color: "#fff", fontSize: 12, fontWeight: "bold" },
  cardSource: { fontSize: 12, color: "#999", marginTop: 6 },
  cardReason: { fontSize: 14, color: "#666", marginTop: 8 },
});

export default FeedScreen;
