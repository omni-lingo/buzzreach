"""Plan definitions for BuzzReach subscription tiers (BILL-002).

Pure data — no logic, no imports beyond contracts.

Plan entitlements:
  free:    $0,   5 opps/day,  email only
  pro:     $49, 100 opps/day, email + Slack, advanced filters
  premium: $149, unlimited (10_000 cap), all features, team members
"""

from contracts.billing.subscription import PlanEntitlements

FREE_PLAN = PlanEntitlements(
    plan_id="free",
    display_name="Free",
    price_cents=0,
    opportunities_per_day=5,
    features=frozenset({"email_delivery"}),
)

PRO_PLAN = PlanEntitlements(
    plan_id="pro",
    display_name="Pro",
    price_cents=4900,
    opportunities_per_day=100,
    features=frozenset({
        "email_delivery",
        "slack_delivery",
        "advanced_filters",
    }),
)

PREMIUM_PLAN = PlanEntitlements(
    plan_id="premium",
    display_name="Premium",
    price_cents=14900,
    opportunities_per_day=10_000,
    features=frozenset({
        "email_delivery",
        "slack_delivery",
        "advanced_filters",
        "team_members",
        "priority_support",
        "custom_branding",
    }),
)

PLANS: dict[str, PlanEntitlements] = {
    "free": FREE_PLAN,
    "pro": PRO_PLAN,
    "premium": PREMIUM_PLAN,
}

PLAN_IDS: frozenset[str] = frozenset(PLANS.keys())
