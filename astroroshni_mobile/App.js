import React, { useState, useEffect, useRef } from 'react';
import { AppState, Platform } from 'react-native';
import { DefaultTheme, NavigationContainer, getPathFromState, getStateFromPath } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar, View, ActivityIndicator, Animated, Text, TouchableOpacity, Linking, ScrollView, StyleSheet } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import * as Application from 'expo-application';
import * as Device from 'expo-device';
import { useTranslation } from 'react-i18next';
import { LinearGradient } from 'expo-linear-gradient';

import i18n from './src/locales/i18n';

import WelcomeScreen from './src/components/Welcome/WelcomeScreen';
import ModernAuthFlow from './src/components/Auth/ModernAuthFlow';
import WebContinueScreen from './src/components/Auth/WebContinueScreen';
import { normalizeWebContinueToken } from './src/utils/webContinueToken';
import ChatScreen from './src/components/Chat/ChatScreen';
import ChatHistoryScreen from './src/components/Chat/ChatHistoryScreen';
import ChatViewScreen from './src/components/Chat/ChatViewScreen';
import PodcastHistoryScreen from './src/components/Chat/PodcastHistoryScreen';
import SpeechChatScreen from './src/components/Chat/SpeechChatScreen';
import BirthFormScreen from './src/components/BirthForm/BirthFormScreen';
import BirthProfileIntroScreen from './src/components/BirthProfileIntro/BirthProfileIntroScreen';
import SelectNativeScreen from './src/components/Native/SelectNativeScreen';
import CreditScreen from './src/credits/CreditScreen';
import ProfileScreen from './src/components/Profile/ProfileScreen';
import AccountSecurityScreen from './src/components/Profile/AccountSecurityScreen';
import AnalysisHubScreen from './src/components/Analysis/AnalysisHubScreen';
import AnalysisDetailScreen from './src/components/Analysis/AnalysisDetailScreen';
import LongevityScreen from './src/components/Longevity/LongevityScreen';
import RelationshipMatchScreen from './src/components/Relationship/RelationshipMatchScreen';
import ReportsStudioScreen from './src/components/Reports/ReportsStudioScreen';
import ReportViewerScreen from './src/components/Reports/ReportViewerScreen';
import ReportHistoryScreen from './src/components/Reports/ReportHistoryScreen';
import KarmaAnalysisScreen from './src/components/KarmaAnalysis/KarmaAnalysisScreen';
import ChartScreen from './src/components/Chart/ChartScreen';
import ActivationExplorerScreen from './src/components/Chart/ActivationExplorerScreen';
import ChartsHubScreen from './src/components/Chart/ChartsHubScreen';
import PlanetaryPositionsScreen from './src/components/Chart/PlanetaryPositionsScreen';
import TradingDashboardScreen from './src/components/Trading/TradingDashboardScreen';
import TradingCalendarScreen from './src/components/Trading/TradingCalendarScreen';
import ChildbirthPlannerScreen from './src/components/ChildbirthPlannerScreen';
import MuhuratHubScreen from './src/components/MuhuratHubScreen';
import DailyPanchangScreen from './src/components/Panchang/DailyPanchangScreen';
import { PanditHome, PanditPractice } from './src/components/Pandit/PanditDeskRoot';
import UniversalMuhuratScreen from './src/components/UniversalMuhuratScreen';
import EventScreen from './src/components/EventScreen';
import MonthlyDeepScreen from './src/components/MonthlyDeepScreen';
import AshtakvargaOracle from './src/components/Ashtakvarga/AshtakvargaOracle';
import AshtakvargaHistoryScreen from './src/components/Ashtakvarga/AshtakvargaHistoryScreen';
import AshtakvargaHistoryDetailScreen from './src/components/Ashtakvarga/AshtakvargaHistoryDetailScreen';
import NumerologyScreen from './src/components/Numerology/NumerologyScreen';
import FinancialDashboard from './src/components/Financial/FinancialDashboard';
import SectorDetailScreen from './src/components/Financial/SectorDetailScreen';
import AllOpportunitiesScreen from './src/components/Financial/AllOpportunitiesScreen';
import KotaChakraScreen from './src/components/KotaChakra/KotaChakraScreen';
import FactsScreen from './src/components/Facts/FactsScreen';
import ShadbalaScreen from './src/components/Shadbala/ShadbalaScreen';
import YogaScreen from './src/components/Yogas/YogaScreen';
import KPScreen from './src/screens/KPScreen';
import SadeSatiScreen from './src/components/SadeSati/SadeSatiScreen';
import NakshatraCalendarScreen from './src/components/NakshatraCalendar/NakshatraCalendarScreen';
import NakshatraGuideScreen from './src/components/NakshatraGuide/NakshatraGuideScreen';
import CosmicRingScreen from './src/components/CosmicRing/CosmicRingScreen';
import MundaneHubScreen from './src/components/Chat/MundaneHubScreen';
import BlogListScreen from './src/components/Blog/BlogListScreen';
import BlogPostDetailScreen from './src/components/Blog/BlogPostDetailScreen';
import BlogLinkScreen from './src/components/Blog/BlogLinkScreen';
import NudgeInboxScreen from './src/components/Notifications/NudgeInboxScreen';
import GlobalErrorHandler from './src/components/GlobalErrorHandler';
import ErrorOverlay from './src/components/ErrorOverlay';
import ErrorBoundary from './src/components/ErrorBoundary';
import AboutScreen from './src/components/About/AboutScreen';
import SupportScreen from './src/components/Support/SupportScreen';
import MembershipComparisonScreen from './src/components/Support/MembershipComparisonScreen';
import { CreditProvider } from './src/credits/CreditContext';
import { AuthGateProvider } from './src/auth/AuthGateContext';
import { ThemeProvider, ThemedStatusBar, useTheme } from './src/context/ThemeContext';
import { ErrorProvider } from './src/context/ErrorContext';
import { storage } from './src/services/storage';
import SplashScreen from './src/components/SplashScreen';
import { attachSentryNavigation } from './src/services/instrumentSentry';
import {
  clearFatalRuntimeError,
  installRuntimeGuard,
  subscribeToFatalRuntimeError,
} from './src/services/runtimeGuard';
import { API_BASE_URL, getEndpoint } from './src/utils/constants';
import { initFacebookAnalytics } from './src/services/facebookAnalytics';
import { trackNavigationRoute } from './src/services/navigationAnalytics';
import { trackGA4EventOnly } from './src/utils/analytics';
import AddToHomeScreenPrompt from './src/platform/AddToHomeScreenPrompt';
import WebAlertProvider from './src/platform/WebAlertProvider';
// Push notifications: imported lazily in useEffect to avoid touching native module at launch (reduces iOS device crash risk).

