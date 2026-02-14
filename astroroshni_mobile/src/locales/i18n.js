import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './en.json';
import es from './es.json';
import hi from './hi.json';
import tamil from './ta.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      english: {
        translation: en,
      },
      es: {
        translation: es,
      },
      hindi: {
        translation: hi,
      },
      tamil: {
        translation: tamil,
      },
    },
    lng: 'english',
    fallbackLng: 'english',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
