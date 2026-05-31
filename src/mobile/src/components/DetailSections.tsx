/**
 * Reusable sub-components for OpportunityDetail modal (MOBILE-003).
 *
 * Extracted from OpportunityDetail.tsx to stay within 300-line limit.
 * Contains: ModalHeader, MetadataSection, DraftSection, ActionButtons.
 *
 * Cross-module contracts:
 * - None — leaf module (internal to mobile detail screen).
 */

import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

// --- ModalHeader ---

function ModalHeader(props: {
  title: string;
  onClose: () => void;
}): React.JSX.Element {
  return (
    <View style={styles.header}>
      <Text style={styles.headerTitle} numberOfLines={2}>
        {props.title}
      </Text>
      <Pressable
        onPress={props.onClose}
        style={styles.closeButton}
        accessibilityRole="button"
        accessibilityLabel="Close detail view"
        testID="close-button"
      >
        <Text style={styles.closeText}>✕</Text>
      </Pressable>
    </View>
  );
}

// --- MetadataSection ---

interface MetadataProps {
  source: string;
  niche: string;
  scorePercent: number;
  url: string;
  reason: string;
}

function MetadataSection(props: MetadataProps): React.JSX.Element {
  return (
    <View style={styles.metaSection}>
      <View style={styles.metaRow}>
        <View style={styles.platformBadge}>
          <Text style={styles.platformText}>{props.source}</Text>
        </View>
        <Text style={styles.niche}>{props.niche}</Text>
        <View style={styles.scoreBadge}>
          <Text style={styles.scoreText}>
            {props.scorePercent}%
          </Text>
        </View>
      </View>
      <Text style={styles.reason}>{props.reason}</Text>
      <Text style={styles.url} numberOfLines={1}>
        {props.url}
      </Text>
    </View>
  );
}

// --- DraftSection ---

function DraftSection(props: {
  draft: string;
}): React.JSX.Element {
  return (
    <View style={styles.draftSection}>
      <Text style={styles.sectionLabel}>Draft Reply</Text>
      <Text style={styles.draftText} selectable>
        {props.draft}
      </Text>
    </View>
  );
}

// --- ActionButtons ---

type ButtonVariant = "primary" | "secondary" | "success" | "muted";

const VARIANT_COLORS: Record<
  ButtonVariant,
  { bg: string; text: string }
> = {
  primary: { bg: "#FF6B35", text: "#ffffff" },
  secondary: { bg: "#333333", text: "#ffffff" },
  success: { bg: "#28a745", text: "#ffffff" },
  muted: { bg: "#e9ecef", text: "#333333" },
};

function ActionButton(props: {
  label: string;
  onPress: () => void;
  variant: ButtonVariant;
}): React.JSX.Element {
  const colors = VARIANT_COLORS[props.variant];
  return (
    <Pressable
      onPress={props.onPress}
      style={[
        styles.actionButton,
        { backgroundColor: colors.bg },
      ]}
      accessibilityRole="button"
      accessibilityLabel={props.label}
    >
      <Text style={[styles.actionText, { color: colors.text }]}>
        {props.label}
      </Text>
    </Pressable>
  );
}

interface ActionButtonsProps {
  copyLabel: string;
  onCopy: () => void;
  onOpenBrowser: () => void;
  onMarkPosted: () => void;
  onArchive: () => void;
}

function ActionButtons(
  props: ActionButtonsProps
): React.JSX.Element {
  return (
    <View style={styles.actions}>
      <ActionButton
        label={props.copyLabel}
        onPress={props.onCopy}
        variant="primary"
      />
      <ActionButton
        label="Open in Browser"
        onPress={props.onOpenBrowser}
        variant="secondary"
      />
      <ActionButton
        label="Mark as Posted"
        onPress={props.onMarkPosted}
        variant="success"
      />
      <ActionButton
        label="Archive"
        onPress={props.onArchive}
        variant="muted"
      />
    </View>
  );
}

// --- Styles ---

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#e9ecef",
    backgroundColor: "#ffffff",
  },
  headerTitle: {
    flex: 1,
    fontSize: 18,
    fontWeight: "600",
    color: "#333333",
  },
  closeButton: {
    minWidth: 48,
    minHeight: 48,
    justifyContent: "center",
    alignItems: "center",
  },
  closeText: { fontSize: 20, color: "#666666" },
  metaSection: { marginBottom: 16 },
  metaRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  platformBadge: {
    backgroundColor: "#f0f0f0",
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  platformText: {
    fontSize: 13,
    color: "#666666",
    fontWeight: "500",
  },
  niche: { fontSize: 13, color: "#999999", flex: 1 },
  scoreBadge: {
    backgroundColor: "#FF6B35",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  scoreText: {
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "bold",
  },
  reason: {
    fontSize: 14,
    color: "#666666",
    marginTop: 10,
  },
  url: {
    fontSize: 12,
    color: "#0066cc",
    marginTop: 6,
  },
  draftSection: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: "#e9ecef",
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333333",
    marginBottom: 8,
  },
  draftText: {
    fontSize: 15,
    color: "#333333",
    lineHeight: 22,
  },
  actions: {
    padding: 16,
    gap: 10,
    borderTopWidth: 1,
    borderTopColor: "#e9ecef",
    backgroundColor: "#ffffff",
  },
  actionButton: {
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 20,
    minHeight: 48,
    justifyContent: "center",
    alignItems: "center",
  },
  actionText: {
    fontSize: 16,
    fontWeight: "600",
  },
});

export {
  ModalHeader,
  MetadataSection,
  DraftSection,
  ActionButtons,
};
