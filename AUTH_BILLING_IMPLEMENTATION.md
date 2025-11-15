# TripFlow Authentication & Billing Implementation

## Implementation Status

### ✅ Completed (Backend)

1. **Dependencies Installed**
   - stripe==13.2.0
   - authlib==1.6.5
   - itsdangerous==2.2.0

2. **Database Models**
   - `Subscription` - User subscription management
   - `SubscriptionUsage` - Usage tracking (trips per month)
   - `PaymentHistory` - Payment records and invoices

3. **Services**
   - `StripeService` - Complete Stripe integration
     - Checkout session creation
     - Billing portal access
     - Webhook handling (checkout, subscription updates, invoices)
     - Usage limit checking
     - Subscription cancellation
   - `OAuthService` - Google & Microsoft OAuth (partially complete)

4. **API Endpoints**
   - `/api/v1/auth/register` - Email/password registration
   - `/api/v1/auth/login` - Email/password login
   - `/api/v1/auth/me` - Get current user
   - `/api/v1/auth/logout` - Logout
   - `/api/v1/auth/refresh` - Refresh access token
   - `/api/v1/billing/pricing` - Get pricing tiers
   - `/api/v1/billing/checkout` - Create Stripe checkout session
   - `/api/v1/billing/portal` - Access billing portal
   - `/api/v1/billing/subscription` - Get subscription details
   - `/api/v1/billing/subscription/cancel` - Cancel subscription
   - `/api/v1/billing/usage` - Get usage stats
   - `/api/v1/billing/history` - Payment history
   - `/api/v1/billing/webhook` - Stripe webhook handler

5. **Configuration**
   - Stripe keys added to config.py
   - OAuth redirect URIs configured
   - CORS settings ready

### 🚧 Remaining Tasks (Backend)

1. **Update auth.py with OAuth routes** (10 minutes)
2. **Add billing router to main.py** (2 minutes)
3. **Create database migration** (5 minutes)
4. **Update .env with Stripe test keys** (2 minutes)

### 🚧 Frontend Implementation Needed

1. **Authentication Components**
   - Login page
   - Register page
   - OAuth login buttons
   - Protected route wrapper

2. **Billing Components**
   - Pricing page
   - Checkout integration
   - Account/subscription management page
   - Usage display

3. **Integration**
   - Auth context/provider
   - API service updates
   - Route protection

## Subscription Tiers

### Free Tier
- **Price**: $0/month
- **Features**:
  - 3 trips per month
  - Basic route planning
  - Map integration

### Premium Tier
- **Price**: $9.99/month
- **Trial**: 14 days free
- **Features**:
  - Unlimited trips
  - Advanced AI recommendations
  - PDF export
  - Priority support

## Architecture

### Authentication Flow

```
1. User Registration/Login
   ├─ Email/Password → JWT tokens
   ├─ Google OAuth → JWT tokens
   └─ Microsoft OAuth → JWT tokens

2. Protected Routes
   ├─ JWT validation via get_current_user
   └─ Active user check via get_current_active_user

3. Token Refresh
   └─ Refresh token → New access token
```

### Billing Flow

```
1. User Clicks "Upgrade to Premium"
   ↓
2. Frontend calls /api/v1/billing/checkout
   ↓
3. Backend creates Stripe Checkout Session
   ↓
4. User redirected to Stripe Checkout
   ↓
5. User completes payment
   ↓
6. Stripe sends webhook to /api/v1/billing/webhook
   ↓
7. Backend updates Subscription & User models
   ↓
8. User redirected to success_url
   ↓
9. Frontend fetches updated user/subscription data
```

### Usage Limit Enforcement

```
1. User Creates Trip
   ↓
2. Backend checks StripeService.check_usage_limit()
   ├─ Free tier: Max 3 trips/month
   └─ Premium: Unlimited
   ↓
3. If limit exceeded → Return HTTP 402 Payment Required
   ↓
4. Frontend shows upgrade prompt
```

