import api from './api';

export interface LanguageInfo {
  code: string;
  name: string;
  nativeName: string;
  translationCount: number;
}

export interface AvailableLanguagesResponse {
  languages: LanguageInfo[];
  totalTranslations: number;
}

// Cache for available languages (cached for 1 hour)
let cachedLanguages: AvailableLanguagesResponse | null = null;
let cacheTimestamp: number = 0;
const CACHE_DURATION_MS = 60 * 60 * 1000; // 1 hour

/**
 * Get available languages from the API.
 * Results are cached for 1 hour to reduce API calls.
 */
export async function getAvailableLanguages(): Promise<AvailableLanguagesResponse> {
  const now = Date.now();

  // Return cached data if still valid
  if (cachedLanguages && (now - cacheTimestamp) < CACHE_DURATION_MS) {
    return cachedLanguages;
  }

  try {
    const response = await api.get<AvailableLanguagesResponse>('/languages/available');
    cachedLanguages = response.data;
    cacheTimestamp = now;
    return response.data;
  } catch (error) {
    // If API fails and we have cached data, return it even if stale
    if (cachedLanguages) {
      console.warn('Failed to fetch languages, using cached data:', error);
      return cachedLanguages;
    }

    // Return fallback if no cache and API fails
    console.error('Failed to fetch languages and no cache available:', error);
    return {
      languages: [
        { code: 'en', name: 'English', nativeName: 'English', translationCount: 0 }
      ],
      totalTranslations: 0
    };
  }
}

/**
 * Get the default language code.
 */
export async function getDefaultLanguage(): Promise<string> {
  try {
    const response = await api.get<{ code: string }>('/languages/default');
    return response.data.code;
  } catch {
    return 'en'; // Fallback to English
  }
}

/**
 * Clear the language cache (useful after data imports or for testing)
 */
export function clearLanguageCache(): void {
  cachedLanguages = null;
  cacheTimestamp = 0;
}
