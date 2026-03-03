import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './en.json';
import es from './es.json';
import hi from './hi.json';
import tamil from './ta.json';
import te from './te.json';
import gu from './gu.json';
import mr from './mr.json';
import de from './de.json';
import fr from './fr.json';
import ru from './ru.json';
import zh from './zh.json';

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
      telugu: {
        translation: te,
      },
      gujarati: {
        translation: gu,
      },
      marathi: {
        translation: mr,
      },
      german: {
        translation: de,
      },
      french: {
        translation: fr,
      },
      russian: {
        translation: ru,
      },
      chinese: {
        translation: zh,
      },
      mandarin: {
        translation: zh,
      },
    },
    lng: 'english',
    fallbackLng: 'english',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
