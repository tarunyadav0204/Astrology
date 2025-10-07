import { APP_CONFIG } from './config/app.config';

// API Configuration
const getApiUrl = () => {
  const hostname = window.location.hostname;
  
  // If accessing via production IP or domain, use production API
  if (hostname === '34.126.214.249' || hostname.includes('your-domain.com')) {
    return APP_CONFIG.api.prod;
  }
  
  // If on localhost, use dev API
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return APP_CONFIG.api.dev;
  }
  
  // For mobile devices accessing via IP, construct URL with same IP
  return `http://${hostname}:8001`;
};

export const API_BASE_URL = getApiUrl();
export { APP_CONFIG };