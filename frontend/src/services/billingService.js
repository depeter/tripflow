import api from './api';

export const billingService = {
  /**
   * Get available pricing tiers
   */
  async getPricing() {
    const response = await api.get('/billing/pricing');
    return response.data;
  },

  /**
   * Create Stripe checkout session
   */
  async createCheckoutSession(tier, successUrl, cancelUrl) {
    const response = await api.post('/billing/checkout', {
      tier,
      success_url: successUrl,
      cancel_url: cancelUrl,
    });
    return response.data;
  },

  /**
   * Get billing portal URL
   */
  async getBillingPortal(returnUrl) {
    const response = await api.post('/billing/portal', {
      return_url: returnUrl,
    });
    return response.data;
  },

  /**
   * Get current subscription
   */
  async getSubscription() {
    const response = await api.get('/billing/subscription');
    return response.data;
  },

  /**
   * Cancel subscription
   */
  async cancelSubscription(immediate = false) {
    const response = await api.post('/billing/subscription/cancel', {
      immediate,
    });
    return response.data;
  },

  /**
   * Get usage statistics
   */
  async getUsage() {
    const response = await api.get('/billing/usage');
    return response.data;
  },

  /**
   * Get payment history
   */
  async getPaymentHistory(limit = 10) {
    const response = await api.get('/billing/history', {
      params: { limit },
    });
    return response.data;
  },
};
