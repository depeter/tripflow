"""
Billing and subscription API endpoints
"""
import stripe
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription, PaymentHistory, SubscriptionUsage
from app.dependencies.auth import get_current_active_user
from app.services.stripe_service import StripeService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


# ===== Schemas =====

class CheckoutRequest(BaseModel):
    tier: str  # 'premium' or 'pro'
    success_url: str
    cancel_url: str


class BillingPortalRequest(BaseModel):
    return_url: str


class CancelSubscriptionRequest(BaseModel):
    immediate: bool = False


class SubscriptionResponse(BaseModel):
    id: int
    tier: str
    status: str
    current_period_end: Optional[str]
    cancel_at_period_end: bool
    trial_end: Optional[str]

    class Config:
        from_attributes = True


class UsageResponse(BaseModel):
    tier: str
    trips_used: int
    trips_limit: int
    can_create_trip: bool
    period_end: str


class PaymentHistoryResponse(BaseModel):
    id: int
    amount: float
    currency: str
    status: str
    description: Optional[str]
    invoice_pdf_url: Optional[str]
    payment_date: Optional[str]

    class Config:
        from_attributes = True


# ===== Endpoints =====

@router.get("/pricing")
async def get_pricing():
    """
    Get available pricing tiers and features
    """
    return {
        'tiers': StripeService.TIER_PRICES
    }


@router.post("/checkout", status_code=status.HTTP_200_OK)
async def create_checkout_session(
    data: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a Stripe Checkout session for subscription

    - **tier**: Subscription tier ('premium')
    - **success_url**: URL to redirect on successful payment
    - **cancel_url**: URL to redirect if payment cancelled
    """
    try:
        session = await StripeService.create_checkout_session(
            user=current_user,
            tier=data.tier,
            success_url=data.success_url,
            cancel_url=data.cancel_url,
            db=db
        )

        return {
            'session_id': session['session_id'],
            'url': session['url']
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/portal")
async def create_billing_portal_session(
    data: BillingPortalRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a Stripe billing portal session for subscription management

    - **return_url**: URL to return to after managing subscription
    """
    try:
        session = await StripeService.create_billing_portal_session(
            user=current_user,
            return_url=data.return_url
        )

        return {
            'url': session['url']
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Billing portal error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's subscription details
    """
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        # Return free tier default
        return {
            'id': 0,
            'tier': 'free',
            'status': 'active',
            'current_period_end': None,
            'cancel_at_period_end': False,
            'trial_end': None
        }

    return subscription


@router.post("/subscription/cancel")
async def cancel_subscription(
    data: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel current user's subscription

    - **immediate**: If true, cancel immediately. If false, cancel at period end.
    """
    try:
        result = await StripeService.cancel_subscription(
            user=current_user,
            db=db,
            immediate=data.immediate
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Cancel subscription error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's usage statistics and limits
    """
    try:
        usage = await StripeService.check_usage_limit(
            user_id=current_user.id,
            db=db
        )

        return usage

    except Exception as e:
        logger.error(f"Get usage error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch usage statistics"
        )


@router.get("/history")
async def get_payment_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10
):
    """
    Get payment history for current user
    """
    result = await db.execute(
        select(PaymentHistory)
        .where(PaymentHistory.user_id == current_user.id)
        .order_by(PaymentHistory.created_at.desc())
        .limit(limit)
    )
    payments = result.scalars().all()

    return {
        'payments': payments,
        'count': len(payments)
    }


# ===== Stripe Webhooks =====

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature")
):
    """
    Handle Stripe webhook events

    This endpoint processes events from Stripe (payments, subscriptions, etc.)
    """
    try:
        # Get raw body
        payload = await request.body()

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload,
                stripe_signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid webhook payload")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle different event types
        event_type = event['type']
        logger.info(f"Received Stripe webhook: {event_type}")

        if event_type == 'checkout.session.completed':
            # Payment successful
            await StripeService.handle_checkout_completed(event['data']['object'], db)

        elif event_type == 'customer.subscription.updated':
            # Subscription updated
            await StripeService.handle_subscription_updated(event['data']['object'], db)

        elif event_type == 'customer.subscription.deleted':
            # Subscription cancelled
            await StripeService.handle_subscription_updated(event['data']['object'], db)

        elif event_type == 'invoice.paid':
            # Invoice paid successfully
            await StripeService.handle_invoice_paid(event['data']['object'], db)

        elif event_type == 'invoice.payment_failed':
            # Payment failed
            logger.warning(f"Payment failed for invoice: {event['data']['object']['id']}")

        return {'status': 'success'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )
