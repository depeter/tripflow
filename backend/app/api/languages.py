"""
Languages API - exposes available languages based on actual translations in the database.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel

from app.db.database import get_db

router = APIRouter(prefix="/languages", tags=["languages"])

# Language metadata (native names)
LANGUAGE_METADATA = {
    'en': {'name': 'English', 'nativeName': 'English'},
    'nl': {'name': 'Dutch', 'nativeName': 'Nederlands'},
    'fr': {'name': 'French', 'nativeName': 'Français'},
    'de': {'name': 'German', 'nativeName': 'Deutsch'},
    'es': {'name': 'Spanish', 'nativeName': 'Español'},
    'it': {'name': 'Italian', 'nativeName': 'Italiano'},
    'pt': {'name': 'Portuguese', 'nativeName': 'Português'},
    'pl': {'name': 'Polish', 'nativeName': 'Polski'},
    'cs': {'name': 'Czech', 'nativeName': 'Čeština'},
    'da': {'name': 'Danish', 'nativeName': 'Dansk'},
    'sv': {'name': 'Swedish', 'nativeName': 'Svenska'},
    'no': {'name': 'Norwegian', 'nativeName': 'Norsk'},
    'fi': {'name': 'Finnish', 'nativeName': 'Suomi'},
}


class LanguageInfo(BaseModel):
    """Language information with translation count"""
    code: str
    name: str
    nativeName: str
    translationCount: int


class AvailableLanguagesResponse(BaseModel):
    """Response containing all available languages"""
    languages: List[LanguageInfo]
    totalTranslations: int


@router.get("/available", response_model=AvailableLanguagesResponse)
async def get_available_languages(db: AsyncSession = Depends(get_db)):
    """
    Get list of available languages based on actual translations in the database.

    Returns languages that have at least one translation, ordered by translation count.
    This is useful for:
    - Populating language selector dropdowns
    - Showing which languages have content available
    - Helping users choose their preferred language
    """
    # Query distinct languages from location_translations with counts
    query = text("""
        SELECT
            language_code,
            COUNT(*) as translation_count
        FROM tripflow.location_translations
        WHERE description IS NOT NULL AND description != ''
        GROUP BY language_code
        ORDER BY translation_count DESC
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    languages = []
    total_translations = 0

    for row in rows:
        lang_code = row[0]
        count = row[1]
        total_translations += count

        # Get metadata or create default
        metadata = LANGUAGE_METADATA.get(lang_code, {
            'name': lang_code.upper(),
            'nativeName': lang_code.upper()
        })

        languages.append(LanguageInfo(
            code=lang_code,
            name=metadata['name'],
            nativeName=metadata['nativeName'],
            translationCount=count
        ))

    return AvailableLanguagesResponse(
        languages=languages,
        totalTranslations=total_translations
    )


@router.get("/default")
async def get_default_language():
    """
    Get the default/recommended language.

    Returns English as the default, but could be extended to detect
    from Accept-Language header or user preferences.
    """
    return {
        "code": "en",
        "name": "English",
        "nativeName": "English"
    }
