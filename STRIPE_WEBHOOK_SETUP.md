# Stripe Webhook Setup for TripFlow

## ✅ What's Already Done

1. ✅ Stripe account configured
2. ✅ TripFlow Premium product created ($9.99/month with 14-day trial)
3. ✅ Stripe keys added to `.env` files
4. ✅ Backend webhook handler implemented at `/api/v1/billing/webhook`

## 🔧 What You Need to Do

### Setup Webhook Endpoint in Stripe Dashboard

1. **Go to Stripe Dashboard**
   - Login at: https://dashboard.stripe.com/
   - Navigate to: **Developers** → **Webhooks**

2. **Add Endpoint**
   - Click **"Add endpoint"** button

3. **Configure Endpoint**
   ```
   Endpoint URL: https://your-production-domain.com/api/v1/billing/webhook

   OR for local testing with Stripe CLI:
   http://localhost:8001/api/v1/billing/webhook
   ```

4. **Select Events to Listen To**
   - Click **"Select events"**
   - Add these events:
     - ✅ `checkout.session.completed` - When customer completes checkout
     - ✅ `customer.subscription.created` - When subscription starts
     - ✅ `customer.subscription.updated` - When subscription changes
     - ✅ `customer.subscription.deleted` - When subscription cancels
     - ✅ `invoice.paid` - When invoice is paid successfully
     - ✅ `invoice.payment_failed` - When payment fails

5. **Add Endpoint**
   - Click **"Add endpoint"** to save

6. **Get Webhook Secret**
   - After creating, click on your new endpoint
   - Click **"Reveal"** under "Signing secret"
   - Copy the secret (starts with `whsec_...`)

7. **Update .env File**
   - Open `/home/peter/work/tripflow/backend/.env`
   - Replace this line:
     ```
     STRIPE_WEBHOOK_SECRET=whsec_REPLACE_THIS_AFTER_WEBHOOK_SETUP
     ```
   - With your actual webhook secret:
     ```
     STRIPE_WEBHOOK_SECRET=whsec_your_actual_secret_here
     ```

8. **Restart Backend**
   ```bash
   # If running locally
   # Press Ctrl+C and restart with:
   cd /home/peter/work/tripflow/backend
   source venv/bin/activate
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

   # If running on server with Docker
   docker restart tripflow-backend
   ```

## 🧪 Testing Webhooks Locally (Optional)

If you want to test webhooks on your local machine before deploying:

### Option 1: Stripe CLI (Recommended)

1. **Install Stripe CLI**
   ```bash
   # On Debian/Ubuntu
   wget https://github.com/stripe/stripe-cli/releases/download/v1.19.4/stripe_1.19.4_linux_amd64.deb
   sudo dpkg -i stripe_1.19.4_linux_amd64.deb
   ```

2. **Login to Stripe**
   ```bash
   stripe login
   ```

3. **Forward Webhooks to Local Server**
   ```bash
   stripe listen --forward-to localhost:8001/api/v1/billing/webhook
   ```

4. **Copy the Webhook Secret**
   - The CLI will display a webhook secret (starts with `whsec_`)
   - Add it to your `.env` file temporarily for testing

5. **Trigger Test Events**
   ```bash
   # Test checkout completed
   stripe trigger checkout.session.completed

   # Test subscription updated
   stripe trigger customer.subscription.updated
   ```

### Option 2: ngrok (Alternative)

1. **Install ngrok**
   ```bash
   wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
   tar xvzf ngrok-v3-stable-linux-amd64.tgz
   ./ngrok http 8001
   ```

2. **Use ngrok URL**
   - ngrok will give you a public URL like `https://abc123.ngrok.io`
   - Add webhook endpoint in Stripe dashboard: `https://abc123.ngrok.io/api/v1/billing/webhook`

## ✅ Verification

After setup, test that webhooks work:

1. **Create Test Subscription**
   - Go to your app
   - Click "Upgrade to Premium"
   - Complete checkout (use test card if in test mode)

2. **Check Webhook Logs**
   - Stripe Dashboard → Developers → Webhooks
   - Click on your endpoint
   - View recent webhook deliveries
   - Should see `checkout.session.completed` with ✅ success

3. **Check Backend Logs**
   ```bash
   # Should see log entries like:
   INFO - Received Stripe webhook: checkout.session.completed
   INFO - Subscription created/updated for user 123
   ```

4. **Verify Database**
   ```bash
   psql -U tripflow -d tripflow -c "SELECT * FROM tripflow.subscriptions LIMIT 5;"
   ```

## 🚨 Important Notes

- **Security**: Never commit webhook secrets to Git
- **Production vs Test**: Use different webhook endpoints for test mode and live mode
- **Webhook Signature**: The backend verifies webhook signatures automatically
- **Retries**: Stripe retries failed webhooks automatically
- **Monitoring**: Check Stripe dashboard regularly for failed webhooks

## 🔗 Resources

- Stripe Webhooks Docs: https://stripe.com/docs/webhooks
- Stripe CLI Docs: https://stripe.com/docs/stripe-cli
- Testing Webhooks: https://stripe.com/docs/webhooks/test

## Your Current Configuration

```
Product: TripFlow Premium
Price: $9.99/month
Trial: 14 days
Price ID: price_1STg0VCv9PIyRes9sFxG6kYO

Publishable Key: pk_live_51STfoKCv9PIyRes9EWYyz0mUjDZgpCs1afQ0QdLyr8m7BS51qY8RVKGGsUS6lVMjzF3lDXC1Wu63qRgXjajG2BW100gnKZOJ4j
Secret Key: sk_live_51STfoK... (in .env file)
Webhook Secret: ⚠️ NEEDS TO BE ADDED AFTER WEBHOOK SETUP
```

## Next Step

**👉 Set up the webhook endpoint in Stripe Dashboard and update the `STRIPE_WEBHOOK_SECRET` in your `.env` file!**
