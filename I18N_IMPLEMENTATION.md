# TripFlow I18n Implementation

## Overview

Static internationalization has been successfully implemented for TripFlow using **react-i18next**. The application now supports multiple languages with easy switching via a header dropdown.

## What's Been Implemented

### 1. Dependencies Installed
```bash
npm install react-i18next i18next i18next-browser-languagedetector --legacy-peer-deps
```

### 2. Project Structure

```
frontend/src/
├── i18n/
│   ├── config.js                # i18n configuration
│   └── locales/
│       ├── en/
│       │   ├── common.json      # Common UI strings (header, buttons, labels)
│       │   └── wizard.json      # Trip wizard steps (step1-step6)
│       └── nl/
│           ├── common.json      # Dutch translations
│           └── wizard.json      # Dutch translations
```

### 3. Current Language Support

- **English (en)** 🇬🇧 - Default language
- **Dutch (nl)** 🇳🇱 - Full translation

### 4. Converted Components

#### ✅ Step1_TripType.jsx
- Hero section (title, subtitle, stats)
- Multi-Day Trip card (title, description, features)
- Day Trip card (title, description, features)

#### ✅ Header.jsx
- Navigation links (Discovery, Plan Trip, My Trips)
- Auth buttons (Sign In, Get Started)
- User menu items (Profile, Settings, Sign Out)
- **Language switcher dropdown** with flag icons

### 5. Features

- **Automatic language detection** from browser settings
- **Persistent language preference** saved in localStorage
- **Namespace organization** (common, wizard) for better code organization
- **Pluralization support** using i18next interpolation
- **Debug mode** in development for easier translation testing
- **Elegant language switcher** with:
  - Flag emojis for visual recognition
  - Dropdown menu with checkmark for active language
  - Smooth animations and hover effects

## How to Use

### For Developers

#### Basic Usage in Components
```javascript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation(['wizard']); // Load wizard namespace

  return (
    <div>
      <h1>{t('step1.title')}</h1>
      <p>{t('step1.subtitle')}</p>
    </div>
  );
}
```

#### With Interpolation
```javascript
// Translation file
{
  "stats": {
    "locations": "{{count}}+ locations"
  }
}

// Component
<span>{t('step1.stats.locations', { count: 1000 })}</span>
// Output: "1000+ locations"
```

#### With Pluralization
```javascript
// Translation file
{
  "days": "{{count}} day",
  "days_plural": "{{count}} days"
}

// Component
<span>{t('step2.days', { count: tripData.duration_days })}</span>
// Output: "1 day" or "3 days" (automatically pluralized)
```

#### Change Language Programmatically
```javascript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { i18n } = useTranslation();

  const switchLanguage = (lang) => {
    i18n.changeLanguage(lang);
  };

  return <button onClick={() => switchLanguage('nl')}>Nederlands</button>;
}
```

### For Users

1. **Language switcher is in the header** (top right)
2. **Click the flag icon** to open language menu
3. **Select your preferred language**
4. **Language preference is saved** and persists across sessions

## Translation File Structure

### Common Namespace (`common.json`)
- `app.*` - App name, tagline
- `header.*` - Navigation, user menu
- `buttons.*` - Reusable button labels
- `labels.*` - Loading, error, success messages
- `language.*` - Language names

### Wizard Namespace (`wizard.json`)
- `step1.*` - Trip type selection
- `step2.*` - Route planning
- `step3.*` - Interests & preferences
- `step4.*` - Location recommendations
- `step5.*` - Route customization
- `step6.*` - Review & finalize

## Next Steps - Converting More Components

### To Convert a Component:

1. **Import the hook:**
```javascript
import { useTranslation } from 'react-i18next';
```

2. **Use the hook in your component:**
```javascript
const { t } = useTranslation(['wizard']); // or ['common']
```

3. **Replace hardcoded strings:**
```javascript
// Before
<h2>Duration</h2>

// After
<h2>{t('step2.duration')}</h2>
```

4. **Add translations to JSON files:**
```json
// en/wizard.json
{
  "step2": {
    "duration": "Duration"
  }
}

// nl/wizard.json
{
  "step2": {
    "duration": "Duur"
  }
}
```

### Components Still to Convert:

