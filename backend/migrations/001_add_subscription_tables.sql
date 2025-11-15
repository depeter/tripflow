-- Migration: Add subscription and billing tables
-- Date: 2025-11-15
-- Description: Add tables for subscription management, usage tracking, and payment history

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS tripflow.subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES tripflow.users(id) ON DELETE CASCADE,

    -- Stripe identifiers
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    stripe_price_id VARCHAR(255),

    -- Subscription details
    tier VARCHAR(50) NOT NULL DEFAULT 'free',
    status VARCHAR(50) NOT NULL DEFAULT 'active',

    -- Billing period
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP WITH TIME ZONE,

    -- Trial
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user_id ON tripflow.subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe_subscription_id ON tripflow.subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_tier ON tripflow.subscriptions(tier);
CREATE INDEX idx_subscriptions_status ON tripflow.subscriptions(status);

-- Create subscription_usage table
CREATE TABLE IF NOT EXISTS tripflow.subscription_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES tripflow.users(id) ON DELETE CASCADE,

    -- Usage counters
    trips_created_this_month INTEGER DEFAULT 0,
    api_calls_this_month INTEGER DEFAULT 0,

    -- Reset tracking
    period_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    period_end TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscription_usage_user_id ON tripflow.subscription_usage(user_id);
CREATE INDEX idx_subscription_usage_period ON tripflow.subscription_usage(period_start, period_end);

-- Create payment_history table
CREATE TABLE IF NOT EXISTS tripflow.payment_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES tripflow.users(id) ON DELETE CASCADE,

    -- Stripe identifiers
    stripe_invoice_id VARCHAR(255) UNIQUE,
    stripe_payment_intent_id VARCHAR(255),

    -- Payment details
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL,

    -- Metadata
    description VARCHAR(500),
    invoice_pdf_url VARCHAR(500),

    -- Timestamps
    payment_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_payment_history_user_id ON tripflow.payment_history(user_id);
CREATE INDEX idx_payment_history_stripe_invoice_id ON tripflow.payment_history(stripe_invoice_id);
CREATE INDEX idx_payment_history_status ON tripflow.payment_history(status);
CREATE INDEX idx_payment_history_payment_date ON tripflow.payment_history(payment_date DESC);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON tripflow.subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscription_usage_updated_at
    BEFORE UPDATE ON tripflow.subscription_usage
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create default subscription records for existing users
INSERT INTO tripflow.subscriptions (user_id, tier, status)
SELECT id, 'free', 'active'
FROM tripflow.users
WHERE id NOT IN (SELECT user_id FROM tripflow.subscriptions)
ON CONFLICT DO NOTHING;

-- Create default usage records for existing users
INSERT INTO tripflow.subscription_usage (user_id, trips_created_this_month, period_start, period_end)
SELECT id, 0, NOW(), NOW() + INTERVAL '30 days'
FROM tripflow.users
WHERE id NOT IN (SELECT user_id FROM tripflow.subscription_usage)
ON CONFLICT DO NOTHING;

COMMENT ON TABLE tripflow.subscriptions IS 'User subscription management';
COMMENT ON TABLE tripflow.subscription_usage IS 'Track usage limits for subscription tiers';
COMMENT ON TABLE tripflow.payment_history IS 'Payment and invoice history';
