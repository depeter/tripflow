import api, { setTokens, clearTokens } from './api';

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_admin: boolean;
  is_active: boolean;
  subscription_tier: 'free' | 'premium' | 'pro';
  avatar_url: string | null;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

// Login with email/password
export async function login(email: string, password: string): Promise<User> {
  // OAuth2 password flow expects form data
  // Use string format to ensure proper form-urlencoded serialization
  const formData = `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;

  const response = await api.post<LoginResponse>('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  setTokens(response.data.access_token, response.data.refresh_token);

  // Get user info
  return getCurrentUser();
}

// Register new user
export async function register(data: RegisterData): Promise<User> {
  const response = await api.post<User>('/auth/register', data);
  return response.data;
}

// Get current user info
export async function getCurrentUser(): Promise<User> {
  const response = await api.get<User>('/auth/me');
  return response.data;
}

// Logout
export function logout(): void {
  clearTokens();
}

// Get Google OAuth URL
export async function getGoogleAuthUrl(): Promise<string> {
  const response = await api.get<{ url: string }>('/auth/google');
  return response.data.url;
}

// Get Microsoft OAuth URL
export async function getMicrosoftAuthUrl(): Promise<string> {
  const response = await api.get<{ url: string }>('/auth/microsoft');
  return response.data.url;
}

// Check if user is authenticated
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('access_token');
}

// Profile preferences types
export interface ProfilePreferences {
  language?: string;  // Language code from available languages API (e.g., 'en', 'nl', 'fr')
  interests?: Array<{
    id: string;
    name: string;
    icon: string;
    selected: boolean;
  }>;
  travelStyle?: {
    pace: 'slow' | 'moderate' | 'fast';
    environment: Array<'nature' | 'cities' | 'villages' | 'coast'>;
    budget: 'budget' | 'mid-range' | 'comfort';
    accommodation: Array<'camping' | 'wild' | 'stellplatz' | 'hotel'>;
  };
  vehicle?: {
    type: 'campervan' | 'motorhome' | 'caravan' | 'car-tent';
    length_m?: number;
    height_m?: number;
  };
  homeBase?: {
    name: string;
    coordinates: { lat: number; lng: number };
  };
}

// Get user profile preferences
export async function getProfilePreferences(): Promise<ProfilePreferences> {
  const response = await api.get<ProfilePreferences>('/auth/preferences');
  return response.data;
}

// Update user profile preferences
export async function updateProfilePreferences(preferences: Partial<ProfilePreferences>): Promise<ProfilePreferences> {
  const response = await api.put<ProfilePreferences>('/auth/preferences', preferences);
  return response.data;
}
