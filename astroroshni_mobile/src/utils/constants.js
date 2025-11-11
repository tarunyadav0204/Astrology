export const COLORS = {
  primary: '#ff6b35',
  secondary: '#f7931e',
  white: '#ffffff',
  black: '#000000',
  gray: '#666666',
  lightGray: '#f0f0f0',
  success: '#4CAF50',
  error: '#e74c3c',
  whatsapp: '#25D366',
  
  // Gradient colors
  gradientStart: '#ff6b35',
  gradientEnd: '#f7931e',
  
  // Card colors
  quickAnswerStart: 'rgba(255, 215, 0, 0.9)',
  quickAnswerEnd: 'rgba(255, 165, 0, 0.9)',
  finalThoughtsStart: 'rgba(173, 216, 230, 0.9)',
  finalThoughtsEnd: 'rgba(135, 206, 235, 0.9)',
};

import { Platform } from 'react-native';

// API Configuration matching web version
const getApiUrl = () => {
  // TEMPORARY: Use full astroroshni.com URL for testing
  return 'https://astroroshni.com';
  
  // Original logic:
  // if (__DEV__) {
  //   return Platform.OS === 'web' ? 'http://localhost:8001' : 'http://192.168.68.102:8001';
  // } else {
  //   return '';
  // }
};

export const API_BASE_URL = getApiUrl();

// Helper function to handle API endpoints for both dev and production
export const getEndpoint = (path) => {
  // TEMPORARY: Use /api prefix for astroroshni.com testing
  return `/api${path}`;
};

export const LANGUAGES = [
  { code: 'english', name: 'English', flag: '🇺🇸' },
  { code: 'hindi', name: 'हिंदी', flag: '🇮🇳' },
  { code: 'telugu', name: 'తెలుగు', flag: '🇮🇳' },
  { code: 'gujarati', name: 'ગુજરાતી', flag: '🇮🇳' },
  { code: 'tamil', name: 'தமிழ்', flag: '🇮🇳' },
];