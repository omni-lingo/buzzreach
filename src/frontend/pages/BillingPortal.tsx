/**
 * Billing portal page (BILL-004).
 *
 * Shows: current plan, usage progress bar, billing cycle dates,
 * payment method (last 4 digits only), and navigation to
 * InvoiceHistory and PlanComparison pages.
 */

import React, { useCallback, useEffect, useState } from "react";

import type { BillingOverview } from "../components/billingApi";
import {
  fetchBillingOverview,
  formatDate,
  formatPrice,
} from "../components/billingApi";

const BillingPortal: React.FC = () => {
  const [overview, setOverview] = useState<BillingOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadOverview = useCallback((): void => {
    setLoading(true);
    setError(null);
    fetchBillingOverview()
      .then(setOverview)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  if (loading) {
    return <div className="billing-portal"><p>Loading billing info...</p></div>;
  }

  if (error) {
    return (
      <div className="billing-portal">
        <div className="error-banner">{error}</div>
        <button onClick={loadOverview}>Retry</button>
      </div>
    );
  }

  if (!overview) {
    return <div className="billing-portal"><p>No billing data available.</p></div>;
  }

  return (
    <div className="billing-portal">
      <h1>Billing &amp; Subscription</h1>
      <CurrentPlanCard overview={overview} />
      <UsageBar overview={overview} />
      <BillingCycle overview={overview} />
      <PaymentMethod overview={overview} />
      <PortalActions />
    </div>
  );
};

interface CardProps {
  overview: BillingOverview;
}

const CurrentPlanCard: React.FC<CardProps> = ({ overview }) => (
  <div className="plan-card">
    <h2>Current Plan</h2>
    <div className="plan-details">
      <span className="plan-name">{overview.plan_name}</span>
      <span className="plan-price">
        {overview.price_cents === 0 ? "Free" : `${formatPrice(overview.price_cents)}/mo`}
      </span>
      <span className={`plan-status status-${overview.status}`}>
        {overview.status}
      </span>
    </div>
    <FeatureList features={overview.features} />
  </div>
);

const FeatureList: React.FC<{ features: string[] }> = ({ features }) => (
  <ul className="feature-list">
    {features.map((f) => (
      <li key={f}>{f.replace(/_/g, " ")}</li>
    ))}
  </ul>
);

const UsageBar: React.FC<CardProps> = ({ overview }) => {
  const pct = Math.min(overview.usage_percentage, 100);
  const barClass = pct >= 90 ? "usage-bar-critical" : "usage-bar-normal";

  return (
    <div className="usage-section">
      <h2>Usage This Month</h2>
      <div className="usage-bar-bg">
        <div className={`usage-bar-fill ${barClass}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="usage-text">
        {overview.usage_current} / {overview.usage_limit} opportunities today
        ({pct.toFixed(1)}%)
      </p>
    </div>
  );
};

const BillingCycle: React.FC<CardProps> = ({ overview }) => (
  <div className="billing-cycle">
    <h2>Billing Cycle</h2>
    <table className="cycle-table">
      <tbody>
        <tr>
          <td>Period Start</td>
          <td>{overview.period_start ? formatDate(overview.period_start) : "N/A"}</td>
        </tr>
        <tr>
          <td>Renewal Date</td>
          <td>{overview.period_end ? formatDate(overview.period_end) : "N/A"}</td>
        </tr>
        <tr>
          <td>Auto-Renew</td>
          <td>{overview.auto_renew ? "Yes" : "No"}</td>
        </tr>
      </tbody>
    </table>
  </div>
);

const PaymentMethod: React.FC<CardProps> = ({ overview }) => (
  <div className="payment-method">
    <h2>Payment Method</h2>
    {overview.card_last4 ? (
      <p>
        {overview.card_brand?.toUpperCase()} ending in {overview.card_last4}
      </p>
    ) : (
      <p>No payment method on file.</p>
    )}
  </div>
);

const PortalActions: React.FC = () => (
  <div className="portal-actions">
    <a href="/billing/invoices" className="btn btn-secondary">
      View Invoices
    </a>
    <a href="/billing/plans" className="btn btn-primary">
      Upgrade / Downgrade
    </a>
  </div>
);

export default BillingPortal;
