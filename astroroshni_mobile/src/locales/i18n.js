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
import houseLifeAreas from './house-life-areas.json';
import homeNextPeak from './home-next-peak.json';
import appUpdate from './app-update.json';
import chatModes from './chat-modes.json';
import chatModeSelector from './chat-mode-selector.json';
import creditConfirmation from './credit-confirmation.json';
import copyAlert from './copy-alert.json';
import partnershipExit from './partnership-exit.json';
import themeDiscovery from './theme-discovery.json';
import planetaryPositions from './planetary-positions.json';
import firstPurchaseStarter from './first-purchase-starter.json';
import instantChatPacing from './instant-chat-pacing.json';
import instantBilling from './instant-billing.json';
import instantExperience from './instant-experience.json';

const INSTANT_MODE_ACTION_COPY = Object.freeze({
  english: 'Mode',
  hindi: 'मोड',
  es: 'Modo',
  fr: 'Mode',
  german: 'Modus',
  russian: 'Режим',
  chinese: '模式',
  tamil: 'பயன்முறை',
  telugu: 'మోడ్',
  gujarati: 'મોડ',
  marathi: 'मोड',
});

const ANSWER_STYLE_COPY = Object.freeze({
  english: { label: 'Answer style', simple: 'Simple', technical: 'Technical', simpleDescription: 'Clear, everyday astrology', technicalDescription: 'Full calculations and terminology', selectionTitle: 'You’re using {{mode}} · {{style}}', selectionBody: '{{styleDescription}}. Choose the consultation mode and answer style, then continue.', newLabel: 'New answer preference', newSelectionBody: 'Tara can now answer in Simple or Technical style. Choose once for Standard, Premium and Live; you can change it later.' },
  hindi: { label: 'उत्तर शैली', simple: 'सरल', technical: 'तकनीकी', simpleDescription: 'साफ़, रोज़मर्रा की भाषा में ज्योतिष', technicalDescription: 'पूरी गणनाएँ और ज्योतिषीय शब्दावली', selectionTitle: 'आप {{mode}} · {{style}} उपयोग कर रहे हैं', selectionBody: '{{styleDescription}}। परामर्श मोड और उत्तर शैली चुनें, फिर आगे बढ़ें।', newLabel: 'नई उत्तर प्राथमिकता', newSelectionBody: 'तारा अब सरल या तकनीकी शैली में उत्तर दे सकती है। Standard, Premium और Live के लिए एक बार चुनें; बाद में इसे बदला जा सकता है।' },
  es: { label: 'Estilo de respuesta', simple: 'Simple', technical: 'Técnica', simpleDescription: 'Astrología clara y cotidiana', technicalDescription: 'Cálculos y terminología completos', selectionTitle: 'Estás usando {{mode}} · {{style}}', selectionBody: '{{styleDescription}}. Elige el modo de consulta y el estilo de respuesta, y continúa.', newLabel: 'Nueva preferencia de respuesta', newSelectionBody: 'Tara ahora puede responder en estilo Simple o Técnico. Elige una vez para Standard, Premium y Live; podrás cambiarlo después.' },
  fr: { label: 'Style de réponse', simple: 'Simple', technical: 'Technique', simpleDescription: 'Astrologie claire et accessible', technicalDescription: 'Calculs complets et terminologie', selectionTitle: 'Vous utilisez {{mode}} · {{style}}', selectionBody: '{{styleDescription}}. Choisissez le mode de consultation et le style de réponse, puis continuez.', newLabel: 'Nouvelle préférence de réponse', newSelectionBody: 'Tara peut maintenant répondre en style Simple ou Technique. Choisissez une fois pour Standard, Premium et Live; vous pourrez modifier ce choix plus tard.' },
  german: { label: 'Antwortstil', simple: 'Einfach', technical: 'Technisch', simpleDescription: 'Klare Astrologie in Alltagssprache', technicalDescription: 'Vollständige Berechnungen und Fachbegriffe', selectionTitle: 'Du verwendest {{mode}} · {{style}}', selectionBody: '{{styleDescription}}. Wähle Beratungsmodus und Antwortstil und fahre dann fort.', newLabel: 'Neue Antwortpräferenz', newSelectionBody: 'Tara kann jetzt einfach oder technisch antworten. Wähle einmal für Standard, Premium und Live; du kannst es später ändern.' },
  russian: { label: 'Стиль ответа', simple: 'Простой', technical: 'Технический', simpleDescription: 'Понятная астрология простыми словами', technicalDescription: 'Полные расчёты и терминология', selectionTitle: 'Вы используете {{mode}} · {{style}}', selectionBody: '{{styleDescription}}. Выберите режим консультации и стиль ответа, затем продолжите.', newLabel: 'Новая настройка ответа', newSelectionBody: 'Теперь Тара может отвечать в простом или техническом стиле. Выберите один раз для Standard, Premium и Live; позже выбор можно изменить.' },
  chinese: { label: '回答风格', simple: '简明', technical: '专业', simpleDescription: '清晰易懂的日常占星解读', technicalDescription: '完整计算与专业术语', selectionTitle: '当前使用：{{mode}} · {{style}}', selectionBody: '{{styleDescription}}。请选择咨询模式和回答风格，然后继续。', newLabel: '新的回答偏好', newSelectionBody: 'Tara 现在可以使用简明或专业风格回答。为 Standard、Premium 和 Live 选择一次，之后仍可更改。' },
  tamil: { label: 'பதில் பாணி', simple: 'எளிமை', technical: 'தொழில்நுட்பம்', simpleDescription: 'தெளிவான அன்றாட மொழியில் ஜோதிடம்', technicalDescription: 'முழு கணக்கீடுகளும் கலைச்சொற்களும்', selectionTitle: 'நீங்கள் பயன்படுத்துவது {{mode}} · {{style}}', selectionBody: '{{styleDescription}}. ஆலோசனை முறையையும் பதில் பாணியையும் தேர்ந்தெடுத்து தொடரவும்.', newLabel: 'புதிய பதில் விருப்பம்', newSelectionBody: 'தாரா இப்போது எளிய அல்லது தொழில்நுட்ப பாணியில் பதிலளிக்கலாம். Standard, Premium, Live அனைத்திற்கும் ஒருமுறை தேர்வு செய்யுங்கள்; பின்னர் மாற்றலாம்.' },
  telugu: { label: 'సమాధాన శైలి', simple: 'సరళం', technical: 'సాంకేతికం', simpleDescription: 'స్పష్టమైన రోజువారీ భాషలో జ్యోతిష్యం', technicalDescription: 'పూర్తి లెక్కలు మరియు పరిభాష', selectionTitle: 'మీరు ఉపయోగిస్తున్నది {{mode}} · {{style}}', selectionBody: '{{styleDescription}}. సంప్రదింపు మోడ్ మరియు సమాధాన శైలిని ఎంచుకుని కొనసాగండి.', newLabel: 'కొత్త సమాధాన ప్రాధాన్యం', newSelectionBody: 'తారా ఇప్పుడు సరళ లేదా సాంకేతిక శైలిలో సమాధానం ఇవ్వగలదు. Standard, Premium, Live కోసం ఒకసారి ఎంచుకోండి; తర్వాత మార్చవచ్చు.' },
  gujarati: { label: 'જવાબની શૈલી', simple: 'સરળ', technical: 'ટેક્નિકલ', simpleDescription: 'સ્પષ્ટ, રોજિંદી ભાષામાં જ્યોતિષ', technicalDescription: 'સંપૂર્ણ ગણતરીઓ અને પરિભાષા', selectionTitle: 'તમે {{mode}} · {{style}} વાપરી રહ્યા છો', selectionBody: '{{styleDescription}}. પરામર્શ મોડ અને જવાબની શૈલી પસંદ કરીને આગળ વધો.', newLabel: 'નવી જવાબ પસંદગી', newSelectionBody: 'તારા હવે સરળ અથવા ટેક્નિકલ શૈલીમાં જવાબ આપી શકે છે. Standard, Premium અને Live માટે એક વખત પસંદ કરો; પછી બદલી શકશો.' },
  marathi: { label: 'उत्तर शैली', simple: 'सोपे', technical: 'तांत्रिक', simpleDescription: 'स्पष्ट, रोजच्या भाषेतील ज्योतिष', technicalDescription: 'संपूर्ण गणना आणि ज्योतिषीय संज्ञा', selectionTitle: 'तुम्ही {{mode}} · {{style}} वापरत आहात', selectionBody: '{{styleDescription}}. सल्ल्याचा मोड आणि उत्तर शैली निवडा, नंतर पुढे जा.', newLabel: 'नवीन उत्तर प्राधान्य', newSelectionBody: 'तारा आता सोप्या किंवा तांत्रिक शैलीत उत्तर देऊ शकते. Standard, Premium आणि Live साठी एकदा निवडा; नंतर बदलता येईल.' },
});

