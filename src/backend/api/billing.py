"""Billing portal API endpoints (BILL-004).

GET  /api/v1/billing/current  — current plan + usage overview
GET  /api/v1/billing/invoices — invoice history
GET  /api/v1/billing/plans    — plan comparison options
POST /api/v1/billing/upgrade  — initiate plan upgrade
POST /api/v1/billing/downgrade — initiate plan downgrade
POST /api/v1/billing/cancel   — cancel subscription (with survey)
POST /api/v1/billing/cancel/confirm — confirm after retention offer

All endpoints require JWT auth. No API keys exposed to frontend.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from contracts.auth.user import UserData
from src.backend.api.auth_deps import get_current_user
from src.backend.api.billing_schemas import (
    BillingOverviewResponse,
    CancelConfirmResponse,
    CancelRequest,
    CancelResponse,
    DowngradeRequest,
    DowngradeResponse,
    InvoiceListResponse,
    InvoiceResponse,
    PlanComparisonResponse,
    PlanOptionResponse,
    UpgradeRequest,
    UpgradeResponse,
)
from src.backend.db.session import get_session
from src.backend.errors import AppError
from src.backend.services.billing_portal_service import BillingPortalService
from src.backend.settings import Settings

log = logging.getLogger("buzzreach.api.billing")

router = APIRouter(
    prefix="/api/v1/billing",
    tags=["billing"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUser = Annotated[UserData, Depends(get_current_user)]


def _get_billing_service(session: SessionDep) -> BillingPortalService:
    """Build a BillingPortalService from current settings."""
    settings = Settings()
    return BillingPortalService(session, settings.stripe_api_key)


@router.get("/current", response_model=BillingOverviewResponse)
def get_current_billing(
    user: CurrentUser,
    service: Annotated[
        BillingPortalService, Depends(_get_billing_service)
    ],
) -> BillingOverviewResponse:
    """Return current plan, usage, and payment info."""
    overview = service.get_overview(user.id)
    log.info(
        "Billing overview served",
        extra={"user_id": str(user.id), "plan_id": overview.plan_id},
    )
    return BillingOverviewResponse(
        plan_id=overview.plan_id,
        plan_name=overview.plan_name,
        price_cents=overview.price_cents,
        status=overview.status,
        usage_current=overview.usage_current,
        usage_limit=overview.usage_limit,
        usage_percentage=overview.usage_percentage,
        period_start=overview.period_start,
        period_end=overview.period_end,
        auto_renew=overview.auto_renew,
        card_last4=overview.card_last4,
        card_brand=overview.card_brand,
        features=overview.features,
    )


@router.get("/invoices", response_model=InvoiceListResponse)
def get_invoices(
    user: CurrentUser,
    service: Annotated[
        BillingPortalService, Depends(_get_billing_service)
    ],
    limit: int = Query(
        default=20, ge=1, le=100, description="Max invoices"
    ),
) -> InvoiceListResponse:
    """Return invoice history from Stripe."""
    items = service.get_invoices(user.id, limit=limit)
    log.info(
        "Invoices served",
        extra={"user_id": str(user.id), "count": len(items)},
    )
    invoices = [
        InvoiceResponse(
            invoice_id=i.invoice_id,
            date=i.date,
            amount_cents=i.amount_cents,
            currency=i.currency,
            status=i.status,
            pdf_url=i.pdf_url,
            description=i.description,
        )
        for i in items
    ]
    return InvoiceListResponse(invoices=invoices, total=len(invoices))


@router.get("/plans", response_model=PlanComparisonResponse)
def get_plans(
    user: CurrentUser,
    service: Annotated[
        BillingPortalService, Depends(_get_billing_service)
    ],
) -> PlanComparisonResponse:
    """Return all plans for comparison."""
    options = service.get_plan_options(user.id)
    log.info(
        "Plan comparison served",
        extra={"user_id": str(user.id)},
    )
    plans = [
        PlanOptionResponse(
            plan_id=o.plan_id,
            display_name=o.display_name,
            price_cents=o.price_cents,
            opportunities_per_day=o.opportunities_per_day,
            features=o.features,
            is_current=o.is_current,
        )
        for o in options
    ]
    return PlanComparisonResponse(plans=plans)


@router.post("/upgrade", response_model=UpgradeResponse)
def upgrade_plan(
    user: CurrentUser,
    body: UpgradeRequest,
    service: Annotated[
        BillingPortalService, Depends(_get_billing_service)
    ],
) -> UpgradeResponse:
    """Initiate plan upgrade via Stripe checkout."""
    try:
        url = service.initiate_upgrade(user.id, body.plan_id)
    except AppError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": exc.code, "message": exc.message},
        ) from None
    log.info(
        "Upgrade initiated",
        extra={"user_id": str(user.id), "plan_id": body.plan_id},
    )
    return UpgradeResponse(checkout_url=url)


@router.post("/downgrade", response_model=DowngradeResponse)
def downgrade_plan(
    user: CurrentUser,
    body: DowngradeRequest,
    service: Annotated[
        BillingPortalService, Depends(_get_billing_service)
    ],
) -> DowngradeResponse:
    """Downgrade to a lower plan with proration."""
    try:
        service.initiate_downgrade(user.id, body.plan_id)
    except AppError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": exc.code, "message": exc.message},
        ) from None
    log.info(
        "Downgrade initiated",
        extra={"user_id": str(user.id), "plan_id": body.plan_id},
    )
    return DowngradeResponse(
        message=f"Downgraded to {body.plan_id}",
        new_plan_id=body.plan_id,
    )


@router.post("/cancel", response_model=CancelResponse)
def cancel_subscription(
    user: CurrentUser,
    body: CancelRequest,
    service: Annotated[
        BillingPortalService, Depends(_get_billing_service)
    ],
) -> CancelResponse:
    """Cancel subscription with survey reason."""
    try:
        retention = service.cancel_subscription(user.id, body.reason)
    except AppError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": exc.code, "message": exc.message},
        ) from None

    if retention:
        msg = "How about 1 month free before you go?"
    else:
        msg = "Subscription canceled. You are now on the free plan."

    log.info(
        "Cancel requested",
        extra={
            "user_id": str(user.id),
            "retention_offered": retention,
        },
    )
    return CancelResponse(retention_offered=retention, message=msg)


@router.post(
    "/cancel/confirm", response_model=CancelConfirmResponse
)
def confirm_cancel(
    user: CurrentUser,
    service: Annotated[
        BillingPortalService, Depends(_get_billing_service)
    ],
) -> CancelConfirmResponse:
    """Confirm cancellation after declining retention offer."""
    try:
        service.confirm_cancel(user.id)
    except AppError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": exc.code, "message": exc.message},
        ) from None
    log.info(
        "Cancel confirmed",
        extra={"user_id": str(user.id)},
    )
    return CancelConfirmResponse(
        message="Subscription canceled. You are now on the free plan."
    )
