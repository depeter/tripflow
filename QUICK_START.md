# TripFlow Authentication & Billing - Quick Start

## ✅ Setup Complete!

Your TripFlow authentication and billing system is now configured and ready to use!

### What's Been Set Up

1. ✅ **Stripe Product Created**: TripFlow Premium ($9.99/month with 14-day trial)
2. ✅ **Database Migration Run**: Subscription tables created
3. ✅ **Environment Variables**: Stripe keys configured in `.env` files
4. ✅ **Backend API**: All authentication and billing endpoints ready
5. ✅ **Frontend Services**: Auth and billing services implemented

### Subscription Tiers

- **Free**: $0/month - 3 trips per month
- **Premium**: $9.99/month - Unlimited trips, 14-day free trial

## 🚀 Start the Application

### 1. Start Backend

```bash
cd /home/peter/work/tripflow/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Backend will be available at: http://localhost:8001
API docs at: http://localhost:8001/docs

### 2. Start Frontend

```bash
cd /home/peter/work/tripflow/frontend
npm start
```

Frontend will be available at: http://localhost:3000

## 🧪 Test the System

### Test Authentication

1. **Register a new user**:
   ```bash
   curl -X POST http://localhost:8001/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password123","full_name":"Test User"}'
   ```

2. **Login**:
   ```bash
   curl -X POST http://localhost:8001/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=password123"
   ```

   Copy the `access_token` from the response.

3. **Get current user**:
   ```bash
   curl http://localhost:8001/api/v1/auth/me \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### Test Billing

1. **Get pricing tiers**:
   ```bash
   curl http://localhost:8001/api/v1/billing/pricing
   ```

2. **Check usage** (requires authentication):
   ```bash
   curl http://localhost:8001/api/v1/billing/usage \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

3. **Create checkout session**:
   ```bash
   curl -X POST http://localhost:8001/api/v1/billing/checkout \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "tier": "premium",
       "success_url": "http://localhost:3000/account?success=true",
       "cancel_url": "http://localhost:3000/pricing?canceled=true"
     }'
   ```

   This will return a `url` - open it in your browser to complete checkout.

## ⚠️ One More Step: Webhook Setup

To receive payment notifications from Stripe, you need to set up webhooks:

**Read**: `/home/peter/work/tripflow/STRIPE_WEBHOOK_SETUP.md`

Quick summary:
1. Go to https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://your-domain.com/api/v1/billing/webhook`
3. Select events: `checkout.session.completed`, `customer.subscription.*`, `invoice.*`
4. Copy webhook secret and update `.env`:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_your_actual_secret
   ```
5. Restart backend

## 📝 API Endpoints Available

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login with email/password
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/google` - Google OAuth (if configured)
- `GET /api/v1/auth/microsoft` - Microsoft OAuth (if configured)

### Billing
- `GET /api/v1/billing/pricing` - Get pricing tiers
- `POST /api/v1/billing/checkout` - Create Stripe checkout session
- `POST /api/v1/billing/portal` - Access billing portal
- `GET /api/v1/billing/subscription` - Get subscription details
- `POST /api/v1/billing/subscription/cancel` - Cancel subscription
- `GET /api/v1/billing/usage` - Get usage statistics
- `GET /api/v1/billing/history` - Get payment history

## 🎨 Frontend Components Needed

The backend is 100% complete. For the frontend, you still need to create:

1. **Login Page** - Template provided in `IMPLEMENTATION_COMPLETE.md`
2. **Register Page** - Similar to login page
3. **Pricing Page** - Template provided in `IMPLEMENTATION_COMPLETE.md`
4. **Account Page** - For subscription management
5. **Protected Routes** - Wrapper component to require authentication

All templates and examples are in: `/home/peter/work/tripflow/IMPLEMENTATION_COMPLETE.md`

## 🚀 Deploy to Production

When ready to deploy:

1. **Update CORS** in backend `.env`:
   ```
   BACKEND_CORS_ORIGINS=["https://your-production-domain.com"]
   ```

2. **Update API URL** in frontend `.env`:
   ```
   REACT_APP_API_BASE_URL=https://your-api-domain.com
   ```

3. **Build Frontend**:
   ```bash
   cd frontend
   npm run build
   ```

4. **Deploy to Scraparr**:
   ```bash
   # Deploy using the deployment script
   ./deploy-auth-to-scraparr.sh
   ```

5. **Set up production webhook** in Stripe dashboard

## 📚 Documentation

- **Implementation Guide**: `AUTH_BILLING_IMPLEMENTATION.md`
- **Complete Documentation**: `IMPLEMENTATION_COMPLETE.md`
- **Webhook Setup**: `STRIPE_WEBHOOK_SETUP.md`

## 🔐 Security Notes

- ✅ JWT tokens with automatic refresh
- ✅ Secure password hashing (bcrypt)
- ✅ Stripe webhook signature verification
- ✅ CORS protection
- ⚠️ Make sure to use HTTPS in production
- ⚠️ Keep `.env` files secure (never commit to Git)

## 💳 Test Cards (Stripe Test Mode)

If you switch to test mode for development:
- **Success**: 4242 4242 4242 4242
- **Decline**: 4000 0000 0000 0002
- **3D Secure**: 4000 0025 0000 3155

## ✅ Current Status

| Component | Status |
|-----------|--------|
| Backend Models | ✅ Complete |
| Backend Services | ✅ Complete |
| Backend API | ✅ Complete |
| Database Migration | ✅ Complete |
| Stripe Configuration | ✅ Complete |
| Frontend Services | ✅ Complete |
| Frontend Components | ⚠️ Templates provided |
| Webhook Setup | ⏳ Needs manual setup |

## 🎉 You're Ready!

Start the backend and frontend servers, then test the registration and billing flow!

For questions, check the documentation files or the inline API docs at http://localhost:8001/docs