const MESSAGE_ACTION_COPY = Object.freeze({
  english: {
    messageActions: 'Message actions', listenPodcast: 'Listen as podcast', podcastReadyToast: 'Podcast ready — tap to listen',
    pausePodcast: 'Pause podcast', resumePodcast: 'Resume podcast', stopPodcast: 'Stop podcast', sharePodcast: 'Share podcast audio',
    copyMessage: 'Copy message', shareMessage: 'Share message', downloadPdf: 'Download as PDF',
    deleteMessage: 'Delete message', deleteMessageConfirm: 'Are you sure you want to delete this message?',
  },
  hindi: {
    messageActions: 'संदेश विकल्प', listenPodcast: 'पॉडकास्ट के रूप में सुनें', podcastReadyToast: 'पॉडकास्ट तैयार है — सुनने के लिए टैप करें',
    pausePodcast: 'पॉडकास्ट रोकें', resumePodcast: 'पॉडकास्ट फिर चलाएँ', stopPodcast: 'पॉडकास्ट बंद करें', sharePodcast: 'पॉडकास्ट ऑडियो साझा करें',
    copyMessage: 'संदेश कॉपी करें', shareMessage: 'संदेश साझा करें', downloadPdf: 'PDF के रूप में डाउनलोड करें',
    deleteMessage: 'संदेश हटाएँ', deleteMessageConfirm: 'क्या आप वाकई यह संदेश हटाना चाहते हैं?',
  },
  es: {
    messageActions: 'Acciones del mensaje', listenPodcast: 'Escuchar como pódcast', podcastReadyToast: 'Pódcast listo — toca para escuchar',
    pausePodcast: 'Pausar pódcast', resumePodcast: 'Reanudar pódcast', stopPodcast: 'Detener pódcast', sharePodcast: 'Compartir audio del pódcast',
    copyMessage: 'Copiar mensaje', shareMessage: 'Compartir mensaje', downloadPdf: 'Descargar como PDF',
    deleteMessage: 'Eliminar mensaje', deleteMessageConfirm: '¿Seguro que quieres eliminar este mensaje?',
  },
  fr: {
    messageActions: 'Actions du message', listenPodcast: 'Écouter en podcast', podcastReadyToast: 'Podcast prêt — touchez pour écouter',
    pausePodcast: 'Mettre le podcast en pause', resumePodcast: 'Reprendre le podcast', stopPodcast: 'Arrêter le podcast', sharePodcast: 'Partager l’audio du podcast',
    copyMessage: 'Copier le message', shareMessage: 'Partager le message', downloadPdf: 'Télécharger en PDF',
    deleteMessage: 'Supprimer le message', deleteMessageConfirm: 'Voulez-vous vraiment supprimer ce message ?',
  },
  german: {
    messageActions: 'Nachrichtenaktionen', listenPodcast: 'Als Podcast anhören', podcastReadyToast: 'Podcast ist bereit — zum Anhören tippen',
    pausePodcast: 'Podcast pausieren', resumePodcast: 'Podcast fortsetzen', stopPodcast: 'Podcast stoppen', sharePodcast: 'Podcast-Audio teilen',
    copyMessage: 'Nachricht kopieren', shareMessage: 'Nachricht teilen', downloadPdf: 'Als PDF herunterladen',
    deleteMessage: 'Nachricht löschen', deleteMessageConfirm: 'Möchtest du diese Nachricht wirklich löschen?',
  },
  russian: {
    messageActions: 'Действия с сообщением', listenPodcast: 'Прослушать как подкаст', podcastReadyToast: 'Подкаст готов — нажмите, чтобы слушать',
    pausePodcast: 'Приостановить подкаст', resumePodcast: 'Продолжить подкаст', stopPodcast: 'Остановить подкаст', sharePodcast: 'Поделиться аудио подкаста',
    copyMessage: 'Копировать сообщение', shareMessage: 'Поделиться сообщением', downloadPdf: 'Скачать как PDF',
    deleteMessage: 'Удалить сообщение', deleteMessageConfirm: 'Вы уверены, что хотите удалить это сообщение?',
  },
  chinese: {
    messageActions: '消息操作', listenPodcast: '以播客形式收听', podcastReadyToast: '播客已准备好 — 点击收听',
    pausePodcast: '暂停播客', resumePodcast: '继续播客', stopPodcast: '停止播客', sharePodcast: '分享播客音频',
    copyMessage: '复制消息', shareMessage: '分享消息', downloadPdf: '下载为 PDF',
    deleteMessage: '删除消息', deleteMessageConfirm: '确定要删除这条消息吗？',
  },
  tamil: {
    messageActions: 'செய்தி செயல்கள்', listenPodcast: 'பாட்காஸ்டாகக் கேளுங்கள்', podcastReadyToast: 'பாட்காஸ்ட் தயார் — கேட்கத் தட்டவும்',
    pausePodcast: 'பாட்காஸ்டை இடைநிறுத்து', resumePodcast: 'பாட்காஸ்டைத் தொடரு', stopPodcast: 'பாட்காஸ்டை நிறுத்து', sharePodcast: 'பாட்காஸ்ட் ஒலியைப் பகிரவும்',
    copyMessage: 'செய்தியை நகலெடு', shareMessage: 'செய்தியைப் பகிரவும்', downloadPdf: 'PDF ஆகப் பதிவிறக்கவும்',
    deleteMessage: 'செய்தியை நீக்கு', deleteMessageConfirm: 'இந்தச் செய்தியை நீக்க விரும்புகிறீர்களா?',
  },
  telugu: {
    messageActions: 'సందేశ చర్యలు', listenPodcast: 'పాడ్‌కాస్ట్‌గా వినండి', podcastReadyToast: 'పాడ్‌కాస్ట్ సిద్ధంగా ఉంది — వినడానికి నొక్కండి',
    pausePodcast: 'పాడ్‌కాస్ట్‌ను పాజ్ చేయండి', resumePodcast: 'పాడ్‌కాస్ట్‌ను కొనసాగించండి', stopPodcast: 'పాడ్‌కాస్ట్‌ను ఆపండి', sharePodcast: 'పాడ్‌కాస్ట్ ఆడియోను పంచుకోండి',
    copyMessage: 'సందేశాన్ని కాపీ చేయండి', shareMessage: 'సందేశాన్ని పంచుకోండి', downloadPdf: 'PDFగా డౌన్‌లోడ్ చేయండి',
    deleteMessage: 'సందేశాన్ని తొలగించండి', deleteMessageConfirm: 'ఈ సందేశాన్ని తొలగించాలని ఖచ్చితంగా అనుకుంటున్నారా?',
  },
  gujarati: {
    messageActions: 'સંદેશ ક્રિયાઓ', listenPodcast: 'પોડકાસ્ટ તરીકે સાંભળો', podcastReadyToast: 'પોડકાસ્ટ તૈયાર છે — સાંભળવા માટે ટેપ કરો',
    pausePodcast: 'પોડકાસ્ટ થોભાવો', resumePodcast: 'પોડકાસ્ટ ફરી ચલાવો', stopPodcast: 'પોડકાસ્ટ બંધ કરો', sharePodcast: 'પોડકાસ્ટ ઑડિયો શેર કરો',
    copyMessage: 'સંદેશ કૉપી કરો', shareMessage: 'સંદેશ શેર કરો', downloadPdf: 'PDF તરીકે ડાઉનલોડ કરો',
    deleteMessage: 'સંદેશ કાઢી નાખો', deleteMessageConfirm: 'શું તમે ખરેખર આ સંદેશ કાઢી નાખવા માંગો છો?',
  },
  marathi: {
    messageActions: 'संदेश क्रिया', listenPodcast: 'पॉडकास्ट म्हणून ऐका', podcastReadyToast: 'पॉडकास्ट तयार आहे — ऐकण्यासाठी टॅप करा',
    pausePodcast: 'पॉडकास्ट थांबवा', resumePodcast: 'पॉडकास्ट पुन्हा सुरू करा', stopPodcast: 'पॉडकास्ट बंद करा', sharePodcast: 'पॉडकास्ट ऑडिओ शेअर करा',
    copyMessage: 'संदेश कॉपी करा', shareMessage: 'संदेश शेअर करा', downloadPdf: 'PDF म्हणून डाउनलोड करा',
    deleteMessage: 'संदेश हटवा', deleteMessageConfirm: 'तुम्हाला हा संदेश नक्की हटवायचा आहे का?',
  },
});

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
      home: {
        ...copy.home,
        houseAreas: houseLifeAreas[language] || houseLifeAreas.english,
      },
      homeNextPeak: homeNextPeak[language] || homeNextPeak.english,
    },
  ]),
);

