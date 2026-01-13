"""User preferences API for tracking likes/dislikes to learn user behavior."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.db.database import get_db

router = APIRouter(prefix="/preferences", tags=["preferences"])


class PreferenceCreate(BaseModel):
    """Record a user preference action."""
    item_type: str  # 'event', 'location', 'plan_type', 'category'
    item_id: Optional[int] = None
    item_name: Optional[str] = None
    action: str  # 'like', 'dislike', 'remove', 'accept', 'skip'
    context: Optional[Dict[str, Any]] = None  # plan_id, themes, category, etc.


class PreferenceResponse(BaseModel):
    """Response for preference operations."""
    id: int
    item_type: str
    item_id: Optional[int]
    item_name: Optional[str]
    action: str
    created_at: datetime


class UserPreferenceSummary(BaseModel):
    """Summary of user preferences for filtering recommendations."""
    liked_categories: List[str]
    disliked_categories: List[str]
    liked_event_types: List[str]
    disliked_event_types: List[str]
    removed_item_ids: List[int]
    preference_count: int


def get_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """Get or generate session ID for anonymous users."""
    return x_session_id or str(uuid.uuid4())


@router.post("", response_model=PreferenceResponse)
async def record_preference(
    pref: PreferenceCreate,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """
    Record a user preference (like, dislike, remove, accept, skip).

    This data is used to learn user preferences and improve recommendations.
    """
    if pref.action not in ('like', 'dislike', 'remove', 'accept', 'skip'):
        raise HTTPException(status_code=400, detail="Invalid action. Must be: like, dislike, remove, accept, skip")

    if pref.item_type not in ('event', 'location', 'plan_type', 'category', 'theme'):
        raise HTTPException(status_code=400, detail="Invalid item_type. Must be: event, location, plan_type, category, theme")

    # Insert preference
    import json
    context_json = json.dumps(pref.context) if pref.context else None

    query = text("""
        INSERT INTO tripflow.user_preferences
        (session_id, item_type, item_id, item_name, action, context)
        VALUES (:session_id, :item_type, :item_id, :item_name, :action, CAST(:context AS jsonb))
        RETURNING id, item_type, item_id, item_name, action, created_at
    """)

    result = await db.execute(query, {
        'session_id': session_id,
        'item_type': pref.item_type,
        'item_id': pref.item_id,
        'item_name': pref.item_name,
        'action': pref.action,
        'context': context_json
    })
    await db.commit()

    row = result.fetchone()
    return PreferenceResponse(
        id=row.id,
        item_type=row.item_type,
        item_id=row.item_id,
        item_name=row.item_name,
        action=row.action,
        created_at=row.created_at
    )


@router.get("/summary", response_model=UserPreferenceSummary)
async def get_preference_summary(
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """
    Get a summary of user preferences for filtering recommendations.

    Returns categories and event types the user likes/dislikes,
    plus IDs of removed items to exclude from future suggestions.
    """
    # Get liked/disliked categories
    category_query = text("""
        SELECT
            action,
            context->>'category' as category
        FROM tripflow.user_preferences
        WHERE session_id = :session_id
          AND item_type = 'category'
          AND context->>'category' IS NOT NULL
    """)
    category_result = await db.execute(category_query, {'session_id': session_id})
    categories = category_result.fetchall()

    liked_categories = [r.category for r in categories if r.action == 'like']
    disliked_categories = [r.category for r in categories if r.action in ('dislike', 'remove')]

    # Get liked/disliked event types from context
    event_type_query = text("""
        SELECT
            action,
            context->>'event_type' as event_type
        FROM tripflow.user_preferences
        WHERE session_id = :session_id
          AND item_type IN ('event', 'category')
          AND context->>'event_type' IS NOT NULL
    """)
    event_type_result = await db.execute(event_type_query, {'session_id': session_id})
    event_types = event_type_result.fetchall()

    liked_event_types = list(set(r.event_type for r in event_types if r.action == 'like'))
    disliked_event_types = list(set(r.event_type for r in event_types if r.action in ('dislike', 'remove')))

    # Get removed item IDs (events and locations)
    removed_query = text("""
        SELECT DISTINCT item_id
        FROM tripflow.user_preferences
        WHERE session_id = :session_id
          AND action = 'remove'
          AND item_id IS NOT NULL
    """)
    removed_result = await db.execute(removed_query, {'session_id': session_id})
    removed_item_ids = [r.item_id for r in removed_result.fetchall()]

    # Total preference count
    count_query = text("""
        SELECT COUNT(*) as cnt
        FROM tripflow.user_preferences
        WHERE session_id = :session_id
    """)
    count_result = await db.execute(count_query, {'session_id': session_id})
    pref_count = count_result.fetchone().cnt

    return UserPreferenceSummary(
        liked_categories=liked_categories,
        disliked_categories=disliked_categories,
        liked_event_types=liked_event_types,
        disliked_event_types=disliked_event_types,
        removed_item_ids=removed_item_ids,
        preference_count=pref_count
    )


@router.get("/history")
async def get_preference_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Get recent preference history for the user."""
    query = text("""
        SELECT id, item_type, item_id, item_name, action, context, created_at
        FROM tripflow.user_preferences
        WHERE session_id = :session_id
        ORDER BY created_at DESC
        LIMIT :limit
    """)

    result = await db.execute(query, {'session_id': session_id, 'limit': limit})
    rows = result.fetchall()

    return [
        {
            'id': r.id,
            'item_type': r.item_type,
            'item_id': r.item_id,
            'item_name': r.item_name,
            'action': r.action,
            'context': r.context,
            'created_at': r.created_at.isoformat() if r.created_at else None
        }
        for r in rows
    ]


@router.delete("/reset")
async def reset_preferences(
    db: AsyncSession = Depends(get_db),
    session_id: str = Depends(get_session_id)
):
    """Reset all preferences for the current session."""
    query = text("""
        DELETE FROM tripflow.user_preferences
        WHERE session_id = :session_id
    """)

    result = await db.execute(query, {'session_id': session_id})
    await db.commit()

    return {'deleted': result.rowcount, 'message': 'Preferences reset successfully'}
