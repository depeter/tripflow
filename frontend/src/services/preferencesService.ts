/**
 * User preferences service for tracking likes/dislikes and learning user behavior.
 */

import api from './api';

// Session ID management
const SESSION_KEY = 'tripflow_session_id';

function getSessionId(): string {
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
}

export interface PreferenceCreate {
  item_type: 'event' | 'location' | 'plan_type' | 'category' | 'theme';
  item_id?: number;
  item_name?: string;
  action: 'like' | 'dislike' | 'remove' | 'accept' | 'skip';
  context?: Record<string, unknown>;
}

export interface PreferenceSummary {
  liked_categories: string[];
  disliked_categories: string[];
  liked_event_types: string[];
  disliked_event_types: string[];
  removed_item_ids: number[];
  preference_count: number;
}

/**
 * Record a user preference (like, dislike, remove, etc.)
 */
export async function recordPreference(pref: PreferenceCreate): Promise<void> {
  try {
    await api.post('/preferences', pref, {
      headers: {
        'X-Session-Id': getSessionId(),
      },
    });
  } catch (error) {
    console.error('Failed to record preference:', error);
    // Don't throw - preference recording should be non-blocking
  }
}

/**
 * Record removal of an item from a suggested plan
 */
export async function recordRemoval(
  itemType: 'event' | 'location',
  itemId: number,
  itemName: string,
  context?: {
    planId?: string;
    planType?: string;
    category?: string;
    eventType?: string;
    themes?: string[];
  }
): Promise<void> {
  return recordPreference({
    item_type: itemType,
    item_id: itemId,
    item_name: itemName,
    action: 'remove',
    context,
  });
}

/**
 * Record acceptance of a plan
 */
export async function recordPlanAccept(
  planId: string,
  planTitle: string,
  planType: string
): Promise<void> {
  return recordPreference({
    item_type: 'plan_type',
    item_name: planTitle,
    action: 'accept',
    context: {
      plan_id: planId,
      plan_type: planType,
    },
  });
}

/**
 * Record skipping/dismissing a plan
 */
export async function recordPlanSkip(
  planId: string,
  planTitle: string,
  planType: string
): Promise<void> {
  return recordPreference({
    item_type: 'plan_type',
    item_name: planTitle,
    action: 'skip',
    context: {
      plan_id: planId,
      plan_type: planType,
    },
  });
}

/**
 * Get user preference summary for filtering
 */
export async function getPreferenceSummary(): Promise<PreferenceSummary> {
  try {
    const response = await api.get('/preferences/summary', {
      headers: {
        'X-Session-Id': getSessionId(),
      },
    });
    return response.data;
  } catch (error) {
    console.error('Failed to get preference summary:', error);
    return {
      liked_categories: [],
      disliked_categories: [],
      liked_event_types: [],
      disliked_event_types: [],
      removed_item_ids: [],
      preference_count: 0,
    };
  }
}

/**
 * Reset all preferences
 */
export async function resetPreferences(): Promise<void> {
  try {
    await api.delete('/preferences/reset', {
      headers: {
        'X-Session-Id': getSessionId(),
      },
    });
  } catch (error) {
    console.error('Failed to reset preferences:', error);
  }
}
