/**
 * Template library browsing screen (QUALITY-003).
 *
 * Browse templates by category, search by name/description,
 * preview template text with sample placeholders, and create
 * custom templates.
 *
 * Cross-module contracts:
 * - Uses TemplateData from contracts/quality/draft_template.py
 * - Calls QUALITY-003 template API endpoints
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { fetchTemplates } from "../api/templates";
import useColorTheme from "../hooks/useColorTheme";
import type { TemplateCategory, TemplateData } from "../types/contracts";

const CATEGORIES: { label: string; value: TemplateCategory | "all" }[] = [
  { label: "All", value: "all" },
  { label: "Reddit", value: "reddit" },
  { label: "Quora", value: "quora" },
  { label: "Blog", value: "blog" },
  { label: "Technical", value: "technical" },
  { label: "Casual", value: "casual" },
  { label: "Professional", value: "professional" },
  { label: "Empathetic", value: "empathetic" },
  { label: "Persuasive", value: "persuasive" },
];

const SAMPLE_VARS: Record<string, string> = {
  product_name: "BuzzReach",
  product_url: "https://buzzreach.app",
  product_description: "finds relevant threads for you",
  user_name: "You",
  suggestion_1: "check the documentation",
  suggestion_2: "try restarting the service",
  feature_1: "AI-powered draft replies",
  feature_2: "Cross-platform discovery",
  feature_3: "One-click posting",
};

/** Replace {placeholder} tokens with sample values for preview. */
function previewText(text: string): string {
  return text.replace(
    /\{(\w+)\}/g,
    (match, key: string) => SAMPLE_VARS[key] ?? match
  );
}

/** Single template card in the list. */
function TemplateCard(props: {
  template: TemplateData;
  colors: ReturnType<typeof useColorTheme>["colors"];
}): React.JSX.Element {
  const { template, colors } = props;
  const [expanded, setExpanded] = useState(false);

  return (
    <Pressable
      style={[styles.card, { backgroundColor: colors.card, borderColor: colors.border }]}
      onPress={() => setExpanded(!expanded)}
    >
      <View style={styles.cardHeader}>
        <Text style={[styles.cardTitle, { color: colors.text }]}>
          {template.name}
        </Text>
        <View style={[styles.badge, { backgroundColor: colors.primary }]}>
          <Text style={styles.badgeText}>{template.category}</Text>
        </View>
      </View>
      <Text style={[styles.cardDesc, { color: colors.textSecondary }]}>
        {template.description}
      </Text>
      {template.is_global && (
        <Text style={[styles.globalTag, { color: colors.textTertiary }]}>
          Global template
        </Text>
      )}
      {expanded && (
        <View style={[styles.preview, { backgroundColor: colors.inputBg }]}>
          <Text style={[styles.previewLabel, { color: colors.textTertiary }]}>
            Preview:
          </Text>
          <Text style={[styles.previewText, { color: colors.text }]}>
            {previewText(template.text)}
          </Text>
        </View>
      )}
    </Pressable>
  );
}

/** Templates library screen with category filter and search. */
function TemplatesPage(): React.JSX.Element {
  const { colors } = useColorTheme();
  const [templates, setTemplates] = useState<TemplateData[]>([]);
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [loading, setLoading] = useState(false);

  const loadTemplates = useCallback(async (): Promise<void> => {
    setLoading(true);
    const category = activeCategory === "all" ? undefined : activeCategory;
    const items = await fetchTemplates({
      category,
      search: search || undefined,
    });
    setTemplates(items);
    setLoading(false);
  }, [activeCategory, search]);

  useEffect(() => {
    void loadTemplates();
  }, [loadTemplates]);

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <TextInput
        style={[styles.searchInput, { backgroundColor: colors.inputBg, color: colors.text, borderColor: colors.border }]}
        placeholder="Search templates..."
        placeholderTextColor={colors.textTertiary}
        value={search}
        onChangeText={setSearch}
      />
      <FlatList
        horizontal
        data={CATEGORIES}
        keyExtractor={(item) => item.value}
        showsHorizontalScrollIndicator={false}
        style={styles.categoryList}
        renderItem={({ item }) => (
          <Pressable
            style={[
              styles.categoryChip,
              { borderColor: colors.border },
              activeCategory === item.value && { backgroundColor: colors.primary },
            ]}
            onPress={() => setActiveCategory(item.value)}
          >
            <Text
              style={[
                styles.categoryText,
                { color: activeCategory === item.value ? "#fff" : colors.text },
              ]}
            >
              {item.label}
            </Text>
          </Pressable>
        )}
      />
      <FlatList
        data={templates}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <TemplateCard template={item} colors={colors} />
        )}
        contentContainerStyle={styles.listContent}
        refreshing={loading}
        onRefresh={loadTemplates}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  searchInput: { height: 44, borderRadius: 8, borderWidth: 1, paddingHorizontal: 12, fontSize: 16, marginBottom: 12 },
  categoryList: { maxHeight: 44, marginBottom: 12 },
  categoryChip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1, marginRight: 8 },
  categoryText: { fontSize: 13, fontWeight: "500" },
  listContent: { paddingBottom: 24 },
  card: { borderRadius: 10, borderWidth: 1, padding: 14, marginBottom: 12 },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 6 },
  cardTitle: { fontSize: 16, fontWeight: "600", flex: 1 },
  badge: { borderRadius: 12, paddingHorizontal: 10, paddingVertical: 3, marginLeft: 8 },
  badgeText: { color: "#fff", fontSize: 11, fontWeight: "600" },
  cardDesc: { fontSize: 13, marginBottom: 4 },
  globalTag: { fontSize: 11, fontStyle: "italic" },
  preview: { marginTop: 10, padding: 10, borderRadius: 6 },
  previewLabel: { fontSize: 11, marginBottom: 4 },
  previewText: { fontSize: 13, lineHeight: 20 },
});

export default TemplatesPage;
export { previewText };
