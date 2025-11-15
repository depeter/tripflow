from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Subscription(Base):
    """
    Subscription model for managing user subscriptions
    """
    __tablename__ = "subscriptions"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('tripflow.users.id'), nullable=False, index=True)

    # Stripe identifiers
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_price_id = Column(String(255), nullable=True)

    # Subscription details
    tier = Column(String(50), nullable=False, default='free')  # free, premium, pro
    status = Column(String(50), nullable=False, default='active')  # active, canceled, past_due, trialing

    # Billing period
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    # Trial
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    # user = relationship("User", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier='{self.tier}', status='{self.status}')>"


class SubscriptionUsage(Base):
    """
    Track subscription usage limits (trips created, API calls, etc.)
    """
    __tablename__ = "subscription_usage"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('tripflow.users.id'), nullable=False, index=True)

    # Usage counters
    trips_created_this_month = Column(Integer, default=0)
    api_calls_this_month = Column(Integer, default=0)

    # Reset tracking
    period_start = Column(DateTime(timezone=True), server_default=func.now())
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SubscriptionUsage(user_id={self.user_id}, trips={self.trips_created_this_month})>"


class PaymentHistory(Base):
    """
    Payment history for invoices and transactions
    """
    __tablename__ = "payment_history"
    __table_args__ = {'schema': 'tripflow'}

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey('tripflow.users.id'), nullable=False, index=True)

    # Stripe identifiers
    stripe_invoice_id = Column(String(255), unique=True, nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)

    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    status = Column(String(50), nullable=False)  # paid, failed, refunded

    # Metadata
    description = Column(String(500), nullable=True)
    invoice_pdf_url = Column(String(500), nullable=True)

    # Timestamps
    payment_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<PaymentHistory(id={self.id}, user_id={self.user_id}, amount={self.amount}, status='{self.status}')>"
