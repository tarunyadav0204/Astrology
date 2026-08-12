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
import premiumUi from './premium-ui.json';
import lifeAnalysis from './life-analysis.json';
import lifeAnalysisPdf from './life-analysis-pdf.json';
import historyUi from './history-ui.json';
import historyDetail from './history-detail.json';
import knowledgeSupport from './knowledge-support.json';
import accountNotifications from './account-notifications.json';
import accountSecurityActions from './account-security-actions.json';
import authDeep from './auth-deep.json';
import homeRecommendations from './home-recommendations.json';

[
  [en, accountSecurityActions.english],
  [es, accountSecurityActions.es],
  [hi, accountSecurityActions.hindi],
  [tamil, accountSecurityActions.tamil],
  [te, accountSecurityActions.telugu],
  [gu, accountSecurityActions.gujarati],
  [mr, accountSecurityActions.marathi],
  [de, accountSecurityActions.de],
  [fr, accountSecurityActions.fr],
  [ru, accountSecurityActions.russian],
  [zh, accountSecurityActions.chinese],
].forEach(([baseCopy, actionCopy]) => {
  baseCopy.accountSecurity = { ...baseCopy.accountSecurity, ...actionCopy };
});

[
  [en, authDeep.english], [es, authDeep.es], [hi, authDeep.hindi], [tamil, authDeep.tamil],
  [te, authDeep.telugu], [gu, authDeep.gujarati], [mr, authDeep.marathi], [de, authDeep.de],
  [fr, authDeep.fr], [ru, authDeep.russian], [zh, authDeep.chinese],
].forEach(([baseCopy, deepCopy]) => {
  baseCopy.authDeep = deepCopy;
});

i18n
  .use(initReactI18next)
  .init({
    resources: {
      english: {
        translation: { ...en, premiumUi: { ...premiumUi.english, homeRecommendations: homeRecommendations.english }, lifeAnalysisFlow: { ...lifeAnalysis.english, ...lifeAnalysisPdf.english }, historyUi: historyUi.english, historyDetail: historyDetail.english, knowledgeSupport: knowledgeSupport.english, notificationInbox: accountNotifications.english },
      },
      es: {
        translation: { ...es, premiumUi: { ...premiumUi.es, homeRecommendations: homeRecommendations.es }, lifeAnalysisFlow: { ...lifeAnalysis.es, ...lifeAnalysisPdf.es }, historyUi: historyUi.es, historyDetail: historyDetail.es, knowledgeSupport: knowledgeSupport.es, notificationInbox: accountNotifications.es },
      },
      hindi: {
        translation: { ...hi, premiumUi: { ...premiumUi.hindi, homeRecommendations: homeRecommendations.hindi }, lifeAnalysisFlow: { ...lifeAnalysis.hindi, ...lifeAnalysisPdf.hindi }, historyUi: historyUi.hindi, historyDetail: historyDetail.hindi, knowledgeSupport: knowledgeSupport.hindi, notificationInbox: accountNotifications.hindi },
      },
      tamil: {
        translation: { ...tamil, premiumUi: { ...premiumUi.tamil, homeRecommendations: homeRecommendations.tamil }, lifeAnalysisFlow: { ...lifeAnalysis.tamil, ...lifeAnalysisPdf.tamil }, historyUi: historyUi.tamil, historyDetail: historyDetail.tamil, knowledgeSupport: knowledgeSupport.tamil, notificationInbox: accountNotifications.tamil },
      },
      telugu: {
        translation: { ...te, premiumUi: { ...premiumUi.telugu, homeRecommendations: homeRecommendations.telugu }, lifeAnalysisFlow: { ...lifeAnalysis.telugu, ...lifeAnalysisPdf.telugu }, historyUi: historyUi.telugu, historyDetail: historyDetail.telugu, knowledgeSupport: knowledgeSupport.telugu, notificationInbox: accountNotifications.telugu },
      },
      gujarati: {
        translation: { ...gu, premiumUi: { ...premiumUi.gujarati, homeRecommendations: homeRecommendations.gujarati }, lifeAnalysisFlow: { ...lifeAnalysis.gujarati, ...lifeAnalysisPdf.gujarati }, historyUi: historyUi.gujarati, historyDetail: historyDetail.gujarati, knowledgeSupport: knowledgeSupport.gujarati, notificationInbox: accountNotifications.gujarati },
      },
      marathi: {
        translation: { ...mr, premiumUi: { ...premiumUi.marathi, homeRecommendations: homeRecommendations.marathi }, lifeAnalysisFlow: { ...lifeAnalysis.marathi, ...lifeAnalysisPdf.marathi }, historyUi: historyUi.marathi, historyDetail: historyDetail.marathi, knowledgeSupport: knowledgeSupport.marathi, notificationInbox: accountNotifications.marathi },
      },
      german: {
        translation: { ...de, premiumUi: { ...premiumUi.german, homeRecommendations: homeRecommendations.german }, lifeAnalysisFlow: { ...lifeAnalysis.de, ...lifeAnalysisPdf.de }, historyUi: historyUi.de, historyDetail: historyDetail.de, knowledgeSupport: knowledgeSupport.de, notificationInbox: accountNotifications.de },
      },
      french: {
        translation: { ...fr, premiumUi: { ...premiumUi.fr, homeRecommendations: homeRecommendations.fr }, lifeAnalysisFlow: { ...lifeAnalysis.fr, ...lifeAnalysisPdf.fr }, historyUi: historyUi.fr, historyDetail: historyDetail.fr, knowledgeSupport: knowledgeSupport.fr, notificationInbox: accountNotifications.fr },
      },
      russian: {
        translation: { ...ru, premiumUi: { ...premiumUi.russian, homeRecommendations: homeRecommendations.russian }, lifeAnalysisFlow: { ...lifeAnalysis.russian, ...lifeAnalysisPdf.russian }, historyUi: historyUi.russian, historyDetail: historyDetail.russian, knowledgeSupport: knowledgeSupport.russian, notificationInbox: accountNotifications.russian },
      },
      chinese: {
        translation: { ...zh, premiumUi: { ...premiumUi.chinese, homeRecommendations: homeRecommendations.chinese }, lifeAnalysisFlow: { ...lifeAnalysis.chinese, ...lifeAnalysisPdf.chinese }, historyUi: historyUi.chinese, historyDetail: historyDetail.chinese, knowledgeSupport: knowledgeSupport.chinese, notificationInbox: accountNotifications.chinese },
      },
      mandarin: {
        translation: { ...zh, premiumUi: { ...premiumUi.chinese, homeRecommendations: homeRecommendations.chinese }, lifeAnalysisFlow: { ...lifeAnalysis.chinese, ...lifeAnalysisPdf.chinese }, historyUi: historyUi.chinese, historyDetail: historyDetail.chinese, knowledgeSupport: knowledgeSupport.chinese, notificationInbox: accountNotifications.chinese },
      },
    },
    lng: 'english',
    fallbackLng: 'english',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
