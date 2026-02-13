# Translation Guide for AstrologyApp

This document explains how to implement both static and dynamic translations in the application using `react-i18next`.

## 1. Basic Setup

To enable translations in any component, you need to import and use the `useTranslation` hook.

```javascript
import { useTranslation } from 'react-i18next';

const MyComponent = () => {
  const { t } = useTranslation();
  // ...
};
```

The `t` function is used for all translations.

## 2. Static Translation

Static translation is used for simple, hardcoded text that does not change.

**Example:** A button label.

**JSON File (`/locales/en/translation.json`):**
```json
{
  "dasha": {
    "viewTimeline": "View Timeline"
  }
}
```

**Component Code:**
```javascript
<Text>{t('dasha.viewTimeline')}</Text>
```

If the key is not found, `react-i18next` will render the key itself ('dasha.viewTimeline'). To prevent this and provide a sensible default, you can pass a default value as the second argument:

```javascript
<Text>{t('dasha.viewTimeline', 'View Timeline')}</Text>
```

## 3. Dynamic Translation

Dynamic translation is needed when the text to be translated depends on a variable, such as data fetched from an API. In this project, a common example is translating zodiac sign names, which may come from the backend in various formats (e.g., "Aries", "ari", "Ari").

Our translation files use a consistent, short format for sign keys (e.g., `signs.Ari`, `signs.Tau`). To handle different data formats from the backend, we use a helper function to standardize the sign name before passing it to the translator.

### The Helper Functions

Add these helper functions to your file. They will map various sign name formats to the standard short key used in the translation files.

```javascript
// A map from full, lowercase sign names to the short key.
const signNameMap = {
  'aries': 'Ari', 'taurus': 'Tau', 'gemini': 'Gem', 'cancer': 'Can',
  'leo': 'Leo', 'virgo': 'Vir', 'libra': 'Lib', 'scorpio': 'Sco',
  'sagittarius': 'Sag', 'capricorn': 'Cap', 'aquarius': 'Aqu', 'pisces': 'Pis'
};

// A map from short, lowercase sign names to the short key.
const shortSignMap = {
  'ari': 'Ari', 'tau': 'Tau', 'gem': 'Gem', 'can': 'Can',
  'leo': 'Leo', 'vir': 'Vir', 'lib': 'Lib', 'sco': 'Sco',
  'sag': 'Sag', 'cap': 'Cap', 'aqu': 'Aqu', 'pis': 'Pis'
};

// This function takes any sign name and returns the standardized short key.
const getShortSign = (sign) => {
    if (typeof sign !== 'string') return sign;
    const lowerSign = sign.toLowerCase();
    return signNameMap[lowerSign] || shortSignMap[lowerSign] || sign;
};
```

### The `tSign` Wrapper Function

Inside your component, create a small wrapper around the `t` function to make dynamic sign translation cleaner.

```javascript
const MyComponent = () => {
  const { t } = useTranslation();

  const tSign = (sign) => {
    if (!sign) return '';
    // Use the helper to get the standard key, then translate.
    // Provide the original sign name as a fallback.
    return t(`signs.${getShortSign(sign)}`, sign);
  };

  // ...
};
```

### Usage in Component

Now you can use `tSign` to translate sign names from your data.

**Example:** You have an API response `maha.name` which could be "Aries".

**JSON File (`/locales/hi/translation.json`):**
```json
{
  "signs": {
    "Ari": "मेष"
  }
}
```

**Component Code:**
```javascript
// const maha = { name: 'Aries', ... }
<Text>{tSign(maha.name)}</Text>
// This will correctly look up 'signs.Ari' and display "मेष".
```

This approach ensures that regardless of the format ("Aries", "ari", "ARI"), the correct translation key is used, making the component robust against data inconsistencies.