## Stripe Webhooks

The following webhook events are handled:

- `checkout.session.completed` - Subscription started
- `customer.subscription.updated` - Subscription changed
- `customer.subscription.deleted` - Subscription cancelled
- `invoice.paid` - Payment successful
- `invoice.payment_failed` - Payment failed

## Environment Variables Needed

Add to `/home/peter/work/tripflow/backend/.env`:

```env
# Stripe (use test mode keys for development)
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_PUBLISHABLE_KEY=pk_test_51...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PREMIUM_PRICE_ID=price_...

# Google OAuth (optional)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# Microsoft OAuth (optional)
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
```

## Stripe Setup Steps

1. **Create Stripe Account** (if needed)
   - Go to https://dashboard.stripe.com/register

2. **Create Product & Price**
   - Dashboard → Products → Add Product
   - Name: "TripFlow Premium"
   - Price: $9.99/month (recurring)
   - Copy the Price ID (starts with `price_...`)

3. **Get API Keys**
   - Dashboard → Developers → API Keys
   - Copy Publishable Key and Secret Key (test mode)

4. **Setup Webhook**
   - Dashboard → Developers → Webhooks
   - Add endpoint: `https://your-domain.com/api/v1/billing/webhook`
   - Select events: checkout.session.completed, customer.subscription.*, invoice.*
   - Copy webhook secret (starts with `whsec_...`)

## OAuth Setup Steps (Optional)

### Google OAuth

1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8001/api/v1/auth/google/callback`
6. Copy Client ID and Client Secret

### Microsoft OAuth

1. Go to https://portal.azure.com/
2. Navigate to Azure Active Directory → App registrations
3. Create new registration
4. Add redirect URI: `http://localhost:8001/api/v1/auth/microsoft/callback`
5. Create client secret
6. Copy Application (client) ID and client secret

## Testing Checklist

### Authentication
- [ ] Register with email/password
- [ ] Login with email/password
- [ ] Get current user (/api/v1/auth/me)
- [ ] Refresh token
- [ ] Logout
- [ ] Google OAuth login (if configured)
- [ ] Microsoft OAuth login (if configured)

### Billing
- [ ] Get pricing tiers
- [ ] Create checkout session
- [ ] Complete payment with Stripe test card: 4242 4242 4242 4242
- [ ] Verify subscription created in database
- [ ] Check usage limits (free vs premium)
- [ ] Access billing portal
- [ ] View payment history
- [ ] Cancel subscription
- [ ] Verify webhook handling

### Usage Limits
- [ ] Free user: Can create 3 trips
- [ ] Free user: Cannot create 4th trip (402 error)
- [ ] Premium user: Can create unlimited trips
- [ ] Usage resets monthly

## Database Migration

Run this to create the new tables:

```bash
cd /home/peter/work/tripflow/backend
source venv/bin/activate

# Create migration
alembic revision --autogenerate -m "Add subscription and billing tables"

# Apply migration
alembic upgrade head
```

## Deployment to Scraparr

1. Commit changes
2. Update .env on server with production Stripe keys
3. Run database migrations on server
4. Configure Stripe webhook URL to production domain
5. Test OAuth redirect URIs with production domain

## Next Steps

1. Complete remaining backend tasks (OAuth routes, main.py update)
2. Create database migration
3. Build frontend components
4. Test full flow locally
5. Deploy to Scraparr server

## Files Created/Modified

### New Files
- `app/models/subscription.py` - Subscription models
- `app/services/stripe_service.py` - Stripe integration
- `app/services/oauth_service.py` - OAuth service
- `app/api/billing.py` - Billing endpoints

### Modified Files
- `app/core/config.py` - Added Stripe/OAuth settings
- `app/models/__init__.py` - Export subscription models
- `requirements.txt` - Added stripe, authlib, itsdangerous

### To Be Modified
- `app/main.py` - Add billing router
- `app/api/auth.py` - Add OAuth endpoints
- Frontend files (to be created)
