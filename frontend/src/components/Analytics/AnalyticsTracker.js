import { useEffect } from 'react';
import { useAnalytics } from '../../hooks/useAnalytics';

const AnalyticsTracker = ({ user, onLogin, onLogout }) => {
  const { trackEvent } = useAnalytics();

  useEffect(() => {
    if (user && trackEvent) {
      trackEvent('user_session_start', 'engagement', 'authenticated_user');
    }
  }, [user, trackEvent]);

  return null;
};

export default AnalyticsTracker;