[
  [en, instantChatPacing.english], [es, instantChatPacing.es], [hi, instantChatPacing.hindi],
  [tamil, instantChatPacing.tamil], [te, instantChatPacing.telugu], [gu, instantChatPacing.gujarati],
  [mr, instantChatPacing.marathi], [de, instantChatPacing.german], [fr, instantChatPacing.fr],
  [ru, instantChatPacing.russian], [zh, instantChatPacing.chinese],
].forEach(([baseCopy, pacingCopy]) => {
  baseCopy.chat = baseCopy.chat || {};
  baseCopy.chat.instantLoader = { ...(baseCopy.chat.instantLoader || {}), ...pacingCopy };
});

[
  [en, instantBilling.english, 'english'], [es, instantBilling.es, 'es'], [hi, instantBilling.hindi, 'hindi'],
  [tamil, instantBilling.tamil, 'tamil'], [te, instantBilling.telugu, 'telugu'], [gu, instantBilling.gujarati, 'gujarati'],
  [mr, instantBilling.marathi, 'marathi'], [de, instantBilling.german, 'german'], [fr, instantBilling.fr, 'fr'],
  [ru, instantBilling.russian, 'russian'], [zh, instantBilling.chinese, 'chinese'],
].forEach(([baseCopy, billingCopy, language]) => {
  baseCopy.chat = baseCopy.chat || {};
  baseCopy.chat.answerStyle = ANSWER_STYLE_COPY[language] || ANSWER_STYLE_COPY.english;
  Object.assign(baseCopy.chat, MESSAGE_ACTION_COPY[language] || MESSAGE_ACTION_COPY.english);
  baseCopy.instantBilling = {
    ...billingCopy,
    ...(instantExperience[language] || instantExperience.english),
    changeMode: INSTANT_MODE_ACTION_COPY[language],
  };
});

