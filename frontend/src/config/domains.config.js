// Domain configuration for multi-domain setup
export const DOMAIN_CONFIG = {
  ASTROVISHNU: {
    domain: 'astrovishnu.com',
    userType: 'software',
    homepage: 'dashboard',
    title: 'AstroVishnu - Professional Astrology Software',
    theme: 'software'
  },
  ASTROROSHNI: {
    domain: 'astroroshni.com', 
    userType: 'general',
    homepage: 'astroroshnihomepage',
    title: 'AstroRoshni - Astrology Services',
    theme: 'general'
  },
  ASTROCLICK: {
    domain: 'astroclick.net',
    userType: 'legacy',
    homepage: 'dashboard',
    title: 'AstroClick - Astrology Platform',
    theme: 'legacy'
  }
};

// Get current domain configuration
export const getCurrentDomainConfig = () => {
  const hostname = window.location.hostname;
  
  // For testing: check URL params first
  const urlParams = new URLSearchParams(window.location.search);
  const testDomain = urlParams.get('domain');
  
  if (testDomain === 'astroroshni') {
    return DOMAIN_CONFIG.ASTROROSHNI;
  }
  if (testDomain === 'astrovishnu') {
    return DOMAIN_CONFIG.ASTROVISHNU;
  }
  
  // Check for exact domain matches
  for (const config of Object.values(DOMAIN_CONFIG)) {
    if (hostname === config.domain || hostname === `www.${config.domain}`) {
      return config;
    }
  }
  
  // Default to AstroRoshni for localhost/unknown domains
  return DOMAIN_CONFIG.ASTROROSHNI;
};

// Check if user has access to a platform
export const hasAccess = (user, platform) => {
  if (!user || !user.subscriptions) return false;
  return user.subscriptions[platform] && user.subscriptions[platform].status === 'active';
};

// Check if user has specific feature access
export const hasFeatureAccess = (user, platform, feature) => {
  if (!hasAccess(user, platform)) return false;
  const subscription = user.subscriptions[platform];
  return subscription.features[feature] === true;
};

/** True when we should not send the user to another origin based on subscriptions. */
function shouldBypassSubscriptionDomainRedirect() {
  if (typeof window === 'undefined') return false;
  if (process.env.REACT_APP_DISABLE_SUBSCRIPTION_DOMAIN_REDIRECT === 'true') {
    return true;
  }
  const h = window.location.hostname;
  return h === 'localhost' || h === '127.0.0.1' || h === '[::1]';
}

// Get redirect URL based on user subscriptions and current domain
export const getRedirectUrl = (user) => {
  if (shouldBypassSubscriptionDomainRedirect()) {
    return null;
  }

  const currentDomain = getCurrentDomainConfig();

  if (!user || !user.subscriptions) {
    return null; // No redirect for unauthenticated users
  }

  const hasAstrovishnu = hasAccess(user, 'astrovishnu');
  const hasAstroroshni = hasAccess(user, 'astroroshni');

  // If user has both platforms, let them stay on current domain
  if (hasAstrovishnu && hasAstroroshni) {
    return null;
  }

  // AstroVishnu-only on the AstroRoshni / consumer domain → send them to the software site.
  if (hasAstrovishnu && !hasAstroroshni && currentDomain.userType === 'general') {
    return `https://${DOMAIN_CONFIG.ASTROVISHNU.domain}`;
  }

  // We intentionally do not redirect to astroroshni.com from AstroVishnu (or from localhost
  // with ?domain=astrovishnu): users stay on the site they opened. If subscription data
  // only lists Astroroshni, they remain here instead of being bounced away.

  return null;
};

// Get user's primary platform (platform with highest tier subscription)
export const getPrimaryPlatform = (user) => {
  if (!user || !user.subscriptions) return null;
  
  const astrovishnu = user.subscriptions.astrovishnu;
  const astroroshni = user.subscriptions.astroroshni;
  
  // If user has both, prefer the one with premium features
  if (astrovishnu && astroroshni) {
    if (astrovishnu.plan_name === 'Premium') return 'astrovishnu';
    if (astroroshni.plan_name === 'Premium') return 'astroroshni';
    return 'astrovishnu'; // Default to astrovishnu if both are same tier
  }
  
  if (astrovishnu) return 'astrovishnu';
  if (astroroshni) return 'astroroshni';
  
  return null;
};

/** sessionStorage flag: open BirthFormModal (change native) after landing on AstroRoshni homepage */
export const ASTROROSHNI_OPEN_NATIVE_SELECTOR_SESSION_KEY = 'astroroshni_open_native_selector';