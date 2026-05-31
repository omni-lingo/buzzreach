"""Request/response schemas for the Billing Portal API (BILL-004).

Defines Pydantic models for billing overview, invoices, plan comparison,
upgrade/downgrade/cancel flows. These shapes are contracts consumed by
the frontend portal pages.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class BillingOverviewResponse(BaseModel):
    """Current plan, usage bar, billing cycle, and payment method."""

    plan_id: str = Field(description="Current plan identifier")
    plan_name: str = Field(description="Display name of the plan")
    price_cents: int = Field(description="Monthly price in cents")
    status: str = Field(description="Subscription status")
    usage_current: int = Field(description="Opportunities used today")
    usage_limit: int = Field(description="Daily opportunity limit")
    usage_percentage: float = Field(
        description="Usage as percentage (0-100)"
    )
    period_start: datetime | None = Field(
        default=None, description="Billing period start"
    )
    period_end: datetime | None = Field(
        default=None, description="Billing period end / renewal date"
    )
    auto_renew: bool = Field(description="Auto-renew enabled")
    card_last4: str | None = Field(
        default=None, description="Last 4 digits of payment card"
    )
    card_brand: str | None = Field(
        default=None, description="Card brand (visa, mastercard, etc.)"
    )
    features: list[str] = Field(
        default_factory=list, description="Enabled features"
    )


class InvoiceResponse(BaseModel):
    """Single invoice record."""

    invoice_id: str = Field(description="Stripe invoice ID")
    date: datetime = Field(description="Invoice creation date")
    amount_cents: int = Field(description="Amount paid in cents")
    currency: str = Field(description="Currency code (usd)")
    status: str = Field(description="Invoice status")
    pdf_url: str | None = Field(
        default=None, description="Download URL for invoice PDF"
    )
    description: str | None = Field(
        default=None, description="Invoice description"
    )


class InvoiceListResponse(BaseModel):
    """List of invoices with count."""

    invoices: list[InvoiceResponse] = Field(default_factory=list)
    total: int = Field(description="Total number of invoices returned")


class PlanOptionResponse(BaseModel):
    """Plan details for the comparison page."""

    plan_id: str = Field(description="Plan identifier")
    display_name: str = Field(description="Plan display name")
    price_cents: int = Field(description="Monthly price in cents")
    opportunities_per_day: int = Field(
        description="Daily opportunity limit"
    )
    features: list[str] = Field(
        default_factory=list, description="Included features"
    )
    is_current: bool = Field(
        description="Whether this is the user's current plan"
    )


class PlanComparisonResponse(BaseModel):
    """All available plans for comparison."""

    plans: list[PlanOptionResponse] = Field(default_factory=list)


class UpgradeRequest(BaseModel):
    """Request to upgrade to a new plan."""

    plan_id: str = Field(description="Target plan identifier")


class UpgradeResponse(BaseModel):
    """Upgrade response with Stripe checkout URL."""

    checkout_url: str = Field(description="Stripe checkout session URL")


class DowngradeRequest(BaseModel):
    """Request to downgrade to a lower plan."""

    plan_id: str = Field(description="Target plan identifier")


class DowngradeResponse(BaseModel):
    """Downgrade confirmation."""

    message: str = Field(description="Confirmation message")
    new_plan_id: str = Field(description="New plan after downgrade")


class CancelRequest(BaseModel):
    """Request to cancel subscription with reason."""

    reason: str = Field(description="Cancellation reason from survey")


class CancelResponse(BaseModel):
    """Cancel response with optional retention offer."""

    retention_offered: bool = Field(
        description="Whether a retention offer was shown"
    )
    message: str = Field(description="Status message")


class CancelConfirmResponse(BaseModel):
    """Confirmation that cancellation was finalized."""

    message: str = Field(description="Confirmation message")
