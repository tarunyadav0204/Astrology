import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from '@babel/parser';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const reportAll = process.argv.includes('--report');
const premiumCopy = JSON.parse(fs.readFileSync(path.join(projectRoot, 'src/locales/premium-ui.json'), 'utf8'));
const lifeAnalysisCopy = JSON.parse(fs.readFileSync(path.join(projectRoot, 'src/locales/life-analysis.json'), 'utf8'));
const lifeAnalysisPdfCopy = JSON.parse(fs.readFileSync(path.join(projectRoot, 'src/locales/life-analysis-pdf.json'), 'utf8'));
const historyUiCopy = JSON.parse(fs.readFileSync(path.join(projectRoot, 'src/locales/history-ui.json'), 'utf8'));
const historyDetailCopy = JSON.parse(fs.readFileSync(path.join(projectRoot, 'src/locales/history-detail.json'), 'utf8'));
const knowledgeSupportCopy = JSON.parse(fs.readFileSync(path.join(projectRoot, 'src/locales/knowledge-support.json'), 'utf8'));
const accountNotificationsCopy = JSON.parse(fs.readFileSync(path.join(projectRoot, 'src/locales/account-notifications.json'), 'utf8'));
const accountSecurityActionsCopy = JSON.parse(fs.readFileSync(path.join(projectRoot, 'src/locales/account-security-actions.json'), 'utf8'));
const authDeepCopy = JSON.parse(fs.readFileSync(path.join(projectRoot, 'src/locales/auth-deep.json'), 'utf8'));
const homeRecommendationsCopy = JSON.parse(fs.readFileSync(path.join(projectRoot, 'src/locales/home-recommendations.json'), 'utf8'));
const chatScreenSource = {
  english: 'marathi', hindi: 'hindi', es: 'es', fr: 'fr', german: 'english', russian: 'german',
  chinese: 'russian', tamil: 'chinese', telugu: 'tamil', gujarati: 'telugu', marathi: 'gujarati',
};
const normalizedPremiumCopy = Object.fromEntries(Object.entries(premiumCopy).map(([language, copy]) => [
  language,
  { ...copy, chatScreen: premiumCopy[chatScreenSource[language]]?.chatScreen || copy.chatScreen },
]));
const protectedFiles = [
  'src/components/Yogas/YogaScreen.js',
  'src/components/Yogas/YogaAccordion.js',
  'src/components/Shadbala/ShadbalaScreen.js',
  'src/components/KarmaAnalysis/KarmaAnalysisScreen.js',
  'src/components/Chat/HomeScreen.js',
  'src/components/Chart/ChartScreen.js',
  'src/components/Chart/ChartWidget.js',
  'src/components/Common/DateNavigator.js',
  'src/components/Profile/ProfileScreen.js',
  'src/components/Common/ThemePicker.js',
  'src/components/Common/AppAlertModal.js',
  'src/components/Home/PremiumTodayOverview.js',
  'src/components/Chat/KpTodayCarousel.js',
  'src/components/Chat/ChatScreen.js',
  'src/components/Chat/MessageBubble.js',
  'src/components/Chat/FeedbackComponent.js',
  'src/components/LoadingBubble.js',
  'src/components/Analysis/AnalysisHubScreen.js',
  'src/components/Analysis/AnalysisDetailScreen.js',
  'src/components/Analysis/AnalysisCreditModal.js',
  'src/components/Chat/ChatHistoryScreen.js',
  'src/components/Chat/ChatViewScreen.js',
  'src/components/Chat/PodcastHistoryScreen.js',
  'src/components/Reports/ReportHistoryScreen.js',
  'src/components/Chat/PremiumConsultationContext.js',
  'src/components/Notifications/NotificationEnableBanner.js',
  'src/components/Notifications/NotificationEnableReminderModal.js',
  'src/components/Blog/BlogListScreen.js',
  'src/components/Blog/BlogPostDetailScreen.js',
  'src/components/Blog/BlogLinkScreen.js',
  'src/components/Support/SupportScreen.js',
  'src/components/Profile/AccountSecurityScreen.js',
  'src/components/Notifications/NudgeInboxScreen.js',
  'src/components/Auth/ModernAuthFlow.js',
  'src/components/Auth/AuthLegalNotice.js',
  'src/components/Auth/screens/AuthKeyboardScreen.js',
  'src/components/Auth/screens/WelcomeScreen.js',
  'src/components/Auth/screens/ChooseLanguageScreen.js',
  'src/components/Auth/screens/WelcomeAfterRegistrationScreen.js',
  'src/components/Auth/screens/OTPScreen.js',
  'src/components/Auth/screens/EmailInputScreen.js',
  'src/components/Auth/screens/ForgotPasswordScreen.js',
];

