/**
 * State management hook for the onboarding wizard (ONBOARD-003).
 *
 * Manages wizard step navigation, form data, validation,
 * auto-save per step, and final completion trigger.
 */

import type React from "react";
import { useCallback, useState } from "react";

import type {
  CompleteRequest,
  CompleteResponse,
} from "../api/onboardingClient";
import {
  completeOnboarding,
  saveOnboardingStep,
} from "../api/onboardingClient";

// --------------- Types ---------------

export type ToneOption =
  | "professional"
  | "casual"
  | "humorous"
  | "technical"
  | "empathetic"
  | "enthusiastic";

export interface WizardFormData {
  product_url: string;
  one_line_pitch: string;
  logo_file: File | null;
  keywords: string;
  tone: ToneOption;
  plan_id: string;
}

export interface WizardValidationErrors {
  product_url?: string;
  one_line_pitch?: string;
  keywords?: string;
}

export interface UseOnboardingReturn {
  currentStep: number;
  formData: WizardFormData;
  errors: WizardValidationErrors;
  saving: boolean;
  completed: boolean;
  completionData: CompleteResponse | null;
  goNext: () => void;
  goBack: () => void;
  skipStep: () => void;
  finish: () => void;
  updateField: <K extends keyof WizardFormData>(
    key: K,
    value: WizardFormData[K]
  ) => void;
}

// --------------- Constants ---------------

const TOTAL_STEPS = 5;

const INITIAL_FORM: WizardFormData = {
  product_url: "",
  one_line_pitch: "",
  logo_file: null,
  keywords: "",
  tone: "professional",
  plan_id: "free",
};

// --------------- Validation ---------------

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

function validateStep(
  step: number,
  form: WizardFormData
): WizardValidationErrors {
  const errors: WizardValidationErrors = {};
  if (step === 2) {
    if (!form.product_url.trim()) {
      errors.product_url = "Product URL is required";
    } else if (!isValidUrl(form.product_url)) {
      errors.product_url = "Please enter a valid URL";
    }
  }
  if (step === 3) {
    const kw = parseKeywords(form.keywords);
    if (kw.length === 0) {
      errors.keywords = "At least one keyword is required";
    }
  }
  return errors;
}

// --------------- Helpers ---------------

function getToken(): string {
  return localStorage.getItem("jwt_token") ?? "";
}

function buildStepData(
  step: number,
  form: WizardFormData
): Record<string, unknown> {
  switch (step) {
    case 2:
      return {
        product_url: form.product_url,
        one_line_pitch: form.one_line_pitch,
      };
    case 3:
      return { keywords: parseKeywords(form.keywords) };
    case 4:
      return { tone: form.tone };
    case 5:
      return { plan_id: form.plan_id };
    default:
      return {};
  }
}

function buildCompletePayload(form: WizardFormData): CompleteRequest {
  return {
    product_url: form.product_url,
    one_line_pitch: form.one_line_pitch,
    keywords: parseKeywords(form.keywords),
    tone: form.tone,
    plan_id: form.plan_id,
  };
}

// --------------- Callback Factories ---------------

function useWizardNavigation(
  currentStep: number,
  formData: WizardFormData,
  setCurrentStep: React.Dispatch<React.SetStateAction<number>>,
  setErrors: React.Dispatch<React.SetStateAction<WizardValidationErrors>>,
  setSaving: React.Dispatch<React.SetStateAction<boolean>>
): { goNext: () => void; goBack: () => void; skipStep: () => void } {
  const autoSaveStep = useCallback(
    (step: number, form: WizardFormData): void => {
      const data = buildStepData(step, form);
      if (Object.keys(data).length === 0) return;
      setSaving(true);
      saveOnboardingStep(getToken(), { step, data })
        .catch(() => {})
        .finally(() => setSaving(false));
    },
    [setSaving]
  );

  const goNext = useCallback((): void => {
    if (currentStep >= TOTAL_STEPS) return;
    const stepErrors = validateStep(currentStep, formData);
    if (Object.keys(stepErrors).length > 0) {
      setErrors(stepErrors);
      return;
    }
    autoSaveStep(currentStep, formData);
    setCurrentStep((prev) => prev + 1);
    setErrors({});
  }, [currentStep, formData, autoSaveStep, setCurrentStep, setErrors]);

  const goBack = useCallback((): void => {
    if (currentStep <= 1) return;
    setCurrentStep((prev) => prev - 1);
    setErrors({});
  }, [currentStep, setCurrentStep, setErrors]);

  const skipStep = useCallback((): void => {
    if (currentStep >= TOTAL_STEPS) return;
    setCurrentStep((prev) => prev + 1);
    setErrors({});
  }, [currentStep, setCurrentStep, setErrors]);

  return { goNext, goBack, skipStep };
}

// --------------- Hook ---------------

function useOnboarding(): UseOnboardingReturn {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<WizardFormData>(INITIAL_FORM);
  const [errors, setErrors] = useState<WizardValidationErrors>({});
  const [saving, setSaving] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [completionData, setCompletionData] =
    useState<CompleteResponse | null>(null);

  const updateField = useCallback(
    <K extends keyof WizardFormData>(
      key: K,
      value: WizardFormData[K]
    ): void => {
      setFormData((prev) => ({ ...prev, [key]: value }));
      setErrors({});
    },
    []
  );

  const { goNext, goBack, skipStep } = useWizardNavigation(
    currentStep, formData, setCurrentStep, setErrors, setSaving
  );

  const finish = useCallback((): void => {
    setSaving(true);
    const payload = buildCompletePayload(formData);
    completeOnboarding(getToken(), payload)
      .then((res) => { setCompleted(true); setCompletionData(res); })
      .catch(() => {})
      .finally(() => setSaving(false));
  }, [formData]);

  return {
    currentStep, formData, errors, saving,
    completed, completionData,
    goNext, goBack, skipStep, finish, updateField,
  };
}

export default useOnboarding;
