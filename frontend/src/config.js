import { APP_CONFIG } from './config/app.config';

// API Configuration
const getApiUrl = () => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  const sameOriginBase = `${protocol}//${hostname}`;

  // Test backend (HTTPS via Caddy)
  if (hostname === 'test.astroroshni.com' || hostname.includes('test.astroroshni.com')) {
    return APP_CONFIG.api.test;
  }

  // AstroRoshni production: always use the same host as the SPA (www vs apex are different origins).
  // Hardcoding https://astroroshni.com while users land on www breaks CORS + cookies; /api is proxied on each host.
  if (hostname.includes('astroroshni.com') && !hostname.startsWith('test.')) {
    return sameOriginBase;
  }

  // Other production frontends: same-origin when possible (avoids www/apex mismatches if those sites add www).
  if (hostname === 'astroclick.net' || hostname.includes('astroclick.net') ||
      hostname === 'astrovishnu.com' || hostname.includes('astrovishnu.com')) {
    return sameOriginBase;
  }
  
  // If accessing via production IP, use production API
  if (hostname === '34.126.214.249') {
    return APP_CONFIG.api.prod;
  }
  
  // If on localhost, use dev API
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return APP_CONFIG.api.dev;
  }
  
  // For mobile devices accessing via IP, construct URL with same protocol
  return `${protocol}//${hostname}:8001`;
};

export const API_BASE_URL = getApiUrl();
export { APP_CONFIG };