const flatten = (value, prefix = '', result = {}) => {
  Object.entries(value || {}).forEach(([key, child]) => {
    const next = prefix ? `${prefix}.${key}` : key;
    if (child && typeof child === 'object' && !Array.isArray(child)) flatten(child, next, result);
    else result[next] = child;
  });
  return result;
};

const isPluralVariant = (key, englishKeySet) => /_(few|many|zero|two)$/.test(key)
  && englishKeySet.has(key.replace(/_(few|many|zero|two)$/, '_other'));

const mergedPremiumCopy = Object.fromEntries(Object.entries(normalizedPremiumCopy).map(([language, copy]) => [
  language,
  { ...copy, homeRecommendations: homeRecommendationsCopy[language] || homeRecommendationsCopy.english },
]));
const failures = [];
const expectedDrawerExplore = {
  english: 'Explore', hindi: 'खोजें', es: 'Explorar', fr: 'Explorer', german: 'Entdecken',
  russian: 'Обзор', chinese: '探索', tamil: 'ஆராய்க', telugu: 'అన్వేషించండి',
  gujarati: 'શોધો', marathi: 'शोधा',
};
Object.entries(expectedDrawerExplore).forEach(([language, expected]) => {
  const actual = mergedPremiumCopy[language]?.chatScreen?.explore;
  if (actual !== expected) failures.push(`premium-ui/${language}: drawer language mismatch (${actual})`);
});
const englishKeys = Object.keys(flatten(mergedPremiumCopy.english)).sort();
const englishKeySet = new Set(englishKeys);

Object.entries(mergedPremiumCopy).forEach(([language, copy]) => {
  const localized = flatten(copy);
  const missing = englishKeys.filter((key) => !(key in localized));
  const extra = Object.keys(localized).filter((key) => !englishKeys.includes(key));
  if (missing.length) failures.push(`${language}: missing ${missing.join(', ')}`);
  if (extra.length) failures.push(`${language}: unexpected ${extra.join(', ')}`);
});

const lifeAnalysisEnglishKeys = Object.keys(flatten(lifeAnalysisCopy.english)).sort();
Object.entries(lifeAnalysisCopy).forEach(([language, copy]) => {
  const localized = flatten(copy);
  const missing = lifeAnalysisEnglishKeys.filter((key) => !(key in localized));
  const extra = Object.keys(localized).filter((key) => !lifeAnalysisEnglishKeys.includes(key));
  if (missing.length) failures.push(`life-analysis/${language}: missing ${missing.join(', ')}`);
  if (extra.length) failures.push(`life-analysis/${language}: unexpected ${extra.join(', ')}`);
});

const lifeAnalysisPdfEnglishKeys = Object.keys(flatten(lifeAnalysisPdfCopy.english)).sort();
Object.entries(lifeAnalysisPdfCopy).forEach(([language, copy]) => {
  const localized = flatten(copy);
  const missing = lifeAnalysisPdfEnglishKeys.filter((key) => !(key in localized));
  const extra = Object.keys(localized).filter((key) => !lifeAnalysisPdfEnglishKeys.includes(key));
  if (missing.length) failures.push(`life-analysis-pdf/${language}: missing ${missing.join(', ')}`);
  if (extra.length) failures.push(`life-analysis-pdf/${language}: unexpected ${extra.join(', ')}`);
});

