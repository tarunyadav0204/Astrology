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

// AstroVishnu is retired. Anyone who still opens that host is sent to AstroRoshni.
export const getRedirectUrl = () => {
  if (typeof window === 'undefined' || shouldBypassSubscriptionDomainRedirect()) {
    return null;
  }

  const host = window.location.hostname;
  if (host === 'astrovishnu.com' || host === 'www.astrovishnu.com') {
    return `https://astroroshni.com${window.location.pathname}${window.location.search}${window.location.hash}`;
  }

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