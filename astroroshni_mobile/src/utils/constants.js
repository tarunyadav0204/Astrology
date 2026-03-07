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
  
  // Partnership mode colors
  partnershipBubble: 'rgba(236, 72, 153, 0.08)',
  partnershipBorder: '#ec4899',
};

import { Platform } from 'react-native';

// API Configuration for AstroRoshni
// Set to true only when testing against local/staging backend (nudge, push, etc.)
const USE_DEV_API = false;
// For simulator leave empty (uses localhost/10.0.2.2). For physical device set your machine IP, e.g. 'http://192.168.1.10:8001'
const DEV_API_HOST = '';

const getApiUrl = () => {
  if (__DEV__ && USE_DEV_API) {
    if (DEV_API_HOST) return DEV_API_HOST;
    if (Platform.OS === 'ios') return 'http://localhost:8001';
    if (Platform.OS === 'android') return 'http://10.0.2.2:8001';
  }
  // if (Platform.OS === 'ios') {
  //   return 'http://localhost:8001';
  // } else {
  //   return 'http://10.0.2.2:8001';
  // }
  return 'https://astroroshni.com';
};

export const API_BASE_URL = getApiUrl();

// Timeout configuration
export const API_TIMEOUT = 5 * 60 * 1000; // 5 minutes in milliseconds

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
  { code: 'marathi', name: 'मराठी', flag: '🇮🇳' },
  { code: 'german', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'french', name: 'Français', flag: '🇫🇷' },
  { code: 'russian', name: 'Русский', flag: '🇷🇺' },
  { code: 'chinese', name: '中文', flag: '🇨🇳' },
  { code: 'mandarin', name: '普通话', flag: '🇨🇳' },
];

export const LANGUAGE_STORAGE_KEY = 'user_language';

export const CREDIT_COSTS = {
  SINGLE_CHAT: 1,
  PARTNERSHIP_CHAT: 2,
};

export const PLANET_NAMES = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];

export const RASHI_NAMES = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

export const NAKSHATRA_NAMES = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
  'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
  'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
  'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
  'Uttara Bhadrapada', 'Revati'
];

export const VOICE_CONFIG = {
  rate: 0.75,           // Slower for more natural speech
  pitch: 0.9,           // Slightly lower pitch for warmth
  volume: 1.0,          // Full volume
  quality: 'enhanced',  // Try enhanced quality
  preferredVoices: {
    'en-US': ['Kathy', 'Samantha', 'Albert'],
    'en-IN': ['Rishi'],
    'hi-IN': [],
    'te-IN': [],
    'ta-IN': [],
    'gu-IN': []
  }
};
