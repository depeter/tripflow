import api from './api';

export const authService = {
  /**
   * Register a new user
   */
  async register(email, password, fullName) {
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  /**
   * Login with email/password
   */
  async login(email, password) {
    const formData = new FormData();
    formData.append('username', email); // OAuth2 format uses 'username'
    formData.append('password', password);

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  /**
   * Get current user information
   */
  async getCurrentUser() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  /**
   * Logout (client-side token removal)
   */
  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  /**
   * Refresh access token
   */
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken,
    });

    const { access_token, refresh_token } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    return access_token;
  },

  /**
   * Initiate Google OAuth
   */
  async loginWithGoogle(redirectUri) {
    const response = await api.get('/auth/google', {
      params: { redirect_uri: redirectUri },
    });
    return response.data.auth_url;
  },

  /**
   * Handle Google OAuth callback
   */
  async handleGoogleCallback(code, redirectUri) {
    const response = await api.get('/auth/google/callback', {
      params: {
        code,
        redirect_uri: redirectUri,
      },
    });
    return response.data;
  },

  /**
   * Initiate Microsoft OAuth
   */
  async loginWithMicrosoft(redirectUri) {
    const response = await api.get('/auth/microsoft', {
      params: { redirect_uri: redirectUri },
    });
    return response.data.auth_url;
  },

  /**
   * Handle Microsoft OAuth callback
   */
  async handleMicrosoftCallback(code, redirectUri) {
    const response = await api.get('/auth/microsoft/callback', {
      params: {
        code,
        redirect_uri: redirectUri,
      },
    });
    return response.data;
  },
};
