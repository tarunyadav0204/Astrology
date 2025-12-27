import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { APP_CONFIG } from '../../config/app.config';
import { getCurrentDomainConfig } from '../../config/domains.config';
import { SEO_CONFIG, generatePageSEO } from '../../config/seo.config';
import { useAstrology } from '../../context/AstrologyContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { apiService } from '../../services/apiService';
import ChartWidget from '../Charts/ChartWidget';
import NavigationHeader from '../Shared/NavigationHeader';
import ChatModal from '../Chat/ChatModal';
import CreditsModal from '../Credits/CreditsModal';
import PanchangWidget from '../PanchangWidget/HomePanchangWidget';
import LoShuGrid from '../Numerology/LoShuGrid';
import NameOptimizer from '../Numerology/NameOptimizer';
import CosmicForecast from '../Numerology/CosmicForecast';

import BirthFormModal from '../BirthForm/BirthFormModal';
import PartnerForm from '../MarriageAnalysis/PartnerForm';
import LoginForm from '../Auth/LoginForm';
import RegisterForm from '../Auth/RegisterForm';
import { showToast } from '../../utils/toast';
import './AstroRoshniHomepage.css';
import './search-section.css';

const AstroRoshniHomepage = ({ user, onLogout, onAdminClick, onLogin, showLoginButton, setCurrentView }) => {
  const navigate = useNavigate();
  const { chartData, birthData } = useAstrology();
  const { trackEvent } = useAnalytics();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [selectedZodiac, setSelectedZodiac] = useState('aries');
  const [horoscopeData, setHoroscopeData] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('daily');
  const [showChatModal, setShowChatModal] = useState(false);
  const [showCreditsModal, setShowCreditsModal] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [authView, setAuthView] = useState('login');
  const [showChartModal, setShowChartModal] = useState(false);
  const [showBirthFormModal, setShowBirthFormModal] = useState(false);
  const [chartRefHighlight, setChartRefHighlight] = useState(null);
  const [matchingData, setMatchingData] = useState({
    boy: { name: '', day: '', month: '', year: '', hours: '', minutes: '', seconds: '', place: '' },
    girl: { name: '', day: '', month: '', year: '', hours: '', minutes: '', seconds: '', place: '' }
  });

  const bannerSlides = [
    { id: 1, image: '/images/banner-ai-astrologers.jpg', title: 'AI Astrologers Available 24/7' },
    { id: 2, image: '/images/banner-premium-reports.jpg', title: 'Premium Astrology Reports' },
    { id: 3, image: '/images/banner-live-consultation.jpg', title: 'Live Consultation with Experts' }
  ];



  const zodiacSigns = [
    { name: 'aries', symbol: '♈', displayName: 'Aries' },
    { name: 'taurus', symbol: '♉', displayName: 'Taurus' },
    { name: 'gemini', symbol: '♊', displayName: 'Gemini' },
    { name: 'cancer', symbol: '♋', displayName: 'Cancer' },
    { name: 'leo', symbol: '♌', displayName: 'Leo' },
    { name: 'virgo', symbol: '♍', displayName: 'Virgo' },
    { name: 'libra', symbol: '♎', displayName: 'Libra' },
    { name: 'scorpio', symbol: '♏', displayName: 'Scorpio' },
    { name: 'sagittarius', symbol: '♐', displayName: 'Sagittarius' },
    { name: 'capricorn', symbol: '♑', displayName: 'Capricorn' },
    { name: 'aquarius', symbol: '♒', displayName: 'Aquarius' },
    { name: 'pisces', symbol: '♓', displayName: 'Pisces' }
  ];

  const services = [
    { icon: '📊', title: 'Free Kundli', desc: 'Complete birth chart analysis' },
    { icon: '💕', title: 'Horoscope Matching', desc: 'Compatibility for marriage' },
    { icon: '🌟', title: 'Daily Horoscope', desc: 'Your daily predictions' },
    { icon: '📞', title: 'Talk to Astrologer', desc: 'Live consultation' },
    { icon: '💎', title: 'Gemstone Report', desc: 'Personalized recommendations' },
    { icon: '🏠', title: 'Vastu Consultation', desc: 'Home & office guidance' },
    { icon: '📈', title: 'Career Report', desc: 'Professional guidance' },
    { icon: '💰', title: 'Finance Report', desc: 'Money & wealth analysis' }
  ];

  const premiumServices = [
    { title: 'Brihat Kundli', price: '₹299', desc: '250+ pages detailed report', icon: '📋' },
    { title: 'Marriage Report', price: '₹199', desc: 'Complete marriage analysis', icon: '💒' },
    { title: 'Career Guidance', price: '₹249', desc: 'Professional path analysis', icon: '💼' },
    { title: 'Health Report', price: '₹179', desc: 'Medical astrology insights', icon: '🏥' },
    { title: 'Finance Report', price: '₹229', desc: 'Wealth & money analysis', icon: '💰' },
    { title: 'Love & Relationship', price: '₹189', desc: 'Romance compatibility guide', icon: '💕' },
    { title: 'Business Report', price: '₹279', desc: 'Enterprise success analysis', icon: '🏢' },
    { title: 'Children Report', price: '₹159', desc: 'Child birth & upbringing', icon: '👶' },
    { title: 'Education Report', price: '₹169', desc: 'Academic success guidance', icon: '🎓' }
  ];

  const testimonials = [
    { name: 'Priya Sharma', location: 'Mumbai', rating: 5, text: 'Accurate predictions helped me find my soulmate!', image: 'https://images.unsplash.com/photo-1494790108755-2616c9c0e8e0?w=80&h=80&fit=crop&crop=face' },
    { name: 'Rajesh Kumar', location: 'Delhi', rating: 5, text: 'Career guidance was spot on. Got promotion within 3 months!', image: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&crop=face' },
    { name: 'Anita Patel', location: 'Ahmedabad', rating: 5, text: 'Marriage compatibility report saved my relationship.', image: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=80&h=80&fit=crop&crop=face' }
  ];

  const vipTiers = [
    { name: 'Gold', price: '₹999/month', features: ['Priority Support', '50% Off Reports', 'Monthly Consultation'], icon: '🥇' },
    { name: 'Platinum', price: '₹1999/month', features: ['Celebrity Astrologer Access', 'Unlimited Reports', 'Weekly Consultation'], icon: '🏆' },
    { name: 'Diamond', price: '₹4999/month', features: ['Personal Astrologer', 'Custom Remedies', 'Daily Guidance'], icon: '💎' }
  ];

  const liveOffers = [
    { title: 'First Consultation FREE', desc: 'Limited time offer for new users', timer: '23:45:12', color: '#f44336' },
    { title: '50% OFF Premium Reports', desc: 'Valid till midnight today', timer: '11:23:45', color: '#ff9800' }
  ];

  const [planetaryPositions, setPlanetaryPositions] = useState([]);
  const [planetaryLoading, setPlanetaryLoading] = useState(false);
  const [muhuratData, setMuhuratData] = useState(null);
  const [muhuratLoading, setMuhuratLoading] = useState(false);
  const [numerologyData, setNumerologyData] = useState(null);
  const [showNumerologyModal, setShowNumerologyModal] = useState(false);
  const [numerologyTab, setNumerologyTab] = useState('blueprint');
  const [birthFormContext, setBirthFormContext] = useState('chart');
  const [showDestinyModal, setShowDestinyModal] = useState(false);
  const [destinyReading, setDestinyReading] = useState(null);

  const generateTodaysData = useCallback(() => {
    const today = new Date();
    const dayOfWeek = today.getDay();
    const dayOfMonth = today.getDate();
    const month = today.getMonth();
    
    // Planetary rulers for each day
    const dayRulers = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
    const rulingPlanet = dayRulers[dayOfWeek];
    
    // Generate lucky numbers based on date
    const baseNumbers = [(dayOfMonth % 9) + 1, ((dayOfMonth + month) % 9) + 1];
    const luckyNumbers = [...baseNumbers, baseNumbers[0] * 3, baseNumbers[1] * 5].slice(0, 4);
    
    // Planet-based attributes
    const planetAttributes = {
      'Sun': {
        colors: ['Golden', 'Orange', 'Red'],
        direction: 'East',
        element: 'Fire',
        gemstone: 'Ruby',
        mantra: 'Om Surya Namaha',
        time: '6:00 AM - 12:00 PM',
        avoidColors: ['Black', 'Dark Blue'],
        bestActivities: ['Leadership', 'New Beginnings', 'Government Work'],
        avoidActivities: ['Night Travel', 'Signing Contracts after Sunset']
      },
      'Moon': {
        colors: ['White', 'Silver', 'Light Blue'],
        direction: 'Northwest',
        element: 'Water',
        gemstone: 'Pearl',
        mantra: 'Om Chandraya Namaha',
        time: '6:00 PM - 12:00 AM',
        avoidColors: ['Red', 'Maroon'],
        bestActivities: ['Meditation', 'Family Time', 'Creative Work'],
        avoidActivities: ['Important Decisions', 'Surgery']
      },
      'Mars': {
        colors: ['Red', 'Coral', 'Orange'],
        direction: 'South',
        element: 'Fire',
        gemstone: 'Red Coral',
        mantra: 'Om Mangalaya Namaha',
        time: '12:00 PM - 6:00 PM',
        avoidColors: ['Green', 'Light Blue'],
        bestActivities: ['Sports', 'Competition', 'Property Deals'],
        avoidActivities: ['Marriage Ceremonies', 'Peace Talks']
      },
      'Mercury': {
        colors: ['Green', 'Emerald', 'Light Green'],
        direction: 'North',
        element: 'Earth',
        gemstone: 'Emerald',
        mantra: 'Om Budhaya Namaha',
        time: '9:00 AM - 3:00 PM',
        avoidColors: ['Red', 'Orange'],
        bestActivities: ['Communication', 'Learning', 'Business'],
        avoidActivities: ['Heavy Physical Work', 'Emotional Decisions']
      },
      'Jupiter': {
        colors: ['Yellow', 'Golden', 'Saffron'],
        direction: 'Northeast',
        element: 'Space',
        gemstone: 'Yellow Sapphire',
        mantra: 'Om Gurave Namaha',
        time: '10:00 AM - 4:00 PM',
        avoidColors: ['Black', 'Dark Colors'],
        bestActivities: ['Education', 'Religious Activities', 'Financial Planning'],
        avoidActivities: ['Gambling', 'Speculation']
      },
      'Venus': {
        colors: ['Pink', 'White', 'Light Blue'],
        direction: 'Southeast',
        element: 'Water',
        gemstone: 'Diamond',
        mantra: 'Om Shukraya Namaha',
        time: '2:00 PM - 8:00 PM',
        avoidColors: ['Black', 'Brown'],
        bestActivities: ['Art', 'Romance', 'Beauty Treatments'],
        avoidActivities: ['Harsh Decisions', 'Conflicts']
      },
      'Saturn': {
        colors: ['Blue', 'Black', 'Dark Purple'],
        direction: 'West',
        element: 'Air',
        gemstone: 'Blue Sapphire',
        mantra: 'Om Shanaye Namaha',
        time: '6:00 AM - 10:00 AM',
        avoidColors: ['Bright Red', 'Orange'],
        bestActivities: ['Hard Work', 'Discipline', 'Long-term Planning'],
        avoidActivities: ['Hasty Decisions', 'Luxury Purchases']
      }
    };
    
    const attrs = planetAttributes[rulingPlanet];
    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const rashis = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    
    return {
      luckyNumbers,
      luckyColors: attrs.colors,
      luckyDirection: attrs.direction,
      luckyTime: attrs.time,
      luckyGemstone: attrs.gemstone,
      luckyElement: attrs.element,
      luckyPlanet: rulingPlanet,
      luckyDay: dayNames[dayOfWeek],
      dailyMantra: attrs.mantra,
      avoidColors: attrs.avoidColors,
      avoidNumbers: [4, 8, 13, 17].filter(n => !luckyNumbers.includes(n)).slice(0, 2),
      bestActivities: attrs.bestActivities,
      avoidActivities: attrs.avoidActivities,
      rulingRashi: rashis[(dayOfMonth + month) % 12]
    };
  }, []);
  
  const [todaysData, setTodaysData] = useState(() => {
    // Initialize with cached data or generate new
    const lastUpdate = localStorage.getItem('lastLuckyUpdate');
    const today = new Date().toDateString();
    const cachedData = localStorage.getItem('todaysLuckyData');
    
    if (lastUpdate === today && cachedData) {
      try {
        return JSON.parse(cachedData);
      } catch (e) {
        console.error('Error parsing cached data:', e);
      }
    }
    
    // Generate new data if no cache or new day
    const newData = {
      luckyNumbers: [1, 3, 7, 9],
      luckyColors: ['Golden', 'Orange', 'Red'],
      luckyDirection: 'East',
      luckyTime: '6:00 AM - 12:00 PM',
      luckyGemstone: 'Ruby',
      luckyElement: 'Fire',
      luckyPlanet: 'Sun',
      luckyDay: 'Today',
      dailyMantra: 'Om Surya Namaha',
      avoidColors: ['Black', 'Dark Blue'],
      avoidNumbers: [4, 8],
      bestActivities: ['Leadership', 'New Beginnings'],
      avoidActivities: ['Night Travel'],
      rulingRashi: 'Aries'
    };
    
    localStorage.setItem('todaysLuckyData', JSON.stringify(newData));
    localStorage.setItem('lastLuckyUpdate', today);
    
    return newData;
  });

  // Banner slider effect
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % bannerSlides.length);
    }, 4000);
    return () => clearInterval(timer);
  }, [bannerSlides.length]);

  // Initial data fetch
  useEffect(() => {
    const initializeData = async () => {
      try {
        await Promise.all([
          fetchHoroscopes(),
          fetchPlanetaryPositions(),
          fetchMuhuratTimes()
        ]);
        
        // Fetch numerology data if user and birth data available
        if (user && birthData) {
          fetchNumerologyData();
        }
      } catch (error) {
        console.error('Error initializing data:', error);
      }
    };
    
    initializeData();
  }, [user, birthData]);

  // Listen for chart modal open event from chat
  useEffect(() => {
    const handleOpenChartModal = () => {
      setShowChartModal(true);
    };
    
    window.addEventListener('openChartModal', handleOpenChartModal);
    return () => window.removeEventListener('openChartModal', handleOpenChartModal);
  }, []);

  // Daily data update check
  useEffect(() => {
    const checkAndUpdateDailyData = () => {
      const lastUpdate = localStorage.getItem('lastLuckyUpdate');
      const today = new Date().toDateString();
      
      if (lastUpdate !== today) {
        const newData = generateTodaysData();
        setTodaysData(newData);
        localStorage.setItem('todaysLuckyData', JSON.stringify(newData));
        localStorage.setItem('lastLuckyUpdate', today);
      }
    };
    
    // Check immediately
    checkAndUpdateDailyData();
    
    // Set up midnight check
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(now.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    const msUntilMidnight = tomorrow.getTime() - now.getTime();
    
    const midnightTimer = setTimeout(() => {
      checkAndUpdateDailyData();
      
      // Set daily interval after first midnight update
      const dailyInterval = setInterval(checkAndUpdateDailyData, 24 * 60 * 60 * 1000);
      
      return () => clearInterval(dailyInterval);
    }, msUntilMidnight);
    
    return () => clearTimeout(midnightTimer);
  }, [generateTodaysData]);

  const fetchPlanetaryPositions = useCallback(async () => {
    setPlanetaryLoading(true);
    try {
      // Use fallback data for non-authenticated users
      setPlanetaryPositions([
        { planet: 'Sun', sign: 'Capricorn', degree: '15.4°', retrograde: false },
        { planet: 'Moon', sign: 'Pisces', degree: '8.7°', retrograde: false },
        { planet: 'Mars', sign: 'Aries', degree: '22.1°', retrograde: false },
        { planet: 'Mercury', sign: 'Sagittarius', degree: '28.3°', retrograde: true },
        { planet: 'Jupiter', sign: 'Taurus', degree: '12.8°', retrograde: false },
        { planet: 'Venus', sign: 'Scorpio', degree: '5.2°', retrograde: false },
        { planet: 'Saturn', sign: 'Aquarius', degree: '18.9°', retrograde: false }
      ]);
    } catch (error) {
      console.error('Error fetching planetary positions:', error);
    } finally {
      setPlanetaryLoading(false);
    }
  }, []);

  const fetchMuhuratTimes = useCallback(async () => {
    setMuhuratLoading(true);
    const today = new Date().toISOString().split('T')[0];
    const latitude = 28.6139;
    const longitude = 77.2090;
    
    try {
      
      const [choghadiya, hora, specialMuhurtas] = await Promise.all([
        apiService.calculateChoghadiya(today, latitude, longitude),
        apiService.calculateHora(today, latitude, longitude),
        apiService.calculateSpecialMuhurtas(today, latitude, longitude)
      ]);
      
      // console.log('API Responses:', { choghadiya, hora, specialMuhurtas });
      
      // Debug API calculations
      // console.log('=== API CALCULATION ANALYSIS ===');
      // console.log('Date requested:', today);
      // console.log('Location:', { latitude, longitude });
      
      // Check Brahma Muhurta calculation
      if (specialMuhurtas.muhurtas) {
        const brahmaMuhurta = specialMuhurtas.muhurtas.find(m => m.name === 'Brahma Muhurta');
        if (brahmaMuhurta) {
          // console.log('Brahma Muhurta Raw:', brahmaMuhurta);
          // console.log('Start:', new Date(brahmaMuhurta.start_time).toString());
          // console.log('End:', new Date(brahmaMuhurta.end_time).toString());
          // console.log('Duration (hours):', (new Date(brahmaMuhurta.end_time) - new Date(brahmaMuhurta.start_time)) / (1000 * 60 * 60));
        }
      }
      
      // Check day duration
      // console.log('Day duration (hours):', specialMuhurtas.day_duration_hours);
      // console.log('Night duration (hours):', specialMuhurtas.night_duration_hours);
      
      // Check if times are in correct timezone
      // console.log('Current local time:', new Date().toString());
      // console.log('Current UTC time:', new Date().toISOString());
      
      // console.log('=== END ANALYSIS ===');
      
      // Parse choghadiya data (combine day and night)
      const allChoghadiya = [...(choghadiya.day_choghadiya || []), ...(choghadiya.night_choghadiya || [])];
      const parsedChoghadiya = allChoghadiya.slice(0, 3).map(item => {
        const startTime = item.start_time.split('T')[1].substring(0, 5);
        const endTime = item.end_time.split('T')[1].substring(0, 5);
        return {
          name: item.name,
          time: `${startTime}-${endTime}`,
          type: item.nature === 'Auspicious' ? 'good' : 'bad'
        };
      });
      
      // Parse hora data - find current and next hora
      const allHoras = [...(hora.day_horas || []), ...(hora.night_horas || [])];
      const now = new Date();
      
      const getPlanetaryFavorability = (planet) => {
        const planetQualities = {
          'Sun': true, 'Moon': true, 'Mars': false, 'Mercury': true,
          'Jupiter': true, 'Venus': true, 'Saturn': false
        };
        return planetQualities[planet] || false;
      };
      
      // Find current hora
      let currentHoraIndex = 0;
      for (let i = 0; i < allHoras.length; i++) {
        const horaStart = new Date(allHoras[i].start_time);
        const horaEnd = new Date(allHoras[i].end_time);
        if (now >= horaStart && now <= horaEnd) {
          currentHoraIndex = i;
          break;
        }
      }
      
      // Get current and next hora
      const currentHoras = allHoras.slice(currentHoraIndex, currentHoraIndex + 2);
      const parsedHora = currentHoras.map(item => {
        const startTime = item.start_time.split('T')[1].substring(0, 5);
        const endTime = item.end_time.split('T')[1].substring(0, 5);
        return {
          planet: item.planet,
          time: `${startTime}-${endTime}`,
          favorable: getPlanetaryFavorability(item.planet)
        };
      });
      
      console.log('Parsed Hora:', parsedHora);
      
      // Parse muhurtas data
      const parsedMuhurtas = specialMuhurtas.muhurtas?.slice(0, 2).map(muhurat => {
        const startTime = muhurat.start_time.split('T')[1].substring(0, 5);
        const endTime = muhurat.end_time.split('T')[1].substring(0, 5);
        return {
          name: muhurat.name,
          time: `${startTime}-${endTime}`,
          purpose: muhurat.purpose || 'Auspicious activities'
        };
      }) || [];
      
      setMuhuratData({
        choghadiya: parsedChoghadiya.length > 0 ? parsedChoghadiya : [
          { name: 'Amrit', time: '06:00-07:30', type: 'good' },
          { name: 'Kaal', time: '07:30-09:00', type: 'bad' },
          { name: 'Shubh', time: '09:00-10:30', type: 'good' }
        ],
        hora: parsedHora.length > 0 ? parsedHora : [
          { planet: 'Current', time: 'Loading...', favorable: true },
          { planet: 'Next', time: 'Loading...', favorable: true }
        ],
        special: parsedMuhurtas.length > 0 ? parsedMuhurtas : [
          { name: 'Abhijit', time: '11:47-12:35', purpose: 'All auspicious works' },
          { name: 'Brahma', time: '04:24-05:12', purpose: 'Spiritual activities' }
        ]
      });
    } catch (error) {
      console.error('Error fetching muhurat times:', error);
      console.error('Error details:', error.response?.data || error.message);
      console.error('Request params:', { today, latitude, longitude });
      setMuhuratData({
        choghadiya: [
          { name: 'Amrit', time: '06:00-07:30', type: 'good' },
          { name: 'Kaal', time: '07:30-09:00', type: 'bad' },
          { name: 'Shubh', time: '09:00-10:30', type: 'good' }
        ],
        hora: [
          { planet: 'API Error', time: 'Check console', favorable: false },
          { planet: 'Backend Issue', time: '400 Bad Request', favorable: false }
        ],
        special: [
          { name: 'API Error', time: 'Backend 400', purpose: 'Check backend logs' },
          { name: 'Server Issue', time: 'Bad Request', purpose: 'Fix backend first' }
        ]
      });
    } finally {
      setMuhuratLoading(false);
    }
  }, []);

  const getSignName = (signIndex) => {
    const signs = [
      'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
      'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ];
    return signs[signIndex] || 'Unknown';
  };

  const fetchHoroscopes = useCallback(async () => {
    setLoading(true);
    try {
      const API_BASE_URL = process.env.NODE_ENV === 'production' 
        ? APP_CONFIG.api.prod 
        : APP_CONFIG.api.dev;
      const endpoint = `${API_BASE_URL}/api/horoscope/all-signs`;
      const response = await fetch(endpoint);
      const data = await response.json();
      setHoroscopeData(data);
    } catch (error) {
      console.error('Error fetching horoscopes:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchNumerologyData = useCallback(async () => {
    if (!user || !birthData) return;
    
    try {
      const API_BASE_URL = process.env.NODE_ENV === 'production' 
        ? APP_CONFIG.api.prod 
        : APP_CONFIG.api.dev;
      
      const response = await fetch(`${API_BASE_URL}/api/numerology/full-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name: birthData.name,
          dob: birthData.date
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setNumerologyData(data.data);
      }
    } catch (error) {
      console.error('Error fetching numerology data:', error);
    }
  }, [user, birthData]);

  const handleNameOptimization = useCallback(async (name, system) => {
    try {
      const API_BASE_URL = process.env.NODE_ENV === 'production' 
        ? APP_CONFIG.api.prod 
        : APP_CONFIG.api.dev;
      
      const response = await fetch(`${API_BASE_URL}/api/numerology/optimize-name`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          name: name,
          system: system
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.data;
      }
      return null;
    } catch (error) {
      console.error('Error optimizing name:', error);
      return null;
    }
  }, []);

  const getCurrentHoroscope = () => {
    if (!horoscopeData[selectedZodiac]) {
      return {
        prediction: {
          overall: 'Loading your personalized horoscope...',
          love: 'Love predictions loading...',
          career: 'Career insights loading...',
          health: 'Health guidance loading...',
          finance: 'Financial outlook loading...'
        },
        lucky_number: '...',
        lucky_color: '...',
        rating: 0
      };
    }
    return horoscopeData[selectedZodiac];
  };

  const handleAdminClick = () => {
    if (onAdminClick) {
      onAdminClick();
    }
  };

  const handlePeriodChange = (period) => {
    setSelectedPeriod(period);
    
    // Track horoscope period change
    if (trackEvent) {
      trackEvent('horoscope_period_changed', 'astrology', period);
    }
    
    // Scroll to horoscope section
    const horoscopeSection = document.querySelector('.horoscope-section');
    if (horoscopeSection) {
      horoscopeSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleMatchingSubmit = (e) => {
    e.preventDefault();
    // Navigate to marriage analysis with pre-populated data
    navigate('/marriage-analysis', { 
      state: { 
        prefilledData: {
          person1: {
            name: matchingData.boy.name,
            date: `${matchingData.boy.year}-${matchingData.boy.month.padStart(2, '0')}-${matchingData.boy.day.padStart(2, '0')}`,
            time: `${matchingData.boy.hours.padStart(2, '0')}:${matchingData.boy.minutes.padStart(2, '0')}:${matchingData.boy.seconds.padStart(2, '0')}`,
            place: matchingData.boy.place
          },
          person2: {
            name: matchingData.girl.name,
            date: `${matchingData.girl.year}-${matchingData.girl.month.padStart(2, '0')}-${matchingData.girl.day.padStart(2, '0')}`,
            time: `${matchingData.girl.hours.padStart(2, '0')}:${matchingData.girl.minutes.padStart(2, '0')}:${matchingData.girl.seconds.padStart(2, '0')}`,
            place: matchingData.girl.place
          }
        }
      }
    });
  };

  const updateMatchingData = (person, field, value) => {
    setMatchingData(prev => ({
      ...prev,
      [person]: {
        ...prev[person],
        [field]: value
      }
    }));
  };

  const seoData = generatePageSEO('home');

  return (
    <div className="investor-homepage">
      <Helmet>
        <title>{seoData.title}</title>
        <meta name="description" content={seoData.description} />
        <meta name="keywords" content={seoData.keywords} />
        
        {/* Open Graph / Facebook */}
        <meta property="og:type" content="website" />
        <meta property="og:url" content={seoData.canonical} />
        <meta property="og:title" content={seoData.title} />
        <meta property="og:description" content={seoData.description} />
        <meta property="og:image" content={seoData.ogImage} />
        <meta property="og:site_name" content={SEO_CONFIG.site.name} />
        
        {/* Twitter */}
        <meta property="twitter:card" content="summary_large_image" />
        <meta property="twitter:url" content={seoData.canonical} />
        <meta property="twitter:title" content={seoData.title} />
        <meta property="twitter:description" content={seoData.description} />
        <meta property="twitter:image" content={seoData.twitterImage} />
        
        {/* Additional SEO Meta Tags */}
        <meta name="robots" content="index, follow" />
        <meta name="author" content={SEO_CONFIG.site.author} />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <meta name="theme-color" content={SEO_CONFIG.site.themeColor} />
        <link rel="canonical" href={seoData.canonical} />
        
        {/* Structured Data - Organization */}
        <script type="application/ld+json">
          {JSON.stringify(SEO_CONFIG.structuredData.organization)}
        </script>
        
        {/* Structured Data - Website */}
        <script type="application/ld+json">
          {JSON.stringify(SEO_CONFIG.structuredData.website)}
        </script>
      </Helmet>
      {/* Animated Solar System */}
      <div className="solar-system">
        <div className="sun"></div>
        <div className="orbit orbit-1">
          <div className="planet planet-1"></div>
        </div>
        <div className="orbit orbit-2">
          <div className="planet planet-2"></div>
        </div>
        <div className="orbit orbit-3">
          <div className="planet planet-3"></div>
        </div>
      </div>
      
      {/* Floating Constellation */}
      <div className="constellation">
        <div className="constellation-star"></div>
        <div className="constellation-star"></div>
        <div className="constellation-star"></div>
        <div className="constellation-star"></div>
        <div className="constellation-star"></div>
        <div className="constellation-line line-1"></div>
        <div className="constellation-line line-2"></div>
      </div>
      
      <NavigationHeader 
        onPeriodChange={handlePeriodChange}
        showZodiacSelector={false}
        zodiacSigns={zodiacSigns}
        selectedZodiac={selectedZodiac}
        onZodiacChange={setSelectedZodiac}
        user={user}
        onAdminClick={handleAdminClick}
        onLogout={onLogout}
        onLogin={onLogin}
        showLoginButton={showLoginButton}
        onCreditsClick={() => setShowCreditsModal(true)}
        onChangeNative={() => { setBirthFormContext('changeNative'); setShowBirthFormModal(true); }}
        birthData={birthData}
      />



      {/* Your Life Categories */}
      <section className="life-categories">
        <div className="container">
          <div className="life-categories-header">
            <span className="life-path-symbol life-path-symbol-1">🌟</span>
            <span className="life-path-symbol life-path-symbol-2">🌙</span>
            <span className="life-path-symbol life-path-symbol-3">✨</span>
            <span className="life-path-symbol life-path-symbol-4">🌙</span>
            <span className="life-path-symbol life-path-symbol-5">⭐</span>
            <span className="life-path-symbol life-path-symbol-6">💫</span>
            <h3>✨ Discover Your Life Path</h3>
            <p>Unlock the secrets of your destiny with best in class Vedic Astrology</p>
            <div className="life-categories-divider"></div>
          </div>
          <div className="life-categories-grid">
            <div className="life-category" onClick={() => user ? navigate('/career-guidance') : onLogin()}>
              <div className="category-icon">💼</div>
              <div className="category-content">
                <h4>Your Career</h4>
                <p>Professional success & growth</p>
              </div>
              <div className="category-arrow">→</div>
            </div>
            <div className="life-category" onClick={() => user ? navigate('/marriage-analysis') : onLogin()}>
              <div className="category-icon">💕</div>
              <div className="category-content">
                <h4>Your Marriage</h4>
                <p>Love, compatibility & relationships</p>
              </div>
              <div className="category-arrow">→</div>
            </div>
            <div className="life-category" onClick={() => user ? onLogin() : onLogin()}>
              <div className="category-icon">🎓</div>
              <div className="category-content">
                <h4>Your Education</h4>
                <p>Learning path & academic success</p>
              </div>
              <div className="category-arrow">→</div>
            </div>
            <div className="life-category" onClick={() => user ? navigate('/health-analysis') : onLogin()}>
              <div className="category-icon">🌿</div>
              <div className="category-content">
                <h4>Your Health</h4>
                <p>Wellness & vitality insights</p>
              </div>
              <div className="category-arrow">→</div>
            </div>
            <div className="life-category" onClick={() => user ? navigate('/wealth-analysis') : onLogin()}>
              <div className="category-icon">💎</div>
              <div className="category-content">
                <h4>Your Wealth</h4>
                <p>Financial prosperity & abundance</p>
              </div>
              <div className="category-arrow">→</div>
            </div>
          </div>
          
          {/* Full-width Ask Astrologer Banner */}
          <div className="ask-astrologer-banner">
            <div className="banner-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <div className="banner-icon">💬</div>
                <div className="banner-text">
                  <h3>Deep Vedic Analysis</h3>
                  <p>Get profound insights from ancient wisdom • Expert guidance • Personalized predictions</p>
                </div>
              </div>
              <button 
                className="ask-tara-prominent-btn"
                onClick={() => user ? setShowChatModal(true) : onLogin()}
                style={{
                  background: 'white',
                  color: '#e91e63',
                  border: '0px solid transparent !important',
                  outline: 'none !important',
                  boxSizing: 'border-box',
                  padding: '12px 24px',
                  borderRadius: '25px',
                  fontWeight: 'bold',
                  fontSize: '16px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 15px rgba(233, 30, 99, 0.3)',
                  animation: 'bounce 2s infinite',
                  transition: 'all 0.3s ease'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = '#e91e63';
                  e.target.style.color = 'white';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'white';
                  e.target.style.color = '#e91e63';
                }}
              >
                ⭐ Ask Tara Now
              </button>
            </div>
            <style>
              {`
                .ask-tara-prominent-btn {
                  border: none !important;
                  outline: none !important;
                }
                .ask-tara-prominent-btn:focus {
                  border: none !important;
                  outline: none !important;
                }
                .ask-tara-prominent-btn:active {
                  border: none !important;
                  outline: none !important;
                }
                @keyframes bounce {
                  0%, 20%, 50%, 80%, 100% {
                    transform: translateY(0);
                  }
                  40% {
                    transform: translateY(-10px);
                  }
                  60% {
                    transform: translateY(-5px);
                  }
                }
              `}
            </style>
          </div>
        </div>
      </section>

      {/* Banner Slider */}
      <section className="banner-slider">
        <div className="slider-container">
          {bannerSlides.map((slide, index) => (
            <div 
              key={slide.id}
              className={`slide ${index === currentSlide ? 'active' : ''}`}
            >
              <div className="slide-content">
                <h2>{slide.title}</h2>
                <button className="cta-btn">Get Started</button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Instant Destiny Reading Section - COMMENTED OUT */}
      {/*
      <section className="instant-destiny-section">
        <div className="container">
          <div className="destiny-header">
            <span className="destiny-symbol destiny-symbol-1">🔮</span>
            <span className="destiny-symbol destiny-symbol-2">⭐</span>
            <span className="destiny-symbol destiny-symbol-3">✨</span>
            <span className="destiny-symbol destiny-symbol-4">🌟</span>
            <h2 className="destiny-title">🔮 Instant Destiny Reading</h2>
            <p className="destiny-subtitle">Discover your life's hidden patterns using classical Vedic techniques</p>
            <div className="destiny-divider"></div>
          </div>
          
          <div className="destiny-content">
            <div className="destiny-card">
              <div className="destiny-icon">🎯</div>
              <h3>AI-Powered Vedic Analysis</h3>
              <p>Get stunning predictions using authentic classical texts like Bhrigu Samhita, Lal Kitab, and Nadi astrology</p>
              
              <div className="destiny-features">
                <div className="feature-item">
                  <span className="feature-icon">📚</span>
                  <span>Bhrigu Chakra Paddhati</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">⚖️</span>
                  <span>Lal Kitab Karmic Analysis</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">⭐</span>
                  <span>Nakshatra Fated Years</span>
                </div>
                <div className="feature-item">
                  <span className="feature-icon">🎭</span>
                  <span>Jaimini Sutra Methods</span>
                </div>
              </div>
              
              {birthData && birthData.name ? (
                <div className="selected-native">
                  <div className="native-info">
                    <span className="native-name">👤 {birthData.name}</span>
                    <button 
                      className="change-native-btn"
                      onClick={() => { setBirthFormContext('changeNative'); setShowBirthFormModal(true); }}
                    >
                      Change Native
                    </button>
                  </div>
                  <p className="native-subtitle">Using your selected birth details for instant analysis</p>
                </div>
              ) : (
                <div className="no-native">
                  <p>Please select your birth details first</p>
                  <button 
                    className="select-native-btn"
                    onClick={() => { setBirthFormContext('destiny'); setShowBirthFormModal(true); }}
                  >
                    Select Native
                  </button>
                </div>
              )}
              
              <button 
                className="destiny-btn"
                onClick={async () => {
                  if (!user) {
                    onLogin();
                    return;
                  }
                  
                  if (!birthData) {
                    setBirthFormContext('destiny');
                    setShowBirthFormModal(true);
                    return;
                  }
                  
                  try {
                    setLoading(true);
                    const API_BASE_URL = process.env.NODE_ENV === 'production' 
                      ? APP_CONFIG.api.prod 
                      : APP_CONFIG.api.dev;
                    
                    const response = await fetch(`${API_BASE_URL}/api/blank-chart/stunning-prediction`, {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                      },
                      body: JSON.stringify({
                        date: birthData.date,
                        time: birthData.time,
                        latitude: birthData.latitude,
                        longitude: birthData.longitude,
                        timezone: birthData.timezone
                      })
                    });
                    
                    const data = await response.json();
                    console.log('Destiny API Response:', data); // Debug log
                    
                    if (data.success) {
                      // Show results in new destiny popup modal
                      setDestinyReading(data);
                      setShowDestinyModal(true);
                    } else {
                      showToast('Failed to get destiny reading. Please try again.', 'error');
                    }
                  } catch (error) {
                    console.error('Destiny reading error:', error);
                    showToast('Error getting destiny reading. Please try again.', 'error');
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={loading}
              >
                {loading ? '🔮 Analyzing Destiny...' : '🚀 REVEAL MY DESTINY NOW'}
              </button>
              
              <div className="destiny-guarantee">
                <span>✨ Powered by Classical Vedic Texts</span>
                <span>🎯 Instant AI Analysis</span>
                <span>📚 Authentic Techniques</span>
              </div>
            </div>
          </div>
        </div>
      </section>
      */}

      {/* Chat Consultation Categories */}
      <section className="chat-consultations">
        <div className="container">
          <div className="section-header">
            <h2>⭐ Ask Tara Your Questions</h2>
            <p className="section-subtitle">Get instant AI-powered Vedic insights on any life topic</p>
          </div>
          
          <div className="consultation-categories">
            <div className="consultation-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="consultation-icon">💕</div>
              <h4>Love & Relationships</h4>
              <p>Marriage compatibility, relationship timing, soulmate analysis</p>
              <div className="consultation-examples">
                <span>"When will I get married?"</span>
                <span>"Is my partner compatible?"</span>
              </div>
              <button className="ask-btn">Ask Tara</button>
            </div>
            
            <div className="consultation-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="consultation-icon">💼</div>
              <h4>Career & Finance</h4>
              <p>Job changes, business success, wealth timing, investment guidance</p>
              <div className="consultation-examples">
                <span>"Should I change my job?"</span>
                <span>"When will I get promotion?"</span>
              </div>
              <button className="ask-btn">Ask Tara</button>
            </div>
            
            <div className="consultation-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="consultation-icon">🏥</div>
              <h4>Health & Wellness</h4>
              <p>Health predictions, disease timing, remedies, lifestyle guidance</p>
              <div className="consultation-examples">
                <span>"What about my health?"</span>
                <span>"Any health concerns ahead?"</span>
              </div>
              <button className="ask-btn">Ask Tara</button>
            </div>
            
            <div className="consultation-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="consultation-icon">👶</div>
              <h4>Family & Children</h4>
              <p>Child birth timing, family harmony, parenting guidance</p>
              <div className="consultation-examples">
                <span>"When will I have children?"</span>
                <span>"Family issues solutions?"</span>
              </div>
              <button className="ask-btn">Ask Tara</button>
            </div>
            
            <div className="consultation-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="consultation-icon">🎓</div>
              <h4>Education & Growth</h4>
              <p>Study success, exam results, skill development, learning path</p>
              <div className="consultation-examples">
                <span>"Will I pass my exams?"</span>
                <span>"Best career field for me?"</span>
              </div>
              <button className="ask-btn">Ask Tara</button>
            </div>
            
            <div className="consultation-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="consultation-icon">🌟</div>
              <h4>General Predictions</h4>
              <p>Life overview, upcoming events, lucky periods, general guidance</p>
              <div className="consultation-examples">
                <span>"What's ahead in my life?"</span>
                <span>"Any major changes coming?"</span>
              </div>
              <button className="ask-btn">Ask Tara</button>
            </div>
          </div>
          
          {/* Meet Tara Introduction */}
          <div className="tara-introduction" style={{
            background: 'linear-gradient(135deg, rgba(233, 30, 99, 0.1), rgba(156, 39, 176, 0.1))',
            borderRadius: '20px',
            padding: '30px',
            margin: '40px 0',
            border: '1px solid rgba(233, 30, 99, 0.2)'
          }}>
            <div className="tara-intro-content" style={{
              display: 'flex',
              alignItems: 'center',
              gap: '30px',
              flexWrap: 'wrap'
            }}>
              <div className="tara-avatar" style={{
                position: 'relative',
                minWidth: '80px',
                height: '80px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <div className="tara-star" style={{
                  fontSize: '60px',
                  animation: 'pulse 2s infinite'
                }}>⭐</div>
              </div>
              <div className="tara-text" style={{ flex: 1 }}>
                <h3 style={{
                  color: '#e91e63',
                  marginBottom: '15px',
                  fontSize: '24px'
                }}>Meet Tara - Your Vedic AI Guide</h3>
                <p style={{
                  color: '#666',
                  marginBottom: '20px',
                  lineHeight: '1.6'
                }}>Named after the Sanskrit word for "star" and the Hindu goddess of guidance, Tara is your personal AI astrologer trained on thousands of years of Vedic wisdom. She combines ancient knowledge with modern AI to provide accurate, personalized insights about your life's journey.</p>
                <div className="tara-features" style={{
                  display: 'flex',
                  gap: '15px',
                  flexWrap: 'wrap'
                }}>
                  <span style={{
                    background: 'rgba(233, 30, 99, 0.1)',
                    padding: '6px 12px',
                    borderRadius: '15px',
                    fontSize: '12px',
                    color: '#e91e63',
                    border: '1px solid rgba(233, 30, 99, 0.3)'
                  }}>🌟 Trained on Classical Vedic Texts</span>
                  <span style={{
                    background: 'rgba(233, 30, 99, 0.1)',
                    padding: '6px 12px',
                    borderRadius: '15px',
                    fontSize: '12px',
                    color: '#e91e63',
                    border: '1px solid rgba(233, 30, 99, 0.3)'
                  }}>⚡ Instant Accurate Responses</span>
                  <span style={{
                    background: 'rgba(233, 30, 99, 0.1)',
                    padding: '6px 12px',
                    borderRadius: '15px',
                    fontSize: '12px',
                    color: '#e91e63',
                    border: '1px solid rgba(233, 30, 99, 0.3)'
                  }}>🎯 Personalized Predictions</span>
                  <span style={{
                    background: 'rgba(233, 30, 99, 0.1)',
                    padding: '6px 12px',
                    borderRadius: '15px',
                    fontSize: '12px',
                    color: '#e91e63',
                    border: '1px solid rgba(233, 30, 99, 0.3)'
                  }}>🕉️ Traditional Wisdom</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="consultation-cta">
            <div className="cta-content">
              <h3>🌟 Unlimited Questions • Instant Answers • 24/7 Available</h3>
              <p>Powered by advanced Vedic AI trained on classical texts</p>
            </div>
            <button 
              className="start-chat-btn"
              onClick={() => user ? setShowChatModal(true) : onLogin()}
            >
              ⭐ Ask Tara Now
            </button>
          </div>
        </div>
      </section>

      {/* AstroRoshni Software Advertisement */}
      <section className="astroroshni-ad">
        <div className="container">
          <div className="astroroshni-banner">
            <div className="astroroshni-content">
              <div className="astroroshni-badge">🌟 WORLD'S #1 ASTROLOGY SOFTWARE</div>
              <h2>AstroVishnu Professional</h2>
              <p className="astroroshni-tagline">The Most Advanced Vedic Astrology Software Globally</p>
              <div className="astroroshni-features">
                <span>✨ Swiss Ephemeris Precision</span>
                <span>🎯 Highest Automation Level</span>
                <span>📊 Feature Rich Charts</span>
                <span>🌟 Advanced Dasha Systems</span>
              </div>
              <div className="astroroshni-pricing">
                <span className="old-price">₹4,999</span>
                <span className="new-price">₹2,999</span>
                <span className="discount">40% OFF</span>
              </div>
              <button className="astroroshni-btn" onClick={() => window.open('/astroroshni', '_blank')}>
                🚀 EXPLORE ASTROVISHNU
              </button>
            </div>
            <div className="astroroshni-visual">
              <div className="software-mockup">
                <div className="mockup-screen">
                  <div className="chart-preview">📊</div>
                  <div className="feature-icons">
                    <span>🌙</span><span>⭐</span><span>🪐</span><span>🌟</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* AI Chat Services */}
      <section className="ai-chat-services">
        <div className="container">
          <div className="ai-services-header">
            <span className="service-symbol service-symbol-1">🌟</span>
            <span className="service-symbol service-symbol-2">📊</span>
            <span className="service-symbol service-symbol-3">💎</span>
            <span className="service-symbol service-symbol-4">🌟</span>
            <span className="service-symbol service-symbol-5">📋</span>
            <span className="service-symbol service-symbol-6">💫</span>
            <span className="service-symbol service-symbol-7">🎯</span>
            <span className="service-symbol service-symbol-8">✨</span>
            <h2 className="ai-services-title">Astrological Services for Accurate Answers</h2>
            <p className="ai-services-subtitle">All available through Tara - ask anything, get instant Vedic insights</p>
            <div className="ai-services-divider"></div>
          </div>
          
          <div className="ai-services-grid">
            <div className="ai-service-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="service-icon">❓</div>
              <h4>Prashna Analysis</h4>
              <p>Horary astrology for specific questions and timing</p>
              <div className="service-examples">
                <span>"When will I get married?"</span>
                <span>"Should I invest in this business?"</span>
                <span>"Will I get the job?"</span>
              </div>
              <button className="chat-service-btn">Ask Tara</button>
            </div>
            
            <div className="ai-service-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="service-icon">📅</div>
              <h4>Varshphal Analysis</h4>
              <p>Annual predictions and yearly forecast insights</p>
              <div className="service-examples">
                <span>"What does 2024 hold for me?"</span>
                <span>"Career prospects this year?"</span>
                <span>"Health predictions for 2024?"</span>
              </div>
              <button className="chat-service-btn">Ask Tara</button>
            </div>
            
            <div className="ai-service-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="service-icon">💕</div>
              <h4>Love & Partnership</h4>
              <p>Relationship compatibility and marriage analysis</p>
              <div className="service-examples">
                <span>"Are we compatible for marriage?"</span>
                <span>"When will I find love?"</span>
                <span>"Relationship problems solutions?"</span>
              </div>
              <button className="chat-service-btn">Ask Tara</button>
            </div>
            
            <div className="ai-service-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="service-icon">🏢</div>
              <h4>Business Relationships</h4>
              <p>Partnership analysis and business compatibility</p>
              <div className="service-examples">
                <span>"Should I partner with them?"</span>
                <span>"Business venture timing?"</span>
                <span>"Team compatibility analysis?"</span>
              </div>
              <button className="chat-service-btn">Ask Tara</button>
            </div>
            
            <div className="ai-service-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="service-icon">🤝</div>
              <h4>Friendship Analysis</h4>
              <p>Social relationships and friendship compatibility</p>
              <div className="service-examples">
                <span>"Why do I have friend conflicts?"</span>
                <span>"Building better friendships?"</span>
                <span>"Social circle analysis?"</span>
              </div>
              <button className="chat-service-btn">Ask Tara</button>
            </div>
            
            <div className="ai-service-card" onClick={() => user ? setShowChatModal(true) : onLogin()}>
              <div className="service-icon">💰</div>
              <h4>Wealth & Finance</h4>
              <p>Money matters and financial growth timing</p>
              <div className="service-examples">
                <span>"When will I become wealthy?"</span>
                <span>"Investment timing guidance?"</span>
                <span>"Financial stability analysis?"</span>
              </div>
              <button className="chat-service-btn">Ask Tara</button>
            </div>
          </div>
          
          <div className="ai-services-cta">
            <div className="cta-content">
              <h3>🤖 Powered by Advanced Vedic AI • Instant Responses • Available 24/7</h3>
              <p>All these services and more are available through Tara</p>
            </div>
            <button 
              className="start-ai-chat-btn"
              onClick={() => user ? setShowChatModal(true) : onLogin()}
            >
              🚀 Start Tara Consultation
            </button>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <div className="main-content">
        <div className="container">
          <div className="vedic-tools-header">
            <span className="vedic-symbol vedic-symbol-1">🕉️</span>
            <span className="vedic-symbol vedic-symbol-2">卍</span>
            <span className="vedic-symbol vedic-symbol-3">🔱</span>
            <span className="vedic-symbol vedic-symbol-4">☸️</span>
            <span className="vedic-symbol vedic-symbol-5">🪔</span>
            <span className="vedic-symbol vedic-symbol-6">🌸</span>
            <h2 className="vedic-tools-title">📊 Vedic Astrology Tools</h2>
            <p className="vedic-tools-subtitle">Discover your destiny with authentic Vedic calculations</p>
            <div className="vedic-tools-divider"></div>
          </div>
          <div className="content-grid">
            {/* Column 1 - Kundli Matching (40%) */}
            <div className="form-card matching-compact">
              <h3>Kundli Matching</h3>
              <PartnerForm 
                onSubmit={() => navigate('/marriage-analysis')} 
                user={user}
                onLogin={() => setShowLoginModal(true)}
              />
            </div>

            {/* Column 2 - Chart Widget (20%) */}
            <div className="form-card birth-chart-widget">
              <div className="birth-chart-content">
                <h3>📊 Birth Chart</h3>
                <p>Generate your complete Vedic birth chart</p>
                <div className="chart-features">
                  <div className="feature-item">🌟 Lagna Chart</div>
                  <div className="feature-item">🌙 Navamsa Chart</div>
                  <div className="feature-item">⏰ Dasha Periods</div>
                  <div className="feature-item">🎯 Predictions</div>
                </div>
                {birthData && birthData.name ? (
                  <div style={{ marginBottom: '10px' }}>
                    <button 
                      onClick={() => user ? setShowBirthFormModal(true) : onLogin()}
                      style={{
                        background: 'rgba(233, 30, 99, 0.1)',
                        border: '1px solid #e91e63',
                        color: '#e91e63',
                        padding: '8px 12px',
                        borderRadius: '20px',
                        fontSize: '12px',
                        cursor: 'pointer',
                        marginBottom: '8px',
                        display: 'block',
                        width: '100%'
                      }}
                    >
                      👤 {birthData.name} (Click to change)
                    </button>
                  </div>
                ) : null}
                <button 
                  className="chart-btn"
                  onClick={() => {
                    if (!user) {
                      onLogin();
                      return;
                    }
                    
                    // Check if chart data already exists (same logic as Ask Question Now)
                    if (birthData && chartData) {
                      // Chart already exists, show it directly
                      setShowChartModal(true);
                    } else {
                      // No chart data, show birth form modal
                      setBirthFormContext('chart');
                      setShowBirthFormModal(true);
                    }
                  }}
                >
                  {birthData && chartData ? 'View Chart' : 'Generate Chart'}
                </button>
              </div>
            </div>

            {/* Column 3 - Nakshatra Widget (20%) */}
            <div className="form-card nakshatra-widget">
              <h3>⭐ Nakshatra Guide</h3>
              <div className="nakshatra-content">
                <p>Discover your birth star and its profound influence on your life</p>
                <div className="nakshatra-features">
                  <div className="feature-item">🌟 Birth Star</div>
                  <div className="feature-item">🔮 Personality Traits</div>
                  <div className="feature-item">🎯 Life Purpose</div>
                  <div className="feature-item">🌈 Compatibility</div>
                </div>
                <div className="nakshatra-info">
                  <p><strong>System:</strong> 27 Vedic Nakshatras</p>
                  <p><strong>Analysis:</strong> Complete Star Map</p>
                </div>
                <button 
                  className="nakshatra-btn"
                  onClick={() => navigate('/nakshatras')}
                >
                  Explore Nakshatras
                </button>
              </div>
            </div>

            {/* Column 4 - Panchang (20%) */}
            <PanchangWidget />
          </div>
        </div>
      </div>



      {/* Horoscope Section */}
      <section className="horoscope-section">
        <div className="container">
          <div className="section-header">
            <h2>Western Horoscopes</h2>
          </div>
          <div className="horoscope-grid">
            <div className="horoscope-content">
              <div className="horoscope-tabs">
                <button className={`tab ${selectedPeriod === 'daily' ? 'active' : ''}`} onClick={() => setSelectedPeriod('daily')}>Daily</button>
                <button className={`tab ${selectedPeriod === 'weekly' ? 'active' : ''}`} onClick={() => { setSelectedPeriod('weekly'); navigate(`/horoscope?period=weekly&sign=${selectedZodiac}`); }}>Weekly</button>
                <button className={`tab ${selectedPeriod === 'monthly' ? 'active' : ''}`} onClick={() => { setSelectedPeriod('monthly'); navigate(`/horoscope?period=monthly&sign=${selectedZodiac}`); }}>Monthly</button>
                <button className={`tab ${selectedPeriod === 'yearly' ? 'active' : ''}`} onClick={() => { setSelectedPeriod('yearly'); navigate(`/horoscope?period=yearly&sign=${selectedZodiac}`); }}>Yearly</button>
              </div>
              
              <div className="zodiac-grid">
                {zodiacSigns.map(sign => (
                  <button 
                    key={sign.name}
                    className={`zodiac-card ${selectedZodiac === sign.name ? 'active' : ''}`}
                    onClick={() => setSelectedZodiac(sign.name)}
                  >
                    <div className="zodiac-icon">{sign.symbol}</div>
                    <div className="zodiac-text">{sign.displayName}</div>
                  </button>
                ))}
              </div>

              <div className="horoscope-content-area">
                <h3>{selectedZodiac.charAt(0).toUpperCase() + selectedZodiac.slice(1)} {selectedPeriod.charAt(0).toUpperCase() + selectedPeriod.slice(1)} Horoscope</h3>
                {loading ? (
                  <div className="horoscope-loading">Loading your personalized horoscope...</div>
                ) : (
                  <div className="horoscope-details">
                    <div className="horoscope-main">
                      <p><strong>Overall:</strong> {getCurrentHoroscope().prediction?.overall}</p>
                    </div>
                    <div className="horoscope-categories">
                      <div className="category">
                        <h4>💕 Love</h4>
                        <p>{getCurrentHoroscope().prediction?.love}</p>
                      </div>
                      <div className="category">
                        <h4>💼 Career</h4>
                        <p>{getCurrentHoroscope().prediction?.career}</p>
                      </div>
                      <div className="category">
                        <h4>🏥 Health</h4>
                        <p>{getCurrentHoroscope().prediction?.health}</p>
                      </div>
                      <div className="category">
                        <h4>💰 Finance</h4>
                        <p>{getCurrentHoroscope().prediction?.finance}</p>
                      </div>
                    </div>
                    <div className="horoscope-extras">
                      <div className="lucky-info">
                        <span><strong>Lucky Number:</strong> {getCurrentHoroscope().lucky_number}</span>
                        <span><strong>Lucky Color:</strong> {getCurrentHoroscope().lucky_color}</span>
                        <span><strong>Rating:</strong> {'⭐'.repeat(getCurrentHoroscope().rating || 0)}</span>
                      </div>
                      <button 
                        className="view-full-btn"
                        onClick={() => navigate(`/horoscope?period=${selectedPeriod}&sign=${selectedZodiac}`)}
                        style={{
                          marginTop: '15px',
                          padding: '10px 20px',
                          background: 'linear-gradient(135deg, #e91e63, #f06292)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '25px',
                          cursor: 'pointer',
                          fontSize: '14px',
                          fontWeight: 'bold'
                        }}
                      >
                        View Full {selectedPeriod.charAt(0).toUpperCase() + selectedPeriod.slice(1)} Horoscope →
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="festivals-sidebar">
              <h3>Festivals & Nakshatras</h3>
              <div className="festival-tabs">
                <button className="tab active" onClick={() => navigate('/festivals')}>Festivals</button>
                <button className="tab" onClick={() => navigate('/nakshatras')}>Nakshatras</button>
              </div>
              <div className="festival-list">
                <a href="/festivals">🎊 Daily Festivals</a>
                <a href="/festivals/monthly">📅 Monthly Calendar</a>
                <a href="/nakshatras">⭐ Nakshatra Guide</a>
                <a href="/nakshatra/ashwini/2025">🌟 2025 Predictions</a>
              </div>
            </div>
          </div>
        </div>
      </section>



      {/* Live Offers Banner */}
      <section className="live-offers">
        <div className="container">
          <div className="offers-scroll">
            {liveOffers.map((offer, index) => (
              <div key={index} className="offer-banner" style={{borderColor: offer.color}}>
                <div className="offer-content">
                  <h3>{offer.title}</h3>
                  <p>{offer.desc}</p>
                  <div className="timer" style={{color: offer.color}}>
                    ⏰ {offer.timer}
                  </div>
                </div>
                <button className="claim-btn" style={{background: offer.color}}>CLAIM NOW</button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust & Social Proof */}
      <section className="trust-section">
        <div className="container">
          <div className="trust-stats">
            <div className="stat-item">
              <div className="stat-number">50,000+</div>
              <div className="stat-label">Happy Customers</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">15+</div>
              <div className="stat-label">Years Experience</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">98%</div>
              <div className="stat-label">Accuracy Rate</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">24/7</div>
              <div className="stat-label">Support Available</div>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Features */}
      <section className="interactive-section">
        <div className="container">
          <div className="cosmic-insights-container">
            <span className="cosmic-icon cosmic-icon-left">✨</span>
            <h2 className="cosmic-insights-title">Today's Cosmic Insights</h2>
            <span className="cosmic-icon cosmic-icon-right">🌟</span>
          </div>
          <div className="interactive-grid">
            <div className="lucky-widget">
              <h3>🍀 Today's Lucky</h3>
              <div className="lucky-content">
                <div className="lucky-item">
                  <strong>🔢 Numbers:</strong> {todaysData.luckyNumbers.join(', ')}
                </div>
                <div className="lucky-item">
                  <strong>🎨 Colors:</strong> {todaysData.luckyColors.join(', ')}
                </div>
                <div className="lucky-item">
                  <strong>🧭 Direction:</strong> {todaysData.luckyDirection}
                </div>
                <div className="lucky-item">
                  <strong>⏰ Time:</strong> {todaysData.luckyTime}
                </div>
                <div className="lucky-item">
                  <strong>💎 Gemstone:</strong> {todaysData.luckyGemstone}
                </div>
                <div className="lucky-item">
                  <strong>🌟 Element:</strong> {todaysData.luckyElement}
                </div>
                <div className="lucky-item">
                  <strong>🪐 Planet:</strong> {todaysData.luckyPlanet}
                </div>
                <div className="lucky-item">
                  <strong>📅 Day:</strong> {todaysData.luckyDay}
                </div>
                <div className="lucky-item mantra">
                  <strong>🕉️ Mantra:</strong> {todaysData.dailyMantra}
                </div>
                <div className="avoid-section">
                  <div className="lucky-item avoid">
                    <strong>❌ Avoid Colors:</strong> {todaysData.avoidColors.join(', ')}
                  </div>
                  <div className="lucky-item avoid">
                    <strong>❌ Avoid Numbers:</strong> {todaysData.avoidNumbers.join(', ')}
                  </div>
                </div>
                <div className="activities-section">
                  <div className="lucky-item best">
                    <strong>✅ Best Activities:</strong> {todaysData.bestActivities.join(', ')}
                  </div>
                  <div className="lucky-item avoid">
                    <strong>⚠️ Avoid Activities:</strong> {todaysData.avoidActivities.join(', ')}
                  </div>
                </div>
                <div className="lucky-item rashi">
                  <strong>🌙 Ruling Rashi:</strong> {todaysData.rulingRashi}
                </div>
              </div>
            </div>
            
            <div className="planetary-widget">
              <h3>🪐 Live Planetary Positions</h3>
              <div className="planet-list">
                {planetaryLoading ? (
                  <div className="loading-planets">Loading current positions...</div>
                ) : (
                  planetaryPositions.map((planet, index) => (
                    <div key={index} className="planet-item">
                      <span className="planet-name">
                        {planet.planet}
                        {planet.retrograde && <span className="retrograde-indicator"> ℞</span>}
                      </span>
                      <span className="planet-sign">{planet.sign} {planet.degree}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
            
            <div className="muhurat-widget">
              <h3>🕐 Today's Muhurat Times</h3>
              <div className="muhurat-content">
                {muhuratLoading ? (
                  <div className="loading-muhurat">Loading auspicious times...</div>
                ) : (
                  <div className="muhurat-sections">
                    <div className="muhurat-section">
                      <h4>⏰ Choghadiya</h4>
                      <div className="muhurat-list">
                        {muhuratData?.choghadiya?.slice(0, 3).map((item, index) => (
                          <div key={index} className={`muhurat-item ${item.type}`}>
                            <span className="muhurat-name">{item.name}</span>
                            <span className="muhurat-time">{item.time}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="muhurat-section">
                      <h4>🪐 Hora</h4>
                      <div className="muhurat-list">
                        {muhuratData?.hora?.slice(0, 2).map((item, index) => (
                          <div key={index} className={`muhurat-item ${item.favorable ? 'good' : 'neutral'}`}>
                            <span className="muhurat-name">{item.planet}</span>
                            <span className="muhurat-time">{item.time}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="muhurat-section">
                      <h4>✨ Special</h4>
                      <div className="muhurat-list">
                        {muhuratData?.special?.slice(0, 2).map((item, index) => (
                          <div key={index} className="muhurat-item good">
                            <span className="muhurat-name">{item.name}</span>
                            <span className="muhurat-time">{item.time}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Numerology Section */}
      <section className="numerology-section">
        <div className="container">
          <div className="numerology-header">
            <span className="numerology-symbol numerology-symbol-1">🔢</span>
            <span className="numerology-symbol numerology-symbol-2">🌟</span>
            <span className="numerology-symbol numerology-symbol-3">🔮</span>
            <span className="numerology-symbol numerology-symbol-4">✨</span>
            <h2 className="numerology-title">🔢 Numerology Insights</h2>
            <p className="numerology-subtitle">Discover your life path through the power of numbers</p>
            <div className="numerology-divider"></div>
          </div>
          
          <div className="numerology-grid">
            <div className="numerology-card lo-shu-card">
              <div className="numerology-icon">🔮</div>
              <h4>Lo Shu Grid Analysis</h4>
              <p>Ancient Chinese numerology grid revealing your personality traits and life patterns</p>
              <div className="numerology-features">
                <span>🎯 Personality Analysis</span>
                <span>💪 Strength & Weakness</span>
                <span>🌟 Life Path Guidance</span>
              </div>
              <button 
                className="numerology-btn"
                onClick={() => {
                  if (!user) {
                    onLogin();
                    return;
                  }
                  setNumerologyTab('blueprint');
                  if (numerologyData) {
                    setShowNumerologyModal(true);
                  } else {
                    fetchNumerologyData();
                    setShowNumerologyModal(true);
                  }
                }}
              >
                {numerologyData ? 'View Grid' : 'Generate Grid'}
              </button>
            </div>
            
            <div className="numerology-card life-path-card">
              <div className="numerology-icon">🌟</div>
              <h4>Life Path Number</h4>
              <p>Your core life purpose and the path you're meant to walk in this lifetime</p>
              <div className="numerology-features">
                <span>🎯 Life Purpose</span>
                <span>💫 Destiny Number</span>
                <span>🌈 Soul Mission</span>
              </div>
              <button 
                className="numerology-btn"
                onClick={() => {
                  if (!user) {
                    onLogin();
                    return;
                  }
                  setNumerologyTab('blueprint');
                  if (numerologyData) {
                    setShowNumerologyModal(true);
                  } else {
                    fetchNumerologyData();
                    setShowNumerologyModal(true);
                  }
                }}
              >
                View Life Path
              </button>
            </div>
            
            <div className="numerology-card name-analysis-card">
              <div className="numerology-icon">📝</div>
              <h4>Name Analysis</h4>
              <p>Discover how your name influences your personality and life experiences</p>
              <div className="numerology-features">
                <span>🎭 Personality Traits</span>
                <span>🔤 Letter Vibrations</span>
                <span>✨ Name Optimization</span>
              </div>
              <button 
                className="numerology-btn"
                onClick={() => {
                  if (!user) {
                    onLogin();
                    return;
                  }
                  setNumerologyTab('names');
                  if (numerologyData) {
                    setShowNumerologyModal(true);
                  } else {
                    fetchNumerologyData();
                    setShowNumerologyModal(true);
                  }
                }}
              >
                Analyze Name
              </button>
            </div>
            
            <div className="numerology-card lucky-numbers-card">
              <div className="numerology-icon">🍀</div>
              <h4>Lucky Numbers</h4>
              <p>Personal lucky numbers based on your birth date and name vibrations</p>
              <div className="numerology-features">
                <span>🎲 Personal Numbers</span>
                <span>📅 Date Selection</span>
                <span>💰 Financial Timing</span>
              </div>
              <button 
                className="numerology-btn"
                onClick={() => {
                  if (!user) {
                    onLogin();
                    return;
                  }
                  setNumerologyTab('forecast');
                  if (numerologyData) {
                    setShowNumerologyModal(true);
                  } else {
                    fetchNumerologyData();
                    setShowNumerologyModal(true);
                  }
                }}
              >
                View Lucky Numbers
              </button>
            </div>
          </div>
          
          {/* <div className="numerology-cta">
            <div className="cta-content">
              <h3>🔢 Complete Numerology Analysis • Ancient Wisdom • Modern Insights</h3>
              <p>Unlock the secrets hidden in your numbers with Tara's guidance</p>
            </div>
            <button 
              className="start-numerology-btn"
              onClick={() => user ? setShowChatModal(true) : onLogin()}
            >
              🌟 Explore Numerology with Tara
            </button>
          </div> */}
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials-section">
        <div className="container">
          <h2>What Our Customers Say</h2>
          <div className="testimonials-grid">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="testimonial-card">
                <div className="testimonial-header">
                  <img src={testimonial.image} alt={testimonial.name} className="testimonial-avatar" />
                  <div className="testimonial-info">
                    <h4>{testimonial.name}</h4>
                    <p>{testimonial.location}</p>
                    <div className="rating">{'⭐'.repeat(testimonial.rating)}</div>
                  </div>
                </div>
                <p className="testimonial-text">"{testimonial.text}"</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* VIP Membership */}
      <section className="vip-section">
        <div className="container">
          <h2>VIP Membership Plans</h2>
          <div className="vip-grid">
            {vipTiers.map((tier, index) => (
              <div key={index} className="vip-card">
                <div className="vip-icon">{tier.icon}</div>
                <h3>{tier.name}</h3>
                <div className="vip-price">{tier.price}</div>
                <ul className="vip-features">
                  {tier.features.map((feature, i) => (
                    <li key={i}>✓ {feature}</li>
                  ))}
                </ul>
                <button className="vip-btn">Choose Plan</button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Educational Content */}
      <section className="education-section">
        <div className="container">
          <h2>Learn Astrology</h2>
          <div className="education-grid">
            <div className="education-card">
              <h3>🎓 Beginner's Guide</h3>
              <p>Start your astrology journey with basics</p>
              <button className="learn-btn" onClick={() => navigate('/beginners-guide')}>Start Learning</button>
            </div>
            <div className="education-card">
              <h3>📚 Advanced Courses</h3>
              <p>Master complex astrological techniques</p>
              <button className="learn-btn" onClick={() => navigate('/advanced-courses')}>Explore Courses</button>
            </div>
            <div className="education-card">
              <h3>🔍 Myth vs Reality</h3>
              <p>Separate facts from misconceptions</p>
              <button className="learn-btn" onClick={() => navigate('/myths-vs-reality')}>Read Articles</button>
            </div>
          </div>
        </div>
      </section>

      {/* Mobile App Promotion */}
      <section className="app-section">
        <div className="container">
          <div className="app-content">
            <div className="app-info">
              <h2>📱 Download Our Mobile App</h2>
              <p>Get instant access to astrology on the go!</p>
              <ul className="app-features">
                <li>✓ Push notifications for important transits</li>
                <li>✓ Offline chart viewing</li>
                <li>✓ Quick consultation booking</li>
                <li>✓ Daily horoscope alerts</li>
              </ul>
              <div className="app-badges">
                <button className="app-badge">📱 App Store</button>
                <button className="app-badge">🤖 Google Play</button>
              </div>
            </div>
            <div className="app-mockup">
              <div className="phone-mockup">📱</div>
            </div>
          </div>
        </div>
      </section>

      {/* Live Chat Widget */}
      <div className="live-chat-widget">
        <button className="chat-widget-btn" onClick={() => user ? setShowChatModal(true) : onLogin()}>
          <span className="chat-text-full">⭐ Ask Tara Now</span>
          <span className="chat-text-short">⭐ Ask Tara</span>
          <span className="chat-pulse"></span>
        </button>
      </div>

      {/* Consultation Section - Hidden for AstroRoshni */}
      {/* 
      <section className="consultation-section">
        <div className="container">
          <h2>Consult Astrologer on Call & Chat</h2>
          <div className="consultation-grid">
            {aiAstrologers.slice(0, 4).map(astrologer => (
              <div key={astrologer.id} className="consultation-card">
                <div className="astrologer-profile">
                  <div className="profile-image">
                    <div 
                      className="placeholder-img" 
                      style={{
                        backgroundImage: `url(${astrologer.image})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center'
                      }}
                    >
                    </div>
                    <span className={`status-dot ${astrologer.status}`}></span>
                  </div>
                  <div className="profile-info">
                    <h4>{astrologer.name}</h4>
                    <p className="expertise">{astrologer.expertise}</p>
                    <p className="experience">{astrologer.experience}</p>
                    <div className="rating">⭐ {astrologer.rating}</div>
                    <div className="rate">{astrologer.rate}</div>
                  </div>
                </div>
                <div className="consultation-actions">
                  <button className="call-btn">📞 Call</button>
                  <button className="chat-btn">💬 Chat</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
      */}

      {/* Footer */}
      <footer className="main-footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-links">
              <a href="#shop">Shop</a>
              <a href="#astrologers">Astrologers</a>
              <a href="#kundli">Free Kundli</a>
              <a href="#matching">Horoscope Matching</a>
              <a href="#zodiac">Zodiac Signs</a>
              <a href="#about">About Us</a>
              <a href="#contact">Contact Us</a>
              <a href="#privacy">Privacy Policy</a>
            </div>
            <div className="footer-bottom">
              <p>© 2025 AstroRoshni.com. All rights reserved.</p>
            </div>
          </div>
        </div>
      </footer>
      
      <ChatModal 
        isOpen={showChatModal} 
        onClose={() => setShowChatModal(false)}
        initialBirthData={null}
        onChartRefClick={(chartRef) => {
          setChartRefHighlight(chartRef);
          setShowChartModal(true);
          setTimeout(() => setChartRefHighlight(null), 5000);
        }}
      />
      
      <CreditsModal 
        isOpen={showCreditsModal} 
        onClose={() => setShowCreditsModal(false)} 
      />
      
      {showLoginModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            borderRadius: '15px',
            padding: '30px',
            maxWidth: '450px',
            width: '90%',
            position: 'relative'
          }}>
            <button 
              onClick={() => setShowLoginModal(false)}
              style={{
                position: 'absolute',
                top: '15px',
                right: '15px',
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#666'
              }}
            >
              ×
            </button>
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '20px' }}>Welcome to AstroRoshni</h2>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '20px' }}>
                <button 
                  onClick={() => setAuthView('login')}
                  style={{
                    padding: '10px 20px',
                    border: 'none',
                    background: authView === 'login' ? '#e91e63' : 'transparent',
                    color: authView === 'login' ? 'white' : '#e91e63',
                    borderRadius: '25px 0 0 25px',
                    cursor: 'pointer',
                    borderRight: '1px solid #e91e63'
                  }}
                >
                  Sign In
                </button>
                <button 
                  onClick={() => setAuthView('register')}
                  style={{
                    padding: '10px 20px',
                    border: 'none',
                    background: authView === 'register' ? '#e91e63' : 'transparent',
                    color: authView === 'register' ? 'white' : '#e91e63',
                    borderRadius: '0 25px 25px 0',
                    cursor: 'pointer'
                  }}
                >
                  Sign Up
                </button>
              </div>
            </div>
            {authView === 'login' ? (
              <LoginForm 
                onLogin={(userData) => {
                  // Handle login success - this should reload the page or update parent state
                  setShowLoginModal(false);
                  window.location.reload(); // Reload to get updated user state
                }} 
                onSwitchToRegister={() => setAuthView('register')} 
              />
            ) : (
              <RegisterForm 
                onRegister={(userData) => {
                  // Handle registration success - this should reload the page or update parent state
                  setShowLoginModal(false);
                  window.location.reload(); // Reload to get updated user state
                }} 
                onSwitchToLogin={() => setAuthView('login')} 
              />
            )}
          </div>
        </div>
      )}
      
      {showChartModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100001
        }}>
          <div style={{
            background: 'white',
            borderRadius: '15px',
            padding: '20px',
            maxWidth: '600px',
            width: '90%',
            maxHeight: '80vh',
            overflow: 'auto',
            position: 'relative'
          }}>
            <button 
              onClick={() => setShowChartModal(false)}
              style={{
                position: 'absolute',
                top: '15px',
                right: '15px',
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#666'
              }}
            >
              ×
            </button>
            <h2 style={{ textAlign: 'center', color: '#e91e63', marginBottom: '20px' }}>Your Birth Chart</h2>
            {chartData && birthData ? (
              <ChartWidget 
                title="Lagna Chart (D1)"
                chartType="lagna"
                chartData={chartData}
                birthData={birthData}
                defaultStyle="north"
                chartRefHighlight={chartRefHighlight}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                📊 Loading Chart...<br/>
                <small>Please wait while we generate your birth chart</small>
              </div>
            )}
          </div>
        </div>
      )}
      
      <BirthFormModal
        isOpen={showBirthFormModal}
        onClose={() => setShowBirthFormModal(false)}
        onSubmit={() => {
          setShowBirthFormModal(false);
          if (birthFormContext === 'numerology') {
            fetchNumerologyData();
            setShowNumerologyModal(true);
          } else if (birthFormContext === 'chart') {
            setShowChartModal(true);
          }
          // For 'changeNative' context, just close the modal and stay on homepage
        }}
        title={birthFormContext === 'numerology' ? 'Numerology - Enter Details' : 'Birth Chart - Enter Details'}
        description={birthFormContext === 'numerology' ? 'Please provide birth information for numerology analysis' : 'Please provide your birth information to generate your Vedic birth chart'}
      />
      
      {showNumerologyModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100001
        }}>
          <div style={{
            background: 'white',
            borderRadius: '15px',
            padding: '20px',
            maxWidth: '900px',
            width: '95%',
            maxHeight: '85vh',
            overflow: 'auto',
            position: 'relative'
          }}>
            <button 
              onClick={() => setShowNumerologyModal(false)}
              style={{
                position: 'absolute',
                top: '15px',
                right: '15px',
                background: 'none',
                border: 'none',
                fontSize: '24px',
                cursor: 'pointer',
                color: '#666'
              }}
            >
              ×
            </button>
            <div style={{ textAlign: 'center', marginBottom: '30px' }}>
              <h2 style={{ color: '#e91e63', marginBottom: '10px' }}>Life Optimization Suite</h2>
              {birthData && (
                <div style={{ 
                  background: 'rgba(233, 30, 99, 0.1)', 
                  padding: '8px 16px', 
                  borderRadius: '20px', 
                  display: 'inline-block',
                  fontSize: '14px',
                  color: '#e91e63',
                  border: '1px solid rgba(233, 30, 99, 0.2)',
                  marginBottom: '15px'
                }}>
                  👤 <strong>{birthData.name}</strong> • 📅 {birthData.date}
                </div>
              )}
              
              {/* Change Native Option */}
              <div style={{ marginTop: '10px' }}>
                <button 
                  onClick={() => {
                    setShowNumerologyModal(false);
                    setBirthFormContext('numerology');
                    setShowBirthFormModal(true);
                  }}
                  style={{
                    background: 'none',
                    border: '1px solid #e91e63',
                    color: '#e91e63',
                    padding: '6px 12px',
                    borderRadius: '15px',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  👤 Change Native
                </button>
              </div>
            </div>
            
            {/* Tab Navigation */}
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '10px',
              marginBottom: '30px',
              borderBottom: '2px solid #f0f0f0',
              paddingBottom: '15px'
            }}>
              <button 
                onClick={() => setNumerologyTab('blueprint')}
                style={{
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '25px',
                  background: numerologyTab === 'blueprint' ? 'linear-gradient(135deg, #e91e63, #f06292)' : 'rgba(233, 30, 99, 0.1)',
                  color: numerologyTab === 'blueprint' ? 'white' : '#e91e63',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  transition: 'all 0.3s ease'
                }}
              >
                🔮 Soul Blueprint
              </button>
              <button 
                onClick={() => setNumerologyTab('forecast')}
                style={{
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '25px',
                  background: numerologyTab === 'forecast' ? 'linear-gradient(135deg, #ff9800, #ffa726)' : 'rgba(255, 152, 0, 0.1)',
                  color: numerologyTab === 'forecast' ? 'white' : '#ff9800',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  transition: 'all 0.3s ease'
                }}
              >
                🌟 Cosmic Weather
              </button>
              <button 
                onClick={() => setNumerologyTab('names')}
                style={{
                  padding: '10px 20px',
                  border: 'none',
                  borderRadius: '25px',
                  background: numerologyTab === 'names' ? 'linear-gradient(135deg, #4caf50, #66bb6a)' : 'rgba(76, 175, 80, 0.1)',
                  color: numerologyTab === 'names' ? 'white' : '#4caf50',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  transition: 'all 0.3s ease'
                }}
              >
                ✨ Name Alchemist
              </button>
            </div>
            
            {/* Tab Content */}
            {numerologyTab === 'blueprint' && (
              numerologyData ? (
                <LoShuGrid numerologyData={numerologyData} />
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                  🔢 Loading Soul Blueprint...<br/>
                  <small>Calculating your life path numbers and Lo Shu grid</small>
                </div>
              )
            )}
            
            {numerologyTab === 'forecast' && (
              numerologyData && numerologyData.forecast ? (
                <CosmicForecast forecastData={numerologyData.forecast} />
              ) : (
                <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                  🌟 Loading Cosmic Weather...<br/>
                  <small>Analyzing your personal year, month, and day cycles</small>
                </div>
              )
            )}
            
            {numerologyTab === 'names' && (
              <NameOptimizer 
                initialName={birthData?.name || ''} 
                onOptimize={handleNameOptimization}
              />
            )}
          </div>
        </div>
      )}
      
      {/* Destiny Reading Modal */}
      {showDestinyModal && destinyReading && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.9)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100002
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
            borderRadius: '20px',
            padding: '30px',
            maxWidth: '800px',
            width: '95%',
            maxHeight: '90vh',
            overflow: 'auto',
            position: 'relative',
            border: '2px solid #e91e63',
            boxShadow: '0 20px 60px rgba(233, 30, 99, 0.3)',
            scrollbarWidth: 'none',
            msOverflowStyle: 'none'
          }}>
            <style>
              {`
                div::-webkit-scrollbar {
                  display: none;
                }
              `}
            </style>
            <button 
              onClick={() => {
                setShowDestinyModal(false);
                setDestinyReading(null);
              }}
              style={{
                position: 'absolute',
                top: '15px',
                right: '15px',
                background: 'rgba(233, 30, 99, 0.2)',
                border: '1px solid #e91e63',
                borderRadius: '50%',
                width: '40px',
                height: '40px',
                fontSize: '20px',
                cursor: 'pointer',
                color: '#e91e63',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              ×
            </button>
            
            <div style={{ textAlign: 'center', marginBottom: '30px' }}>
              <div style={{
                fontSize: '60px',
                marginBottom: '15px',
                background: 'linear-gradient(45deg, #e91e63, #f06292, #ff9800)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                animation: 'pulse 2s infinite'
              }}>🔮</div>
              <h2 style={{ 
                color: '#e91e63', 
                marginBottom: '10px',
                fontSize: '28px',
                textShadow: '0 2px 10px rgba(233, 30, 99, 0.3)'
              }}>Your Destiny Reading</h2>
              <p style={{ 
                color: '#b0b0b0', 
                fontSize: '16px',
                marginBottom: '20px'
              }}>Revealed through Classical Vedic Techniques</p>
              
              {birthData && (
                <div style={{ 
                  background: 'rgba(233, 30, 99, 0.1)', 
                  padding: '10px 20px', 
                  borderRadius: '25px', 
                  display: 'inline-block',
                  fontSize: '14px',
                  color: '#e91e63',
                  border: '1px solid rgba(233, 30, 99, 0.3)',
                  marginBottom: '20px'
                }}>
                  👤 <strong>{birthData.name}</strong> • 📅 {birthData.date} • 🕐 {birthData.time}
                </div>
              )}
            </div>
            
            <div style={{
              background: 'rgba(255, 255, 255, 0.05)',
              borderRadius: '15px',
              padding: '25px',
              border: '1px solid rgba(233, 30, 99, 0.2)',
              marginBottom: '20px'
            }}>
              <div style={{
                color: '#ffffff',
                lineHeight: '1.8',
                fontSize: '16px',
                whiteSpace: 'pre-wrap'
              }}>
                <div dangerouslySetInnerHTML={{
                  __html: (destinyReading.ai_prediction || destinyReading.prediction || 'Loading your destiny reading...')
                    .replace(/\*\*(.*?)\*\*/g, '<span style="font-weight: bold; color: #ffd700;">$1</span>')
                    .replace(/^### (.*$)/gm, '<span style="font-weight: bold; color: #ffd700; font-size: 18px;">$1</span>')
                    .replace(/\*\*\*/g, '<div style="text-align: center; margin: 20px 0; color: #e91e63; font-size: 20px;">✨ ⭐ ✨</div>')
                }} />
              </div>
            </div>
            
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '25px',
              flexWrap: 'wrap',
              gap: '15px'
            }}>
              <div style={{
                display: 'flex',
                gap: '15px',
                flexWrap: 'wrap'
              }}>
                <span style={{
                  background: 'rgba(76, 175, 80, 0.2)',
                  padding: '6px 12px',
                  borderRadius: '15px',
                  fontSize: '12px',
                  color: '#4caf50',
                  border: '1px solid rgba(76, 175, 80, 0.3)'
                }}>✨ Bhrigu Samhita</span>
                <span style={{
                  background: 'rgba(255, 152, 0, 0.2)',
                  padding: '6px 12px',
                  borderRadius: '15px',
                  fontSize: '12px',
                  color: '#ff9800',
                  border: '1px solid rgba(255, 152, 0, 0.3)'
                }}>📚 Lal Kitab</span>
                <span style={{
                  background: 'rgba(156, 39, 176, 0.2)',
                  padding: '6px 12px',
                  borderRadius: '15px',
                  fontSize: '12px',
                  color: '#9c27b0',
                  border: '1px solid rgba(156, 39, 176, 0.3)'
                }}>⭐ Nadi Astrology</span>
              </div>
              
              <div style={{
                display: 'flex',
                gap: '10px'
              }}>
                <button 
                  onClick={() => user ? setShowChatModal(true) : onLogin()}
                  style={{
                    background: 'linear-gradient(135deg, #e91e63, #f06292)',
                    color: 'white',
                    border: 'none',
                    padding: '12px 20px',
                    borderRadius: '25px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: 'bold'
                  }}
                >
                  💬 Ask Tara More
                </button>
                <button 
                  onClick={() => {
                    setShowDestinyModal(false);
                    setDestinyReading(null);
                  }}
                  style={{
                    background: 'rgba(255, 255, 255, 0.1)',
                    color: '#b0b0b0',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    padding: '12px 20px',
                    borderRadius: '25px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AstroRoshniHomepage;