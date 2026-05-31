/**
 * One-click action buttons for opportunities (MOBILE-004).
 *
 * Provides two large action buttons:
 * - "Copy Draft": copies draft reply to clipboard, shows toast
 * - "Open Thread": opens URL in native browser or Reddit app
 *
 * Both buttons meet 56x56dp minimum tap area for accessibility.
 * No network calls for clipboard; action logging is fire-and-forget.
 *
 * Cross-module contracts:
 * - Integrates into MOBILE-003 (OpportunityDetail)
 * - Logs actions via FEAT-003 (logOpportunityAction)
 * - Uses OpportunityData from contracts/opportunity/opportunity.py
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import { Animated, Pressable, StyleSheet, Text, View } from "react-native";

import { logOpportunityAction } from "../api/opportunities";
import type { OpportunityData } from "../types/contracts";
import { copyDraft } from "../utils/clipboard";
import { openInRedditApp, openThread } from "../utils/urlLauncher";

interface OpportunityActionsProps {
  opportunity: OpportunityData;
  includeFooter: boolean;
  onCopyComplete?: () => void;
  onOpenComplete?: () => void;
}

/** Toast notification for copy confirmation. */
function CopyToast(props: { visible: boolean }): React.JSX.Element {
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (props.visible) {
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.delay(1600),
        Animated.timing(opacity, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [props.visible, opacity]);

  if (!props.visible) {
    return <></>;
  }

  return (
    <Animated.View style={[styles.toast, { opacity }]}>
      <Text style={styles.toastText}>Copied to clipboard</Text>
    </Animated.View>
  );
}

/** Determines if a URL is a Reddit link. */
function isRedditUrl(url: string): boolean {
  return /reddit\.com/i.test(url);
}

/**
 * Action buttons for opportunity detail view.
 * Large "Copy Draft" (primary) and "Open Thread" (secondary) buttons.
 */
function OpportunityActions(
  props: OpportunityActionsProps
): React.JSX.Element {
  const { opportunity, includeFooter, onCopyComplete, onOpenComplete } =
    props;
  const [showToast, setShowToast] = useState(false);
  const toastKey = useRef(0);

  const handleCopy = useCallback(async (): Promise<void> => {
    const draft = opportunity.edited_draft ?? opportunity.draft_reply;
    const success = await copyDraft(draft, includeFooter);

    if (success) {
      toastKey.current += 1;
      setShowToast(true);
      setTimeout(() => setShowToast(false), 2000);
      void logOpportunityAction(opportunity.id, "copied");
    }

    onCopyComplete?.();
  }, [opportunity, includeFooter, onCopyComplete]);

  const handleOpen = useCallback(async (): Promise<void> => {
    if (isRedditUrl(opportunity.url)) {
      await openInRedditApp(opportunity.url);
    } else {
      await openThread(opportunity.url);
    }

    void logOpportunityAction(opportunity.id, "viewed");
    onOpenComplete?.();
  }, [opportunity, onOpenComplete]);

  return (
    <View style={styles.container}>
      <Pressable
        onPress={handleCopy}
        style={styles.copyButton}
        accessibilityRole="button"
        accessibilityLabel="Copy Draft"
        testID="copy-draft-button"
      >
        <Text style={styles.copyText}>Copy Draft</Text>
      </Pressable>

      <Pressable
        onPress={handleOpen}
        style={styles.openButton}
        accessibilityRole="button"
        accessibilityLabel="Open Thread"
        testID="open-thread-button"
      >
        <Text style={styles.openText}>Open Thread</Text>
      </Pressable>

      <CopyToast key={toastKey.current} visible={showToast} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 12,
    paddingVertical: 8,
  },
  copyButton: {
    backgroundColor: "#FF6B35",
    borderRadius: 12,
    minHeight: 56,
    minWidth: 56,
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  copyText: {
    color: "#ffffff",
    fontSize: 17,
    fontWeight: "700",
  },
  openButton: {
    backgroundColor: "#333333",
    borderRadius: 12,
    minHeight: 56,
    minWidth: 56,
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  openText: {
    color: "#ffffff",
    fontSize: 17,
    fontWeight: "700",
  },
  toast: {
    position: "absolute",
    bottom: -48,
    left: 0,
    right: 0,
    alignItems: "center",
  },
  toastText: {
    backgroundColor: "#28a745",
    color: "#ffffff",
    fontSize: 14,
    fontWeight: "600",
    paddingVertical: 8,
    paddingHorizontal: 20,
    borderRadius: 20,
    overflow: "hidden",
  },
});

export { OpportunityActions };
export type { OpportunityActionsProps };
