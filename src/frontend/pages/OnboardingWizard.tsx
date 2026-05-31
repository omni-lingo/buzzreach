/**
 * First-Run Setup Wizard page (ONBOARD-003).
 *
 * 5-step wizard shown to new users on first login:
 *   1. Welcome — hero message
 *   2. Product — URL, pitch, logo upload
 *   3. Audience — keywords (textarea)
 *   4. Tone — persona selection with examples
 *   5. Plan — free/pro/premium comparison
 *
 * Desktop: side-by-side (wizard left, preview right).
 * Mobile: full-screen vertical steps.
 * Config auto-saved after each step; initial scan triggered on finish.
 */

import React from "react";

import {
  AudienceStep,
  PlanStep,
  ProductStep,
  ToneStep,
  WelcomeStep,
} from "../components/WizardSteps";
import type { UseOnboardingReturn } from "../hooks/useOnboarding";
import useOnboarding from "../hooks/useOnboarding";

// --------------- Constants ---------------

const TOTAL_STEPS = 5;

const STEP_LABELS: string[] = [
  "Welcome",
  "Product",
  "Audience",
  "Tone",
  "Plan",
];

// --------------- Sub-components ---------------

interface ProgressBarProps {
  currentStep: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ currentStep }) => (
  <div className="wizard-progress">
    <span className="wizard-progress-text">
      Step {currentStep} of {TOTAL_STEPS}
    </span>
    <div className="wizard-progress-bar">
      {STEP_LABELS.map((label, idx) => (
        <div
          key={label}
          className={`progress-dot ${
            idx + 1 <= currentStep ? "progress-active" : ""
          }`}
          title={label}
        />
      ))}
    </div>
  </div>
);

interface WizardNavProps {
  currentStep: number;
  saving: boolean;
  onBack: () => void;
  onNext: () => void;
  onSkip: () => void;
  onFinish: () => void;
}

const WizardNav: React.FC<WizardNavProps> = ({
  currentStep,
  saving,
  onBack,
  onNext,
  onSkip,
  onFinish,
}) => {
  const isLastStep = currentStep === TOTAL_STEPS;

  return (
    <div className="wizard-nav">
      {currentStep > 1 && (
        <button type="button" className="btn-back" onClick={onBack} disabled={saving}>
          Back
        </button>
      )}
      {!isLastStep && (
        <>
          <button type="button" className="btn-skip" onClick={onSkip} disabled={saving}>
            Skip
          </button>
          <button type="button" className="btn-next" onClick={onNext} disabled={saving}>
            {saving ? "Saving..." : "Next"}
          </button>
        </>
      )}
      {isLastStep && (
        <button type="button" className="btn-finish" onClick={onFinish} disabled={saving}>
          {saving ? "Finishing..." : "Finish setup"}
        </button>
      )}
    </div>
  );
};

interface CompletionScreenProps {
  scanQueued: boolean;
}

const CompletionScreen: React.FC<CompletionScreenProps> = ({ scanQueued }) => (
  <div className="onboarding-complete">
    <h2>You're all set!</h2>
    <p>Your first opportunities coming soon...</p>
    {scanQueued && (
      <p className="scan-status">
        Initial scan has been queued. Results will appear on your dashboard.
      </p>
    )}
    <a href="/dashboard" className="btn btn-primary">
      Go to Dashboard
    </a>
  </div>
);

// --------------- Preview Panel ---------------

interface PreviewPanelProps {
  currentStep: number;
  productUrl: string;
  pitch: string;
  keywords: string;
  tone: string;
}

const PreviewPanel: React.FC<PreviewPanelProps> = ({
  currentStep,
  productUrl,
  pitch,
  keywords,
  tone,
}) => (
  <aside className="wizard-preview">
    <h3>Preview</h3>
    <dl className="preview-list">
      {currentStep >= 2 && productUrl && (
        <>
          <dt>Product</dt>
          <dd>{productUrl}</dd>
          {pitch && <dd className="preview-pitch">{pitch}</dd>}
        </>
      )}
      {currentStep >= 3 && keywords && (
        <>
          <dt>Keywords</dt>
          <dd>{keywords.split("\n").filter(Boolean).join(", ")}</dd>
        </>
      )}
      {currentStep >= 4 && (
        <>
          <dt>Tone</dt>
          <dd>{tone}</dd>
        </>
      )}
    </dl>
  </aside>
);

// --------------- Step Renderer ---------------

interface StepRendererProps {
  currentStep: number;
  formData: ReturnType<typeof useOnboarding>["formData"];
  errors: ReturnType<typeof useOnboarding>["errors"];
  updateField: ReturnType<typeof useOnboarding>["updateField"];
}

const StepRenderer: React.FC<StepRendererProps> = ({
  currentStep,
  formData,
  errors,
  updateField,
}) => {
  switch (currentStep) {
    case 1:
      return <WelcomeStep />;
    case 2:
      return (
        <ProductStep
          formData={formData}
          errors={errors}
          updateField={updateField}
        />
      );
    case 3:
      return (
        <AudienceStep
          formData={formData}
          errors={errors}
          updateField={updateField}
        />
      );
    case 4:
      return <ToneStep formData={formData} updateField={updateField} />;
    case 5:
      return <PlanStep formData={formData} updateField={updateField} />;
    default:
      return null;
  }
};

// --------------- Wizard Body ---------------

interface WizardBodyProps {
  state: UseOnboardingReturn;
}

const WizardBody: React.FC<WizardBodyProps> = ({ state }) => (
  <div className="wizard-layout">
    <main className="wizard-main">
      <StepRenderer
        currentStep={state.currentStep}
        formData={state.formData}
        errors={state.errors}
        updateField={state.updateField}
      />
      <WizardNav
        currentStep={state.currentStep}
        saving={state.saving}
        onBack={state.goBack}
        onNext={state.goNext}
        onSkip={state.skipStep}
        onFinish={state.finish}
      />
    </main>
    <PreviewPanel
      currentStep={state.currentStep}
      productUrl={state.formData.product_url}
      pitch={state.formData.one_line_pitch}
      keywords={state.formData.keywords}
      tone={state.formData.tone}
    />
  </div>
);

// --------------- Main Component ---------------

const OnboardingWizard: React.FC = () => {
  const state = useOnboarding();

  if (state.completed) {
    return (
      <div className="onboarding-wizard">
        <CompletionScreen scanQueued={state.completionData?.scan_queued ?? false} />
      </div>
    );
  }

  return (
    <div className="onboarding-wizard">
      <ProgressBar currentStep={state.currentStep} />
      <WizardBody state={state} />
    </div>
  );
};

export default OnboardingWizard;
