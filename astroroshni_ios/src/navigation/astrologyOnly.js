import { Alert } from 'react-native';
import { IS_ASTROLOGY_ONLY } from '../config/appVariant';

/** Routes that imply fortune-telling, life forecasting, or trading predictions. */
export const BLOCKED_ROUTES = new Set([
  'EventScreen',
  'AnalysisHub',
  'AnalysisDetail',
  'KarmaAnalysis',
  'TradingDashboard',
  'TradingCalendar',
  'ChildbirthPlanner',
  'MuhuratHub',
  'UniversalMuhurat',
  'Numerology',
  'FinancialDashboard',
  'SectorDetail',
  'AllOpportunities',
  'MundaneHub',
]);

export function isBlockedRoute(routeName) {
  return IS_ASTROLOGY_ONLY && BLOCKED_ROUTES.has(routeName);
}

/**
 * Navigate only if allowed in the educational iOS build.
 * @returns {boolean} whether navigation was performed
 */
export function navigateSafe(navigation, routeName, params) {
  if (isBlockedRoute(routeName)) {
    Alert.alert(
      'Study edition',
      'This feature is not included in AstroRoshni Study. Use charts, dashas, and Learn chat to explore Vedic chart techniques.',
      [{ text: 'OK' }]
    );
    return false;
  }
  navigation.navigate(routeName, params);
  return true;
}
