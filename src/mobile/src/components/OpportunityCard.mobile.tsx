/**
 * Opportunity card component optimized for mobile touch (MOBILE-003).
 *
 * - Large hit targets (48dp minimum)
 * - Condensed layout for mobile width
 * - Draft preview (first 100 chars, hidden until visible)
 * - Privacy: full draft not exposed in feed
 *
 * Cross-module contracts:
 * - Renders OpportunityData from contracts/opportunity/opportunity.py
 */

import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import type { OpportunityData } from "../types/contracts";

const DRAFT_PREVIEW_LENGTH = 100;

interface OpportunityCardProps {
  opportunity: OpportunityData;
  onPress: (opportunity: OpportunityData) => void;
}

/** Truncate text to maxLen, appending "..." if truncated. */
function truncateText(text: string, maxLen: number): string {
  if (text.length <= maxLen) {
    return text;
  }
  return text.slice(0, maxLen) + "...";
}

/** Mobile-optimized opportunity card with 48dp touch targets. */
function OpportunityCard(
  props: OpportunityCardProps
): React.JSX.Element {
  const { opportunity, onPress } = props;
  const scorePercent = Math.round(opportunity.relevance_score * 100);
  const draftSnippet = truncateText(
    opportunity.draft_reply,
    DRAFT_PREVIEW_LENGTH
  );

  return (
    <Pressable
      style={styles.card}
      onPress={() => onPress(opportunity)}
      accessibilityRole="button"
      accessibilityLabel={`Opportunity: ${opportunity.title}`}
    >
      <View style={styles.header}>
        <Text style={styles.title} numberOfLines={2}>
          {opportunity.title}
        </Text>
        <View style={styles.scoreBadge}>
          <Text style={styles.scoreText}>{scorePercent}%</Text>
        </View>
      </View>

      <View style={styles.metaRow}>
        <View style={styles.platformBadge}>
          <Text style={styles.platformText}>{opportunity.source}</Text>
        </View>
        <Text style={styles.niche}>{opportunity.niche}</Text>
      </View>

      <Text style={styles.reason} numberOfLines={2}>
        {opportunity.why_matched}
      </Text>

      <Text
        style={styles.draftPreview}
        numberOfLines={2}
        testID="draft-preview"
      >
        {draftSnippet}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#ffffff",
    marginHorizontal: 16,
    marginTop: 12,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#e9ecef",
    minHeight: 48,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  title: {
    fontSize: 16,
    fontWeight: "600",
    color: "#333333",
    flex: 1,
    marginRight: 8,
  },
  scoreBadge: {
    backgroundColor: "#FF6B35",
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    minWidth: 48,
    minHeight: 28,
    justifyContent: "center",
    alignItems: "center",
  },
  scoreText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "bold",
  },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 8,
    gap: 8,
  },
  platformBadge: {
    backgroundColor: "#f0f0f0",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  platformText: {
    fontSize: 12,
    color: "#666666",
    fontWeight: "500",
  },
  niche: {
    fontSize: 12,
    color: "#999999",
  },
  reason: {
    fontSize: 13,
    color: "#666666",
    marginTop: 8,
  },
  draftPreview: {
    fontSize: 13,
    color: "#999999",
    fontStyle: "italic",
    marginTop: 8,
  },
});

export default OpportunityCard;
export { truncateText };
