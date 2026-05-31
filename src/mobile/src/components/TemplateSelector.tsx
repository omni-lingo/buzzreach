/**
 * Template selector modal for the draft editor (QUALITY-003).
 *
 * "Use template" button opens a modal showing relevant templates.
 * Selecting a template applies its text to the draft field.
 * Template text can be edited after application.
 *
 * Cross-module contracts:
 * - Used by draft editor (FEAT-001)
 * - Uses TemplateData from contracts/quality/draft_template.py
 * - Calls QUALITY-003 template API via templates.ts
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  FlatList,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { fetchTemplates } from "../api/templates";
import useColorTheme from "../hooks/useColorTheme";
import type { TemplateData } from "../types/contracts";

interface TemplateSelectorProps {
  visible: boolean;
  onClose: () => void;
  onApply: (text: string) => void;
}

/** Replace {placeholder} tokens with sample values for preview. */
function interpolatePreview(text: string): string {
  const samples: Record<string, string> = {
    product_name: "YourProduct",
    product_url: "https://example.com",
    user_name: "User",
  };
  return text.replace(
    /\{(\w+)\}/g,
    (match, key: string) => samples[key] ?? match
  );
}

/** Single template item in the selector list. */
function SelectorItem(props: {
  template: TemplateData;
  onSelect: (template: TemplateData) => void;
  colors: ReturnType<typeof useColorTheme>["colors"];
}): React.JSX.Element {
  const { template, colors, onSelect } = props;

  return (
    <Pressable
      style={[styles.item, { backgroundColor: colors.card, borderColor: colors.border }]}
      onPress={() => onSelect(template)}
    >
      <View style={styles.itemHeader}>
        <Text style={[styles.itemName, { color: colors.text }]}>
          {template.name}
        </Text>
        <View style={[styles.badge, { backgroundColor: colors.primary }]}>
          <Text style={styles.badgeText}>{template.category}</Text>
        </View>
      </View>
      <Text
        style={[styles.itemDesc, { color: colors.textSecondary }]}
        numberOfLines={2}
      >
        {template.description}
      </Text>
    </Pressable>
  );
}

/** Modal for selecting and applying a template to the draft editor. */
function TemplateSelector(
  props: TemplateSelectorProps
): React.JSX.Element | null {
  const { visible, onClose, onApply } = props;
  const { colors } = useColorTheme();
  const [templates, setTemplates] = useState<TemplateData[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<TemplateData | null>(null);
  const [loading, setLoading] = useState(false);

  const loadTemplates = useCallback(async (): Promise<void> => {
    setLoading(true);
    const items = await fetchTemplates({
      search: search || undefined,
    });
    setTemplates(items);
    setLoading(false);
  }, [search]);

  useEffect(() => {
    if (visible) {
      void loadTemplates();
    }
  }, [visible, loadTemplates]);

  if (!visible) {
    return null;
  }

  const handleApply = (): void => {
    if (selected) {
      onApply(selected.text);
      setSelected(null);
      onClose();
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.header}>
          <Text style={[styles.title, { color: colors.text }]}>
            Use Template
          </Text>
          <Pressable onPress={onClose}>
            <Text style={[styles.closeBtn, { color: colors.primary }]}>
              Close
            </Text>
          </Pressable>
        </View>

        <TextInput
          style={[styles.searchInput, { backgroundColor: colors.inputBg, color: colors.text, borderColor: colors.border }]}
          placeholder="Search templates..."
          placeholderTextColor={colors.textTertiary}
          value={search}
          onChangeText={setSearch}
        />

        {selected ? (
          <View style={styles.previewSection}>
            <Text style={[styles.previewTitle, { color: colors.text }]}>
              {selected.name}
            </Text>
            <View style={[styles.previewBox, { backgroundColor: colors.inputBg }]}>
              <Text style={[styles.previewText, { color: colors.text }]}>
                {interpolatePreview(selected.text)}
              </Text>
            </View>
            <View style={styles.previewActions}>
              <Pressable
                style={[styles.actionBtn, { borderColor: colors.border }]}
                onPress={() => setSelected(null)}
              >
                <Text style={{ color: colors.text }}>Back</Text>
              </Pressable>
              <Pressable
                style={[styles.actionBtn, { backgroundColor: colors.primary }]}
                onPress={handleApply}
              >
                <Text style={{ color: "#fff" }}>Apply Template</Text>
              </Pressable>
            </View>
          </View>
        ) : (
          <FlatList
            data={templates}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <SelectorItem
                template={item}
                onSelect={setSelected}
                colors={colors}
              />
            )}
            refreshing={loading}
            onRefresh={loadTemplates}
            contentContainerStyle={styles.listContent}
          />
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
  title: { fontSize: 20, fontWeight: "700" },
  closeBtn: { fontSize: 16, fontWeight: "600" },
  searchInput: { height: 44, borderRadius: 8, borderWidth: 1, paddingHorizontal: 12, fontSize: 16, marginBottom: 12 },
  listContent: { paddingBottom: 24 },
  item: { borderRadius: 10, borderWidth: 1, padding: 14, marginBottom: 10 },
  itemHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 4 },
  itemName: { fontSize: 15, fontWeight: "600", flex: 1 },
  badge: { borderRadius: 12, paddingHorizontal: 10, paddingVertical: 3, marginLeft: 8 },
  badgeText: { color: "#fff", fontSize: 11, fontWeight: "600" },
  itemDesc: { fontSize: 13 },
  previewSection: { flex: 1 },
  previewTitle: { fontSize: 18, fontWeight: "600", marginBottom: 12 },
  previewBox: { borderRadius: 8, padding: 12, flex: 1 },
  previewText: { fontSize: 14, lineHeight: 22 },
  previewActions: { flexDirection: "row", justifyContent: "space-between", marginTop: 16 },
  actionBtn: { paddingHorizontal: 20, paddingVertical: 12, borderRadius: 8, borderWidth: 1, borderColor: "transparent" },
});

export default TemplateSelector;
