export const COLORS = {
  // Premium Pink Orange Sunset Theme
  primary: '#f97316',
  secondary: '#ec4899',
  white: '#ffffff',
  black: '#0d1117',
  gray: '#656d76',
  lightGray: '#fef7f0',
  success: '#238636',
  error: '#da3633',
  whatsapp: '#25D366',
  
  // Premium sunset colors
  background: '#fefcfb',
  surface: '#ffffff',
  accent: '#f97316',
  textPrimary: '#1a1a1a',
  textSecondary: '#6b7280',
  border: '#fed7d7',
  
  // Gradient colors - sunset premium
  gradientStart: '#fefcfb',
  gradientEnd: '#fef7f0',
  
  // Card colors - sunset gradients
  quickAnswerStart: 'rgba(249, 115, 22, 0.1)',
  quickAnswerEnd: 'rgba(236, 72, 153, 0.1)',
  finalThoughtsStart: 'rgba(254, 247, 240, 0.9)',
  finalThoughtsEnd: 'rgba(254, 215, 215, 0.9)',
};

import { Platform } from 'react-native';

// API Configuration for AstroRoshni
const getApiUrl = () => {
  // Production
  // return 'https://astroroshni.com';
  
  // Localhost for testing
  if (Platform.OS === 'ios') {
    return 'http://localhost:8001';
  } else {
    return 'http://10.0.2.2:8001';
  }
};

export const API_BASE_URL = getApiUrl();


// Helper function to handle API endpoints for both dev and production
export const getEndpoint = (path) => {
  return `/api${path}`; // Always use /api prefix to match web version
};

export const LANGUAGES = [
  { code: 'english', name: 'English', flag: '🇺🇸' },
  { code: 'hindi', name: 'हिंदी', flag: '🇮🇳' },
  { code: 'telugu', name: 'తెలుగు', flag: '🇮🇳' },
  { code: 'gujarati', name: 'ગુજરાતી', flag: '🇮🇳' },
  { code: 'tamil', name: 'தமிழ்', flag: '🇮🇳' },
];