Object.entries(normalizedPremiumUi).forEach(([language, copy]) => {
  copy.planetaryPositions = planetaryPositions[language] || planetaryPositions.english;
});

[
  [en, firstPurchaseStarter.english], [es, firstPurchaseStarter.es], [hi, firstPurchaseStarter.hindi],
  [tamil, firstPurchaseStarter.tamil], [te, firstPurchaseStarter.telugu], [gu, firstPurchaseStarter.gujarati],
  [mr, firstPurchaseStarter.marathi], [de, firstPurchaseStarter.german], [fr, firstPurchaseStarter.fr],
  [ru, firstPurchaseStarter.russian], [zh, firstPurchaseStarter.chinese],
].forEach(([baseCopy, starterCopy]) => {
  baseCopy.chat = baseCopy.chat || {};
  baseCopy.chat.firstPurchaseOffer = { ...(baseCopy.chat.firstPurchaseOffer || {}), ...starterCopy };
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
  [en, chatModes.english, 'english'], [es, chatModes.es, 'es'], [hi, chatModes.hindi, 'hindi'], [tamil, chatModes.tamil, 'tamil'],
  [te, chatModes.telugu, 'telugu'], [gu, chatModes.gujarati, 'gujarati'], [mr, chatModes.marathi, 'marathi'], [de, chatModes.german, 'german'],
  [fr, chatModes.fr, 'fr'], [ru, chatModes.russian, 'russian'], [zh, chatModes.chinese, 'chinese'],
].forEach(([baseCopy, modeCopy, language]) => {
  baseCopy.chatModes = modeCopy;
  baseCopy.chat = baseCopy.chat || {};
  baseCopy.chat.modeIntro = {
    ...(baseCopy.chat.modeIntro || {}),
    ...(chatModeSelector[language] || chatModeSelector.english),
  };
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