const historyUiEnglishKeys = Object.keys(flatten(historyUiCopy.english)).sort();
Object.entries(historyUiCopy).forEach(([language, copy]) => {
  const localized = flatten(copy);
  const missing = historyUiEnglishKeys.filter((key) => !(key in localized));
  const historyKeySet = new Set(historyUiEnglishKeys);
  const extra = Object.keys(localized).filter((key) => !historyKeySet.has(key) && !isPluralVariant(key, historyKeySet));
  if (missing.length) failures.push(`history-ui/${language}: missing ${missing.join(', ')}`);
  if (extra.length) failures.push(`history-ui/${language}: unexpected ${extra.join(', ')}`);
});

const historyDetailEnglishKeys = Object.keys(flatten(historyDetailCopy.english)).sort();
const historyDetailKeySet = new Set(historyDetailEnglishKeys);
Object.entries(historyDetailCopy).forEach(([language, copy]) => {
  const localized = flatten(copy);
  const missing = historyDetailEnglishKeys.filter((key) => !(key in localized));
  const extra = Object.keys(localized).filter((key) => !historyDetailKeySet.has(key) && !isPluralVariant(key, historyDetailKeySet));
  if (missing.length) failures.push(`history-detail/${language}: missing ${missing.join(', ')}`);
  if (extra.length) failures.push(`history-detail/${language}: unexpected ${extra.join(', ')}`);
});

const knowledgeSupportEnglishKeys = Object.keys(flatten(knowledgeSupportCopy.english)).sort();
const knowledgeSupportKeySet = new Set(knowledgeSupportEnglishKeys);
Object.entries(knowledgeSupportCopy).forEach(([language, copy]) => {
  const localized = flatten(copy);
  const missing = knowledgeSupportEnglishKeys.filter((key) => !(key in localized));
  const extra = Object.keys(localized).filter((key) => !knowledgeSupportKeySet.has(key) && !isPluralVariant(key, knowledgeSupportKeySet));
  if (missing.length) failures.push(`knowledge-support/${language}: missing ${missing.join(', ')}`);
  if (extra.length) failures.push(`knowledge-support/${language}: unexpected ${extra.join(', ')}`);
});

const accountNotificationsEnglishKeys = Object.keys(flatten(accountNotificationsCopy.english)).sort();
const accountNotificationsKeySet = new Set(accountNotificationsEnglishKeys);
Object.entries(accountNotificationsCopy).forEach(([language, copy]) => {
  const localized = flatten(copy);
  const missing = accountNotificationsEnglishKeys.filter((key) => !(key in localized));
  const extra = Object.keys(localized).filter((key) => !accountNotificationsKeySet.has(key) && !isPluralVariant(key, accountNotificationsKeySet));
  if (missing.length) failures.push(`account-notifications/${language}: missing ${missing.join(', ')}`);
  if (extra.length) failures.push(`account-notifications/${language}: unexpected ${extra.join(', ')}`);
});

const accountSecurityActionsEnglishKeys = Object.keys(flatten(accountSecurityActionsCopy.english)).sort();
const accountSecurityActionsKeySet = new Set(accountSecurityActionsEnglishKeys);
Object.entries(accountSecurityActionsCopy).forEach(([language, copy]) => {
  const localized = flatten(copy);
  const missing = accountSecurityActionsEnglishKeys.filter((key) => !(key in localized));
  const extra = Object.keys(localized).filter((key) => !accountSecurityActionsKeySet.has(key) && !isPluralVariant(key, accountSecurityActionsKeySet));
  if (missing.length) failures.push(`account-security-actions/${language}: missing ${missing.join(', ')}`);
  if (extra.length) failures.push(`account-security-actions/${language}: unexpected ${extra.join(', ')}`);
});

