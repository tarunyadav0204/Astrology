import { trackScreenView } from '../utils/analytics';
import { trackMobileJourneyEvent } from './journeyTracker';

/** Default Meta ViewContent mapping per stack route (App.js). */
const ROUTE_VIEW_META = {
  Welcome: { content_id: 'welcome', content_type: 'onboarding' },
  Login: { content_id: 'auth_flow', content_type: 'onboarding' },
  Home: { content_id: 'home', content_type: 'main' },
  BirthForm: { content_id: 'birth_form', content_type: 'onboarding' },
  BirthProfileIntro: { content_id: 'birth_profile_intro', content_type: 'onboarding' },
  SelectNative: { content_id: 'select_native', content_type: 'chart' },
  ChatHistory: { content_id: 'chat_history', content_type: 'chat' },
  ChatView: { content_id: 'chat_thread', content_type: 'chat' },
  PodcastHistory: { content_id: 'podcast_history', content_type: 'chat' },
  SpeechChat: { content_id: 'speech_chat', content_type: 'chat' },
  MundaneHub: { content_id: 'mundane_hub', content_type: 'mundane' },
  Credits: { content_id: 'credits_store', content_type: 'monetization' },
  Profile: { content_id: 'profile', content_type: 'account' },
  NudgeInbox: { content_id: 'nudge_inbox', content_type: 'notifications' },
  AnalysisHub: { content_id: 'analysis_hub', content_type: 'analysis' },
  AnalysisDetail: { content_type: 'analysis' },
  RelationshipMatch: { content_id: 'kundli_matching', content_type: 'analysis' },
  KarmaAnalysis: { content_id: 'karma_analysis', content_type: 'analysis' },
  Chart: { content_id: 'birth_chart', content_type: 'chart' },
  PlanetaryPositions: { content_id: 'planetary_positions', content_type: 'chart' },
  TradingDashboard: { content_id: 'trading_dashboard', content_type: 'trading' },
  TradingCalendar: { content_id: 'trading_calendar', content_type: 'trading' },
  ChildbirthPlanner: { content_id: 'childbirth_planner', content_type: 'muhurat' },
  MuhuratHub: { content_id: 'muhurat_hub', content_type: 'muhurat' },
  UniversalMuhurat: { content_id: 'universal_muhurat', content_type: 'muhurat' },
  EventScreen: { content_id: 'life_events', content_type: 'timeline' },
  MonthlyDeepScreen: { content_id: 'monthly_timeline', content_type: 'timeline' },
  AshtakvargaOracle: { content_id: 'ashtakavarga', content_type: 'tools' },
  AshtakvargaHistory: { content_id: 'ashtakavarga_history', content_type: 'tools' },
  AshtakvargaHistoryDetail: { content_id: 'ashtakavarga_detail', content_type: 'tools' },
  Numerology: { content_id: 'numerology', content_type: 'tools' },
  FinancialDashboard: { content_id: 'financial_dashboard', content_type: 'financial' },
  SectorDetail: { content_id: 'sector_detail', content_type: 'financial' },
  AllOpportunities: { content_id: 'all_opportunities', content_type: 'financial' },
  KotaChakra: { content_id: 'kota_chakra', content_type: 'tools' },
  Facts: { content_id: 'facts', content_type: 'education' },
  Shadbala: { content_id: 'shadbala', content_type: 'chart' },
  Yogas: { content_id: 'yogas', content_type: 'chart' },
  KPSystem: { content_id: 'kp_system', content_type: 'chart' },
  SadeSati: { content_id: 'sade_sati', content_type: 'chart' },
  NakshatraCalendar: { content_id: 'nakshatra_calendar', content_type: 'panchang' },
  NakshatraGuide: { content_id: 'nakshatra_guide', content_type: 'education' },
  CosmicRing: { content_id: 'cosmic_ring', content_type: 'tools' },
  BlogList: { content_id: 'blog_list', content_type: 'content' },
  BlogPostDetail: { content_type: 'blog' },
  Support: { content_id: 'support', content_type: 'account' },
  MembershipComparison: { content_id: 'membership_comparison', content_type: 'monetization' },
  About: { content_id: 'about', content_type: 'account' },
  DashaBrowser: { content_id: 'dasha_browser', content_type: 'chart' },
  CascadingDashaBrowser: { content_id: 'cascading_dasha', content_type: 'chart' },
};

let previousMeta = null;
let previousScreenStartedAt = 0;

export function isMainStackRoute(screenName) {
  return Boolean(ROUTE_VIEW_META[screenName]);
}

function getActiveRoute(state) {
  if (!state || !state.routes?.length) return null;
  const index = typeof state.index === 'number' ? state.index : state.routes.length - 1;
  const route = state.routes[index];
  if (!route) return null;
  if (route.state) return getActiveRoute(route.state);
  return route;
}

function resolveViewMeta(route) {
  const name = route?.name || 'Unknown';
  const base = ROUTE_VIEW_META[name] || { content_id: name, content_type: 'screen' };
  const params = route.params || {};

  let content_id = base.content_id || name;
  const content_type = base.content_type || 'screen';

  if (name === 'AnalysisDetail' && params.analysisType) {
    content_id = `analysis:${params.analysisType}`;
  } else if (name === 'BlogPostDetail' && params.slug) {
    content_id = `blog:${params.slug}`;
  } else if (name === 'ChatView' && params.sessionId) {
    content_id = `chat:${params.sessionId}`;
  } else if (name === 'SectorDetail' && params.sector) {
    content_id = `sector:${params.sector}`;
  } else if (name === 'UniversalMuhurat' && params.type) {
    content_id = `muhurat:${params.type}`;
  }

  return { content_id, content_type, route_name: name };
}

function screenKey(meta) {
  return `${meta.route_name}:${meta.content_id}`;
}

function emitScreenExit(meta, startedAt) {
  if (!meta?.route_name) return;
  const durationMs = Math.max(0, Date.now() - startedAt);
  trackMobileJourneyEvent('mobile_screen_exit', {
    screen_name: meta.route_name,
    duration_ms: durationMs,
    resource_type: 'screen',
    resource_id: meta.content_id,
    metadata: {
      content_type: meta.content_type,
      duration_bucket:
        durationMs < 5000 ? 'lt_5s' : durationMs < 30000 ? '5s_30s' : durationMs < 120000 ? '30s_2m' : 'gt_2m',
    },
  });
}

export function trackNavigationRoute(state) {
  const route = getActiveRoute(state);
  if (!route?.name) return;

  const meta = resolveViewMeta(route);
  const key = screenKey(meta);

  const prevKey = previousMeta ? screenKey(previousMeta) : null;
  if (key === prevKey) return;

  if (previousMeta && previousScreenStartedAt) {
    emitScreenExit(previousMeta, previousScreenStartedAt);
  }

  trackScreenView(meta.route_name, {
    content_id: meta.content_id,
    content_type: meta.content_type,
  });

  previousMeta = meta;
  previousScreenStartedAt = Date.now();
}
