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
import appUpdate from './app-update.json';
import chatModes from './chat-modes.json';
import creditConfirmation from './credit-confirmation.json';
import copyAlert from './copy-alert.json';
import partnershipExit from './partnership-exit.json';
import themeDiscovery from './theme-discovery.json';
import planetaryPositions from './planetary-positions.json';

// The original premium-ui import accumulated a shifted chatScreen block: the
// English key contains German, German contains Russian, and the later Indic
// languages are shifted in the same way. Keep the legacy file stable for now,
// but normalize that one namespace before exposing it to i18next.
const CHAT_SCREEN_SOURCE = Object.freeze({
  english: 'marathi',
  hindi: 'hindi',
  es: 'es',
  fr: 'fr',
  german: 'english',
  russian: 'german',
  chinese: 'russian',
  tamil: 'chinese',
  telugu: 'tamil',
  gujarati: 'telugu',
  marathi: 'gujarati',
});

const normalizedPremiumUi = Object.fromEntries(
  Object.entries(premiumUi).map(([language, copy]) => [
    language,
    {
      ...copy,
      chatScreen: premiumUi[CHAT_SCREEN_SOURCE[language]]?.chatScreen || copy.chatScreen,
    },
  ]),
);

Object.entries(normalizedPremiumUi).forEach(([language, copy]) => {
  copy.planetaryPositions = planetaryPositions[language] || planetaryPositions.english;
});

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

[
  [en, chatModes.english], [es, chatModes.es], [hi, chatModes.hindi], [tamil, chatModes.tamil],
  [te, chatModes.telugu], [gu, chatModes.gujarati], [mr, chatModes.marathi], [de, chatModes.german],
  [fr, chatModes.fr], [ru, chatModes.russian], [zh, chatModes.chinese],
].forEach(([baseCopy, modeCopy]) => {
  baseCopy.chatModes = modeCopy;
});

[
  [en, creditConfirmation.english], [es, creditConfirmation.es], [hi, creditConfirmation.hindi], [tamil, creditConfirmation.tamil],
  [te, creditConfirmation.telugu], [gu, creditConfirmation.gujarati], [mr, creditConfirmation.marathi], [de, creditConfirmation.german],
  [fr, creditConfirmation.fr], [ru, creditConfirmation.russian], [zh, creditConfirmation.chinese],
].forEach(([baseCopy, confirmationCopy]) => {
  baseCopy.creditConfirmation = confirmationCopy;
});

[
  [en, copyAlert.english], [es, copyAlert.es], [hi, copyAlert.hindi], [tamil, copyAlert.tamil],
  [te, copyAlert.telugu], [gu, copyAlert.gujarati], [mr, copyAlert.marathi], [de, copyAlert.german],
  [fr, copyAlert.fr], [ru, copyAlert.russian], [zh, copyAlert.chinese],
].forEach(([baseCopy, alertCopy]) => {
  baseCopy.copyAlert = alertCopy;
});

[
  [en, partnershipExit.english], [es, partnershipExit.es], [hi, partnershipExit.hindi], [tamil, partnershipExit.tamil],
  [te, partnershipExit.telugu], [gu, partnershipExit.gujarati], [mr, partnershipExit.marathi], [de, partnershipExit.german],
  [fr, partnershipExit.fr], [ru, partnershipExit.russian], [zh, partnershipExit.chinese],
].forEach(([baseCopy, exitCopy]) => {
  baseCopy.partnershipExit = exitCopy;
});

