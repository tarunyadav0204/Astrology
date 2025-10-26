import { APP_CONFIG } from './config/app.config';

// API Configuration
const getApiUrl = () => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  
  // If accessing via production domains, use production API (load balancer)
  if (hostname === 'astroclick.net' || hostname.includes('astroclick.net') ||
      hostname === 'astroroshni.com' || hostname.includes('astroroshni.com') ||
      hostname === 'astrovishnu.com' || hostname.includes('astrovishnu.com')) {
    return APP_CONFIG.api.prod;
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