const authDeepEnglishKeys = Object.keys(flatten(authDeepCopy.english)).sort();
const authDeepKeySet = new Set(authDeepEnglishKeys);
Object.entries(authDeepCopy).forEach(([language, copy]) => {
  const localized = flatten(copy);
  const missing = authDeepEnglishKeys.filter((key) => !(key in localized));
  const extra = Object.keys(localized).filter((key) => !authDeepKeySet.has(key) && !isPluralVariant(key, authDeepKeySet));
  if (missing.length) failures.push(`auth-deep/${language}: missing ${missing.join(', ')}`);
  if (extra.length) failures.push(`auth-deep/${language}: unexpected ${extra.join(', ')}`);
});

const visibleAttributes = new Set(['accessibilityLabel', 'placeholder', 'label', 'title']);

const walk = (node, visit) => {
  if (!node || typeof node !== 'object') return;
  visit(node);
  Object.entries(node).forEach(([key, value]) => {
    if (key === 'loc' || key === 'start' || key === 'end') return;
    if (Array.isArray(value)) value.forEach((child) => walk(child, visit));
    else if (value && typeof value === 'object' && value.type) walk(value, visit);
  });
};

const findSourceFiles = (directory) => fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
  const absolute = path.join(directory, entry.name);
  if (entry.isDirectory()) return findSourceFiles(absolute);
  if (!/\.[jt]sx?$/.test(entry.name)) return [];
  return [path.relative(projectRoot, absolute)];
});

const filesToScan = reportAll
  ? findSourceFiles(path.join(projectRoot, 'src'))
  : protectedFiles;
const hardcodedFindings = [];

filesToScan.forEach((relativePath) => {
  const source = fs.readFileSync(path.join(projectRoot, relativePath), 'utf8');
  const ast = parse(source, { sourceType: 'module', plugins: ['jsx'] });
  walk(ast, (node) => {
    if (
      node.type === 'CallExpression'
      && node.callee?.type === 'Identifier'
      && node.callee.name === 't'
      && node.arguments?.[0]?.type === 'StringLiteral'
      && node.arguments[0].value.startsWith('premiumUi.')
    ) {
      const referencedKey = node.arguments[0].value.slice('premiumUi.'.length);
      if (!englishKeySet.has(referencedKey) && !referencedKey.includes('${')) {
        failures.push(`${relativePath}:${node.loc?.start.line}: unknown premium key “${node.arguments[0].value}”`);
      }
    }
    if (node.type === 'JSXText') {
      const text = node.value.replace(/\s+/g, ' ').trim();
      if (/[A-Za-z]{2}/.test(text)) hardcodedFindings.push(`${relativePath}:${node.loc?.start.line}: hardcoded text “${text.slice(0, 90)}”`);
    }
    if (node.type === 'JSXAttribute' && visibleAttributes.has(node.name?.name) && node.value?.type === 'StringLiteral' && /[A-Za-z]{2}/.test(node.value.value)) {
      hardcodedFindings.push(`${relativePath}:${node.loc?.start.line}: hardcoded attribute “${node.value.value}”`);
    }
  });
});

if (reportAll) {
  const counts = new Map();
  hardcodedFindings.forEach((finding) => {
    const file = finding.split(':')[0];
    counts.set(file, (counts.get(file) || 0) + 1);
  });
  console.log(`Visible hardcoded copy report: ${hardcodedFindings.length} findings across ${counts.size} files.`);
  [...counts.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .forEach(([file, count]) => console.log(`${String(count).padStart(4)}  ${file}`));
  process.exit(failures.length ? 1 : 0);
}

failures.push(...hardcodedFindings);

if (failures.length) {
  console.error(`i18n audit failed (${failures.length} issues):`);
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(`i18n audit passed: ${englishKeys.length} premium keys, ${lifeAnalysisEnglishKeys.length + lifeAnalysisPdfEnglishKeys.length} Life Analysis keys, ${historyUiEnglishKeys.length + historyDetailEnglishKeys.length} history keys, ${knowledgeSupportEnglishKeys.length} knowledge/support keys, and ${accountNotificationsEnglishKeys.length} notification keys across ${Object.keys(premiumCopy).length} languages; ${protectedFiles.length} screens protected.`);
