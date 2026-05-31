/**
 * Reusable settings form with validation (FE-001).
 *
 * Orchestrates form state, validation, and submission.
 * Section sub-components live in SettingsFormSections.tsx.
 */

import React, { useCallback, useState } from "react";

import type { SaveSettingsRequest } from "../api/settingsClient";

import {
  DeliverySection,
  ProductSection,
  SearchFilterSection,
  ToneSection,
} from "./SettingsFormSections";

// --------------- Types ---------------

export interface SettingsFormData {
  product_url: string;
  one_line_pitch: string;
  keywords: string;
  tone: string;
  delivery_email: string;
  slack_webhook_url: string;
  delivery_frequency: "hourly" | "daily" | "weekly";
  platform_preferences: string[];
  exclude_domains: string;
}

interface SettingsFormProps {
  initial: SettingsFormData;
  saving: boolean;
  onSave: (data: SaveSettingsRequest) => void;
}

export interface ValidationErrors {
  keywords?: string;
  delivery_email?: string;
  product_url?: string;
}

// --------------- Validation ---------------

function validate(form: SettingsFormData): ValidationErrors {
  const errors: ValidationErrors = {};
  const keywords = parseKeywords(form.keywords);
  if (keywords.length === 0) {
    errors.keywords = "At least one keyword is required";
  }
  if (form.delivery_email && !isValidEmail(form.delivery_email)) {
    errors.delivery_email = "Invalid email address";
  }
  if (form.product_url && !isValidUrl(form.product_url)) {
    errors.product_url = "Invalid URL format";
  }
  return errors;
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

function parseKeywords(text: string): string[] {
  return text
    .split("\n")
    .map((k) => k.trim())
    .filter((k) => k.length > 0);
}

function parseDomains(text: string): string[] {
  return text
    .split("\n")
    .map((d) => d.trim())
    .filter((d) => d.length > 0);
}

// --------------- Component ---------------

const SettingsForm: React.FC<SettingsFormProps> = ({
  initial,
  saving,
  onSave,
}) => {
  const [form, setForm] = useState<SettingsFormData>(initial);
  const [errors, setErrors] = useState<ValidationErrors>({});

  const updateField = useCallback(
    <K extends keyof SettingsFormData>(
      key: K,
      value: SettingsFormData[K]
    ): void => {
      setForm((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  const togglePlatform = useCallback((platform: string): void => {
    setForm((prev) => {
      const current = prev.platform_preferences;
      const next = current.includes(platform)
        ? current.filter((p) => p !== platform)
        : [...current, platform];
      return { ...prev, platform_preferences: next };
    });
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent): void => {
      e.preventDefault();
      const validationErrors = validate(form);
      setErrors(validationErrors);
      if (Object.keys(validationErrors).length > 0) return;

      onSave({
        product_url: form.product_url,
        one_line_pitch: form.one_line_pitch,
        keywords: parseKeywords(form.keywords),
        tone: form.tone,
        delivery_email: form.delivery_email,
        slack_webhook_url: form.slack_webhook_url,
        delivery_frequency: form.delivery_frequency,
        platform_preferences: form.platform_preferences,
        exclude_domains: parseDomains(form.exclude_domains),
      });
    },
    [form, onSave]
  );

  return (
    <form className="settings-form" onSubmit={handleSubmit}>
      <ProductSection
        form={form}
        errors={errors}
        onUpdate={updateField}
      />
      <ToneSection form={form} onUpdate={updateField} />
      <DeliverySection
        form={form}
        errors={errors}
        onUpdate={updateField}
      />
      <SearchFilterSection
        form={form}
        onUpdate={updateField}
        onTogglePlatform={togglePlatform}
      />
      <button type="submit" className="btn-save" disabled={saving}>
        {saving ? "Saving..." : "Save settings"}
      </button>
    </form>
  );
};

export default SettingsForm;