const Stack = createStackNavigator();
const transparentNavigationTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: 'transparent',
    card: 'transparent',
  },
};

function ThemedAppBackground({ children }) {
  const { colors } = useTheme();
  const gradient = colors.homeGradient || [
    colors.background,
    colors.backgroundSecondary || colors.background,
    colors.background,
  ];

  return (
    <LinearGradient colors={gradient} style={themedAppBackgroundStyles.fill}>
      {children}
    </LinearGradient>
  );
}

const themedAppBackgroundStyles = StyleSheet.create({
  fill: {
    flex: 1,
    ...(Platform.OS === 'web' ? { minHeight: 0, height: '100%', overflow: 'hidden' } : null),
  },
});

function ForceUpdateScreen({ info, onUpdate }) {
  const { colors, typography } = useTheme();
  const { t } = useTranslation();
  const releaseNotes = info?.releaseNotes;
  const platformLabel = info?.platform === 'ios' ? 'iOS' : 'Android';

  return (
    <View style={[forceUpdateStyles.screen, { backgroundColor: colors.background }]}>
      <ThemedStatusBar />
      <View
        pointerEvents="none"
        style={[
          forceUpdateStyles.orbit,
          forceUpdateStyles.orbitLarge,
          { borderColor: colors.cosmicLine },
        ]}
      />
      <View
        pointerEvents="none"
        style={[
          forceUpdateStyles.orbit,
          forceUpdateStyles.orbitSmall,
          { borderColor: colors.cosmicLine },
        ]}
      />

      <ScrollView
        contentContainerStyle={forceUpdateStyles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View
          style={[
            forceUpdateStyles.hero,
            { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine },
          ]}
        >
          <View style={[forceUpdateStyles.heroRule, { backgroundColor: colors.accent }]} />
          <Text style={[forceUpdateStyles.eyebrow, typography?.eyebrow, { color: colors.accent }]}>{t('appUpdate.eyebrow')}</Text>
          <Text style={[forceUpdateStyles.title, { color: colors.textInverse }]}>{t('appUpdate.title')}</Text>
          <Text style={[forceUpdateStyles.heroBody, { color: colors.textInverseMuted }]}>{t('appUpdate.body')}</Text>

          <View style={[forceUpdateStyles.versionTrack, { borderColor: colors.cosmicLine }]}>
            <View style={forceUpdateStyles.versionItem}>
              <Text style={[forceUpdateStyles.versionLabel, { color: colors.textInverseMuted }]}>{t('appUpdate.yourVersion')}</Text>
              <Text style={[forceUpdateStyles.versionValue, { color: colors.textInverse }]}>{info?.currentVersion || '—'}</Text>
            </View>
            <Text style={[forceUpdateStyles.versionArrow, { color: colors.accent }]}>→</Text>
            <View style={[forceUpdateStyles.versionItem, forceUpdateStyles.versionItemEnd]}>
              <Text style={[forceUpdateStyles.versionLabel, { color: colors.textInverseMuted }]}>{t('appUpdate.required')}</Text>
              <Text style={[forceUpdateStyles.versionValue, { color: colors.accent }]}>{info?.minVersion || '—'}</Text>
            </View>
          </View>
        </View>

        {releaseNotes ? (
          <View style={[forceUpdateStyles.notes, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
            <Text style={[forceUpdateStyles.notesEyebrow, typography?.eyebrow, { color: colors.primary }]}>{t('appUpdate.whatsNew')}</Text>
            <Text style={[forceUpdateStyles.notesBody, { color: colors.text }]}>{releaseNotes}</Text>
          </View>
        ) : null}

        <TouchableOpacity
          onPress={onUpdate}
          activeOpacity={0.86}
          style={[forceUpdateStyles.updateButton, { backgroundColor: colors.primaryStrong }]}
          accessibilityRole="button"
          accessibilityLabel={t('appUpdate.accessibility', { platform: platformLabel })}
        >
          <Text style={[forceUpdateStyles.updateButtonText, { color: colors.onPrimary }]}>{t('appUpdate.update')}</Text>
          <Text style={[forceUpdateStyles.updateArrow, { color: colors.onPrimary }]}>↗</Text>
        </TouchableOpacity>
        <Text style={[forceUpdateStyles.storeHint, { color: colors.textTertiary }]}>{t('appUpdate.opensStore', { store: t(platformLabel === 'iOS' ? 'appUpdate.appStore' : 'appUpdate.playStore') })}</Text>
      </ScrollView>
    </View>
  );
}

const forceUpdateStyles = StyleSheet.create({
  screen: { flex: 1, overflow: 'hidden' },
  scrollContent: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: 22, paddingVertical: 42 },
  orbit: { position: 'absolute', borderWidth: 1, borderRadius: 999 },
  orbitLarge: { width: 310, height: 310, right: -155, top: -105 },
  orbitSmall: { width: 180, height: 180, left: -105, bottom: 20 },
  hero: { width: '100%', maxWidth: 460, alignSelf: 'center', padding: 28, borderWidth: 1, borderRadius: 30, overflow: 'hidden' },
  heroRule: { width: 54, height: 2, marginBottom: 24 },
  eyebrow: { fontSize: 11, lineHeight: 15, fontWeight: '800', letterSpacing: 2.1, marginBottom: 14 },
  title: { fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 44, lineHeight: 48, fontWeight: '500', marginBottom: 18 },
  heroBody: { fontSize: 16, lineHeight: 25, marginBottom: 26 },
  versionTrack: { flexDirection: 'row', alignItems: 'center', borderTopWidth: 1, paddingTop: 20 },
  versionItem: { flex: 1 },
  versionItemEnd: { alignItems: 'flex-end' },
  versionLabel: { fontSize: 10, fontWeight: '800', letterSpacing: 1.3, marginBottom: 5 },
  versionValue: { fontSize: 22, lineHeight: 28, fontWeight: '700' },
  versionArrow: { fontSize: 22, paddingHorizontal: 16 },
  notes: { width: '100%', maxWidth: 460, alignSelf: 'center', borderWidth: 1, borderRadius: 22, padding: 20, marginTop: 16 },
  notesEyebrow: { fontSize: 10, lineHeight: 14, fontWeight: '800', letterSpacing: 1.7, marginBottom: 9 },
  notesBody: { fontSize: 15, lineHeight: 23 },
  updateButton: { width: '100%', maxWidth: 460, minHeight: 58, alignSelf: 'center', borderRadius: 999, marginTop: 20, paddingHorizontal: 24, flexDirection: 'row', alignItems: 'center', justifyContent: 'center' },
  updateButtonText: { fontSize: 16, lineHeight: 22, fontWeight: '800' },
  updateArrow: { position: 'absolute', right: 23, fontSize: 20 },
  storeHint: { marginTop: 12, textAlign: 'center', fontSize: 12, lineHeight: 18 },
});

/** Production Expo Web lives at /mobile/; local `expo start --web` stays at /. */
function isMobileWebShell() {
  if (Platform.OS !== 'web' || typeof window === 'undefined') return false;
  try {
    if (typeof document !== 'undefined') {
      const shell = document.documentElement?.getAttribute?.('data-ar-shell');
      if (shell === 'expo-web') return true;
    }
    return /^\/mobile(\/|$)/.test(String(window.location?.pathname || ''));
  } catch (_) {
    return false;
  }
}

function getWebLinkingPrefixes() {
  if (typeof window === 'undefined' || !window.location?.origin) {
    return [];
  }
  const origin = window.location.origin;
  // Never include bare origin while inside /mobile/ — React Navigation would rewrite
  // Home ('') to `/`, and the next PWA launch can restore the CRA website.
  if (isMobileWebShell()) {
    return [`${origin}/mobile`];
  }
  return [origin];
}

function ensureMobileWebPath(path) {
  const clean = String(path || '').replace(/^\/+/, '');
  return clean ? `/mobile/${clean}` : '/mobile/';
}

/** Keep history URL under /mobile/ if navigation ever drops the prefix. */
function guardMobileWebHistoryUrl() {
  if (!isMobileWebShell() || typeof window === 'undefined' || !window.history?.replaceState) {
    return;
  }
  try {
    const path = String(window.location?.pathname || '');
    if (path === '/mobile' || path === '/mobile/') return;
    if (path === '/' || path === '') {
      window.history.replaceState(
        window.history.state,
        '',
        `/mobile/${window.location.search || ''}${window.location.hash || ''}`,
      );
      return;
    }
    if (
      path.startsWith('/') &&
      !path.startsWith('/mobile/') &&
      !path.startsWith('/_expo') &&
      !path.startsWith('/api')
    ) {
      window.history.replaceState(
        window.history.state,
        '',
        `/mobile${path}${window.location.search || ''}${window.location.hash || ''}`,
      );
    }
  } catch (_) {
    /* ignore */
  }
}

const linking = {
  prefixes: [
    'https://astroroshni.com/mobile',
    'https://www.astroroshni.com/mobile',
    'astroroshni://',
    ...getWebLinkingPrefixes(),
    // Keep site-root prefixes last and only for native / local web deep links.
    ...(isMobileWebShell()
      ? []
      : ['https://astroroshni.com', 'https://www.astroroshni.com']),
  ],
  config: {
    screens: {
      Home: '',
      KarmaAnalysis: 'karma-analysis',
      RelationshipMatch: 'kundli-matching',
      ReportsStudio: 'reports',
      ChartsHub: 'charts',
      ActivationExplorer: 'charts/activations',
      ReportViewer: 'reports/view',
      ReportHistory: 'reports/history',
      BlogList: 'blog',
      BlogPostDetail: 'blog/:slug',
      Profile: 'profile',
      Credits: 'credits',
      WebContinue: 'c/:token',
      About: 'about',
      Support: 'contact',
      MuhuratHub: 'muhurat-finder',
      UniversalMuhurat: 'muhurat',
      PanditHome: 'pandit',
      PanditPractice: 'pandit/practice',
      NakshatraCalendar: 'nakshatras',
      NakshatraGuide: 'nakshatra-study',
      AnalysisHub: 'analysis',
    },
  },
  getStateFromPath(path, options) {
    let raw = String(path || '').split('?')[0];
    // Tolerate /mobile prefix if the matched linking prefix did not strip it.
    raw = raw.replace(/^\/?mobile\/?/, '/');
    const normalizedPath = `/${raw.replace(/^\/+|\/+$/g, '')}`;
    // Let App bootstrap choose Welcome vs Home for the site root (/ or /mobile).
    if (normalizedPath === '/') {
      return undefined;
    }
    const pathAliases = {
      '/panchang': '/muhurat',
      '/monthly-panchang': '/muhurat',
      '/festivals': '/muhurat',
      '/festivals/monthly': '/muhurat',
      '/marriage-analysis': '/kundli-matching',
      '/policy': '/about',
      '/pandit-desk': '/pandit',
      '/for-pandits': '/pandit',
    };
    return getStateFromPath(pathAliases[normalizedPath] || raw, options);
  },
  getPathFromState(state, options) {
    const path = getPathFromState(state, options);
    if (isMobileWebShell()) {
      return ensureMobileWebPath(path);
    }
    return path;
  },
};
const APP_CONFIG_FETCH_TIMEOUT_MS = 2500;

/**
 * WhatsApp / CRM continue links.
 * Prefer ?c=TOKEN on /mobile/ (works on GCS without SPA deep-link rewrite).
 * Also accept legacy path /mobile/c/:token when the edge router is in front.
 */
function getWebContinueTokenFromLocation() {
  if (Platform.OS !== 'web' || typeof window === 'undefined') return null;
  try {
    const params = new URLSearchParams(String(window.location?.search || ''));
    const fromQuery = String(params.get('c') || params.get('continue') || '').trim();
    if (fromQuery) return normalizeWebContinueToken(decodeURIComponent(fromQuery));

    const path = String(window.location?.pathname || '');
    const match = path.match(/\/(?:mobile\/)?c\/([^/?#]+)/i);
    if (!match?.[1]) return null;
    return normalizeWebContinueToken(decodeURIComponent(match[1])) || null;
  } catch (_) {
    return null;
  }
}

const MIUI_BRAND_RE = /xiaomi|redmi|poco/i;
const isMiuiFontBugDevice =
  Platform.OS === 'android' &&
  (
    MIUI_BRAND_RE.test(String(Device.brand || '')) ||
    MIUI_BRAND_RE.test(String(Device.manufacturer || ''))
  );

const normalizeMiuiFontWeight = (value) => {
  if (value == null) return value;
  if (value === 'normal' || value === '400' || value === 400) return 'normal';
  if (value === 'bold' || value === '700' || value === 700) return 'bold';

  const numeric = Number(value);
  if (Number.isFinite(numeric)) {
    return numeric >= 600 ? 'bold' : 'normal';
  }

  const normalized = String(value).trim().toLowerCase();
  if (!normalized) return value;
  if (normalized === 'semibold' || normalized === 'medium' || normalized === '500') return 'normal';
  if (normalized === 'extrabold' || normalized === 'ultrabold' || normalized === '800' || normalized === '900') return 'bold';
  return value;
};

const sanitizeMiuiTextStyle = (style) => {
  if (!style || !isMiuiFontBugDevice) return style;
  if (Array.isArray(style)) return style.map(sanitizeMiuiTextStyle);
  if (typeof style !== 'object') return style;

  const nextStyle = { ...style };
  if ('fontWeight' in nextStyle) {
    nextStyle.fontWeight = normalizeMiuiFontWeight(nextStyle.fontWeight);
  }
  if ('fontVariant' in nextStyle) {
    delete nextStyle.fontVariant;
  }
  return nextStyle;
};

if (isMiuiFontBugDevice && !global.__ASTROROSHNI_MIUI_TEXT_PATCHED__) {
  const originalCreateElement = React.createElement;
  React.createElement = function patchedCreateElement(type, props, ...children) {
    if (type === Text && props?.style) {
      return originalCreateElement(
        type,
        {
          ...props,
          style: sanitizeMiuiTextStyle(props.style),
        },
        ...children
      );
    }
    return originalCreateElement(type, props, ...children);
  };
  global.__ASTROROSHNI_MIUI_TEXT_PATCHED__ = true;
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  // Guest-first: land on Home unless bootstrap decides otherwise (web continue, etc.).
  const [initialRoute, setInitialRoute] = useState('Home');
  const [webContinueToken] = useState(() => getWebContinueTokenFromLocation());
  const [initialTheme, setInitialTheme] = useState(null);
  const [initialPanditMode, setInitialPanditMode] = useState(false);
  const [forceUpdateInfo, setForceUpdateInfo] = useState(null);
  const [fatalRuntimeError, setFatalRuntimeError] = useState(null);
  const [isRecoveringFromCrash, setIsRecoveringFromCrash] = useState(false);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const navigationRef = useRef(null);

  useEffect(() => {
    installRuntimeGuard();
    const unsubscribe = subscribeToFatalRuntimeError(setFatalRuntimeError);

    bootstrap();

    return unsubscribe;
  }, []);

  useEffect(() => {
    if (Platform.OS !== 'web') return undefined;
    guardMobileWebHistoryUrl();
    const onNav = () => guardMobileWebHistoryUrl();
    window.addEventListener('popstate', onNav);
    // Catch delayed history writes from React Navigation after first paint.
    const timer = setInterval(guardMobileWebHistoryUrl, 1500);
    return () => {
      window.removeEventListener('popstate', onNav);
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (!isLoading) {
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 280,
        useNativeDriver: true,
      }).start();
    }
  }, [isLoading]);

  const loadSavedLanguage = async () => {
    try {
      const savedLanguage = await storage.getLanguage();
      if (savedLanguage) {
        i18n.changeLanguage(savedLanguage);
      }
    } catch (error) {
      console.log('Error loading saved language:', error);
    }
  };

  const SPLASH_MIN_MS = Platform.OS === 'web' ? 800 : 1500;

  const checkForceUpdate = async () => {
    let timeoutId = null;
    let controller = null;
    try {
      controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
      if (controller) {
        timeoutId = setTimeout(() => controller.abort(), APP_CONFIG_FETCH_TIMEOUT_MS);
      }
      const res = await fetch(`${API_BASE_URL}${getEndpoint('/app/config')}`, {
        signal: controller?.signal,
      });
      if (!res.ok) return;
      const data = await res.json();

      const minAndroid = Number(data?.min_android_version_code || 0);
      const minIos = Number(data?.min_ios_build_number || 0);
      const releaseNotes =
        typeof data?.app_update_release_notes === 'string' ? data.app_update_release_notes.trim() : '';

      if (Platform.OS === 'android') {
        // Use installed native build number; expoConfig can be stale/mismatched in some release paths.
        const nativeBuild = Number(Application.nativeBuildVersion || 0);
        const fallbackBuild = Number(Constants.expoConfig?.android?.versionCode || 0);
        const current = nativeBuild || fallbackBuild;
        if (minAndroid && current && current < minAndroid) {
          setForceUpdateInfo({
            platform: 'android',
            currentVersion: current,
            minVersion: minAndroid,
            releaseNotes,
          });
        }
      } else if (Platform.OS === 'ios') {
        const nativeBuild = Number(Application.nativeBuildVersion || 0);
        const fallbackBuild = Number(Constants.expoConfig?.ios?.buildNumber || 0);
        const current = nativeBuild || fallbackBuild;
        if (minIos && current && current < minIos) {
          setForceUpdateInfo({
            platform: 'ios',
            currentVersion: current,
            minVersion: minIos,
            releaseNotes,
          });
        }
      }
    } catch (e) {
      // If config fetch fails, do not block app usage.
      if (__DEV__) {
        console.warn('[App] Failed to fetch app config for version gate:', e?.message || e);
      }
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    }
  };

  const bootstrap = async () => {
    const start = Date.now();
    try {
      // Load theme first so first paint has correct theme (avoids flash/flicker)
      const savedTheme = await AsyncStorage.getItem('appTheme');
      const panditFlag = await AsyncStorage.getItem('panditMode');
      const panditOn = panditFlag === '1' || panditFlag === 'true';
      setInitialPanditMode(panditOn);
      // ThemeProvider normalizes legacy light/dark values as well as the new
      // semantic theme ids. Heritage is the premium consumer default.
      setInitialTheme(savedTheme || 'heritage');

      loadSavedLanguage();

      if (Constants.appOwnership !== 'expo') {
        initFacebookAnalytics().catch(() => {});
      }

      try {
        // Avoid noisy CORS failures when developing Expo Web off astroroshni.com.
        const sameOriginWeb =
          Platform.OS !== 'web' ||
          (typeof window !== 'undefined' &&
            /astroroshni\.com$/i.test(window.location?.hostname || ''));
        if (sameOriginWeb) {
          const { sendAcquisitionFirstOpenOnce } = require('./src/services/acquisitionTracking');
          // Attribution is useful but must never delay the first usable screen.
          sendAcquisitionFirstOpenOnce().catch(() => {});
        }
      } catch (_) {
        /* optional */
      }

      // Check if this build is still allowed by backend config.
      await checkForceUpdate();

      const continueToken = getWebContinueTokenFromLocation() || webContinueToken;
      if (continueToken) {
        setInitialRoute('WebContinue');
        trackGA4EventOnly('app_open', {
          auth_state: 'web_continue',
          app_version: Application.nativeApplicationVersion || '',
          app_build: Application.nativeBuildVersion || '',
          platform: Platform.OS,
        }).catch(() => {});
        return;
      }

      const authToken = await storage.getAuthToken();
      trackGA4EventOnly('app_open', {
        auth_state: authToken ? 'logged_in' : 'guest',
        app_version: Application.nativeApplicationVersion || '',
        app_build: Application.nativeBuildVersion || '',
        platform: Platform.OS,
      }).catch(() => {});

      if (authToken) {
        try {
          const { chartAPI } = require('./src/services/api');
          // Suppress global 401 handler during bootstrap — we handle guest fallback here.
          const response = await Promise.race([
            chartAPI.getExistingCharts('', 10, 0, { suppressGlobalError: true }),
            new Promise((_, reject) =>
              setTimeout(() => reject(new Error('Timeout')), 3500)
            )
          ]);
          if (response.data && response.data.charts && response.data.charts.length > 0) {
            await storage.getBirthDetails();
          }
          setInitialRoute('Home');
        } catch (apiError) {
          // Backend GET /api/birth-charts uses get_current_user → returns 401 for invalid/expired token.
          // Axios puts status on error.response.status. Only clear session on 401; on timeout/network error go Home.
          const status = apiError?.response?.status;
          const isUnauth = status === 401;
          if (__DEV__ && apiError) {
            console.log('[Bootstrap] getExistingCharts failed:', status ?? 'no status', apiError?.message || apiError?.code);
          }
          if (isUnauth) {
            try {
              await storage.clearAccountSession();
            } catch (clearErr) {
              console.log('Clear storage on bootstrap auth fail:', clearErr);
            }
            // Expired session: still allow guest Home (free tools) instead of hard Welcome wall.
            setInitialRoute('Home');
            trackGA4EventOnly('guest_home_opened', { source: 'expired_session' }).catch(() => {});
            try {
              const { trackGuestActivity } = require('./src/services/acquisitionTracking');
              trackGuestActivity('guest_open').catch(() => {});
            } catch (_) {}
          } else {
            setInitialRoute('Home');
          }
        }
      } else {
        // Guests can explore free chart tools without registering.
        setInitialRoute('Home');
        trackGA4EventOnly('guest_home_opened', { source: 'cold_start' }).catch(() => {});
        try {
          const { trackGuestActivity } = require('./src/services/acquisitionTracking');
          trackGuestActivity('guest_open').catch(() => {});
        } catch (_) {}
      }
    } catch (error) {
      console.log('Bootstrap error:', error);
      setInitialRoute('Home');
    } finally {
      try {
        const { linkAcquisitionInstallationToUser } = require('./src/services/acquisitionTracking');
        storage.getAuthToken().then((tok) => {
          if (tok) linkAcquisitionInstallationToUser().catch(() => {});
        });
      } catch (_) {
        /* optional */
      }
      const elapsed = Date.now() - start;
      const remaining = Math.max(0, SPLASH_MIN_MS - elapsed);
      setTimeout(() => setIsLoading(false), remaining);
    }
  };

  // When app is ready and user is logged in, register push token; retry on foreground and once after delay.
  // On iOS skip loading the notification module entirely to avoid native crash on device (expo-notifications
  // and/or expo-device can crash when entitlements/APNs config is wrong). Android unchanged.
  const skipPushOnIos = Platform.OS === 'ios';
  useEffect(() => {
    if (isLoading) return;
    if (skipPushOnIos) {
      if (__DEV__) console.warn('[App] Push notifications skipped on iOS (crash workaround).');
      return;
    }
    let notifCleanupRef = null;
    let coldStartTimerRef = null;
    const deferMs = Platform.OS === 'ios' ? 800 : 100;
    const notifSetupTimer = setTimeout(() => {
      try {
        const pushNotifications = require('./src/services/pushNotifications');
        pushNotifications.setupNotificationHandler();
        const cleanup = pushNotifications.setupNotificationResponseListener(navigationRef);
        if (typeof cleanup === 'function') notifCleanupRef = cleanup;
        // When app was killed and opened by notification tap, the tap is not delivered to the listener.
        // Check for last notification response after nav is ready (cold start).
        coldStartTimerRef = setTimeout(() => {
          pushNotifications.handleColdStartNotificationResponse(navigationRef).catch(() => {});
        }, 600);
      } catch (e) {
        if (__DEV__) console.warn('[App] Notification setup failed (non-fatal):', e?.message || e);
      }
    }, deferMs);
    const tryRegisterPush = async () => {
      try {
        const token = await storage.getAuthToken();
        if (!token) return;
        const pushNotifications = require('./src/services/pushNotifications');
        await pushNotifications.syncPushTokenIfPermissionGranted();
      } catch (e) {
        if (__DEV__) console.warn('[App] registerPushToken failed:', e?.message || e);
      }
    };
    tryRegisterPush();
    const delayed = setTimeout(tryRegisterPush, 3000);
    const sub = AppState.addEventListener('change', (state) => {
      if (state === 'active') tryRegisterPush();
    });
    return () => {
      clearTimeout(delayed);
      clearTimeout(notifSetupTimer);
      if (coldStartTimerRef != null) clearTimeout(coldStartTimerRef);
      sub?.remove?.();
      if (typeof notifCleanupRef === 'function') notifCleanupRef();
    };
  }, [isLoading, skipPushOnIos]);

  const handleUpdatePress = () => {
    try {
      if (Platform.OS === 'android') {
        const pkg = Constants.expoConfig?.android?.package || 'com.astroroshni.mobile';
        const playUrl = `https://play.google.com/store/apps/details?id=${pkg}`;
        Linking.openURL(playUrl);
      } else if (Platform.OS === 'ios') {
        // TODO: replace with actual App Store URL for AstroRoshni
        const appStoreUrl = 'https://astroroshni.com';
        Linking.openURL(appStoreUrl);
      }
    } catch (e) {
      if (__DEV__) {
        console.warn('[App] Failed to open store URL:', e?.message || e);
      }
    }
  };

  const handleRecoverFromFatalError = async () => {
    setIsRecoveringFromCrash(true);
    try {
      await clearFatalRuntimeError();
      setFatalRuntimeError(null);
      setForceUpdateInfo(null);
      setIsLoading(true);
      await bootstrap();
    } finally {
      setIsRecoveringFromCrash(false);
    }
  };

  if (isLoading) {
    return (
      <SafeAreaProvider>
        <SplashScreen themeId={initialTheme || 'heritage'} panditMode={initialPanditMode} />
      </SafeAreaProvider>
    );
  }

  if (fatalRuntimeError) {
    return (
      <SafeAreaProvider>
        <StatusBar barStyle="light-content" backgroundColor="#7f1d1d" />
        <View style={{ flex: 1, backgroundColor: '#1f2937', padding: 24, justifyContent: 'center' }}>
          <View
            style={{
              backgroundColor: '#111827',
              borderRadius: 20,
              padding: 24,
              borderWidth: 1,
              borderColor: '#374151',
            }}
          >
            <Text style={{ color: '#f9fafb', fontSize: 24, fontWeight: '700', marginBottom: 12 }}>
              App recovered from an unexpected error
            </Text>
            <Text style={{ color: '#d1d5db', fontSize: 15, lineHeight: 22, marginBottom: 20 }}>
              We blocked a JavaScript crash and moved the app to a safe screen. You can try again without fully closing the app.
            </Text>
            <Text style={{ color: '#fca5a5', fontSize: 13, marginBottom: 24 }}>
              {fatalRuntimeError.message || 'Unknown runtime error'}
            </Text>
            <TouchableOpacity
              onPress={handleRecoverFromFatalError}
              disabled={isRecoveringFromCrash}
              style={{
                backgroundColor: '#f97316',
                borderRadius: 999,
                paddingVertical: 14,
                alignItems: 'center',
                marginBottom: 12,
                opacity: isRecoveringFromCrash ? 0.7 : 1,
              }}
            >
              {isRecoveringFromCrash ? (
                <ActivityIndicator color="#ffffff" />
              ) : (
                <Text style={{ color: '#ffffff', fontSize: 16, fontWeight: '700' }}>Try again</Text>
              )}
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => {
                clearFatalRuntimeError().catch(() => {});
                setFatalRuntimeError(null);
                setInitialRoute('Welcome');
              }}
              style={{
                paddingVertical: 12,
                alignItems: 'center',
              }}
            >
              <Text style={{ color: '#d1d5db', fontSize: 15, fontWeight: '600' }}>Go to welcome screen</Text>
            </TouchableOpacity>
          </View>
        </View>
      </SafeAreaProvider>
    );
  }

  if (forceUpdateInfo) {
    return (
      <SafeAreaProvider>
        <ThemeProvider initialTheme={initialTheme} initialPanditMode={initialPanditMode}>
          <ForceUpdateScreen info={forceUpdateInfo} onUpdate={handleUpdatePress} />
        </ThemeProvider>
      </SafeAreaProvider>
    );
  }

  return (
    <GestureHandlerRootView
      style={{
        flex: 1,
        // Web: fixed shell so Home tabs stay pinned; inner screens scroll.
        ...(Platform.OS === 'web' ? { minHeight: 0, height: '100%', overflow: 'hidden' } : null),
      }}
    >
      <SafeAreaProvider
        style={
          Platform.OS === 'web'
            ? { flex: 1, minHeight: 0, height: '100%', overflow: 'hidden' }
            : undefined
        }
      >
        <ThemeProvider initialTheme={initialTheme} initialPanditMode={initialPanditMode}>
        <WebAlertProvider>
        <ThemedAppBackground>
        <Animated.View
          style={{
            flex: 1,
            opacity: fadeAnim,
            ...(Platform.OS === 'web' ? { minHeight: 0, height: '100%', overflow: 'hidden' } : null),
          }}
        >
          <ErrorProvider>
            <CreditProvider>
              <ErrorBoundary>
              <NavigationContainer
                theme={transparentNavigationTheme}
                linking={linking}
                onStateChange={(state) => {
                  trackNavigationRoute(state);
                  guardMobileWebHistoryUrl();
                }}
                onReady={() => {
                  guardMobileWebHistoryUrl();
                  if (navigationRef.current) {
                    trackNavigationRoute(navigationRef.current.getRootState());
                  }
                }}
                ref={(nav) => {
                  navigationRef.current = nav;
                  attachSentryNavigation(nav);
                }}
              >
              <GlobalErrorHandler />
              <AuthGateProvider>
              <ThemedStatusBar />
        <Stack.Navigator
          initialRouteName={webContinueToken ? 'WebContinue' : initialRoute}
          screenOptions={{
            headerStyle: {
              backgroundColor: '#ff6b35',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
            // Web: no edge-swipe stack gestures (they steal touch from page scroll in device mode).
            gestureEnabled: Platform.OS !== 'web',
            gestureDirection: 'horizontal',
            cardStyle: {
              backgroundColor: 'transparent',
              ...(Platform.OS === 'web'
                ? {
                    flex: 1,
                    minHeight: 0,
                    height: '100%',
                    overflow: 'hidden',
                  }
                : null),
            },
          }}
        >
          <Stack.Screen 
            name="Welcome" 
            component={WelcomeScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Login" 
            component={ModernAuthFlow}
            options={{
              headerShown: false,
              // Inner auth (forgot password, OTP, etc.) is not separate stack routes; without this,
              // iOS edge-swipe pops the whole Login screen (e.g. back to Home after logout bug pattern).
              gestureEnabled: false,
            }}
          />
          <Stack.Screen 
            name="Home" 
            component={ChatScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="BirthForm" 
            component={BirthFormScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="BirthProfileIntro" 
            component={BirthProfileIntroScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="SelectNative" 
            component={SelectNativeScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="ChatHistory" 
            component={ChatHistoryScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="ChatView" 
            component={ChatViewScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="PodcastHistory" 
            component={PodcastHistoryScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="SpeechChat"
            component={SpeechChatScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="MundaneHub" 
            component={MundaneHubScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Credits" 
            component={CreditScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="WebContinue"
            component={WebContinueScreen}
            initialParams={webContinueToken ? { token: webContinueToken } : undefined}
            options={{ headerShown: false, gestureEnabled: false }}
          />
          <Stack.Screen 
            name="Profile" 
            component={ProfileScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="AccountSecurity"
            component={AccountSecurityScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="NudgeInbox"
            component={NudgeInboxScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="AnalysisHub" 
            component={AnalysisHubScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="AnalysisDetail" 
            component={AnalysisDetailScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Longevity"
            component={LongevityScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="RelationshipMatch"
            component={RelationshipMatchScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="ReportsStudio"
            component={ReportsStudioScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="ReportViewer"
            component={ReportViewerScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="ReportHistory"
            component={ReportHistoryScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="KarmaAnalysis" 
            component={KarmaAnalysisScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="ChartsHub"
            component={ChartsHubScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Chart"
            component={ChartScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="ActivationExplorer"
            component={ActivationExplorerScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="TradingDashboard" 
            component={TradingDashboardScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="TradingCalendar" 
            component={TradingCalendarScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="ChildbirthPlanner" 
            component={ChildbirthPlannerScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="MuhuratHub" 
            component={MuhuratHubScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="PanditHome"
            component={PanditHome}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="PanditPractice"
            component={PanditPractice}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="DailyPanchang"
            component={DailyPanchangScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="UniversalMuhurat" 
            component={UniversalMuhuratScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="EventScreen" 
            component={EventScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="MonthlyDeepScreen" 
            component={MonthlyDeepScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="AshtakvargaOracle" 
            component={AshtakvargaOracle}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="AshtakvargaHistory"
            component={AshtakvargaHistoryScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="AshtakvargaHistoryDetail"
            component={AshtakvargaHistoryDetailScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Numerology" 
            component={NumerologyScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="PlanetaryPositions" 
            component={PlanetaryPositionsScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="FinancialDashboard" 
            component={FinancialDashboard}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="SectorDetail" 
            component={SectorDetailScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="AllOpportunities" 
            component={AllOpportunitiesScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="KotaChakra" 
            component={KotaChakraScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Facts" 
            component={FactsScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="About" 
            component={AboutScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Shadbala" 
            component={ShadbalaScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="Yogas" 
            component={YogaScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="KPSystem"
            component={KPScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="SadeSati"
            component={SadeSatiScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="NakshatraCalendar"
            component={NakshatraCalendarScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="NakshatraGuide"
            component={NakshatraGuideScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="CosmicRing"
            component={CosmicRingScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="BlogList" 
            component={BlogListScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="BlogPostDetail" 
            component={BlogPostDetailScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="BlogLink"
            component={BlogLinkScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Support"
            component={SupportScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="MembershipComparison"
            component={MembershipComparisonScreen}
            options={{ headerShown: false }}
          />
        </Stack.Navigator>
        <ErrorOverlay />
        {Platform.OS === 'web' ? <AddToHomeScreenPrompt /> : null}
        </AuthGateProvider>
        </NavigationContainer>
        </ErrorBoundary>
      </CreditProvider>
      </ErrorProvider>
        </Animated.View>
        </ThemedAppBackground>
        </WebAlertProvider>
      </ThemeProvider>
    </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
