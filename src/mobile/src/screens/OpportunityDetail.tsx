/**
 * Opportunity detail modal screen (MOBILE-003).
 *
 * Shows full opportunity data with action buttons:
 * - Copy to Clipboard (copies draft reply)
 * - Open in Browser (launches URL)
 * - Mark as Posted (logs action, removes from feed)
 * - Archive (logs action, removes from feed)
 *
 * Sub-components live in components/DetailSections.tsx.
 *
 * Cross-module contracts:
 * - Renders OpportunityData from contracts/opportunity/opportunity.py
 * - Calls FEAT-003 action logging via opportunities API
 * - Integrates with MOBILE-004 (URL launcher via expo-linking)
 */

import * as Clipboard from "expo-clipboard";
import * as Linking from "expo-linking";
import React, { useState } from "react";
import {
  Modal,
  ScrollView,
  StyleSheet,
  View,
} from "react-native";

import { logOpportunityAction } from "../api/opportunities";
import {
  ActionButtons,
  DraftSection,
  MetadataSection,
  ModalHeader,
} from "../components/DetailSections";
import type { OpportunityData } from "../types/contracts";

interface OpportunityDetailProps {
  opportunity: OpportunityData;
  visible: boolean;
  onClose: () => void;
  onArchive: (id: string) => void;
  onMarkPosted: (id: string) => void;
}

/** Full-screen modal showing opportunity details and actions. */
function OpportunityDetail(
  props: OpportunityDetailProps
): React.JSX.Element | null {
  const { opportunity, visible, onClose, onArchive, onMarkPosted } =
    props;
  const [copyLabel, setCopyLabel] = useState("Copy to Clipboard");
  const scorePercent = Math.round(
    opportunity.relevance_score * 100
  );

  if (!visible) {
    return null;
  }

  const handleCopy = async (): Promise<void> => {
    const text = opportunity.edited_draft ?? opportunity.draft_reply;
    await Clipboard.setStringAsync(text);
    void logOpportunityAction(opportunity.id, "copied");
    setCopyLabel("Copied!");
    setTimeout(() => setCopyLabel("Copy to Clipboard"), 2000);
  };

  const handleOpenBrowser = (): void => {
    void Linking.openURL(opportunity.url);
    void logOpportunityAction(opportunity.id, "viewed");
  };

  const handleMarkPosted = async (): Promise<void> => {
    await logOpportunityAction(
      opportunity.id,
      "posted",
      opportunity.url
    );
    onMarkPosted(opportunity.id);
    onClose();
  };

  const handleArchive = async (): Promise<void> => {
    await logOpportunityAction(opportunity.id, "archived");
    onArchive(opportunity.id);
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        <ModalHeader
          title={opportunity.title}
          onClose={onClose}
        />

        <ScrollView
          style={styles.scrollContent}
          contentContainerStyle={styles.scrollInner}
        >
          <MetadataSection
            source={opportunity.source}
            niche={opportunity.niche}
            scorePercent={scorePercent}
            url={opportunity.url}
            reason={opportunity.why_matched}
          />

          <DraftSection
            draft={
              opportunity.edited_draft ?? opportunity.draft_reply
            }
          />
        </ScrollView>

        <ActionButtons
          copyLabel={copyLabel}
          onCopy={handleCopy}
          onOpenBrowser={handleOpenBrowser}
          onMarkPosted={handleMarkPosted}
          onArchive={handleArchive}
        />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f8f9fa" },
  scrollContent: { flex: 1 },
  scrollInner: { padding: 16 },
});

export default OpportunityDetail;
