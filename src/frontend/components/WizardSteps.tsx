/**
 * Step sub-components for the onboarding wizard (ONBOARD-003).
 *
 * Each step renders its own form fields, explanation, and examples.
 * Split from OnboardingWizard.tsx by domain (one component per step).
 */

import React, { useCallback, useEffect, useState } from "react";

import type { PlanOption } from "./billingApi";
import { fetchPlans, formatPrice } from "./billingApi";
import type {
  ToneOption,
  WizardFormData,
  WizardValidationErrors,
} from "../hooks/useOnboarding";

// --------------- Shared Props ---------------

interface StepProps {
  formData: WizardFormData;
  errors: WizardValidationErrors;
  updateField: <K extends keyof WizardFormData>(
    key: K,
    value: WizardFormData[K]
  ) => void;
}

// --------------- Step 1: Welcome ---------------

export const WelcomeStep: React.FC = () => (
  <div className="step-welcome">
    <h2>Let's set up BuzzReach</h2>
    <p className="step-description">
      We'll walk you through a quick setup to start finding high-relevance
      opportunities for your product. This takes about 2 minutes.
    </p>
    <p className="step-hint">
      You can skip any step and update your settings later.
    </p>
  </div>
);

// --------------- Step 2: Product ---------------

export const ProductStep: React.FC<StepProps> = ({
  formData,
  errors,
  updateField,
}) => (
  <div className="step-product">
    <h2>What do you sell?</h2>
    <p className="step-description">
      Tell us about your product so we can find relevant conversations.
    </p>

    <label htmlFor="wizardProductUrl">Product URL</label>
    <input
      id="wizardProductUrl"
      type="url"
      value={formData.product_url}
      onChange={(e) => updateField("product_url", e.target.value)}
      placeholder="https://yourproduct.com"
    />
    {errors.product_url && (
      <span className="field-error">{errors.product_url}</span>
    )}

    <label htmlFor="wizardPitch">One-line pitch</label>
    <input
      id="wizardPitch"
      type="text"
      value={formData.one_line_pitch}
      onChange={(e) => updateField("one_line_pitch", e.target.value)}
      maxLength={200}
      placeholder="e.g. AI-powered outreach tool for SaaS founders"
    />

    <label htmlFor="wizardLogo">Logo (optional)</label>
    <input
      id="wizardLogo"
      type="file"
      accept="image/*"
      onChange={(e) => {
        const file = e.target.files?.[0] ?? null;
        updateField("logo_file", file);
      }}
    />
  </div>
);

// --------------- Step 3: Target Audience ---------------

export const AudienceStep: React.FC<StepProps> = ({
  formData,
  errors,
  updateField,
}) => (
  <div className="step-audience">
    <h2>Target audience</h2>
    <p className="step-description">
      What keywords do your ideal customers search for? Enter one per line.
    </p>
    <p className="step-example">
      Examples: &quot;best CRM for startups&quot;, &quot;how to automate
      outreach&quot;, &quot;alternatives to Mailchimp&quot;
    </p>

    <label htmlFor="wizardKeywords">Keywords (one per line)</label>
    <textarea
      id="wizardKeywords"
      value={formData.keywords}
      onChange={(e) => updateField("keywords", e.target.value)}
      rows={5}
      placeholder={"best CRM for startups\nhow to automate outreach"}
    />
    {errors.keywords && (
      <span className="field-error">{errors.keywords}</span>
    )}
  </div>
);

// --------------- Step 4: Tone & Style ---------------

const TONE_OPTIONS: { value: ToneOption; label: string; example: string }[] = [
  {
    value: "professional",
    label: "Professional",
    example:
      "Great question. Our platform addresses this by providing automated discovery across multiple channels.",
  },
  {
    value: "casual",
    label: "Casual",
    example:
      "Hey! We actually built something for this — it finds relevant threads automatically so you don't have to hunt.",
  },
  {
    value: "humorous",
    label: "Humorous",
    example:
      "Funny you should ask — we got tired of doom-scrolling Reddit for leads too, so we automated the whole thing.",
  },
  {
    value: "technical",
    label: "Technical",
    example:
      "We use NLP-based relevance scoring across Reddit, HN, and Quora APIs to surface threads matching your ICP.",
  },
  {
    value: "empathetic",
    label: "Empathetic",
    example:
      "I totally understand the frustration. Finding the right conversations is hard — that's exactly why we built BuzzReach.",
  },
  {
    value: "enthusiastic",
    label: "Enthusiastic",
    example:
      "This is EXACTLY the kind of problem we love solving! BuzzReach finds these conversations for you automatically!",
  },
];

export const ToneStep: React.FC<Omit<StepProps, "errors">> = ({
  formData,
  updateField,
}) => {
  const selectedTone = TONE_OPTIONS.find((t) => t.value === formData.tone);

  return (
    <div className="step-tone">
      <h2>Tone & style</h2>
      <p className="step-description">
        How should your auto-generated replies sound? Pick a persona below.
      </p>

      <div className="tone-options">
        {TONE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            data-tone={opt.value}
            className={`tone-btn ${
              formData.tone === opt.value ? "tone-selected" : ""
            }`}
            onClick={() => updateField("tone", opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="tone-examples">
        {selectedTone && (
          <blockquote className="tone-example-text">
            {selectedTone.example}
          </blockquote>
        )}
      </div>
    </div>
  );
};

// --------------- Step 5: Plan ---------------

interface PlanCardItemProps {
  plan: PlanOption;
  isSelected: boolean;
  onSelect: (planId: string) => void;
}

const PlanCardItem: React.FC<PlanCardItemProps> = ({
  plan,
  isSelected,
  onSelect,
}) => (
  <div
    data-plan={plan.plan_id}
    className={`plan-card ${isSelected ? "plan-selected" : ""}`}
    onClick={() => onSelect(plan.plan_id)}
    role="button"
    tabIndex={0}
    onKeyDown={(e) => {
      if (e.key === "Enter" || e.key === " ") onSelect(plan.plan_id);
    }}
  >
    <h3>{plan.display_name}</h3>
    <p className="plan-price">
      {plan.price_cents === 0 ? "Free" : `${formatPrice(plan.price_cents)}/mo`}
    </p>
    <p className="plan-opps">
      {plan.opportunities_per_day >= 10000
        ? "Unlimited"
        : plan.opportunities_per_day}{" "}
      opportunities/day
    </p>
    <ul className="plan-features">
      {plan.features.map((f) => (
        <li key={f}>{f.replace(/_/g, " ")}</li>
      ))}
    </ul>
  </div>
);

export const PlanStep: React.FC<Omit<StepProps, "errors">> = ({
  formData,
  updateField,
}) => {
  const [plans, setPlans] = useState<PlanOption[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPlans = useCallback((): void => {
    setLoading(true);
    fetchPlans()
      .then((res) => setPlans(res.plans))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { loadPlans(); }, [loadPlans]);

  const handleSelect = useCallback(
    (planId: string) => updateField("plan_id", planId),
    [updateField]
  );

  return (
    <div className="step-plan">
      <h2>Choose your plan</h2>
      <p className="step-description">
        Start free or unlock more opportunities with a paid plan.
        You can change this anytime.
      </p>
      {loading && <p>Loading plans...</p>}
      {!loading && (
        <div className="plans-grid">
          {plans.map((plan) => (
            <PlanCardItem
              key={plan.plan_id}
              plan={plan}
              isSelected={formData.plan_id === plan.plan_id}
              onSelect={handleSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};
