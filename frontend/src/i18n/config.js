import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import enCommon from './locales/en/common.json';
import enWizard from './locales/en/wizard.json';
import nlCommon from './locales/nl/common.json';
import nlWizard from './locales/nl/wizard.json';

const resources = {
  en: {
    common: enCommon,
    wizard: enWizard,
  },
  nl: {
    common: nlCommon,
    wizard: nlWizard,
  },
};

i18n
  // Detect user language
  .use(LanguageDetector)
  // Pass the i18n instance to react-i18next
  .use(initReactI18next)
  // Initialize i18next
  .init({
    resources,
    fallbackLng: 'en',
    defaultNS: 'common',
    ns: ['common', 'wizard'],

    // Language detection options
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // Enable debug in development
    debug: process.env.NODE_ENV === 'development',
  });

export default i18n;
