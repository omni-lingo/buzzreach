/**
 * Form section sub-components for SettingsForm (FE-001).
 *
 * Split from SettingsForm.tsx by domain: product config, tone,
 * delivery preferences, and search filters.
 */

import React from "react";

import type { SettingsFormData, ValidationErrors } from "./SettingsForm";

// --------------- Constants ---------------

const TONE_OPTIONS = [
  "professional",
  "casual",
  "humorous",
  "technical",
  "empathetic",
  "enthusiastic",
] as const;

const FREQUENCY_OPTIONS = ["hourly", "daily", "weekly"] as const;

const PLATFORM_OPTIONS = [
  "reddit",
  "quora",
  "hackernews",
  "stackoverflow",
  "twitter",
] as const;

// --------------- Shared Props ---------------

export interface SectionProps {
  form: SettingsFormData;
  errors?: ValidationErrors;
  onUpdate: <K extends keyof SettingsFormData>(
    key: K,
    value: SettingsFormData[K]
  ) => void;
}

// --------------- Product Section ---------------

export const ProductSection: React.FC<SectionProps> = ({
  form,
  errors,
  onUpdate,
}) => (
  <fieldset className="settings-section">
    <legend>Product Configuration</legend>
    <label htmlFor="productUrl">Product URL</label>
    <input
      id="productUrl"
      type="url"
      value={form.product_url}
      onChange={(e) => onUpdate("product_url", e.target.value)}
      placeholder="https://yourproduct.com"
    />
    {errors?.product_url && (
      <span className="field-error">{errors.product_url}</span>
    )}

    <label htmlFor="oneLinePitch">One-line pitch</label>
    <input
      id="oneLinePitch"
      type="text"
      value={form.one_line_pitch}
      onChange={(e) => onUpdate("one_line_pitch", e.target.value)}
      maxLength={200}
      placeholder="Describe your product in one line"
    />

    <label htmlFor="keywords">Keywords (one per line)</label>
    <textarea
      id="keywords"
      value={form.keywords}
      onChange={(e) => onUpdate("keywords", e.target.value)}
      rows={4}
      placeholder={"react\ntypescript\nnextjs"}
    />
    {errors?.keywords && (
      <span className="field-error">{errors.keywords}</span>
    )}
  </fieldset>
);

// --------------- Tone Section ---------------

export const ToneSection: React.FC<
  Omit<SectionProps, "errors">
> = ({ form, onUpdate }) => (
  <fieldset className="settings-section">
    <legend>Tone / Persona</legend>
    <label htmlFor="tone">Reply tone</label>
    <select
      id="tone"
      value={form.tone}
      onChange={(e) => onUpdate("tone", e.target.value)}
    >
      {TONE_OPTIONS.map((t) => (
        <option key={t} value={t}>
          {t.charAt(0).toUpperCase() + t.slice(1)}
        </option>
      ))}
    </select>
  </fieldset>
);

// --------------- Delivery Section ---------------

export const DeliverySection: React.FC<SectionProps> = ({
  form,
  errors,
  onUpdate,
}) => (
  <fieldset className="settings-section">
    <legend>Delivery Preferences</legend>
    <label htmlFor="deliveryEmail">Email address</label>
    <input
      id="deliveryEmail"
      type="email"
      value={form.delivery_email}
      onChange={(e) => onUpdate("delivery_email", e.target.value)}
      placeholder="you@company.com"
    />
    {errors?.delivery_email && (
      <span className="field-error">{errors.delivery_email}</span>
    )}

    <label htmlFor="slackWebhook">Slack webhook URL</label>
    <input
      id="slackWebhook"
      type="url"
      value={form.slack_webhook_url}
      onChange={(e) => onUpdate("slack_webhook_url", e.target.value)}
      placeholder="https://hooks.slack.com/services/..."
    />

    <label htmlFor="deliveryFrequency">Frequency</label>
    <select
      id="deliveryFrequency"
      value={form.delivery_frequency}
      onChange={(e) =>
        onUpdate(
          "delivery_frequency",
          e.target.value as "hourly" | "daily" | "weekly"
        )
      }
    >
      {FREQUENCY_OPTIONS.map((f) => (
        <option key={f} value={f}>
          {f.charAt(0).toUpperCase() + f.slice(1)}
        </option>
      ))}
    </select>
  </fieldset>
);

// --------------- Search Filter Section ---------------

interface SearchFilterProps extends Omit<SectionProps, "errors"> {
  onTogglePlatform: (platform: string) => void;
}

export const SearchFilterSection: React.FC<SearchFilterProps> = ({
  form,
  onUpdate,
  onTogglePlatform,
}) => (
  <fieldset className="settings-section">
    <legend>Search Filters</legend>
    <label>Platform preferences</label>
    <div className="platform-checkboxes">
      {PLATFORM_OPTIONS.map((p) => (
        <label key={p} className="checkbox-label">
          <input
            type="checkbox"
            checked={form.platform_preferences.includes(p)}
            onChange={() => onTogglePlatform(p)}
          />
          {p}
        </label>
      ))}
    </div>

    <label htmlFor="excludeDomains">
      Exclude domains (one per line)
    </label>
    <textarea
      id="excludeDomains"
      value={form.exclude_domains}
      onChange={(e) => onUpdate("exclude_domains", e.target.value)}
      rows={3}
      placeholder={"spam.com\njunk.org"}
    />
  </fieldset>
);
