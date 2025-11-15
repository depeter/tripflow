"""
Stripe payment processing service
"""
import stripe
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.models.subscription import Subscription, PaymentHistory, SubscriptionUsage
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for handling Stripe payment operations"""

    # Subscription tier pricing
    TIER_PRICES = {
        'free': {
            'price': 0,
            'stripe_price_id': None,
            'trips_per_month': 3,
            'features': ['3 trips per month', 'Basic route planning', 'Map integration']
        },
        'premium': {
            'price': 9.99,
            'stripe_price_id': settings.STRIPE_PREMIUM_PRICE_ID,
            'trips_per_month': -1,  # Unlimited
            'features': ['Unlimited trips', 'Advanced recommendations', 'PDF export', 'Priority support']
        },
    }

    @staticmethod
    async def create_customer(user: User, db: AsyncSession) -> str:
        """Create a Stripe customer for a user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={'user_id': user.id}
            )

            # Update user with Stripe customer ID
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(stripe_customer_id=customer.id)
            )
            await db.commit()

            return customer.id
        except Exception as e:
            logger.error(f"Error creating Stripe customer: {e}")
            raise

    @staticmethod
    async def create_checkout_session(
        user: User,
        tier: str,
        success_url: str,
        cancel_url: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for subscription
        """
        try:
            # Ensure user has Stripe customer ID
            if not user.stripe_customer_id:
                customer_id = await StripeService.create_customer(user, db)
            else:
                customer_id = user.stripe_customer_id

            tier_info = StripeService.TIER_PRICES.get(tier)
            if not tier_info or not tier_info['stripe_price_id']:
                raise ValueError(f"Invalid tier: {tier}")

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': tier_info['stripe_price_id'],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    'trial_period_days': 14,  # 14-day trial
                    'metadata': {
                        'user_id': user.id,
                        'tier': tier,
                    }
                },
                metadata={
                    'user_id': user.id,
                    'tier': tier,
                }
            )

            return {
                'session_id': session.id,
                'url': session.url
            }

        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            raise

    @staticmethod
    async def create_billing_portal_session(
        user: User,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe billing portal session for subscription management
        """
        try:
            if not user.stripe_customer_id:
                raise ValueError("User does not have a Stripe customer ID")

            session = stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url,
            )

            return {
                'url': session.url
            }

        except Exception as e:
            logger.error(f"Error creating billing portal session: {e}")
            raise

    @staticmethod
    async def handle_checkout_completed(
        session: Dict[str, Any],
        db: AsyncSession
    ):
        """
        Handle successful checkout completion
        Called by webhook
        """
        try:
            user_id = int(session['metadata']['user_id'])
            tier = session['metadata']['tier']
            subscription_id = session['subscription']

            # Fetch subscription details from Stripe
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)

            # Create or update subscription record
            result = await db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            subscription = result.scalar_one_or_none()

            if subscription:
                # Update existing
                subscription.stripe_subscription_id = stripe_subscription.id
                subscription.stripe_customer_id = stripe_subscription.customer
                subscription.stripe_price_id = stripe_subscription['items']['data'][0]['price']['id']
                subscription.tier = tier
                subscription.status = stripe_subscription.status
                subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
                subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                subscription.trial_start = datetime.fromtimestamp(stripe_subscription.trial_start) if stripe_subscription.trial_start else None
                subscription.trial_end = datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None
            else:
                # Create new
                subscription = Subscription(
                    user_id=user_id,
                    stripe_subscription_id=stripe_subscription.id,
                    stripe_customer_id=stripe_subscription.customer,
                    stripe_price_id=stripe_subscription['items']['data'][0]['price']['id'],
                    tier=tier,
                    status=stripe_subscription.status,
                    current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                    current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                    trial_start=datetime.fromtimestamp(stripe_subscription.trial_start) if stripe_subscription.trial_start else None,
                    trial_end=datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None,
                )
                db.add(subscription)

            # Update user subscription tier
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(subscription_tier=tier)
            )

            # Create or reset usage tracking
            usage_result = await db.execute(
                select(SubscriptionUsage).where(SubscriptionUsage.user_id == user_id)
            )
            usage = usage_result.scalar_one_or_none()

            if not usage:
                usage = SubscriptionUsage(
                    user_id=user_id,
                    trips_created_this_month=0,
                    api_calls_this_month=0,
                    period_start=datetime.utcnow(),
                    period_end=datetime.utcnow() + timedelta(days=30)
                )
                db.add(usage)

            await db.commit()
            logger.info(f"Subscription created/updated for user {user_id}")

        except Exception as e:
            logger.error(f"Error handling checkout completed: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def handle_subscription_updated(
        subscription_data: Dict[str, Any],
        db: AsyncSession
    ):
        """
        Handle subscription update events
        """
        try:
            subscription_id = subscription_data['id']

            result = await db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
            )
            subscription = result.scalar_one_or_none()

            if subscription:
                subscription.status = subscription_data['status']
                subscription.current_period_start = datetime.fromtimestamp(subscription_data['current_period_start'])
                subscription.current_period_end = datetime.fromtimestamp(subscription_data['current_period_end'])
                subscription.cancel_at_period_end = subscription_data.get('cancel_at_period_end', False)

                if subscription_data.get('canceled_at'):
                    subscription.canceled_at = datetime.fromtimestamp(subscription_data['canceled_at'])

                # Update user tier if subscription cancelled
                if subscription.status in ['canceled', 'unpaid']:
                    await db.execute(
                        update(User)
                        .where(User.id == subscription.user_id)
                        .values(subscription_tier='free')
                    )

                await db.commit()
                logger.info(f"Subscription updated: {subscription_id}")

        except Exception as e:
            logger.error(f"Error handling subscription updated: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def handle_invoice_paid(
        invoice_data: Dict[str, Any],
        db: AsyncSession
    ):
        """
        Handle successful invoice payment
        """
        try:
            customer_id = invoice_data['customer']

            # Find user by Stripe customer ID
            result = await db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()

            if user:
                payment = PaymentHistory(
                    user_id=user.id,
                    stripe_invoice_id=invoice_data['id'],
                    stripe_payment_intent_id=invoice_data.get('payment_intent'),
                    amount=invoice_data['amount_paid'] / 100,  # Convert from cents
                    currency=invoice_data['currency'].upper(),
                    status='paid',
                    description=invoice_data.get('description', 'Subscription payment'),
                    invoice_pdf_url=invoice_data.get('invoice_pdf'),
                    payment_date=datetime.fromtimestamp(invoice_data['status_transitions']['paid_at'])
                )
                db.add(payment)
                await db.commit()
                logger.info(f"Payment recorded for user {user.id}")

        except Exception as e:
            logger.error(f"Error handling invoice paid: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def cancel_subscription(
        user: User,
        db: AsyncSession,
        immediate: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel a user's subscription
        """
        try:
            result = await db.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
            subscription = result.scalar_one_or_none()

            if not subscription or not subscription.stripe_subscription_id:
                raise ValueError("No active subscription found")

            if immediate:
                # Cancel immediately
                deleted_subscription = stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = 'canceled'
                subscription.canceled_at = datetime.utcnow()

                # Downgrade to free tier
                await db.execute(
                    update(User)
                    .where(User.id == user.id)
                    .values(subscription_tier='free')
                )
            else:
                # Cancel at period end
                updated_subscription = stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True

            await db.commit()

            return {
                'status': subscription.status,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'current_period_end': subscription.current_period_end
            }

        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def check_usage_limit(user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """
        Check if user has exceeded their usage limits
        """
        try:
            # Get user's subscription
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                raise ValueError("User not found")

            tier = user.subscription_tier
            tier_info = StripeService.TIER_PRICES.get(tier, StripeService.TIER_PRICES['free'])

            # Get usage
            usage_result = await db.execute(
                select(SubscriptionUsage).where(SubscriptionUsage.user_id == user_id)
            )
            usage = usage_result.scalar_one_or_none()

            if not usage:
                # Create usage record if doesn't exist
                usage = SubscriptionUsage(
                    user_id=user_id,
                    trips_created_this_month=0,
                    api_calls_this_month=0,
                    period_start=datetime.utcnow(),
                    period_end=datetime.utcnow() + timedelta(days=30)
                )
                db.add(usage)
                await db.commit()

            # Check if period needs reset
            if datetime.utcnow() > usage.period_end:
                usage.trips_created_this_month = 0
                usage.api_calls_this_month = 0
                usage.period_start = datetime.utcnow()
                usage.period_end = datetime.utcnow() + timedelta(days=30)
                await db.commit()

            trips_limit = tier_info['trips_per_month']
            can_create = trips_limit == -1 or usage.trips_created_this_month < trips_limit

            return {
                'tier': tier,
                'trips_used': usage.trips_created_this_month,
                'trips_limit': trips_limit,
                'can_create_trip': can_create,
                'period_end': usage.period_end
            }

        except Exception as e:
            logger.error(f"Error checking usage limit: {e}")
            raise

    @staticmethod
    async def increment_trip_count(user_id: int, db: AsyncSession):
        """Increment the trip counter for a user"""
        try:
            result = await db.execute(
                select(SubscriptionUsage).where(SubscriptionUsage.user_id == user_id)
            )
            usage = result.scalar_one_or_none()

            if usage:
                usage.trips_created_this_month += 1
                await db.commit()

        except Exception as e:
            logger.error(f"Error incrementing trip count: {e}")
            await db.rollback()
            raise
