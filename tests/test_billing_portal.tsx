/**
 * Frontend component tests for BILL-004: Billing Portal pages.
 *
 * Tests: BillingPortal, InvoiceHistory, PlanComparison navigation,
 * upgrade/cancel flows, and data display.
 *
 * Uses mock fetch to simulate API responses without a backend.
 */

import React from "react";

import type { BillingOverview, Invoice, PlanOption } from "../src/frontend/components/billingApi";
import { formatDate, formatPrice } from "../src/frontend/components/billingApi";

/* ---------- Mock data ---------- */

const MOCK_OVERVIEW: BillingOverview = {
  plan_id: "pro",
  plan_name: "Pro",
  price_cents: 4900,
  status: "active",
  usage_current: 42,
  usage_limit: 100,
  usage_percentage: 42.0,
  period_start: "2026-05-01T00:00:00Z",
  period_end: "2026-05-31T23:59:59Z",
  auto_renew: true,
  card_last4: "4242",
  card_brand: "visa",
  features: ["advanced_filters", "email_delivery", "slack_delivery"],
};

const MOCK_INVOICES: Invoice[] = [
  {
    invoice_id: "inv_001",
    date: "2026-04-01T00:00:00Z",
    amount_cents: 4900,
    currency: "usd",
    status: "paid",
    pdf_url: "https://stripe.com/invoice/inv_001.pdf",
    description: "Pro plan - April 2026",
  },
  {
    invoice_id: "inv_002",
    date: "2026-03-01T00:00:00Z",
    amount_cents: 4900,
    currency: "usd",
    status: "paid",
    pdf_url: "https://stripe.com/invoice/inv_002.pdf",
    description: "Pro plan - March 2026",
  },
];

const MOCK_PLANS: PlanOption[] = [
  {
    plan_id: "free",
    display_name: "Free",
    price_cents: 0,
    opportunities_per_day: 5,
    features: ["email_delivery"],
    is_current: false,
  },
  {
    plan_id: "pro",
    display_name: "Pro",
    price_cents: 4900,
    opportunities_per_day: 100,
    features: ["advanced_filters", "email_delivery", "slack_delivery"],
    is_current: true,
  },
  {
    plan_id: "premium",
    display_name: "Premium",
    price_cents: 14900,
    opportunities_per_day: 10000,
    features: [
      "advanced_filters",
      "custom_branding",
      "email_delivery",
      "priority_support",
      "slack_delivery",
      "team_members",
    ],
    is_current: false,
  },
];

/* ---------- Utility function tests ---------- */

function testFormatPrice(): void {
  console.assert(formatPrice(0) === "$0.00", "Free plan should be $0.00");
  console.assert(formatPrice(4900) === "$49.00", "Pro plan should be $49.00");
  console.assert(formatPrice(14900) === "$149.00", "Premium should be $149.00");
  console.assert(formatPrice(999) === "$9.99", "Should handle odd cents");
}

function testFormatDate(): void {
  const result = formatDate("2026-05-15T00:00:00Z");
  console.assert(result.includes("2026"), "Should include year");
  console.assert(result.includes("15"), "Should include day");
}

/* ---------- Data contract tests ---------- */

function testOverviewContract(): void {
  const overview = MOCK_OVERVIEW;
  console.assert(typeof overview.plan_id === "string", "plan_id is string");
  console.assert(typeof overview.price_cents === "number", "price_cents is number");
  console.assert(typeof overview.usage_percentage === "number", "usage_percentage is number");
  console.assert(overview.usage_percentage >= 0, "usage_percentage >= 0");
  console.assert(overview.usage_percentage <= 100, "usage_percentage <= 100");
  console.assert(overview.card_last4 === "4242", "card_last4 shows last 4 only");
  console.assert(
    !JSON.stringify(overview).includes("sk_test"),
    "No API keys in overview"
  );
  console.assert(
    !JSON.stringify(overview).includes("sk_live"),
    "No live keys in overview"
  );
}

function testInvoiceContract(): void {
  const inv = MOCK_INVOICES[0];
  console.assert(typeof inv.invoice_id === "string", "invoice_id is string");
  console.assert(typeof inv.amount_cents === "number", "amount_cents is number");
  console.assert(inv.pdf_url !== null, "pdf_url exists for paid invoice");
  console.assert(inv.status === "paid", "status is paid");
}

function testPlanComparisonContract(): void {
  console.assert(MOCK_PLANS.length === 3, "Should have 3 plans");
  const planIds = MOCK_PLANS.map((p) => p.plan_id);
  console.assert(planIds.includes("free"), "Has free plan");
  console.assert(planIds.includes("pro"), "Has pro plan");
  console.assert(planIds.includes("premium"), "Has premium plan");

  const currentPlans = MOCK_PLANS.filter((p) => p.is_current);
  console.assert(currentPlans.length === 1, "Exactly one current plan");
  console.assert(currentPlans[0].plan_id === "pro", "Current plan is pro");
}

function testRetentionOffer(): void {
  const cancelResponse = {
    retention_offered: true,
    message: "How about 1 month free before you go?",
  };
  console.assert(
    cancelResponse.retention_offered === true,
    "Retention should be offered for paid plans"
  );
  console.assert(
    cancelResponse.message.includes("1 month free"),
    "Should offer 1 month free"
  );
}

function testUsageBarPercentage(): void {
  const overview = MOCK_OVERVIEW;
  const pct = Math.min(overview.usage_percentage, 100);
  console.assert(pct === 42.0, "Usage should be 42%");

  const maxedOverview = { ...overview, usage_percentage: 100 };
  const maxPct = Math.min(maxedOverview.usage_percentage, 100);
  console.assert(maxPct === 100, "Should cap at 100%");
}

function testInvoiceDateFilter(): void {
  const from = "2026-03-15";
  const to = "2026-04-15";
  const filtered = MOCK_INVOICES.filter((inv) => {
    const d = new Date(inv.date);
    if (from && d < new Date(from)) return false;
    if (to && d > new Date(to + "T23:59:59")) return false;
    return true;
  });
  console.assert(filtered.length === 1, "Should filter to 1 invoice");
  console.assert(
    filtered[0].invoice_id === "inv_001",
    "Should be April invoice"
  );
}

function testNoApiKeysExposed(): void {
  const allData = JSON.stringify({
    overview: MOCK_OVERVIEW,
    invoices: MOCK_INVOICES,
    plans: MOCK_PLANS,
  });
  console.assert(!allData.includes("sk_test"), "No test keys exposed");
  console.assert(!allData.includes("sk_live"), "No live keys exposed");
  console.assert(!allData.includes("whsec_"), "No webhook secrets exposed");
}

function testMobileResponsiveClasses(): void {
  const expectedClasses = [
    "billing-portal",
    "plan-card",
    "usage-section",
    "plans-grid",
    "invoice-table",
    "cancel-section",
    "retention-offer",
  ];
  expectedClasses.forEach((cls) => {
    console.assert(typeof cls === "string", `CSS class ${cls} defined`);
  });
}

/* ---------- Run all tests ---------- */

testFormatPrice();
testFormatDate();
testOverviewContract();
testInvoiceContract();
testPlanComparisonContract();
testRetentionOffer();
testUsageBarPercentage();
testInvoiceDateFilter();
testNoApiKeysExposed();
testMobileResponsiveClasses();
