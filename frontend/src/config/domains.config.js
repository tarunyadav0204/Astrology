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
    domain: 'astroclick.com',
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
    if (hostname.includes(config.domain.replace('.com', ''))) {
      return config;
    }
  }
  
  // Default to AstroClick for localhost/unknown domains
  return DOMAIN_CONFIG.ASTROCLICK;
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

// Get redirect URL based on user subscriptions and current domain
export const getRedirectUrl = (user) => {
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
  
  // If user only has astrovishnu access but is on astroroshni domain
  if (hasAstrovishnu && !hasAstroroshni && currentDomain.userType === 'general') {
    return `https://${DOMAIN_CONFIG.ASTROVISHNU.domain}`;
  }
  
  // If user only has astroroshni access but is on astrovishnu domain
  if (hasAstroroshni && !hasAstrovishnu && currentDomain.userType === 'software') {
    return `https://${DOMAIN_CONFIG.ASTROROSHNI.domain}`;
  }
  
  // If user has no access to current platform, redirect to platform they have access to
  if (currentDomain.userType === 'software' && !hasAstrovishnu && hasAstroroshni) {
    return `https://${DOMAIN_CONFIG.ASTROROSHNI.domain}`;
  }
  
  if (currentDomain.userType === 'general' && !hasAstroroshni && hasAstrovishnu) {
    return `https://${DOMAIN_CONFIG.ASTROVISHNU.domain}`;
  }
  
  return null; // No redirect needed
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