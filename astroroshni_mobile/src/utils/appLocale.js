/** BCP-47 locale for Date formatting from react-i18next language code. */
const APP_LOCALE_BY_I18N = {
  english: 'en-US',
  hindi: 'hi-IN',
  es: 'es',
  tamil: 'ta-IN',
  telugu: 'te-IN',
  gujarati: 'gu-IN',
  marathi: 'mr-IN',
  german: 'de-DE',
  french: 'fr-FR',
  russian: 'ru-RU',
  chinese: 'zh-CN',
  mandarin: 'zh-CN',
};

export function appLocaleForI18n(lang) {
  return APP_LOCALE_BY_I18N[lang] || 'en-US';
}