i18n
  .use(initReactI18next)
  .init({
    resources: {
      english: {
        translation: { ...en, premiumUi: { ...normalizedPremiumUi.english, homeRecommendations: homeRecommendations.english }, themeDiscovery: themeDiscovery.english, appUpdate: appUpdate.english, lifeAnalysisFlow: { ...lifeAnalysis.english, ...lifeAnalysisPdf.english }, historyUi: historyUi.english, historyDetail: historyDetail.english, knowledgeSupport: knowledgeSupport.english, notificationInbox: accountNotifications.english },
      },
      es: {
        translation: { ...es, premiumUi: { ...normalizedPremiumUi.es, homeRecommendations: homeRecommendations.es }, themeDiscovery: themeDiscovery.es, appUpdate: appUpdate.es, lifeAnalysisFlow: { ...lifeAnalysis.es, ...lifeAnalysisPdf.es }, historyUi: historyUi.es, historyDetail: historyDetail.es, knowledgeSupport: knowledgeSupport.es, notificationInbox: accountNotifications.es },
      },
      hindi: {
        translation: { ...hi, premiumUi: { ...normalizedPremiumUi.hindi, homeRecommendations: homeRecommendations.hindi }, themeDiscovery: themeDiscovery.hindi, appUpdate: appUpdate.hindi, lifeAnalysisFlow: { ...lifeAnalysis.hindi, ...lifeAnalysisPdf.hindi }, historyUi: historyUi.hindi, historyDetail: historyDetail.hindi, knowledgeSupport: knowledgeSupport.hindi, notificationInbox: accountNotifications.hindi },
      },
      tamil: {
        translation: { ...tamil, premiumUi: { ...normalizedPremiumUi.tamil, homeRecommendations: homeRecommendations.tamil }, themeDiscovery: themeDiscovery.tamil, appUpdate: appUpdate.tamil, lifeAnalysisFlow: { ...lifeAnalysis.tamil, ...lifeAnalysisPdf.tamil }, historyUi: historyUi.tamil, historyDetail: historyDetail.tamil, knowledgeSupport: knowledgeSupport.tamil, notificationInbox: accountNotifications.tamil },
      },
      telugu: {
        translation: { ...te, premiumUi: { ...normalizedPremiumUi.telugu, homeRecommendations: homeRecommendations.telugu }, themeDiscovery: themeDiscovery.telugu, appUpdate: appUpdate.telugu, lifeAnalysisFlow: { ...lifeAnalysis.telugu, ...lifeAnalysisPdf.telugu }, historyUi: historyUi.telugu, historyDetail: historyDetail.telugu, knowledgeSupport: knowledgeSupport.telugu, notificationInbox: accountNotifications.telugu },
      },
      gujarati: {
        translation: { ...gu, premiumUi: { ...normalizedPremiumUi.gujarati, homeRecommendations: homeRecommendations.gujarati }, themeDiscovery: themeDiscovery.gujarati, appUpdate: appUpdate.gujarati, lifeAnalysisFlow: { ...lifeAnalysis.gujarati, ...lifeAnalysisPdf.gujarati }, historyUi: historyUi.gujarati, historyDetail: historyDetail.gujarati, knowledgeSupport: knowledgeSupport.gujarati, notificationInbox: accountNotifications.gujarati },
      },
      marathi: {
        translation: { ...mr, premiumUi: { ...normalizedPremiumUi.marathi, homeRecommendations: homeRecommendations.marathi }, themeDiscovery: themeDiscovery.marathi, appUpdate: appUpdate.marathi, lifeAnalysisFlow: { ...lifeAnalysis.marathi, ...lifeAnalysisPdf.marathi }, historyUi: historyUi.marathi, historyDetail: historyDetail.marathi, knowledgeSupport: knowledgeSupport.marathi, notificationInbox: accountNotifications.marathi },
      },
      german: {
        translation: { ...de, premiumUi: { ...normalizedPremiumUi.german, homeRecommendations: homeRecommendations.german }, themeDiscovery: themeDiscovery.german, appUpdate: appUpdate.german, lifeAnalysisFlow: { ...lifeAnalysis.de, ...lifeAnalysisPdf.de }, historyUi: historyUi.de, historyDetail: historyDetail.de, knowledgeSupport: knowledgeSupport.de, notificationInbox: accountNotifications.de },
      },
      french: {
        translation: { ...fr, premiumUi: { ...normalizedPremiumUi.fr, homeRecommendations: homeRecommendations.fr }, themeDiscovery: themeDiscovery.fr, appUpdate: appUpdate.french, lifeAnalysisFlow: { ...lifeAnalysis.fr, ...lifeAnalysisPdf.fr }, historyUi: historyUi.fr, historyDetail: historyDetail.fr, knowledgeSupport: knowledgeSupport.fr, notificationInbox: accountNotifications.fr },
      },
      russian: {
        translation: { ...ru, premiumUi: { ...normalizedPremiumUi.russian, homeRecommendations: homeRecommendations.russian }, themeDiscovery: themeDiscovery.russian, appUpdate: appUpdate.russian, lifeAnalysisFlow: { ...lifeAnalysis.russian, ...lifeAnalysisPdf.russian }, historyUi: historyUi.russian, historyDetail: historyDetail.russian, knowledgeSupport: knowledgeSupport.russian, notificationInbox: accountNotifications.russian },
      },
      chinese: {
        translation: { ...zh, premiumUi: { ...normalizedPremiumUi.chinese, homeRecommendations: homeRecommendations.chinese }, themeDiscovery: themeDiscovery.chinese, appUpdate: appUpdate.chinese, lifeAnalysisFlow: { ...lifeAnalysis.chinese, ...lifeAnalysisPdf.chinese }, historyUi: historyUi.chinese, historyDetail: historyDetail.chinese, knowledgeSupport: knowledgeSupport.chinese, notificationInbox: accountNotifications.chinese },
      },
      mandarin: {
        translation: { ...zh, premiumUi: { ...normalizedPremiumUi.chinese, homeRecommendations: homeRecommendations.chinese }, themeDiscovery: themeDiscovery.chinese, appUpdate: appUpdate.chinese, lifeAnalysisFlow: { ...lifeAnalysis.chinese, ...lifeAnalysisPdf.chinese }, historyUi: historyUi.chinese, historyDetail: historyDetail.chinese, knowledgeSupport: knowledgeSupport.chinese, notificationInbox: accountNotifications.chinese },
      },
    },
    lng: 'english',
    fallbackLng: 'english',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