- `Step2_Duration.jsx` - Route planning fields
- `Step3_Preferences.jsx` - Interest tags
- `Step4_Recommendations.jsx` - Location cards, filters
- `Step5_CustomizeRoute.jsx` - Drag-and-drop instructions
- `Step6_ReviewFinalize.jsx` - Trip summary, action buttons
- `Login.jsx` - Login form labels
- `Register.jsx` - Registration form
- `LocationCard.jsx` - Location details
- `MapView.jsx` - Map controls (if any)

## Adding New Languages

To add a new language (e.g., French):

1. **Create translation directories:**
```bash
mkdir -p src/i18n/locales/fr
```

2. **Create translation files:**
```bash
touch src/i18n/locales/fr/common.json
touch src/i18n/locales/fr/wizard.json
```

3. **Copy from English and translate:**
```bash
cp src/i18n/locales/en/common.json src/i18n/locales/fr/common.json
# Edit fr/common.json and translate all values
```

4. **Update i18n config:**
```javascript
// src/i18n/config.js
import frCommon from './locales/fr/common.json';
import frWizard from './locales/fr/wizard.json';

const resources = {
  en: { common: enCommon, wizard: enWizard },
  nl: { common: nlCommon, wizard: nlWizard },
  fr: { common: frCommon, wizard: frWizard }, // Add this
};
```

5. **Update language switcher:**
```javascript
// src/components/Header.jsx
const languages = [
  { code: 'en', name: t('language.en'), flag: '🇬🇧' },
  { code: 'nl', name: t('language.nl'), flag: '🇳🇱' },
  { code: 'fr', name: t('language.fr'), flag: '🇫🇷' }, // Add this
];
```

6. **Add language name to common.json:**
```json
// All language files should have:
{
  "language": {
    "en": "English",
    "nl": "Nederlands",
    "fr": "Français"
  }
}
```

## Translation Quality Tips

1. **Keep it concise** - UI strings should be short
2. **Maintain tone** - Friendly, helpful, encouraging
3. **Consider context** - Button text vs. paragraph text
4. **Test pluralization** - Ensure singular/plural forms work
5. **Check character length** - Some languages are longer (German, Dutch)
6. **Preserve formatting** - Keep HTML entities, line breaks
7. **Ask native speakers** - For professional translations

## Testing

### Check Current Language
```javascript
console.log(i18n.language); // 'en' or 'nl'
```

### Test Language Switch
1. Open browser console
2. Run: `localStorage.setItem('i18nextLng', 'nl')`
3. Refresh page → Should load Dutch
4. Click language switcher → Should switch back to English

### Debug Mode
In development, i18n debug is enabled. Check console for:
- Missing translation keys
- Namespace loading status
- Language detection logs

## Benefits of This Approach

✅ **No API costs** - All translations are static files
✅ **Instant switching** - No loading delays
✅ **Offline support** - Works without internet
✅ **SEO friendly** - Can implement language-specific URLs
✅ **Type-safe** - Can generate TypeScript types from JSON
✅ **Developer friendly** - Easy to add new strings
✅ **User friendly** - Persistent language preference

## Next Phase: Dynamic Content Translation

For dynamic content (location descriptions, reviews, events), we'll implement:

1. **Backend translation endpoint** with NLLB-200
2. **Redis caching** for translated content
3. **Pre-translation scripts** for bulk data
4. **Fallback to English** if translation fails

See separate documentation for Phase 2 (AI-powered translation).

---

## Quick Reference

| Task | Command/File |
|------|--------------|
| Add new string | Edit `src/i18n/locales/{lang}/{namespace}.json` |
| Use in component | `const { t } = useTranslation(['namespace'])` |
| Change language | `i18n.changeLanguage('nl')` |
| Current language | `i18n.language` |
| Add new language | Create `locales/{code}/` folder + update config |
| Debug translations | Check browser console in dev mode |

## Resources

- [react-i18next docs](https://react.i18next.com/)
- [i18next docs](https://www.i18next.com/)
- [Pluralization rules](https://www.i18next.com/translation-function/plurals)
- [Interpolation](https://www.i18next.com/translation-function/interpolation)

---

**Implementation Date:** November 20, 2025
**Status:** ✅ Phase 1 Complete (Static UI)
**Next:** Phase 2 (Dynamic Content Translation with NLLB)
