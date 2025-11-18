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
import BirthFormModal from '../BirthForm/BirthFormModal';
import PartnerForm from '../MarriageAnalysis/PartnerForm';
import LoginForm from '../Auth/LoginForm';
import RegisterForm from '../Auth/RegisterForm';
import { showToast } from '../../utils/toast';
import './AstroRoshniHomepage.css';

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

  const aiAstrologers = [
    { id: 1, name: 'Acharya Joshi', expertise: 'Vedic, KP System', experience: '15+ Years', rate: '₹21/min', rating: 4.8, image: 'https://images.unsplash.com/photo-1566753323558-f4e0952af115?w=150&h=150&fit=crop&crop=face', status: 'online' },
    { id: 2, name: 'Dr. Priya Sharma', expertise: 'Numerology, Tarot', experience: '12+ Years', rate: '₹18/min', rating: 4.9, image: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face', status: 'online' },
    { id: 3, name: 'Pandit Raj Kumar', expertise: 'Vedic, Palmistry', experience: '20+ Years', rate: '₹25/min', rating: 4.7, image: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150&h=150&fit=crop&crop=face', status: 'busy' },
    { id: 4, name: 'Astro Ananya', expertise: 'Love, Career', experience: '8+ Years', rate: '₹15/min', rating: 4.6, image: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&h=150&fit=crop&crop=face', status: 'online' },
    { id: 5, name: 'Guru Vikash', expertise: 'Vastu, Remedies', experience: '18+ Years', rate: '₹22/min', rating: 4.8, image: 'https://images.unsplash.com/photo-1582233479366-6d38bc390a08?w=150&h=150&fit=crop&crop=face', status: 'online' }
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
    { icon: '🔮', title: 'Daily Horoscope', desc: 'Your daily predictions' },
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
      } catch (error) {
        console.error('Error initializing data:', error);
      }
    };
    
    initializeData();
  }, []);

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
      
      console.log('API Responses:', { choghadiya, hora, specialMuhurtas });
      
      // Debug API calculations
      console.log('=== API CALCULATION ANALYSIS ===');
      console.log('Date requested:', today);
      console.log('Location:', { latitude, longitude });
      
      // Check Brahma Muhurta calculation
      if (specialMuhurtas.muhurtas) {
        const brahmaMuhurta = specialMuhurtas.muhurtas.find(m => m.name === 'Brahma Muhurta');
        if (brahmaMuhurta) {
          console.log('Brahma Muhurta Raw:', brahmaMuhurta);
          console.log('Start:', new Date(brahmaMuhurta.start_time).toString());
          console.log('End:', new Date(brahmaMuhurta.end_time).toString());
          console.log('Duration (hours):', (new Date(brahmaMuhurta.end_time) - new Date(brahmaMuhurta.start_time)) / (1000 * 60 * 60));
        }
      }
      
      // Check day duration
      console.log('Day duration (hours):', specialMuhurtas.day_duration_hours);
      console.log('Night duration (hours):', specialMuhurtas.night_duration_hours);
      
      // Check if times are in correct timezone
      console.log('Current local time:', new Date().toString());
      console.log('Current UTC time:', new Date().toISOString());
      
      console.log('=== END ANALYSIS ===');
      
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
      />

      {/* Your Life Categories */}
      <section className="life-categories">
        <div className="container">
          <div className="life-categories-header">
            <span className="life-path-symbol life-path-symbol-1">🌟</span>
            <span className="life-path-symbol life-path-symbol-2">🔮</span>
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
          <div className="ask-astrologer-banner" onClick={() => user ? setShowChatModal(true) : onLogin()}>
            <div className="banner-content">
              <div className="banner-icon">💬</div>
              <div className="banner-text">
                <h3>Deep Vedic Analysis</h3>
                <p>Get profound insights from ancient wisdom • Expert guidance • Personalized predictions</p>
              </div>
              <div className="banner-cta">
                <span>Start Chat →</span>
              </div>
            </div>
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

      {/* AI Astrologers Section */}
      <section className="ai-astrologers">
        <div className="container">
          <div className="section-header">
            <h2>AI Astrologers</h2>
            <a href="#all-astrologers" className="view-all">View All →</a>
          </div>
          
          <div className="astrologers-scroll">
            {aiAstrologers.map(astrologer => (
              <div key={astrologer.id} className="astrologer-card">
                <div className="astrologer-image">
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
                <div className="astrologer-info">
                  <h4>{astrologer.name}</h4>
                  <p className="expertise">{astrologer.expertise}</p>
                  <p className="experience">{astrologer.experience}</p>
                  <div className="rating">
                    ⭐ {astrologer.rating}
                  </div>
                  <div className="rate">{astrologer.rate}</div>
                  <div className="action-buttons">
                    <button className="call-btn">📞 Call</button>
                    <button className="chat-btn">💬 Chat</button>
                  </div>
                </div>
              </div>
            ))}
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
                <span>🔮 Advanced Dasha Systems</span>
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
                    <span>🌙</span><span>⭐</span><span>🪐</span><span>🔮</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Premium Services - Moved Higher */}
      <section className="premium-services">
        <div className="container">
          <div className="premium-services-header">
            <span className="service-symbol service-symbol-1">🔮</span>
            <span className="service-symbol service-symbol-2">📊</span>
            <span className="service-symbol service-symbol-3">💎</span>
            <span className="service-symbol service-symbol-4">🌟</span>
            <span className="service-symbol service-symbol-5">📋</span>
            <span className="service-symbol service-symbol-6">💫</span>
            <span className="service-symbol service-symbol-7">🎯</span>
            <span className="service-symbol service-symbol-8">✨</span>
            <h2 className="premium-services-title">Astrological Services for Accurate Answers</h2>
            <p className="premium-services-subtitle">Professional insights backed by ancient wisdom and modern precision</p>
            <div className="premium-services-divider"></div>
          </div>
          <div className="premium-grid">
            <div className="featured-service">
              <div className="ribbon">33% OFF</div>
              <div className="service-image">
                <div className="placeholder-img">📊</div>
              </div>
              <h3>AstroVishnu Software - 1 Year</h3>
              <p>Advanced astrology software with cloud features</p>
              <button className="buy-btn">BUY NOW</button>
            </div>
            
            {premiumServices.map((service, index) => (
              <div key={index} className="premium-card">
                <div className="service-image">
                  <div className="placeholder-img">{service.icon}</div>
                </div>
                <h4>{service.title}</h4>
                <p>{service.desc}</p>
                <div className="price">{service.price}</div>
                <button 
                  className="check-btn" 
                  onClick={() => {
                    if (service.title === 'Marriage Report') {
                      navigate('/marriage-analysis');
                    } else if (service.title === 'Career Guidance') {
                      navigate('/career-guidance');
                    } else if (service.title === 'Health Report') {
                      navigate('/health-analysis');
                    } else if (service.title === 'Finance Report') {
                      navigate('/wealth-analysis');
                    }
                  }}
                >
                  Check Now
                </button>
              </div>
            ))}
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
                <button 
                  className="chart-btn"
                  onClick={() => user ? setShowBirthFormModal(true) : onLogin()}
                >
                  Generate Chart
                </button>
              </div>
            </div>

            {/* Column 3 - Nakshatra Widget (20%) */}
            <div className="form-card nakshatra-widget">
              <h3>Nakshatra Guide</h3>
              <div className="nakshatra-content">
                <p>Discover the 27 lunar mansions and their influence</p>
                <div className="nakshatra-features">
                  <div className="feature-item">📅 Annual Periods</div>
                  <div className="feature-item">⭐ Characteristics</div>
                  <div className="feature-item">🔮 Predictions</div>
                  <div className="feature-item">🎯 Lucky Periods</div>
                </div>
                <div className="nakshatra-info">
                  <p><strong>Total:</strong> 27 Nakshatras</p>
                  <p><strong>Year:</strong> 2025 Calendar</p>
                </div>
                <button 
                  className="nakshatra-btn"
                  onClick={() => navigate('/nakshatras')}
                >
                  Explore Now
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
                <button className={`tab ${selectedPeriod === 'weekly' ? 'active' : ''}`} onClick={() => setSelectedPeriod('weekly')}>Weekly</button>
                <button className={`tab ${selectedPeriod === 'monthly' ? 'active' : ''}`} onClick={() => setSelectedPeriod('monthly')}>Monthly</button>
                <button className={`tab ${selectedPeriod === 'yearly' ? 'active' : ''}`} onClick={() => setSelectedPeriod('yearly')}>Yearly</button>
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
          💬 Ask Question Now
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
          setShowChartModal(true);
        }}
        title="Birth Chart - Enter Details"
        description="Please provide your birth information to generate your Vedic birth chart"
      />
    </div>
  );
};

export default AstroRoshniHomepage;