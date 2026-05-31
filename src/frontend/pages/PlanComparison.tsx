/**
 * Plan comparison and upgrade/downgrade page (BILL-004).
 *
 * Shows side-by-side plan comparison (free/pro/premium), current plan
 * highlighted, upgrade to Stripe checkout, downgrade with proration,
 * and cancel subscription with retention offer.
 */

import React, { useCallback, useEffect, useState } from "react";

import type { CancelResponse, PlanOption } from "../components/billingApi";
import {
  confirmCancel,
  fetchPlans,
  formatPrice,
  requestCancel,
  requestDowngrade,
  requestUpgrade,
} from "../components/billingApi";

const PlanComparison: React.FC = () => {
  const [plans, setPlans] = useState<PlanOption[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const loadPlans = useCallback((): void => {
    setLoading(true);
    setError(null);
    fetchPlans()
      .then((res) => setPlans(res.plans))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadPlans();
  }, [loadPlans]);

  return (
    <div className="plan-comparison">
      <h1>Choose Your Plan</h1>
      <a href="/billing" className="back-link">Back to Billing</a>

      {error && <div className="error-banner">{error}</div>}
      {actionMsg && <div className="success-banner">{actionMsg}</div>}

      {loading && <p>Loading plans...</p>}

      {!loading && (
        <div className="plans-grid">
          {plans.map((plan) => (
            <PlanCard
              key={plan.plan_id}
              plan={plan}
              plans={plans}
              onAction={setActionMsg}
              onError={setError}
              onReload={loadPlans}
            />
          ))}
        </div>
      )}

      <CancelSection
        plans={plans}
        onAction={setActionMsg}
        onError={setError}
        onReload={loadPlans}
      />
    </div>
  );
};

interface PlanCardProps {
  plan: PlanOption;
  plans: PlanOption[];
  onAction: (msg: string) => void;
  onError: (msg: string) => void;
  onReload: () => void;
}

const PlanCard: React.FC<PlanCardProps> = ({
  plan,
  plans,
  onAction,
  onError,
  onReload,
}) => {
  const currentPlan = plans.find((p) => p.is_current);
  const isUpgrade = currentPlan
    ? plan.price_cents > currentPlan.price_cents
    : false;
  const isDowngrade = currentPlan
    ? plan.price_cents < currentPlan.price_cents && !plan.is_current
    : false;

  const handleUpgrade = (): void => {
    requestUpgrade(plan.plan_id)
      .then((res) => {
        window.location.href = res.checkout_url;
      })
      .catch((e: Error) => onError(e.message));
  };

  const handleDowngrade = (): void => {
    requestDowngrade(plan.plan_id)
      .then((res) => {
        onAction(res.message);
        onReload();
      })
      .catch((e: Error) => onError(e.message));
  };

  return (
    <div className={`plan-card ${plan.is_current ? "plan-current" : ""}`}>
      <h2>{plan.display_name}</h2>
      <p className="plan-price">
        {plan.price_cents === 0 ? "Free" : `${formatPrice(plan.price_cents)}/mo`}
      </p>
      <p className="plan-opps">
        {plan.opportunities_per_day >= 10000
          ? "Unlimited"
          : plan.opportunities_per_day}{" "}
        opps/day
      </p>
      <ul className="plan-features">
        {plan.features.map((f) => (
          <li key={f}>{f.replace(/_/g, " ")}</li>
        ))}
      </ul>
      {plan.is_current && <span className="current-badge">Current Plan</span>}
      {isUpgrade && (
        <button className="btn btn-primary" onClick={handleUpgrade}>
          Upgrade
        </button>
      )}
      {isDowngrade && (
        <div>
          <button className="btn btn-secondary" onClick={handleDowngrade}>
            Downgrade
          </button>
          <p className="proration-note">
            Proration will be applied to your next invoice.
          </p>
        </div>
      )}
    </div>
  );
};

interface CancelSectionProps {
  plans: PlanOption[];
  onAction: (msg: string) => void;
  onError: (msg: string) => void;
  onReload: () => void;
}

const CancelSection: React.FC<CancelSectionProps> = ({
  plans,
  onAction,
  onError,
  onReload,
}) => {
  const [reason, setReason] = useState("");
  const [retention, setRetention] = useState<CancelResponse | null>(null);

  const currentPlan = plans.find((p) => p.is_current);
  if (!currentPlan || currentPlan.plan_id === "free") return null;

  const handleCancel = (): void => {
    if (!reason.trim()) {
      onError("Please provide a reason for cancellation.");
      return;
    }
    requestCancel(reason)
      .then((res) => {
        if (res.retention_offered) {
          setRetention(res);
        } else {
          onAction(res.message);
          onReload();
        }
      })
      .catch((e: Error) => onError(e.message));
  };

  const handleConfirmCancel = (): void => {
    confirmCancel()
      .then((res) => {
        setRetention(null);
        onAction(res.message);
        onReload();
      })
      .catch((e: Error) => onError(e.message));
  };

  return (
    <div className="cancel-section">
      <h2>Cancel Subscription</h2>
      {retention ? (
        <RetentionOffer
          message={retention.message}
          onStay={() => setRetention(null)}
          onConfirm={handleConfirmCancel}
        />
      ) : (
        <div className="cancel-form">
          <label>
            Reason for cancellation
            <select value={reason} onChange={(e) => setReason(e.target.value)}>
              <option value="">Select a reason...</option>
              <option value="too_expensive">Too expensive</option>
              <option value="not_using">Not using enough</option>
              <option value="missing_features">Missing features</option>
              <option value="switching">Switching to competitor</option>
              <option value="other">Other</option>
            </select>
          </label>
          <button className="btn btn-danger" onClick={handleCancel}>
            Cancel Subscription
          </button>
        </div>
      )}
    </div>
  );
};

interface RetentionOfferProps {
  message: string;
  onStay: () => void;
  onConfirm: () => void;
}

const RetentionOffer: React.FC<RetentionOfferProps> = ({
  message,
  onStay,
  onConfirm,
}) => (
  <div className="retention-offer">
    <p className="retention-message">{message}</p>
    <div className="retention-actions">
      <button className="btn btn-primary" onClick={onStay}>
        Stay on my plan
      </button>
      <button className="btn btn-danger" onClick={onConfirm}>
        Cancel anyway
      </button>
    </div>
  </div>
);

export default PlanComparison;
