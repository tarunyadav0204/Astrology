import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  Modal,
  Platform,
  StatusBar,
  Dimensions,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/Ionicons';
import { COLORS, API_BASE_URL } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { chartAPI } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import JaiminiKalachakraHomeRN from './JaiminiKalachakraHomeRN';
import YoginiDashaTab from './YoginiDashaTab';
import CharaDashaTab from './CharaDashaTab';
import Svg, { Circle, Path, Text as SvgText, G, Defs, LinearGradient, Stop } from 'react-native-svg';
import DateNavigator from '../Common/DateNavigator';
import { useAnalytics } from '../../hooks/useAnalytics';
import { trackAstrologyEvent } from '../../utils/analytics';
import { useTranslation } from 'react-i18next';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const signNameMap = {
  'aries': 'Ari', 'taurus': 'Tau', 'gemini': 'Gem', 'cancer': 'Can',
  'leo': 'Leo', 'virgo': 'Vir', 'libra': 'Lib', 'scorpio': 'Sco',
  'sagittarius': 'Sag', 'capricorn': 'Cap', 'aquarius': 'Aqu', 'pisces': 'Pis'
};
const shortSignMap = {
  'ari': 'Ari', 'tau': 'Tau', 'gem': 'Gem', 'can': 'Can',
  'leo': 'Leo', 'vir': 'Vir', 'lib': 'Lib', 'sco': 'Sco',
  'sag': 'Sag', 'cap': 'Cap', 'aqu': 'Aqu', 'pis': 'Pis'
};

const getShortSign = (sign) => {
    if (typeof sign !== 'string') return sign;
    const lowerSign = sign.toLowerCase();
    return signNameMap[lowerSign] || shortSignMap[lowerSign] || sign;
};


const CascadingDashaBrowser = ({ visible, onClose, birthData, onRequireBirthData }) => {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  useAnalytics('CascadingDashaBrowser');

  const insets = useSafeAreaInsets();
  const [cascadingData, setCascadingData] = useState(null);
  const [kalchakraData, setKalchakraData] = useState(null);
  const [kalchakraAntarData, setKalchakraAntarData] = useState(null);
  const [kalchakraSystemInfo, setKalchakraSystemInfo] = useState(null);
  const [jaiminiData, setJaiminiData] = useState(null);
  const [jaiminiAntarData, setJaiminiAntarData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // When visible but no birth data, stop loading and show empty state
  useEffect(() => {
    if (visible && (!birthData || !birthData.name)) {
      setLoading(false);
      setError(null);
    }
  }, [visible, birthData]);
  const [transitDate, setTransitDate] = useState(new Date());
  const [selectedDashas, setSelectedDashas] = useState({});
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [dashaType, setDashaType] = useState('vimshottari'); // 'vimshottari', 'kalchakra', 'jaimini', or 'yogini'
  const [yoginiData, setYoginiData] = useState(null);
  const [showSystemInfo, setShowSystemInfo] = useState(false);
  const [showKalachakraViz, setShowKalachakraViz] = useState(false);
  const [kalchakraViewMode, setKalchakraViewMode] = useState('chips'); // 'chips', 'wheel', 'timeline'

  const [jaiminiTab, setJaiminiTab] = useState('home'); // 'home', 'periods', 'analysis'

  const tSign = (sign) => {
    if (!sign) return '';
    return t(`signs.${getShortSign(sign)}`, sign);
  };

  const formatPeriodDuration = (years) => {
    if (!years) return '';
    
    const totalDays = years * 365.25;
    const totalMonths = years * 12;
    
    if (totalDays < 90) { // Less than 3 months
      return `${Math.round(totalDays)}${t('dasha.dayShort', 'd')}`;
    } else if (totalMonths < 12) { // Less than 1 year
      return `${Math.round(totalMonths)}${t('dasha.monthShort', 'm')}`;
    } else {
      const wholeYears = Math.floor(years);
      const remainingMonths = Math.round((years - wholeYears) * 12);
      
      if (remainingMonths === 0) {
        return `${wholeYears}${t('dasha.yearShort', 'y')}`;
      } else {
        return `${wholeYears}${t('dasha.yearShort', 'y')} ${remainingMonths}${t('dasha.monthShort', 'm')}`;
      }
    }
  };
  const scrollRefs = {
    maha: React.useRef(null),
    antar: React.useRef(null),
    pratyantar: React.useRef(null),
    sookshma: React.useRef(null),
    prana: React.useRef(null),
    kalchakra_maha: React.useRef(null),
    kalchakra_antar: React.useRef(null),
    jaimini_maha: React.useRef(null)
  };

  useEffect(() => {
    if (visible && birthData) {
      if (dashaType === 'vimshottari') {
        fetchCascadingDashas();
      } else if (dashaType === 'kalchakra') {
        fetchKalchakraDashas();
      } else if (dashaType === 'jaimini') {
        fetchJaiminiKalchakraDashas();
      } else if (dashaType === 'yogini') {
        fetchYoginiDasha();
      }
      trackAstrologyEvent.dashaViewed(dashaType);
    }
  }, [visible, birthData, transitDate, dashaType]);

  useEffect(() => {
    if (dashaType === 'vimshottari' && cascadingData) {
      autoSelectCurrentDashas();
    } else if (dashaType === 'kalchakra' && kalchakraData) {
      autoSelectCurrentKalchakraDashas();
    } else if (dashaType === 'jaimini' && jaiminiData) {
      autoSelectCurrentJaiminiDashas();
    }
  }, [cascadingData, kalchakraData, jaiminiData, dashaType]);

  // Auto-scroll to selected dashas
  useEffect(() => {
    Object.keys(selectedDashas).forEach(dashaType => {
      const selectedValue = selectedDashas[dashaType];
      const scrollRef = scrollRefs[dashaType];
      if (selectedValue && scrollRef?.current) {
        const options = getDashaOptions(dashaType);
        let selectedIndex = -1;
        
        if (dashaType === 'kalchakra_maha') {
          selectedIndex = options.findIndex(d => d.name === selectedValue);
        } else if (dashaType === 'kalchakra_antar') {
          selectedIndex = options.findIndex(d => d.name === selectedValue);
        } else {
          selectedIndex = options.findIndex(d => d.planet === selectedValue);
        }
        
        if (selectedIndex >= 0) {
          const cardWidth = dashaType.includes('kalchakra') ? 98 : 78;
          const scrollX = Math.max(0, selectedIndex * cardWidth - 50); // Center the selected chip
          setTimeout(() => {
            scrollRef.current?.scrollTo({ x: scrollX, animated: true });
          }, 200);
        }
      }
    });
  }, [selectedDashas, cascadingData, kalchakraData]);

  // Auto-scroll to current Kalchakra dasha on load
  useEffect(() => {
    if (dashaType === 'kalchakra' && kalchakraData?.mahadashas && scrollRefs.kalchakra_maha?.current) {
      const currentDate = new Date();
      const currentIndex = kalchakraData.mahadashas.findIndex(period => {
        const startDate = new Date(period.start);
        const endDate = new Date(period.end);
        return currentDate >= startDate && currentDate <= endDate;
      });
      
      if (currentIndex >= 0) {
        setTimeout(() => {
          scrollRefs.kalchakra_maha.current?.scrollTo({ 
            x: currentIndex * 98, 
            animated: true 
          });
        }, 300);
      }
    }
  }, [kalchakraData, dashaType]);

  // Auto-scroll to current Kalchakra antardasha
  useEffect(() => {
    if (dashaType === 'kalchakra' && kalchakraAntarData?.antar_periods && scrollRefs.kalchakra_antar?.current) {
      const currentIndex = kalchakraAntarData.antar_periods.findIndex(period => period.current);
      
      if (currentIndex >= 0) {
        setTimeout(() => {
          scrollRefs.kalchakra_antar.current?.scrollTo({ 
            x: currentIndex * 78, 
            animated: true 
          });
        }, 300);
      }
    }
  }, [kalchakraAntarData, dashaType]);

  const fetchCascadingDashas = async () => {
    try {
      console.log('\n' + '='.repeat(60));
      console.log('📱 COMPONENT: fetchCascadingDashas called');
      console.log('='.repeat(60));
      
      setLoading(true);
      setError(null);
      
      const targetDate = transitDate.toISOString().split('T')[0];
      console.log('Transit Date:', transitDate);
      console.log('Target Date (formatted):', targetDate);
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        place: birthData.place || 'Unknown'
      };
      
      // DEBUG: Log birth data being used in mobile app
      console.log('📱 MOBILE BIRTH DATA DEBUG:');
      console.log('   Raw birthData:', JSON.stringify(birthData, null, 2));
      console.log('   Formatted formattedBirthData:', JSON.stringify(formattedBirthData, null, 2));
      
      console.log('Formatted Birth Data:', JSON.stringify(formattedBirthData, null, 2));
      
      const response = await chartAPI.calculateCascadingDashas(formattedBirthData, targetDate);
      
      console.log('\n✅ COMPONENT: Response received');
      console.log('Response data keys:', Object.keys(response.data));
      console.log('Has error:', !!response.data.error);
      
      if (response.data.error) {
        console.error('❌ Error in response:', response.data.error);
        setError(`Vimshottari calculation failed: ${response.data.error}`);
        return;
      }
      
      // Check if we have maha_dashas in the response
      const mahadashas = response.data.maha_dashas || [];
      console.log('Maha dashas count:', mahadashas.length);
      
      if (mahadashas.length === 0) {
        console.warn('⚠️ No maha dashas in response');
        setError('Vimshottari calculation returned no dasha periods.');
        return;
      }
      
      console.log('First 3 maha dashas:');
      mahadashas.slice(0, 3).forEach((m, i) => {
        console.log(`  ${i+1}. ${m.planet}: ${m.start} to ${m.end} (current: ${m.current})`);
      });
      
      console.log('\n💾 Setting cascading data in state');
      setCascadingData(response.data);
      console.log('✅ State updated successfully\n');
    } catch (err) {
      console.error('❌ COMPONENT: Error in fetchCascadingDashas:', err);
      console.error('Error details:', err.message);
      setError('Failed to load cascading dasha data');
    } finally {
      setLoading(false);
    }
  };

  const fetchJaiminiAntardasha = async (mahaSign) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        location: birthData.place || 'Unknown'
      };
      
      const response = await fetch(`${API_BASE_URL}/api/calculate-jaimini-kalchakra-antardasha`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: formattedBirthData,
          maha_sign: mahaSign
        })
      });
      
      if (response.ok) {
        const antarData = await response.json();
        setJaiminiAntarData(antarData);
      }
    } catch (err) {

    }
  };

  const fetchYoginiDasha = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const formattedBirthData = {
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude)
      };
      
      const response = await chartAPI.calculateYoginiDasha(formattedBirthData, 5);
      
      if (response.data.error) {
        setError(`Yogini Dasha calculation failed: ${response.data.error}`);
        return;
      }
      
      // console.log('Yogini Dasha Response:', JSON.stringify(response.data, null, 2));
      setYoginiData(response.data);
    } catch (err) {
      setError('Failed to load Yogini Dasha data');
    } finally {
      setLoading(false);
    }
  };

  const fetchJaiminiKalchakraDashas = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = await AsyncStorage.getItem('authToken');
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        location: birthData.place || 'Unknown'
      };
      
      const response = await fetch(`${API_BASE_URL}/api/calculate-jaimini-kalchakra-dasha`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: formattedBirthData
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const jaiminiData = await response.json();
      
      if (jaiminiData.error) {
        setError(`Jaimini calculation failed: ${jaiminiData.error}`);
        return;
      }
      
      // Check if we have valid data structure
      if (!jaiminiData.periods || jaiminiData.periods.length === 0) {
        setError('Jaimini calculation returned no dasha periods. This may be due to a backend calculation error.');
        return;
      }
      
      setJaiminiData(jaiminiData);
      
    } catch (err) {
      setError('Failed to load Jaimini Kalchakra dasha data');
    } finally {
      setLoading(false);
    }
  };

  const fetchKalchakraDashas = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const token = await AsyncStorage.getItem('authToken');
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        location: birthData.place || 'Unknown'
      };
      
      // Fetch main Kalchakra data
      const response = await fetch(`${API_BASE_URL}/api/calculate-kalchakra-dasha`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: formattedBirthData
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const kalchakraData = await response.json();
      
      if (kalchakraData.error) {
        setError(`Kalchakra calculation failed: ${kalchakraData.error}`);
        return;
      }
      
      
      // Check if we have valid data structure
      if (!kalchakraData.mahadashas || kalchakraData.mahadashas.length === 0) {
        setError('Kalchakra calculation returned no dasha periods. This may be due to a backend calculation error.');
        return;
      }
      
      setKalchakraData(kalchakraData);
      
      // Fetch system info
      try {
        const infoResponse = await fetch(`${API_BASE_URL}/api/kalchakra-dasha-info`);
        if (infoResponse.ok) {
          const systemInfo = await infoResponse.json();
          setKalchakraSystemInfo(systemInfo);
        }
      } catch (infoErr) {
      }
      
    } catch (err) {
      setError('Failed to load Kalchakra dasha data');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchKalchakraAntardasha = async (mahaSign) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        location: birthData.place || 'Unknown'
      };
      
      const response = await fetch(`${API_BASE_URL}/api/calculate-kalchakra-antardasha`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: formattedBirthData,
          maha_sign: mahaSign,
          target_date: new Date().toISOString().split('T')[0]
        })
      });
      
      if (response.ok) {
        const antarData = await response.json();
        setKalchakraAntarData(antarData);
      } else {
      }
    } catch (err) {

    }
  };

  const autoSelectCurrentDashas = () => {
    if (!cascadingData) {
      return;
    }
    
    const currentSelections = {};
    
    const currentMaha = cascadingData.maha_dashas?.find(d => d.current);
    if (currentMaha) {
      currentSelections.maha = currentMaha.planet;
    }
    
    const currentAntar = cascadingData.antar_dashas?.find(d => d.current);
    if (currentAntar) {
      currentSelections.antar = currentAntar.planet;
    }
    
    const currentPratyantar = cascadingData.pratyantar_dashas?.find(d => d.current);
    if (currentPratyantar) {
      currentSelections.pratyantar = currentPratyantar.planet;
    }
    
    const currentSookshma = cascadingData.sookshma_dashas?.find(d => d.current);
    if (currentSookshma) {
      currentSelections.sookshma = currentSookshma.planet;
    }
    
    const currentPrana = cascadingData.prana_dashas?.find(d => d.current);
    if (currentPrana) {
      currentSelections.prana = currentPrana.planet;
    }
    
    setSelectedDashas(currentSelections);
  };

  const autoSelectCurrentJaiminiDashas = () => {
    if (!jaiminiData?.periods) {
      return;
    }
    
    if (jaiminiData.periods.length === 0) {
      return;
    }
    
    // Find the period marked as current by backend
    const currentPeriod = jaiminiData.periods.find(period => period.current === true);
    
    if (currentPeriod) {
      setSelectedDashas({ jaimini_maha: currentPeriod.id || currentPeriod.sign || currentPeriod.planet });
      fetchJaiminiAntardasha(currentPeriod.sign || currentPeriod.planet);
    } else if (jaiminiData.periods.length > 0) {
      // Fallback: select first period
      const firstPeriod = jaiminiData.periods[0];
      setSelectedDashas({ jaimini_maha: firstPeriod.id || firstPeriod.sign });
      fetchJaiminiAntardasha(firstPeriod.sign);
    }
  };

  // Auto-select current antardasha when antardasha data loads
  useEffect(() => {
    if (jaiminiAntarData?.antar_periods) {
      const currentAntar = jaiminiAntarData.antar_periods.find(period => period.current);
      if (currentAntar) {
        setTimeout(() => {
          setSelectedDashas(prev => ({ ...prev, jaimini_antar: currentAntar.sign }));
        }, 200);
      }
    }
  }, [jaiminiAntarData]);

  // Auto-scroll to selected Jaimini period (show earlier periods for context)
  useEffect(() => {
    if (selectedDashas.jaimini_maha && jaiminiData?.periods && scrollRefs.jaimini_maha?.current) {
      const selectedIndex = jaiminiData.periods.findIndex(period => 
        (period.id || period.sign) === selectedDashas.jaimini_maha
      );
      if (selectedIndex >= 0) {
        setTimeout(() => {
          // Scroll to show 3-4 periods before current (card width ~120)
          const scrollX = Math.max(0, (selectedIndex - 3) * 120);
          scrollRefs.jaimini_maha.current?.scrollTo({ 
            x: scrollX, 
            animated: true 
          });
        }, 100);
      }
    }
  }, [selectedDashas.jaimini_maha, jaiminiData]);

  const autoSelectCurrentKalchakraDashas = () => {
    if (!kalchakraData?.mahadashas) return;
    
    // Use current mahadasha from backend response
    const currentMaha = kalchakraData.current_mahadasha || kalchakraData.mahadashas.find(period => {
      const startDate = new Date(period.start);
      const endDate = new Date(period.end);
      const now = new Date();
      return now >= startDate && now <= endDate;
    });
    
    if (currentMaha) {
      const selections = { kalchakra_maha: currentMaha.name };
      
      // Auto-select current antardasha if available
      if (kalchakraData.current_antardasha) {
        selections.kalchakra_antar = kalchakraData.current_antardasha.name;
      }
      
      setSelectedDashas(selections);
      
      // Fetch antardashas for current mahadasha
      fetchKalchakraAntardasha(currentMaha.name);
    }
  };
  
  const handleKalchakraMahaSelection = (signName) => {
    setSelectedDashas({ kalchakra_maha: signName });
    
    // Auto-scroll to selected mahadasha
    setTimeout(() => {
      if (scrollRefs.kalchakra_maha?.current && kalchakraData?.mahadashas) {
        const selectedIndex = kalchakraData.mahadashas.findIndex(d => d.name === signName);
        if (selectedIndex >= 0) {
          const scrollX = Math.max(0, selectedIndex * 98 - 50);
          scrollRefs.kalchakra_maha.current.scrollTo({ x: scrollX, animated: true });
        }
      }
    }, 100);
  };
  
  const calculateProgress = (startDate, endDate, currentDate = new Date()) => {
    const start = new Date(startDate).getTime();
    const end = new Date(endDate).getTime();
    const current = currentDate.getTime();
    
    if (current < start) return 0;
    if (current > end) return 100;
    
    return ((current - start) / (end - start)) * 100;
  };
  
  const getRemainingTime = (endDate) => {
    const end = new Date(endDate);
    const now = new Date();
    const diffMs = end - now;
    
    if (diffMs <= 0) return t('dasha.completed', 'Completed');
    
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffYears = Math.floor(diffDays / 365);
    const remainingDays = diffDays % 365;
    const diffMonths = Math.floor(remainingDays / 30);
    const finalDays = remainingDays % 30;
    
    if (diffYears > 0) {
      return `${diffYears}${t('dasha.yearShort', 'y')} ${diffMonths}${t('dasha.monthShort', 'm')} ${t('dasha.remaining', 'remaining')}`;
    } else if (diffMonths > 0) {
      return `${diffMonths}${t('dasha.monthShort', 'm')} ${finalDays}${t('dasha.dayShort', 'd')} ${t('dasha.remaining', 'remaining')}`;
    } else {
      return `${finalDays}${t('dasha.dayShort', 'd')} ${t('dasha.remaining', 'remaining')}`;
    }
  };

  const adjustDate = (days) => {
    const newDate = new Date(transitDate);
    newDate.setDate(newDate.getDate() + days);
    setTransitDate(newDate);
  };

  const handleDashaSelection = async (dashaType, option) => {
    // Find the selected dasha details
    const selectedDasha = getDashaOptions(dashaType).find(d => d.planet === option);
    if (!selectedDasha) return;
    
    // Set new date to middle of selected dasha period to get its children
    const startDate = new Date(selectedDasha.start);
    const endDate = new Date(selectedDasha.end);
    const middleDate = new Date(startDate.getTime() + (endDate.getTime() - startDate.getTime()) / 2);
    
    // Update selected dashas
    setSelectedDashas(prev => {
      const newSelections = { ...prev, [dashaType]: option };
      
      // Clear child selections when parent changes
      if (dashaType === 'maha') {
        delete newSelections.antar;
        delete newSelections.pratyantar;
        delete newSelections.sookshma;
        delete newSelections.prana;
      } else if (dashaType === 'antar') {
        delete newSelections.pratyantar;
        delete newSelections.sookshma;
        delete newSelections.prana;
      } else if (dashaType === 'pratyantar') {
        delete newSelections.sookshma;
        delete newSelections.prana;
      } else if (dashaType === 'sookshma') {
        delete newSelections.prana;
      }
      
      return newSelections;
    });
    
    // Update transit date to fetch children for selected dasha
    setTransitDate(middleDate);
  };

  const getDashaOptions = (dashaLevel) => {
    if (dashaType === 'kalchakra') {
      if (dashaLevel === 'kalchakra_maha') {
        const options = kalchakraData?.mahadashas || [];
        return options;
      } else if (dashaLevel === 'kalchakra_antar') {
        // Filter all_antardashas for the selected mahadasha
        const selectedMaha = selectedDashas.kalchakra_maha;
        if (selectedMaha && kalchakraData?.all_antardashas) {
          const filtered = kalchakraData.all_antardashas.filter(antar => 
            antar.maha_name === selectedMaha
          );
          return filtered;
        }
        return [];
      }
      return [];
    }
    
    if (!cascadingData) {
      return [];
    }
    
    let options = [];
    switch (dashaLevel) {
      case 'maha':
        options = cascadingData.maha_dashas || [];
        break;
      case 'antar':
        options = cascadingData.antar_dashas || [];
        break;
      case 'pratyantar':
        options = cascadingData.pratyantar_dashas || [];
        break;
      case 'sookshma':
        options = cascadingData.sookshma_dashas || [];
        break;
      case 'prana':
        options = cascadingData.prana_dashas || [];
        break;
      default:
        options = [];
    }
    
    if (options.length > 0) {
    }
    
    return options;
  };



  const renderDashaTypeSelector = () => {
    const tabActive = (key) => dashaType === key;
    const tabStyle = (key) => [styles.dashaTypeTab, tabActive(key) && { backgroundColor: colors.primary }];
    const tabTextStyle = (key) => ({ color: tabActive(key) ? '#fff' : colors.textSecondary });
    return (
      <View style={[styles.dashaTypeSelector, { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabScrollView}>
          <TouchableOpacity
            style={tabStyle('vimshottari')}
            onPress={() => {
              setDashaType('vimshottari');
              setSelectedDashas({});
              setKalchakraAntarData(null);
              setJaiminiData(null);
            }}
          >
            <Text style={[styles.dashaTypeTabText, tabTextStyle('vimshottari')]} numberOfLines={1}>
              {t('dasha.vimshottari')}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={tabStyle('kalchakra')}
            onPress={() => {
              setDashaType('kalchakra');
              setSelectedDashas({});
              setKalchakraAntarData(null);
              setJaiminiData(null);
            }}
          >
            <View style={styles.tabContent}>
              <Text style={[styles.dashaTypeTabText, tabTextStyle('kalchakra')]} numberOfLines={1}>
                {t('dasha.kalchakra')}
              </Text>
              {kalchakraSystemInfo && (
                <TouchableOpacity style={styles.infoButton} onPress={() => setShowSystemInfo(true)}>
                  <Text style={styles.infoIcon}>ℹ️</Text>
                </TouchableOpacity>
              )}
            </View>
          </TouchableOpacity>
          <TouchableOpacity
            style={tabStyle('yogini')}
            onPress={() => {
              setDashaType('yogini');
              setSelectedDashas({});
            }}
          >
            <Text style={[styles.dashaTypeTabText, tabTextStyle('yogini')]} numberOfLines={1}>
              {t('dasha.yogini')}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={tabStyle('chara')}
            onPress={() => {
              setDashaType('chara');
              setSelectedDashas({});
            }}
          >
            <Text style={[styles.dashaTypeTabText, tabTextStyle('chara')]} numberOfLines={1}>
              {t('dasha.chara')}
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </View>
    );
  };

  const renderDateNavigation = () => (
    <DateNavigator date={transitDate} onDateChange={setTransitDate} cosmicTheme={isDark} resetDate={new Date()} />
  );



  const getDashaDetails = (dashaLevel, planet) => {
    if (dashaType === 'kalchakra') {
      if (dashaLevel === 'kalchakra_maha') {
        if (!kalchakraData?.periods || !planet) return null;
        return kalchakraData.periods.find(d => d.planet === planet);
      } else if (dashaLevel === 'kalchakra_antar') {
        if (!kalchakraAntarData?.antar_periods || !planet) return null;
        return kalchakraAntarData.antar_periods.find(d => d.planet === planet);
      }
      return null;
    }
    
    if (!cascadingData || !planet) return null;
    
    let dashas = [];
    switch (dashaLevel) {
      case 'maha': dashas = cascadingData.maha_dashas || []; break;
      case 'antar': dashas = cascadingData.antar_dashas || []; break;
      case 'pratyantar': dashas = cascadingData.pratyantar_dashas || []; break;
      case 'sookshma': dashas = cascadingData.sookshma_dashas || []; break;
      case 'prana': dashas = cascadingData.prana_dashas || []; break;
      default: return null;
    }
    
    return dashas.find(d => d.planet === planet);
  };

  const renderJaiminiCurrentStatus = () => {
    return null; // Remove the purple status card
  };

  const renderKalchakraCurrentStatus = () => {
    if (!kalchakraData) return null;
    
    const currentMaha = kalchakraData.current_mahadasha || kalchakraData.mahadashas?.find(period => {
      const startDate = new Date(period.start);
      const endDate = new Date(period.end);
      const now = new Date();
      return now >= startDate && now <= endDate;
    });
    
    const currentAntar = kalchakraData.current_antardasha;
    
    if (!currentMaha) return null;
    
    const mahaProgress = calculateProgress(currentMaha.start, currentMaha.end);
    const antarProgress = currentAntar ? calculateProgress(currentAntar.start, currentAntar.end) : 0;
    
    return (
      <View style={[styles.currentStatusCard, { backgroundColor: isDark ? colors.surface : colors.cardBackground, borderColor: colors.cardBorder }]}>
        <Text style={[styles.currentStatusTitle, { color: colors.primary }]}>{t('dasha.currentBPHSKalachakra')}</Text>
        
        <View style={styles.compactPeriodRow}>
          <View style={styles.periodColumn}>
            <Text style={[styles.periodLabel, { color: colors.textSecondary }]}>{t('dasha.maha')}</Text>
            <Text style={[styles.periodName, { color: colors.primary }]}>{tSign(currentMaha.name)}</Text>
            <Text style={[styles.periodGati, { color: colors.textSecondary }]}>{currentMaha.gati}</Text>
          </View>
          
          {currentAntar && (
            <View style={styles.periodColumn}>
              <Text style={[styles.periodLabel, { color: colors.textSecondary }]}>{t('dasha.antar')}</Text>
              <Text style={[styles.periodName, { color: colors.primary }]}>{tSign(currentAntar.name)}</Text>
              <Text style={[styles.periodProgress, { color: colors.primary }]}>{Math.round(antarProgress)}%</Text>
            </View>
          )}
          
          <View style={styles.systemColumn}>
            <Text style={[styles.systemLabel, { color: colors.textSecondary }]}>{kalchakraData.cycle_len}y • {kalchakraData.direction}</Text>
            <Text style={[styles.systemLabel, { color: colors.textSecondary }]}>{t('dasha.nakshatra')}.{kalchakraData.nakshatra}.{kalchakraData.pada}</Text>
            <Text style={[styles.systemLabel, { color: colors.textSecondary }]}>{tSign(kalchakraData.deha)}→{tSign(kalchakraData.jeeva)}</Text>
          </View>
        </View>
        
        <View style={[styles.compactProgressBar, { backgroundColor: isDark ? 'rgba(255,255,255,0.15)' : colors.surface }]}>
          <View style={[styles.compactProgressFill, { width: `${mahaProgress}%`, backgroundColor: colors.primary }]} />
          <Text style={[styles.compactProgressText, { color: colors.text }]}>{Math.round(mahaProgress)}% • {getRemainingTime(currentMaha.end)}</Text>
        </View>
      </View>
    );
  };
  
  const renderBreadcrumb = () => {
    if (dashaType === 'kalchakra') {
      return renderKalchakraCurrentStatus();
    } else if (dashaType === 'jaimini') {
      return renderJaiminiCurrentStatus();
    } else if (dashaType === 'yogini' || dashaType === 'chara') {
      return null; // Yogini and Chara have their own hero sections, no breadcrumb needed
    }
    
    if (!cascadingData) {
      return (
        <View style={[styles.breadcrumb, dashaType === 'vimshottari' && { backgroundColor: isDark ? colors.surface : colors.cardBackground, borderRadius: 8 }]}>
          <Text style={[styles.breadcrumbText, dashaType === 'vimshottari' && { color: colors.textSecondary }]}>{t('dasha.selectDashas')}</Text>
        </View>
      );
    }

    const breadcrumbItems = [];
    
    if (selectedDashas.maha) {
      const details = getDashaDetails('maha', selectedDashas.maha);
      breadcrumbItems.push({ planet: selectedDashas.maha, details });
    }
    
    if (selectedDashas.antar) {
      const details = getDashaDetails('antar', selectedDashas.antar);
      breadcrumbItems.push({ planet: selectedDashas.antar, details });
    }
    
    if (selectedDashas.pratyantar) {
      const details = getDashaDetails('pratyantar', selectedDashas.pratyantar);
      breadcrumbItems.push({ planet: selectedDashas.pratyantar, details });
    }
    
    if (selectedDashas.sookshma) {
      const details = getDashaDetails('sookshma', selectedDashas.sookshma);
      breadcrumbItems.push({ planet: selectedDashas.sookshma, details });
    }
    
    if (selectedDashas.prana) {
      const details = getDashaDetails('prana', selectedDashas.prana);
      breadcrumbItems.push({ planet: selectedDashas.prana, details });
    }
    
    const vimTheme = dashaType === 'vimshottari';
    return (
      <View style={[styles.breadcrumb, vimTheme && { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
        {breadcrumbItems.length === 0 ? (
          <Text style={[styles.breadcrumbText, vimTheme && { color: colors.textSecondary }]}>{t('dasha.selectDashasHierarchy')}</Text>
        ) : (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.breadcrumbScroll}>
            {breadcrumbItems.map((item, index) => (
              <View key={`breadcrumb-${item.planet}-${index}`} style={styles.breadcrumbRow}>
                <View style={[styles.breadcrumbCard, vimTheme && { backgroundColor: isDark ? colors.background : colors.surface, borderColor: colors.cardBorder }]}>
                  <Text style={[styles.breadcrumbPlanet, vimTheme && { color: colors.primary }]}>{t(`planets.${item.planet}`, item.planet)}</Text>
                  {item.details && (
                    <>
                      <Text style={[styles.breadcrumbPeriod, vimTheme && { color: colors.text }]}>{formatPeriodDuration(item.details.years)}</Text>
                      <Text style={[styles.breadcrumbDates, vimTheme && { color: colors.textSecondary }]}>
                        {new Date(item.details.start).toLocaleDateString('en-US', {month: 'short', year: '2-digit'})} - {new Date(item.details.end).toLocaleDateString('en-US', {month: 'short', year: '2-digit'})}
                      </Text>
                    </>
                  )}
                </View>
                {index < breadcrumbItems.length - 1 && (
                  <Text style={[styles.breadcrumbArrow, vimTheme && { color: colors.textSecondary }]}>→</Text>
                )}
              </View>
            ))}
          </ScrollView>
        )}
      </View>
    );
  };



  const renderJaiminiTabs = () => {
    return (
      <React.Fragment>
        <View style={styles.jaiminiTabSelector}>
          <TouchableOpacity
            style={[styles.jaiminiTab, jaiminiTab === 'home' && styles.activeJaiminiTab]}
            onPress={() => setJaiminiTab('home')}
          >
            <Text style={[styles.jaiminiTabText, jaiminiTab === 'home' && styles.activeJaiminiTabText]}>{t('common.home')}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.jaiminiTab, jaiminiTab === 'periods' && styles.activeJaiminiTab]}
            onPress={() => setJaiminiTab('periods')}
          >
            <Text style={[styles.jaiminiTabText, jaiminiTab === 'periods' && styles.activeJaiminiTabText]}>{t('dasha.periods')}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.jaiminiTab, jaiminiTab === 'analysis' && styles.activeJaiminiTab]}
            onPress={() => setJaiminiTab('analysis')}
          >
            <Text style={[styles.jaiminiTabText, jaiminiTab === 'analysis' && styles.activeJaiminiTabText]}>{t('dasha.analysis')}</Text>
          </TouchableOpacity>
        </View>
        
        {jaiminiTab === 'home' && (
          <JaiminiKalachakraHomeRN birthData={birthData} />
        )}
        
        {jaiminiTab === 'periods' && renderJaiminiPeriodsList()}
        
        {jaiminiTab === 'analysis' && renderJaiminiAnalysis()}
      </React.Fragment>
    );
  };

  const renderJaiminiPeriodsList = () => {
    return renderJaiminiKalchakraDashaList();
  };

  const renderJaiminiAnalysis = () => {
    if (!jaiminiData?.cards) {
      return (
        <View style={styles.selectorContainer}>
          <Text style={styles.selectorLabel}>{t('dasha.analysis')}</Text>
          <View style={[styles.optionCard, styles.disabledOption]}>
            <Text style={styles.disabledOptionText}>{t('dasha.noAnalysis')}</Text>
          </View>
        </View>
      );
    }

    return (
      <View style={styles.predictionCardsSection}>
        <ScrollView style={styles.cardsContainer} showsVerticalScrollIndicator={false}>
          {/* Status Card */}
          {jaiminiData.cards.status_card && (
            <View style={styles.statusCard}>
              <Text style={styles.cardTitle}>{t('dasha.currentStatus')}</Text>
              <View style={styles.statusRow}>
                <Text style={styles.statusSign}>{jaiminiData.cards.status_card.sign_name}</Text>
                <Text style={styles.statusScore}>{jaiminiData.cards.status_card.strength_score}/100</Text>
              </View>
              <View style={styles.progressBarContainer}>
                <View style={styles.progressBar}>
                  <View style={[styles.progressFill, { width: `${jaiminiData.cards.status_card.progress_percent}%` }]} />
                </View>
                <Text style={styles.progressText}>{jaiminiData.cards.status_card.progress_percent}%</Text>
              </View>
              <Text style={styles.timeRemaining}>{jaiminiData.cards.status_card.time_remaining}</Text>
              <Text style={styles.chakraInfo}>Chakra {jaiminiData.cards.status_card.chakra} • {jaiminiData.cards.status_card.direction}</Text>
            </View>
          )}
          
          {/* Focus Card */}
          {jaiminiData.cards.focus_card && (
            <View style={styles.focusCard}>
              <Text style={styles.cardTitle}>{t('dasha.lifeFocus')}</Text>
              <Text style={styles.focusTheme}>{jaiminiData.cards.focus_card.theme}</Text>
              <Text style={styles.energyStyle}>⚡ {jaiminiData.cards.focus_card.energy_style}</Text>
              <Text style={styles.keyAreas}>🏠 {jaiminiData.cards.focus_card.key_areas}</Text>
              <View style={styles.keywordsContainer}>
                {jaiminiData.cards.focus_card.keywords.map((keyword, index) => (
                  <View key={index} style={styles.keywordTag}>
                    <Text style={styles.keywordText}>{keyword}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}
          
          {/* Timeline Card */}
          {jaiminiData.cards.timeline_card && (
            <View style={styles.timelineCard}>
              <Text style={styles.cardTitle}>{t('dasha.timeline')}</Text>
              <View style={styles.currentPeriodInfo}>
                <Text style={styles.currentPeriodName}>{jaiminiData.cards.timeline_card.current_period.name}</Text>
                <Text style={styles.currentPeriodDates}>
                  {new Date(jaiminiData.cards.timeline_card.current_period.start).toLocaleDateString()} - 
                  {new Date(jaiminiData.cards.timeline_card.current_period.end).toLocaleDateString()}
                </Text>
              </View>
              {jaiminiData.cards.timeline_card.next_events.length > 0 && (
                <View style={styles.nextEventsContainer}>
                  <Text style={styles.nextEventsTitle}>{t('dasha.upcomingEvents')}</Text>
                  {jaiminiData.cards.timeline_card.next_events.map((event, index) => (
                    <Text key={index} style={styles.nextEventText}>• {event.name} ({new Date(event.date).toLocaleDateString()})</Text>
                  ))}
                </View>
              )}
            </View>
          )}
          
          {/* Predictions Card */}
          {jaiminiData.cards.predictions_card && (
            <View style={styles.predictionsCard}>
              <Text style={styles.cardTitle}>{t('dasha.predictions')}</Text>
              {jaiminiData.cards.predictions_card.next_6_months.length > 0 && (
                <View style={styles.predictionSection}>
                  <Text style={styles.predictionSectionTitle}>{t('dasha.next6Months')}</Text>
                  {jaiminiData.cards.predictions_card.next_6_months.map((event, index) => (
                    <Text key={index} style={styles.predictionText}>• {event}</Text>
                  ))}
                </View>
              )}
              {jaiminiData.cards.predictions_card.next_2_years.length > 0 && (
                <View style={styles.predictionSection}>
                  <Text style={styles.predictionSectionTitle}>{t('dasha.next2Years')}</Text>
                  {jaiminiData.cards.predictions_card.next_2_years.map((theme, index) => (
                    <Text key={index} style={styles.predictionText}>• {theme}</Text>
                  ))}
                </View>
              )}
              {jaiminiData.cards.predictions_card.jump_effects.length > 0 && (
                <View style={styles.predictionSection}>
                  <Text style={styles.predictionSectionTitle}>{t('dasha.jumpEffects')}</Text>
                  {jaiminiData.cards.predictions_card.jump_effects.map((effect, index) => (
                    <Text key={index} style={styles.predictionText}>⚡ {effect}</Text>
                  ))}
                </View>
              )}
            </View>
          )}
          
          {/* Strength Card */}
          {jaiminiData.cards.strength_card && (
            <View style={styles.strengthCard}>
              <Text style={styles.cardTitle}>{t('dasha.strengthComparison')}</Text>
              <View style={styles.strengthComparison}>
                <View style={styles.strengthItem}>
                  <Text style={styles.strengthLabel}>{t('dasha.current')}</Text>
                  <View style={styles.strengthBar}>
                    <View style={[styles.strengthFill, { width: `${jaiminiData.cards.strength_card.current_strength}%` }]} />
                  </View>
                  <Text style={styles.strengthValue}>{jaiminiData.cards.strength_card.current_strength}/100</Text>
                </View>
                <View style={styles.strengthItem}>
                  <Text style={styles.strengthLabel}>{t('dasha.next')} ({jaiminiData.cards.strength_card.next_sign_name})</Text>
                  <View style={styles.strengthBar}>
                    <View style={[styles.strengthFill, { width: `${jaiminiData.cards.strength_card.next_strength}%` }]} />
                  </View>
                  <Text style={styles.strengthValue}>{jaiminiData.cards.strength_card.next_strength}/100</Text>
                </View>
              </View>
              <View style={[styles.guidanceContainer, {
                backgroundColor: jaiminiData.cards.strength_card.comparison === 'significant_increase' ? '#e8f5e8' :
                               jaiminiData.cards.strength_card.comparison === 'significant_decrease' ? '#ffebee' : '#fff3e0'
              }]}>
                <Text style={[styles.guidanceText, {
                  color: jaiminiData.cards.strength_card.comparison === 'significant_increase' ? '#2e7d32' :
                         jaiminiData.cards.strength_card.comparison === 'significant_decrease' ? '#c62828' : '#ef6c00'
                }]}>
                  💡 {jaiminiData.cards.strength_card.guidance}
                </Text>
              </View>
            </View>
          )}
        </ScrollView>
      </View>
    );
  };

  const renderJaiminiKalchakraDashaList = () => {
    if (!jaiminiData) {
      return (
        <View style={styles.selectorContainer}>
          <Text style={styles.selectorLabel}>{t('dasha.jaiminiKalchakraDasha')}</Text>
          <View style={[styles.optionCard, styles.disabledOption]}>
            <Text style={styles.disabledOptionText}>{t('dasha.loading')}</Text>
          </View>
        </View>
      );
    }
    
    if (jaiminiData.error) {
      return (
        <View style={styles.selectorContainer}>
          <Text style={styles.selectorLabel}>{t('dasha.jaiminiKalchakraDasha')}</Text>
          <View style={[styles.optionCard, styles.disabledOption]}>
            <Text style={styles.disabledOptionText}>{t('common.error')}: {jaiminiData.error}</Text>
          </View>
        </View>
      );
    }
    
    if (!jaiminiData.periods || jaiminiData.periods.length === 0) {
      return (
        <View style={styles.selectorContainer}>
          <Text style={styles.selectorLabel}>{t('dasha.jaiminiKalchakraDasha')}</Text>
          <View style={[styles.optionCard, styles.disabledOption]}>
            <Text style={styles.disabledOptionText}>{t('dasha.noPeriodsCalculated')}</Text>
          </View>
        </View>
      );
    }

    return (
      <React.Fragment>
        <View style={styles.jaiminiInfoCard}>
          <Text style={styles.jaiminiInfoTitle}>{t('dasha.jaiminiKalchakraSystem')}</Text>
          <Text style={styles.jaiminiInfoText}>{t('dasha.janmaRashi')}: {jaiminiData.janma_rashi}</Text>
          <Text style={styles.jaiminiInfoText}>{t('dasha.chakra1')}: {jaiminiData.chakra1_direction} • {t('dasha.chakra2')}: {jaiminiData.chakra2_direction}</Text>
          <Text style={styles.jaiminiInfoText}>{t('dasha.totalCycle')}: {jaiminiData.total_cycle_years} {t('dasha.years')}</Text>
          
          {jaiminiData.reversals && jaiminiData.reversals.length > 0 && (
            <View style={styles.reversalInfo}>
              <Text style={styles.reversalTitle}>{t('dasha.directionReversals')}</Text>
              {jaiminiData.reversals.map((reversal, index) => (
                <Text key={index} style={styles.reversalText}>
                  {reversal.type}: {reversal.from_direction} → {reversal.to_direction}
                </Text>
              ))}
            </View>
          )}
          
          {jaiminiData.jumps && jaiminiData.jumps.length > 0 && (
            <View style={styles.jumpInfo}>
              <Text style={styles.jumpTitle}>{t('dasha.signJumps')}</Text>
              {jaiminiData.jumps.map((jump, index) => (
                <Text key={index} style={styles.jumpText}>
                  {t('dasha.skipped')}: {jump.skipped_sign} ({jump.reason})
                </Text>
              ))}
            </View>
          )}
          
          {jaiminiData.predictions && (
            <View style={styles.predictionInfo}>
              <Text style={styles.predictionTitle}>{t('dasha.upcomingEvents')}</Text>
              
              {jaiminiData.predictions.cycle_progress && (
                <Text style={styles.predictionText}>
                  {t('dasha.cycleProgress')}: {jaiminiData.predictions.cycle_progress}% {t('dasha.complete')}
                </Text>
              )}
              
              {jaiminiData.predictions.next_reversal && (
                <Text style={styles.predictionText}>
                  {t('dasha.nextReversal')}: {jaiminiData.predictions.next_reversal.significance} in {jaiminiData.predictions.next_reversal.years_until} {t('dasha.years')}
                </Text>
              )}
              
              {jaiminiData.predictions.next_cycle_reset && (
                <Text style={styles.predictionText}>
                  {t('dasha.cycleReset')}: {jaiminiData.predictions.next_cycle_reset.years_until} {t('dasha.years')} ({t('dasha.cycle')} {jaiminiData.predictions.next_cycle_reset.cycle_number})
                </Text>
              )}
              
              {jaiminiData.predictions.upcoming_events && jaiminiData.predictions.upcoming_events.slice(0, 2).map((event, index) => (
                <Text key={index} style={styles.predictionText}>
                  {event.sign} {event.type}: {event.years_until}y ({event.duration_years}y duration)
                </Text>
              ))}
            </View>
          )}
          

        </View>
        
        <View style={styles.selectorContainer}>
          <Text style={styles.selectorLabel}>{t('dasha.jaiminiKalchakraMahadasha')}</Text>
          <ScrollView 
            ref={scrollRefs.jaimini_maha}
            horizontal 
            showsHorizontalScrollIndicator={false} 
            style={styles.optionsScroll}
          >
            {jaiminiData.periods.map((period, index) => {
              const currentDate = new Date();
              const startDate = new Date(period.start_date);
              const endDate = new Date(period.end_date);
              const isActuallyCurrent = currentDate >= startDate && currentDate <= endDate;
              const progress = calculateProgress(period.start_date, period.end_date);
              
              return (
                <TouchableOpacity
                  key={`${period.sign}-${index}`}
                  style={[
                    styles.jaiminiCard,
                    period.chakra === 1 ? styles.jaiminiChakra1Card : styles.jaiminiChakra2Card,
                    isActuallyCurrent && styles.currentJaiminiCard,
                    selectedDashas.jaimini_maha === (period.id || period.sign) && styles.selectedJaiminiCard
                  ]}
                  onPress={() => {
                    setSelectedDashas({ jaimini_maha: period.id || period.sign });
                    fetchJaiminiAntardasha(period.sign);
                    
                    // Auto-scroll to selected jaimini mahadasha
                    setTimeout(() => {
                      if (scrollRefs.jaimini_maha?.current && jaiminiData?.periods) {
                        const selectedIndex = jaiminiData.periods.findIndex(p => (p.id || p.sign) === (period.id || period.sign));
                        if (selectedIndex >= 0) {
                          const scrollX = Math.max(0, selectedIndex * 120 - 60);
                          scrollRefs.jaimini_maha.current.scrollTo({ x: scrollX, animated: true });
                        }
                      }
                    }, 100);
                  }}
                >
                  <Text style={[ 
                    styles.jaiminiSign,
                    isActuallyCurrent && styles.currentJaiminiSign,
                    selectedDashas.jaimini_maha === (period.id || period.sign) && styles.selectedJaiminiText
                  ]}>
                    {t(`signs.${period.sign}`, period.sign)}
                  </Text>
                  <Text style={[ 
                    styles.jaiminiPeriod,
                    isActuallyCurrent && styles.currentJaiminiPeriod,
                    selectedDashas.jaimini_maha === (period.id || period.sign) && styles.selectedJaiminiText
                  ]}>
                    {formatPeriodDuration(period.duration_years)}
                  </Text>
                  <Text style={[ 
                    styles.jaiminiChakra,
                    isActuallyCurrent && styles.currentJaiminiChakra,
                    selectedDashas.jaimini_maha === (period.id || period.sign) && styles.selectedJaiminiText
                  ]}>
                    C{period.chakra} {period.direction === t('dasha.forward') ? '→' : '←'}
                  </Text>
                  <Text style={[ 
                    styles.jaiminiDates,
                    isActuallyCurrent && styles.currentJaiminiDates,
                    selectedDashas.jaimini_maha === (period.id || period.sign) && styles.selectedJaiminiText
                  ]}>
                    {new Date(period.start_date).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})} - {new Date(period.end_date).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})}
                  </Text>
                  {isActuallyCurrent && (
                    <View style={styles.jaiminiProgressBar}>
                      <View style={[styles.jaiminiProgressFill, { width: `${progress}%` }]} />
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>
        
        {jaiminiAntarData?.antar_periods && (
          <View style={styles.selectorContainer}>
            <Text style={styles.selectorLabel}>{t('dasha.jaiminiAntardasha')} ({jaiminiAntarData.maha_sign})</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.optionsScroll}>
              {jaiminiAntarData.antar_periods.map((period, index) => {
                const isActuallyCurrent = period.current;
                const progress = calculateProgress(period.start_date, period.end_date);
                
                return (
                  <TouchableOpacity
                    key={`antar-${period.sign}-${index}`}
                    style={[ 
                      styles.jaiminiAntarCard,
                      isActuallyCurrent && styles.currentJaiminiAntarCard,
                      selectedDashas.jaimini_antar === period.sign && styles.selectedJaiminiAntarCard
                    ]}
                    onPress={() => {
                      setSelectedDashas(prev => ({ ...prev, jaimini_antar: period.sign }));
                      
                      // Auto-scroll to selected jaimini antardasha
                      setTimeout(() => {
                        if (scrollRefs.jaimini_maha?.current && jaiminiAntarData?.antar_periods) {
                          const selectedIndex = jaiminiAntarData.antar_periods.findIndex(p => p.sign === period.sign);
                          if (selectedIndex >= 0) {
                            const scrollX = Math.max(0, selectedIndex * 78 - 50);
                            scrollRefs.jaimini_maha.current.scrollTo({ x: scrollX, animated: true });
                          }
                        }
                      }, 100);
                    }}
                  >
                    <Text style={[ 
                      styles.jaiminiAntarSign,
                      isActuallyCurrent && styles.currentJaiminiAntarSign,
                      selectedDashas.jaimini_antar === period.sign && styles.selectedJaiminiText
                    ]}>
                      {t(`signs.${period.sign}`, period.sign)}
                    </Text>
                    <Text style={[ 
                      styles.jaiminiAntarPeriod,
                      isActuallyCurrent && styles.currentJaiminiAntarPeriod,
                      selectedDashas.jaimini_antar === period.sign && styles.selectedJaiminiText
                    ]}>
                      {formatPeriodDuration(period.years)}
                    </Text>
                    <Text style={[ 
                      styles.jaiminiAntarDates,
                      isActuallyCurrent && styles.currentJaiminiAntarDates,
                      selectedDashas.jaimini_antar === period.sign && styles.selectedJaiminiText
                    ]}>
                      {new Date(period.start_date).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})} - {new Date(period.end_date).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})}
                    </Text>
                    {isActuallyCurrent && (
                      <View style={styles.jaiminiAntarProgressBar}>
                        <View style={[styles.jaiminiAntarProgressFill, { width: `${progress}%` }]} />
                      </View>
                    )}
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          </View>
        )}
        

      </React.Fragment>
    );
  };

  const renderKalchakraViewToggle = () => {
    const active = (mode) => kalchakraViewMode === mode;
    return (
      <View style={[styles.kalchakraViewToggle, { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
        <TouchableOpacity
          style={[styles.viewToggleBtn, active('chips') && { backgroundColor: colors.primary }]}
          onPress={() => setKalchakraViewMode('chips')}
        >
          <Text style={[styles.viewToggleText, { color: colors.textSecondary }, active('chips') && { color: '#fff' }]}>{t('dasha.periods')}</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.viewToggleBtn, active('wheel') && { backgroundColor: colors.primary }]}
          onPress={() => setKalchakraViewMode('wheel')}
        >
          <Text style={[styles.viewToggleText, { color: colors.textSecondary }, active('wheel') && { color: '#fff' }]}>{t('dasha.wheel')}</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.viewToggleBtn, active('timeline') && { backgroundColor: colors.primary }]}
          onPress={() => setKalchakraViewMode('timeline')}
        >
          <Text style={[styles.viewToggleText, { color: colors.textSecondary }, active('timeline') && { color: '#fff' }]}>{t('dasha.timeline')}</Text>
        </TouchableOpacity>
      </View>
    );
  };

  const renderKalchakraWheel = () => {
    if (!kalchakraData) {
      return (
        <View style={[styles.wheelContainer, { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
          <Text style={[styles.wheelTitle, { color: colors.text }]}>{t('dasha.loadingWheel')}</Text>
        </View>
      );
    }

    const signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
    const size = 380;
    const center = size / 2;
    const outerRadius = 140;
    const innerRadius = 100;
    
    const getSignNumber = (signName) => {
      return signs.indexOf(signName) + 1;
    };
    
    const sequenceSigns = kalchakraData.wheel_data?.sequence_signs || kalchakraData.sequence_numbers || [];
    const currentSign = kalchakraData.wheel_data?.current_sign || kalchakraData.current_mahadasha?.sign;
    const dehaSign = kalchakraData.deha ? getSignNumber(kalchakraData.deha) : (sequenceSigns[0] || null);
    const jeevaSign = kalchakraData.jeeva ? getSignNumber(kalchakraData.jeeva) : (sequenceSigns[sequenceSigns.length - 1] || null);
    const mahadashas = kalchakraData.mahadashas || [];
    
    // Calculate current age
    const birthDate = new Date(birthData.date);
    const currentAge = Math.floor((new Date() - birthDate) / (365.25 * 24 * 60 * 60 * 1000));
    
    
    // Calculate cumulative ages
    let cumulativeAge = 0;
    mahadashas.forEach((maha, index) => {
      cumulativeAge += Math.round(maha.years);
    });
    const getGatiForSign = (signNumber) => {
      const maha = mahadashas.find(m => m.sign === signNumber);
      return maha?.gati || t('dasha.normal');
    };
    
    const getGatiColor = (gati) => {
      if (gati.includes(t('dasha.manduka'))) return '#ffe0b2';
      if (gati.includes(t('dasha.simhavalokana'))) return '#ffcc80';
      if (gati.includes(t('dasha.markata'))) return '#ffab91';
      if (gati === t('dasha.start')) return '#c8e6c9';
      return '#e1bee7';
    };
    
    const createArcPath = (startAngle, endAngle, radius) => {
      const start = {
        x: center + Math.cos(startAngle) * radius,
        y: center + Math.sin(startAngle) * radius
      };
      const end = {
        x: center + Math.cos(endAngle) * radius,
        y: center + Math.sin(endAngle) * radius
      };
      const largeArcFlag = endAngle - startAngle <= Math.PI ? "0" : "1";
      return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${end.x} ${end.y}`;
    };

    return (
      <View style={[styles.wheelContainer, { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
        <View style={styles.wheelHeader}>
          <Text style={[styles.wheelTitle, { color: colors.primary }]}>{t('dasha.kalchakraWheel')}</Text>
          <Text style={[styles.wheelSubtitle, { color: colors.textSecondary }]}>{tSign(kalchakraData.deha)} → {tSign(kalchakraData.jeeva)} ({kalchakraData.direction})</Text>
        </View>
        
        <Svg width={size} height={size} style={styles.svgWheel}>
          <Defs>
            <LinearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#e1bee7" stopOpacity="0.8" />
              <Stop offset="100%" stopColor="#9c27b0" stopOpacity="0.3" />
            </LinearGradient>
            <LinearGradient id="activeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#9c27b0" stopOpacity="1" />
              <Stop offset="100%" stopColor="#673ab7" stopOpacity="0.8" />
            </LinearGradient>
            <LinearGradient id="centerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <Stop offset="0%" stopColor="#9c27b0" stopOpacity="1" />
              <Stop offset="50%" stopColor="#673ab7" stopOpacity="1" />
              <Stop offset="100%" stopColor="#4a148c" stopOpacity="1" />
            </LinearGradient>
          </Defs>
          
          {/* Outer ring */}
          <Circle cx={center} cy={center} r={outerRadius} fill="none" stroke="#e1bee7" strokeWidth="2" />
          <Circle cx={center} cy={center} r={innerRadius} fill="none" stroke="#e1bee7" strokeWidth="2" />
          
          {/* Sign segments */}
          {signs.map((sign, index) => {
            const signNumber = index + 1;
            const startAngle = ((index * 30) - 90) * (Math.PI / 180);
            const endAngle = (((index + 1) * 30) - 90) * (Math.PI / 180);
            
            const mahaForSign = mahadashas.find(m => m.sign === signNumber);
            const isInSequence = !!mahaForSign;
            const isCurrent = currentSign === signNumber;
            const isDeha = dehaSign === signNumber;
            const isJeeva = jeevaSign === signNumber;
            const gati = getGatiForSign(signNumber);
            const hasSpecialGati = gati !== t('dasha.normal') && gati !== t('dasha.start');
            
            const segmentColor = isCurrent ? '#9c27b0' : 
                               isDeha ? '#ffcdd2' :
                               isJeeva ? '#c8e6c9' :
                               hasSpecialGati ? getGatiColor(gati) :
                               isInSequence ? '#e1bee7' : '#f5f5f5';
            
            // Create segment path
            const outerStart = {
              x: center + Math.cos(startAngle) * outerRadius,
              y: center + Math.sin(startAngle) * outerRadius
            };
            const outerEnd = {
              x: center + Math.cos(endAngle) * outerRadius,
              y: center + Math.sin(endAngle) * outerRadius
            };
            const innerStart = {
              x: center + Math.cos(startAngle) * innerRadius,
              y: center + Math.sin(startAngle) * innerRadius
            };
            const innerEnd = {
              x: center + Math.cos(endAngle) * innerRadius,
              y: center + Math.sin(endAngle) * innerRadius
            };
            
            const segmentPath = `
              M ${outerStart.x} ${outerStart.y}
              A ${outerRadius} ${outerRadius} 0 0 1 ${outerEnd.x} ${outerEnd.y}
              L ${innerEnd.x} ${innerEnd.y}
              A ${innerRadius} ${innerRadius} 0 0 0 ${innerStart.x} ${innerStart.y}
              Z
            `;
            
            return (
              <G key={sign}>
                <Path
                  d={segmentPath}
                  fill={segmentColor}
                  stroke="white"
                  strokeWidth="1"
                  opacity={isInSequence || isDeha || isJeeva ? 1 : 0.2}
                />
                
                {/* Sign text */}
                <SvgText
                  x={center + Math.cos((startAngle + endAngle) / 2) * ((outerRadius + innerRadius) / 2)}
                  y={center + Math.sin((startAngle + endAngle) / 2) * ((outerRadius + innerRadius) / 2) - 8}
                  fontSize="11"
                  fontWeight="600"
                  fill={isCurrent ? 'white' : '#333'}
                  textAnchor="middle"
                  alignmentBaseline="middle"
                >
                  {tSign(sign)}
                </SvgText>
                
                {/* Years inside ring below sign name */}
                {isInSequence && (
                  <SvgText
                    x={center + Math.cos((startAngle + endAngle) / 2) * ((outerRadius + innerRadius) / 2)}
                    y={center + Math.sin((startAngle + endAngle) / 2) * ((outerRadius + innerRadius) / 2) + 8}
                    fontSize="9"
                    fontWeight="600"
                    fill={isCurrent ? 'white' : '#666'}
                    textAnchor="middle"
                    alignmentBaseline="middle"
                  >
                    {(() => {
                      const maha = mahadashas.find(m => m.name === sign);
                      return maha ? `${Math.round(maha.years)}y` : '';
                    })()} 
                  </SvgText>
                )}
                

                

                
                {/* Sequence number */}
                {isInSequence && (
                  <Circle
                    cx={center + Math.cos((startAngle + endAngle) / 2) * (innerRadius - 15)}
                    cy={center + Math.sin((startAngle + endAngle) / 2) * (innerRadius - 15)}
                    r="10"
                    fill="#9c27b0"
                    stroke="white"
                    strokeWidth="2"
                  />
                )}
                {isInSequence && (
                  <SvgText
                    x={center + Math.cos((startAngle + endAngle) / 2) * (innerRadius - 15)}
                    y={center + Math.sin((startAngle + endAngle) / 2) * (innerRadius - 15)}
                    fontSize="10"
                    fontWeight="700"
                    fill="white"
                    textAnchor="middle"
                    alignmentBaseline="middle"
                  >
                    {(() => {
                      const maha = mahadashas.find(m => m.sign === signNumber);
                      const sequenceIndex = mahadashas.findIndex(m => m.sign === signNumber);
                      return sequenceIndex >= 0 ? sequenceIndex + 1 : '';
                    })()} 
                  </SvgText>
                )}
                
                {/* Gati indicator outside circle */}
                {hasSpecialGati && (
                  <SvgText
                    x={center + Math.cos((startAngle + endAngle) / 2) * (outerRadius + 18)}
                    y={center + Math.sin((startAngle + endAngle) / 2) * (outerRadius + 18)}
                    fontSize="12"
                    textAnchor="middle"
                    alignmentBaseline="middle"
                  >
                    {gati.includes(t('dasha.manduka')) ? '🐸' : 
                     gati.includes(t('dasha.simhavalokana')) ? '🦁' : 
                     gati.includes(t('dasha.markata')) ? '🐒' : '⚡'}
                  </SvgText>
                )}
                
                {/* Red S for Deha (starting sign) outside circle */}
                {isDeha && (
                  <SvgText
                    x={center + Math.cos((startAngle + endAngle) / 2) * (outerRadius + 18)}
                    y={center + Math.sin((startAngle + endAngle) / 2) * (outerRadius + 18)}
                    fontSize="12"
                    fontWeight="700"
                    fill="#d32f2f"
                    textAnchor="middle"
                    alignmentBaseline="middle"
                  >
                    S
                  </SvgText>
                )}
                
                {/* Arrow for current period outside circle */}
                {isCurrent && (
                  <SvgText
                    x={center + Math.cos((startAngle + endAngle) / 2) * (outerRadius + 18)}
                    y={center + Math.sin((startAngle + endAngle) / 2) * (outerRadius + 18)}
                    fontSize="10"
                    fill="#ff6f00"
                    textAnchor="middle"
                    alignmentBaseline="middle"
                  >
                    ▶
                  </SvgText>
                )}
              </G>
            );
          })}
          
          {/* Sequence connection lines */}
          {mahadashas.map((maha, index) => {
            if (index === mahadashas.length - 1) return null; // Skip last one
            const currentSignIndex = signs.findIndex(s => s === maha.name) || 0;
            const nextMaha = mahadashas[index + 1];
            const nextSignIndex = signs.findIndex(s => s === nextMaha.name) || 0;
            
            const currentAngle = ((currentSignIndex * 30) + 15 - 90) * (Math.PI / 180);
            const nextAngle = ((nextSignIndex * 30) + 15 - 90) * (Math.PI / 180);
            
            const currentPos = {
              x: center + Math.cos(currentAngle) * (innerRadius - 25),
              y: center + Math.sin(currentAngle) * (innerRadius - 25)
            };
            const nextPos = {
              x: center + Math.cos(nextAngle) * (innerRadius - 25),
              y: center + Math.sin(nextAngle) * (innerRadius - 25)
            };
            
            return (
              <Path
                key={`connection-${index}`}
                d={`M ${currentPos.x} ${currentPos.y} L ${nextPos.x} ${nextPos.y}`}
                stroke="#9c27b0"
                strokeWidth="2"
                strokeDasharray="3,3"
                opacity="0.6"
              />
            );
          })}
          

          
          {/* Current date line */}
          {(() => {
            const currentMaha = mahadashas.find(m => {
              const startDate = new Date(m.start);
              const endDate = new Date(m.end);
              const now = new Date();
              return now >= startDate && now <= endDate;
            });
            
            if (currentMaha) {
              const currentSignIndex = signs.findIndex(s => s === currentMaha.name);
              const startDate = new Date(currentMaha.start);
              const endDate = new Date(currentMaha.end);
              const now = new Date();
              const progress = (now - startDate) / (endDate - startDate);
              
              const signStartAngle = ((currentSignIndex * 30) - 90) * (Math.PI / 180);
              const signEndAngle = (((currentSignIndex + 1) * 30) - 90) * (Math.PI / 180);
              const currentAngle = signStartAngle + (signEndAngle - signStartAngle) * progress;
              
              const innerPoint = {
                x: center + Math.cos(currentAngle) * innerRadius,
                y: center + Math.sin(currentAngle) * innerRadius
              };
              const outerPoint = {
                x: center + Math.cos(currentAngle) * outerRadius,
                y: center + Math.sin(currentAngle) * outerRadius
              };
              
              return (
                <Path
                  d={`M ${innerPoint.x} ${innerPoint.y} L ${outerPoint.x} ${outerPoint.y}`}
                  stroke="#ff6f00"
                  strokeWidth="3"
                  opacity="0.8"
                />
              );
            }
            return null;
          })()}
          

          
          {/* Center circle */}
          <Circle cx={center} cy={center} r="45" fill="url(#centerGradient)" stroke="white" strokeWidth="3" />
          <SvgText
            x={center}
            y={center - 8}
            fontSize="14"
            fontWeight="700"
            fill="white"
            textAnchor="middle"
            alignmentBaseline="middle"
          >
            {kalchakraData.cycle_len}y
          </SvgText>
          <SvgText
            x={center}
            y={center + 8}
            fontSize="10"
            fill="white"
            textAnchor="middle"
            alignmentBaseline="middle"
          >
            {kalchakraData.direction}
          </SvgText>
          

        </Svg>
        
        {/* Legend */}
        <View style={styles.wheelLegend}>
          <View style={styles.legendRow}>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: colors.primary }]} />
              <Text style={[styles.legendText, { color: colors.textSecondary }]}>{t('dasha.current')}</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#ffcdd2' }]} />
              <Text style={[styles.legendText, { color: colors.textSecondary }]}>{t('dasha.deha')}</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#c8e6c9' }]} />
              <Text style={[styles.legendText, { color: colors.textSecondary }]}>{t('dasha.jeeva')}</Text>
            </View>
          </View>
          <View style={styles.legendRow}>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: isDark ? colors.secondary : '#e1bee7' }]} />
              <Text style={[styles.legendText, { color: colors.textSecondary }]}>{t('dasha.sequence')}</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendColor, { backgroundColor: '#ffe0b2' }]} />
              <Text style={[styles.legendText, { color: colors.textSecondary }]}>{t('dasha.gati')}</Text>
            </View>
          </View>
        </View>
      </View>
    );
  };

  const renderKalchakraTimeline = () => {
    if (!kalchakraData) {
      return (
        <View style={[styles.timelineContainer, { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
          <Text style={[styles.timelineTitle, { color: colors.text }]}>{t('dasha.loadingTimeline')}</Text>
        </View>
      );
    }

    const mahadashas = kalchakraData.mahadashas || [];
    const currentDate = new Date();
    const rowBg = (current, deha, jeeva) => {
      if (current) return isDark ? colors.primary : '#e8f5e8';
      if (deha) return isDark ? 'rgba(255,205,210,0.3)' : '#ffebee';
      if (jeeva) return isDark ? 'rgba(232,245,233,0.3)' : '#e3f2fd';
      return isDark ? colors.surface : colors.cardBackground;
    };

    return (
      <View style={[styles.timelineContainer, { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
        <View style={styles.timelineHeader}>
          <Text style={[styles.timelineTitle, { color: colors.primary }]}>{t('dasha.kalchakraTimeline')}</Text>
          <View style={styles.dehaJeevaInfo}>
            <Text style={[styles.dehaJeevaText, { color: colors.primary }]}>🎯 {tSign(kalchakraData.deha)} → {tSign(kalchakraData.jeeva)}</Text>
            <Text style={[styles.cycleInfo, { color: colors.textSecondary }]}>{kalchakraData.cycle_len}y • {kalchakraData.direction}</Text>
          </View>
        </View>
        
        <View style={[styles.timelineTable, { borderColor: colors.cardBorder }]}>
          <View style={[styles.tableHeader, { backgroundColor: isDark ? colors.background : colors.surface }]}>
            <Text style={[styles.headerCell, { color: colors.primary }]}>{t('dasha.sign')}</Text>
            <Text style={[styles.headerCell, { color: colors.primary }]}>{t('dasha.gati')}</Text>
            <Text style={[styles.headerCell, { color: colors.primary }]}>{t('dasha.duration')}</Text>
            <Text style={[styles.headerCell, { color: colors.primary }]}>{t('dasha.period')}</Text>
          </View>
          
          {mahadashas.map((maha, index) => {
            const startDate = new Date(maha.start);
            const endDate = new Date(maha.end);
            const isCurrent = currentDate >= startDate && currentDate <= endDate;
            const isDeha = maha.name === kalchakraData.deha;
            const isJeeva = maha.name === kalchakraData.jeeva;
            
            return (
              <View key={index} style={[styles.tableRow, { backgroundColor: rowBg(isCurrent, isDeha, isJeeva), borderBottomColor: colors.cardBorder }]}>
                <View style={styles.signCell}>
                  <Text style={[styles.signText, { color: colors.text }, isCurrent && { color: isDark ? '#fff' : '#2e7d32', fontWeight: '700' }]}>
                    {tSign(maha.name)}
                  </Text>
                  {isDeha && <Text style={[styles.specialLabel, { color: colors.primary }]}>{t('dasha.deha')}</Text>}
                  {isJeeva && <Text style={[styles.specialLabel, { color: colors.primary }]}>{t('dasha.jeeva')}</Text>}
                </View>
                <View style={styles.gatiCell}>
                  <Text style={[styles.gatiText, { color: isCurrent && isDark ? '#fff' : colors.text }]}>
                    {maha.gati?.includes(t('dasha.manduka')) ? '🐸' :
                     maha.gati?.includes(t('dasha.simhavalokana')) ? '🦁' :
                     maha.gati?.includes(t('dasha.markata')) ? '🐒' : '⚡'}
                  </Text>
                  <Text style={[styles.gatiName, { color: isCurrent && isDark ? 'rgba(255,255,255,0.9)' : colors.textSecondary }]}>
                    {maha.gati ? t(`gati.${maha.gati.replace(' Gati', '')}`, maha.gati.replace(' Gati', '')) : t('dasha.normal')}
                  </Text>
                </View>
                <Text style={[styles.durationCell, { color: isCurrent && isDark ? '#fff' : colors.text }]}>
                  {formatPeriodDuration(maha.years)}
                </Text>
                <Text style={[styles.periodCell, { color: isCurrent && isDark ? 'rgba(255,255,255,0.9)' : colors.textSecondary }]}>
                  {startDate.toLocaleDateString('en-US', {month: 'short', year: '2-digit'})} - {endDate.toLocaleDateString('en-US', {month: 'short', year: '2-digit'})}
                </Text>
              </View>
            );
          })}
        </View>
        
        {mahadashas.length === 0 && (
          <Text style={[styles.timelineEmpty, { color: colors.textSecondary }]}>{t('dasha.noTimelineData')}</Text>
        )}
      </View>
    );
  };

  const renderKalchakraDashaList = () => {
    const mahaOptions = getDashaOptions('kalchakra_maha');
    const antarOptions = getDashaOptions('kalchakra_antar');
    
    return (
      <React.Fragment>
        {renderKalchakraViewToggle()}
        
        {kalchakraViewMode === 'wheel' && renderKalchakraWheel()}
        {kalchakraViewMode === 'timeline' && renderKalchakraTimeline()}
        

        
        {kalchakraViewMode === 'chips' && (
          <React.Fragment>
            <View style={[styles.selectorContainer, { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
              <Text style={[styles.selectorLabel, { color: colors.text }]}>{t('dasha.kalchakraMahadasha')}</Text>
              <ScrollView 
                ref={scrollRefs.kalchakra_maha}
                horizontal 
                showsHorizontalScrollIndicator={false} 
                style={styles.optionsScroll}
              >
                {mahaOptions.length === 0 ? (
                  <View style={[styles.optionCard, styles.disabledOption, { backgroundColor: isDark ? colors.background : colors.surface, borderColor: colors.cardBorder }]}>
                    <Text style={[styles.disabledOptionText, { color: colors.textSecondary }]}>{t('dasha.noPeriods')}</Text>
                  </View>
                ) : (
                  mahaOptions.map((period, index) => {
                    const isSelected = selectedDashas.kalchakra_maha === period.name;
                    const currentDate = new Date();
                    const startDate = new Date(period.start);
                    const endDate = new Date(period.end);
                    const isActuallyCurrent = currentDate >= startDate && currentDate <= endDate;
                    const progress = calculateProgress(period.start, period.end);
                    const cardBg = isActuallyCurrent && !isSelected ? colors.accent : isSelected ? colors.primary : (isDark ? colors.background : colors.surface);
                    const cardBorder = isActuallyCurrent && !isSelected ? colors.accent : isSelected ? colors.primary : colors.cardBorder;
                    const textColor = (isSelected || isActuallyCurrent) ? '#fff' : colors.text;
                    const subColor = (isSelected || isActuallyCurrent) ? '#fff' : colors.textSecondary;
                    return (
                      <TouchableOpacity
                        key={`${period.name}-${index}`}
                        style={[styles.kalchakraCard, { backgroundColor: cardBg, borderColor: cardBorder }]}
                        onPress={() => handleKalchakraMahaSelection(period.name)}
                      >
                        <Text style={[styles.kalchakraPlanet, { color: textColor }]}>{tSign(period.name)}</Text>
                        <Text style={[styles.kalchakraPeriod, { color: subColor }]}>{formatPeriodDuration(period.years)}</Text>
                        <Text style={[styles.kalchakraSequence, { color: subColor }]}>{period.gati}</Text>
                        <Text style={[styles.kalchakraDates, { color: subColor }]}>
                          {new Date(period.start).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})} - {new Date(period.end).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})}
                        </Text>
                        {isActuallyCurrent && (
                          <View style={[styles.kalchakraProgressBar, { backgroundColor: isDark ? 'rgba(255,255,255,0.3)' : 'rgba(255,255,255,0.3)' }]}>
                            <View style={[styles.kalchakraProgressFill, { width: `${progress}%`, backgroundColor: colors.accent }]} />
                          </View>
                        )}
                      </TouchableOpacity>
                    );
                  })
                )}
              </ScrollView>
            </View>
            
            {selectedDashas.kalchakra_maha && antarOptions.length > 0 && (
              <View style={[styles.selectorContainer, { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
                <Text style={[styles.selectorLabel, { color: colors.text }]}>{t('dasha.kalchakraAntardasha')} ({tSign(selectedDashas.kalchakra_maha)})</Text>
                <ScrollView 
                  ref={scrollRefs.kalchakra_antar}
                  horizontal 
                  showsHorizontalScrollIndicator={false} 
                  style={styles.optionsScroll}
                >
                  {antarOptions.map((period, index) => {
                    const isSelected = selectedDashas.kalchakra_antar === period.name;
                    const isActuallyCurrent = period.current;
                    const progress = calculateProgress(period.start, period.end);
                    const antarBg = isActuallyCurrent && !isSelected ? colors.accent : isSelected ? colors.success : (isDark ? colors.background : colors.surface);
                    const antarBorder = isActuallyCurrent && !isSelected ? colors.accent : isSelected ? colors.success : colors.cardBorder;
                    const antarText = (isSelected || isActuallyCurrent) ? '#fff' : colors.text;
                    const antarSub = (isSelected || isActuallyCurrent) ? '#fff' : colors.textSecondary;
                    return (
                      <TouchableOpacity
                        key={`antar-${period.name}-${index}`}
                        style={[styles.kalchakraAntarCard, { backgroundColor: antarBg, borderColor: antarBorder }]}
                        onPress={() => {
                          setSelectedDashas(prev => ({ ...prev, kalchakra_antar: period.name }));
                          setTimeout(() => {
                            if (scrollRefs.kalchakra_antar?.current && antarOptions) {
                              const selectedIndex = antarOptions.findIndex(d => d.name === period.name);
                              if (selectedIndex >= 0) {
                                const scrollX = Math.max(0, selectedIndex * 78 - 50);
                                scrollRefs.kalchakra_antar.current.scrollTo({ x: scrollX, animated: true });
                              }
                            }
                          }, 100);
                        }}
                      >
                        <Text style={[styles.kalchakraAntarPlanet, { color: antarText }]}>{tSign(period.name)}</Text>
                        <Text style={[styles.kalchakraAntarPeriod, { color: antarSub }]}>{formatPeriodDuration(period.years)}</Text>
                        <Text style={[styles.kalchakraAntarDates, { color: antarSub }]}>
                          {new Date(period.start).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})} - {new Date(period.end).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})}
                        </Text>
                        {isActuallyCurrent && (
                          <View style={[styles.kalchakraAntarProgressBar, { backgroundColor: 'rgba(255,255,255,0.3)' }]}>
                            <View style={[styles.kalchakraAntarProgressFill, { width: `${progress}%`, backgroundColor: colors.accent }]} />
                          </View>
                        )}
                      </TouchableOpacity>
                    );
                  })}
                </ScrollView>
              </View>
            )}
          </React.Fragment>
        )}
      </React.Fragment>
    );
  };
  
  const renderSystemInfoModal = () => (
    <Modal visible={showSystemInfo} animationType="slide" transparent>
      <View style={[styles.modalOverlay, { backgroundColor: 'rgba(0,0,0,0.6)' }]}>
        <View style={[styles.systemInfoModal, { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
          <View style={[styles.systemInfoHeader, { borderBottomColor: colors.cardBorder }]}>
            <Text style={[styles.systemInfoTitle, { color: colors.primary }]}>{t('dasha.bphsKalchakraDasha')}</Text>
            <TouchableOpacity onPress={() => setShowSystemInfo(false)}>
              <Text style={[styles.modalCloseIcon, { color: colors.text }]}>✕</Text>
            </TouchableOpacity>
          </View>
          
          {kalchakraSystemInfo && (
            <ScrollView style={styles.systemInfoContent}>
              <Text style={[styles.systemInfoSubtitle, { color: colors.text }]}>{kalchakraSystemInfo.system_name}</Text>
              <Text style={[styles.systemInfoDescription, { color: colors.textSecondary }]}>{kalchakraSystemInfo.specialty}</Text>
              
              <View style={styles.systemInfoSection}>
                <Text style={[styles.systemInfoSectionTitle, { color: colors.primary }]}>{t('dasha.source')}</Text>
                <Text style={[styles.systemInfoText, { color: colors.textSecondary }]}>{kalchakraSystemInfo.source}</Text>
              </View>
              
              <View style={styles.systemInfoSection}>
                <Text style={[styles.systemInfoSectionTitle, { color: colors.primary }]}>{t('dasha.keyFeatures')}</Text>
                <Text style={[styles.systemInfoText, { color: colors.textSecondary }]}>• {kalchakraSystemInfo.total_combinations} nakshatra-pada combinations</Text>
                <Text style={[styles.systemInfoText, { color: colors.textSecondary }]}>• {kalchakraSystemInfo.cycle_length_years}-year complete cycle</Text>
                <Text style={[styles.systemInfoText, { color: colors.textSecondary }]}>• {kalchakraSystemInfo.based_on}</Text>
                <Text style={[styles.systemInfoText, { color: colors.textSecondary }]}>• {kalchakraSystemInfo.timing_method}</Text>
              </View>
              
              <View style={styles.systemInfoSection}>
                <Text style={[styles.systemInfoSectionTitle, { color: colors.primary }]}>{t('dasha.authenticity')}</Text>
                <Text style={[styles.systemInfoText, { color: colors.textSecondary }]}>{kalchakraSystemInfo.authenticity}</Text>
              </View>
            </ScrollView>
          )}
        </View>
      </View>
    </Modal>
  );

  const renderDashaSelector = (dashaLevel, title) => {
    const options = getDashaOptions(dashaLevel);
    const selectedValue = selectedDashas[dashaLevel];
    const vimTheme = dashaType === 'vimshottari';

    return (
      <View style={[styles.selectorContainer, vimTheme && { backgroundColor: isDark ? colors.surface : colors.cardBackground }]}>
        <Text style={[styles.selectorLabel, vimTheme && { color: colors.text }]}>{title}</Text>
        <ScrollView ref={scrollRefs[dashaLevel]} horizontal showsHorizontalScrollIndicator={false} style={styles.optionsScroll}>
          {options.length === 0 ? (
            <View style={[styles.optionCard, styles.disabledOption, vimTheme && { backgroundColor: isDark ? colors.background : colors.surface, borderColor: colors.cardBorder }]}>
              <Text style={[styles.disabledOptionText, vimTheme && { color: colors.textSecondary }]}>{t('dasha.noOptions')}</Text>
            </View>
          ) : (
            options.map((dasha, index) => {
              const isSelected = selectedValue === dasha.planet;
              const currentDate = transitDate;
              const startDate = new Date(dasha.start);
              const endDate = new Date(dasha.end);
              const isActuallyCurrent = currentDate >= startDate && currentDate <= endDate;

              return (
                <TouchableOpacity
                  key={`${dasha.planet}-${index}`}
                  style={[
                    styles.optionCard,
                    vimTheme && { backgroundColor: isDark ? colors.background : colors.surface, borderColor: colors.cardBorder },
                    isSelected && (vimTheme ? { backgroundColor: colors.primary, borderColor: colors.primary } : styles.selectedOptionCard),
                    isActuallyCurrent && !isSelected && (vimTheme ? { backgroundColor: colors.accent, borderColor: colors.accent } : styles.currentOptionCard)
                  ]}
                  onPress={() => {
                    handleDashaSelection(dashaLevel, dasha.planet);
                  }}
                >
                  <Text style={[
                    styles.optionPlanet,
                    vimTheme && !isSelected && !isActuallyCurrent && { color: colors.text },
                    isSelected && (vimTheme ? { color: '#fff' } : styles.selectedOptionPlanet),
                    isActuallyCurrent && !isSelected && (vimTheme ? { color: '#fff' } : styles.currentOptionPlanet)
                  ]}>
                    {t(`planets.${dasha.planet}`, dasha.planet)}
                  </Text>
                  <Text style={[
                    styles.optionPeriod,
                    vimTheme && !isSelected && !isActuallyCurrent && { color: colors.text },
                    isSelected && (vimTheme ? { color: '#fff' } : styles.selectedOptionPeriod),
                    isActuallyCurrent && !isSelected && (vimTheme ? { color: '#fff' } : styles.currentOptionPeriod)
                  ]}>
                    {formatPeriodDuration(dasha.years)}
                  </Text>
                  <Text style={[
                    styles.optionDates,
                    vimTheme && !isSelected && !isActuallyCurrent && { color: colors.textSecondary },
                    isSelected && (vimTheme ? { color: '#fff' } : styles.selectedOptionDates),
                    isActuallyCurrent && !isSelected && (vimTheme ? { color: '#fff' } : styles.currentOptionDates)
                  ]}>
                    {new Date(dasha.start).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})} - {new Date(dasha.end).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})}
                  </Text>
                </TouchableOpacity>
              );
            })
          )}
        </ScrollView>
      </View>
    );
  };

  // No birth data: show empty state instead of loader
  if (visible && (!birthData || !birthData.name)) {
    return (
      <Modal visible={visible} animationType="slide" presentationStyle="fullScreen">
        <View style={{ flex: 1, backgroundColor: colors.background, paddingTop: insets.top }}>
          <StatusBar barStyle={colors.statusBarStyle} />
          <View style={[styles.header, { backgroundColor: colors.surface, borderBottomColor: colors.cardBorder }]}>
            <TouchableOpacity onPress={onClose} style={[styles.closeButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.15)' : colors.surface }]}>
              <Text style={[styles.closeIcon, { color: colors.text }]}>✕</Text>
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>{t('dasha.browserTitle')}</Text>
            <View style={styles.placeholder} />
          </View>
          <View style={[styles.loadingContainer, { justifyContent: 'center', paddingHorizontal: 24 }]}>
            <Text style={[styles.loadingText, { color: colors.text, textAlign: 'center', marginBottom: 8 }]}>
              {t('dasha.birthDataRequired', 'Birth data is required to view dashas.')}
            </Text>
            <Text style={[styles.loadingText, { color: colors.textSecondary, textAlign: 'center', fontSize: 14, marginBottom: 24 }]}>
              {t('dasha.addBirthProfileHint', 'Add your birth profile from the home screen to continue.')}
            </Text>
            {onRequireBirthData ? (
              <TouchableOpacity
                onPress={() => { onRequireBirthData(); onClose(); }}
                style={[styles.retryButton, { backgroundColor: colors.primary, alignSelf: 'center', paddingHorizontal: 24 }]}
              >
                <Text style={[styles.retryText, { color: '#fff' }]}>{t('birthProfileIntro.emptyStateCta', 'Add birth profile')}</Text>
              </TouchableOpacity>
            ) : null}
            <TouchableOpacity
              onPress={onClose}
              style={{ marginTop: 16, paddingVertical: 12, paddingHorizontal: 24, alignSelf: 'center' }}
            >
              <Text style={{ color: colors.textSecondary, fontWeight: '600' }}>{t('common.close', 'Close')}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    );
  }

  if (loading) {
    return (
      <Modal visible={visible} animationType="slide" presentationStyle="fullScreen">
        <View style={{ flex: 1, backgroundColor: colors.background, paddingTop: insets.top }}>
          <StatusBar barStyle={colors.statusBarStyle} />
          <View style={[styles.header, { backgroundColor: colors.surface, borderBottomColor: colors.cardBorder }]}>
            <TouchableOpacity onPress={onClose} style={[styles.closeButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.15)' : colors.surface }]}>
              <Text style={[styles.closeIcon, { color: colors.text }]}>✕</Text>
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>{t('dasha.browserTitle')}</Text>
            <View style={styles.placeholder} />
          </View>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={[styles.loadingText, { color: colors.textSecondary }]}>{t('dasha.loading')}</Text>
          </View>
        </View>
      </Modal>
    );
  }

  if (error) {
    return (
      <Modal visible={visible} animationType="slide" presentationStyle="fullScreen">
        <View style={{ flex: 1, backgroundColor: colors.background, paddingTop: insets.top }}>
          <StatusBar barStyle={colors.statusBarStyle} />
          <View style={[styles.header, { backgroundColor: colors.surface, borderBottomColor: colors.cardBorder }]}>
            <TouchableOpacity onPress={onClose} style={[styles.closeButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.15)' : colors.surface }]}>
              <Text style={[styles.closeIcon, { color: colors.text }]}>✕</Text>
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>{t('dasha.browserTitle')}</Text>
            <View style={styles.placeholder} />
          </View>
          <View style={styles.errorContainer}>
            <Text style={[styles.errorText, { color: colors.error }]}>{error}</Text>
            <TouchableOpacity style={[styles.retryButton, { backgroundColor: colors.primary }]} onPress={fetchCascadingDashas}>
              <Text style={[styles.retryText, { color: '#fff' }]}>{t('common.retry')}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    );
  }

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="fullScreen">
      <View style={{ flex: 1, backgroundColor: colors.background, paddingTop: insets.top }}>
        <StatusBar barStyle={colors.statusBarStyle} />
        <View style={[styles.header, { backgroundColor: colors.surface, borderBottomColor: colors.cardBorder }]}>
          <TouchableOpacity onPress={onClose} style={[styles.closeButton, { backgroundColor: isDark ? 'rgba(255,255,255,0.15)' : colors.surface }]}>
            <Text style={[styles.closeIcon, { color: colors.text }]}>✕</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: colors.text }]}>{t('dasha.browserFor', { name: birthData?.name || t('common.user') })}</Text>
          <View style={styles.placeholder} />
        </View>
        
        <ScrollView style={[styles.content, { backgroundColor: colors.background }]}>
          {renderDashaTypeSelector()}
          {dashaType === 'vimshottari' && renderDateNavigation()}
          {renderBreadcrumb()}
          
          <View style={styles.selectorsContainer}>
            {dashaType === 'vimshottari' ? (
              <React.Fragment>
                {renderDashaSelector('maha', t('dasha.mahaDasha'))}
                {renderDashaSelector('antar', t('dasha.antarDasha'))}
                {renderDashaSelector('pratyantar', t('dasha.pratyantarDasha'))}
                {renderDashaSelector('sookshma', t('dasha.sookshmaDasha'))}
                {renderDashaSelector('prana', t('dasha.pranaDasha'))}
              </React.Fragment>
            ) : dashaType === 'kalchakra' ? (
              <React.Fragment>
                {renderKalchakraDashaList()}
              </React.Fragment>
            ) : dashaType === 'yogini' ? (
              <YoginiDashaTab data={yoginiData} />
            ) : dashaType === 'chara' ? (
              <CharaDashaTab birthData={birthData} />
            ) : null}
          </View>
        </ScrollView>
        
        {renderSystemInfoModal()}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    paddingTop: Platform.OS === 'ios' ? 0 : 0,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  closeButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: COLORS.lightGray,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  placeholder: {
    width: 40,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  dateNav: {
    marginBottom: 12,
  },
  compactNavRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  navButtonGroup: {
    flexDirection: 'row',
    gap: 4,
  },
  compactNavButton: {
    paddingHorizontal: 6,
    paddingVertical: 4,
    backgroundColor: COLORS.lightGray,
    borderRadius: 6,
    minWidth: 28,
  },
  compactNavText: {
    color: COLORS.accent,
    fontSize: 9,
    fontWeight: '600',
    textAlign: 'center',
  },
  compactDateButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    minWidth: 80,
    height: 32,
    justifyContent: 'center',
  },
  compactDateText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.white,
    textAlign: 'center',
  },
  compactCalendarButton: {
    padding: 8,
    backgroundColor: COLORS.accent,
    borderRadius: 8,
    height: 32,
    width: 32,
    justifyContent: 'center',
    alignItems: 'center',
  },

  breadcrumb: {
    padding: 10,
    backgroundColor: COLORS.lightGray,
    borderRadius: 8,
    marginBottom: 8,
  },
  breadcrumbText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  breadcrumbScroll: {
    flexDirection: 'row',
  },
  breadcrumbRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  breadcrumbCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 6,
    padding: 8,
    marginRight: 8,
    minWidth: 70,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  breadcrumbPlanet: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.accent,
    textAlign: 'center',
  },
  breadcrumbPeriod: {
    fontSize: 11,
    color: COLORS.textPrimary,
    textAlign: 'center',
    marginTop: 2,
  },
  breadcrumbDates: {
    fontSize: 9,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 1,
  },
  breadcrumbArrow: {
    fontSize: 16,
    color: COLORS.textSecondary,
    marginHorizontal: 4,
  },
  selectorsContainer: {
    gap: 8,
  },
  selectorContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 8,
    padding: 12,
  },
  selectorLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 6,
  },
  optionsScroll: {
    flexDirection: 'row',
  },
  optionCard: {
    backgroundColor: COLORS.lightGray,
    borderRadius: 6,
    padding: 6,
    marginRight: 6,
    minWidth: 75,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  selectedOptionCard: {
    backgroundColor: COLORS.accent,
    borderColor: COLORS.accent,
  },
  disabledOption: {
    opacity: 0.5,
    backgroundColor: COLORS.lightGray,
  },
  optionPlanet: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
    textAlign: 'center',
  },
  selectedOptionPlanet: {
    color: COLORS.white,
  },
  optionPeriod: {
    fontSize: 9,
    color: COLORS.textPrimary,
    textAlign: 'center',
    marginTop: 1,
  },
  selectedOptionPeriod: {
    color: COLORS.white,
  },
  optionDates: {
    fontSize: 7,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 1,
    lineHeight: 9,
  },
  selectedOptionDates: {
    color: COLORS.white,
  },
  currentOptionCard: {
    backgroundColor: '#ff6f00',
    borderColor: '#ff6f00',
  },
  currentOptionPlanet: {
    color: COLORS.white,
  },
  currentOptionPeriod: {
    color: COLORS.white,
  },
  currentOptionDates: {
    color: COLORS.white,
  },
  disabledOptionText: {
    color: COLORS.textSecondary,
    fontSize: 12,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: COLORS.textSecondary,
    marginTop: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  errorText: {
    fontSize: 16,
    color: COLORS.error,
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: COLORS.accent,
    borderRadius: 8,
  },
  retryText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  doneButton: {
    backgroundColor: COLORS.accent,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    alignSelf: 'center',
    marginTop: 10,
  },
  doneButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  closeIcon: {
    fontSize: 20,
    color: COLORS.textPrimary,
  },
  calendarIcon: {
    fontSize: 16,
  },
  dashaTypeSelector: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 4,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  tabScrollView: {
    flexDirection: 'row',
  },
  dashaTypeTab: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginRight: 8,
  },
  tabContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  activeDashaTypeTab: {
    backgroundColor: COLORS.accent,
  },
  dashaTypeTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  activeDashaTypeTabText: {
    color: COLORS.white,
  },
  kalchakraOptionCard: {
    backgroundColor: '#f3e5f5',
    borderColor: '#9c27b0',
  },
  selectedKalchakraCard: {
    backgroundColor: '#9c27b0',
    borderColor: '#9c27b0',
  },
  currentKalchakraCard: {
    backgroundColor: '#673ab7',
    borderColor: '#673ab7',
  },
  kalchakraSequence: {
    fontSize: 8,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 1,
    fontWeight: '600',
  },
  selectedKalchakraSequence: {
    color: COLORS.white,
  },
  currentKalchakraSequence: {
    color: COLORS.white,
  },
  kalchakraCycle: {
    fontSize: 8,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 1,
    fontWeight: '600',
  },
  kalchakraViewToggle: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    borderRadius: 8,
    padding: 4,
    marginBottom: 12,
  },
  viewToggleBtn: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  activeViewToggle: {
    backgroundColor: '#9c27b0',
  },
  viewToggleText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  activeViewToggleText: {
    color: COLORS.white,
  },
  wheelContainer: {
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 4,
    paddingBottom: 8,
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    marginBottom: 12,
  },
  wheelHeader: {
    alignItems: 'center',
    marginBottom: 10,
  },
  wheelTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#9c27b0',
  },
  wheelSubtitle: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  svgWheel: {
    alignSelf: 'center',
    marginVertical: 4,
  },
  wheelLegend: {
    marginTop: 4,
    alignItems: 'center',
  },
  legendRow: {
    flexDirection: 'row',
    gap: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendText: {
    fontSize: 10,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  legendEmoji: {
    fontSize: 12,
  },
  timelineContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  timelineHeader: {
    marginBottom: 16,
  },
  timelineTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#9c27b0',
    marginBottom: 8,
  },
  dehaJeevaInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dehaJeevaText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#673ab7',
  },
  cycleInfo: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  timelineTable: {
    borderRadius: 8,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: '#f3e5f5',
    paddingVertical: 8,
  },
  headerCell: {
    flex: 1,
    fontSize: 11,
    fontWeight: '700',
    color: '#9c27b0',
    textAlign: 'center',
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    backgroundColor: COLORS.surface,
  },
  currentRow: {
    backgroundColor: '#e8f5e8',
  },
  dehaRow: {
    backgroundColor: '#ffebee',
  },
  jeevaRow: {
    backgroundColor: '#e3f2fd',
  },
  signCell: {
    flex: 1,
    alignItems: 'center',
  },
  signText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  specialLabel: {
    fontSize: 8,
    fontWeight: '700',
    color: '#9c27b0',
    marginTop: 2,
  },
  gatiCell: {
    flex: 1,
    alignItems: 'center',
  },
  gatiText: {
    fontSize: 14,
  },
  gatiName: {
    fontSize: 9,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  durationCell: {
    flex: 1,
    fontSize: 11,
    color: COLORS.textPrimary,
    textAlign: 'center',
    fontWeight: '600',
  },
  periodCell: {
    flex: 1,
    fontSize: 10,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  currentText: {
    color: '#2e7d32',
    fontWeight: '700',
  },
  timelineItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  timelineGati: {
    fontSize: 12,
    fontWeight: '600',
    color: '#673ab7',
  },
  timelineTransition: {
    fontSize: 12,
    color: COLORS.textPrimary,
  },
  debugContainer: {
    backgroundColor: '#ffebee',
    padding: 10,
    borderRadius: 8,
    marginTop: 10,
  },
  debugText: {
    fontSize: 12,
    color: '#d32f2f',
  },
  timelineEmpty: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    fontStyle: 'italic',
    marginTop: 20,
  },

  gatiLegend: {
    marginTop: 16,
    alignItems: 'center',
  },
  gatiLegendTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  gatiLegendRow: {
    flexDirection: 'row',
    gap: 12,
  },
  gatiLegendItem: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  sequenceFlow: {
    marginTop: 16,
    marginBottom: 8,
  },
  sequenceTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 8,
    textAlign: 'center',
  },
  sequenceChain: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
  },
  sequenceItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sequenceSign: {
    backgroundColor: '#e1bee7',
    borderRadius: 6,
    padding: 6,
    alignItems: 'center',
    minWidth: 40,
    borderWidth: 1,
    borderColor: '#9c27b0',
  },
  sequenceSignSpecial: {
    backgroundColor: '#ffcc02',
    borderColor: '#ff6f00',
  },
  sequenceSignText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#9c27b0',
  },
  sequenceGatiText: {
    fontSize: 12,
    marginTop: 2,
  },
  sequenceArrow: {
    fontSize: 16,
    color: '#9c27b0',
    marginHorizontal: 4,
  },
  infoButton: {
    padding: 2,
  },
  infoIcon: {
    fontSize: 16,
    color: COLORS.white,
  },
  currentStatusCard: {
    backgroundColor: '#f3e5f5',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#9c27b0',
  },
  currentStatusTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#9c27b0',
    marginBottom: 8,
    textAlign: 'center',
  },
  compactPeriodRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  periodColumn: {
    alignItems: 'center',
    flex: 1,
  },
  systemColumn: {
    alignItems: 'flex-end',
    flex: 1,
  },
  periodLabel: {
    fontSize: 10,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  periodName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#9c27b0',
    marginTop: 2,
  },
  periodGati: {
    fontSize: 9,
    color: COLORS.textSecondary,
    marginTop: 1,
  },
  periodProgress: {
    fontSize: 9,
    color: '#673ab7',
    fontWeight: '600',
    marginTop: 2,
  },
  systemLabel: {
    fontSize: 9,
    color: COLORS.textSecondary,
    textAlign: 'right',
    marginBottom: 1,
  },
  compactProgressBar: {
    position: 'relative',
    height: 16,
    backgroundColor: '#e1bee7',
    borderRadius: 8,
    justifyContent: 'center',
  },
  compactProgressFill: {
    position: 'absolute',
    left: 0,
    top: 0,
    height: '100%',
    backgroundColor: '#9c27b0',
    borderRadius: 8,
  },
  compactProgressText: {
    fontSize: 10,
    color: COLORS.white,
    fontWeight: '600',
    textAlign: 'center',
    zIndex: 1,
  },
  kalchakraCard: {
    backgroundColor: '#f3e5f5',
    borderRadius: 8,
    padding: 10,
    marginRight: 8,
    minWidth: 90,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#9c27b0',
    position: 'relative',
  },
  selectedKalchakraCard: {
    backgroundColor: '#9c27b0',
    borderColor: '#9c27b0',
  },
  currentKalchakraCard: {
    backgroundColor: '#673ab7',
    borderColor: '#673ab7',
  },
  kalchakraPlanet: {
    fontSize: 14,
    fontWeight: '700',
    color: '#9c27b0',
    textAlign: 'center',
  },
  selectedKalchakraPlanet: {
    color: COLORS.white,
  },
  currentKalchakraPlanet: {
    color: COLORS.white,
  },
  kalchakraPeriod: {
    fontSize: 11,
    color: '#9c27b0',
    textAlign: 'center',
    marginTop: 2,
    fontWeight: '600',
  },
  selectedKalchakraPeriod: {
    color: COLORS.white,
  },
  currentKalchakraPeriod: {
    color: COLORS.white,
  },
  kalchakraDates: {
    fontSize: 9,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 2,
    lineHeight: 11,
  },
  selectedKalchakraDates: {
    color: COLORS.white,
  },
  currentKalchakraDates: {
    color: COLORS.white,
  },
  kalchakraProgressBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 3,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
  },
  kalchakraProgressFill: {
    height: '100%',
    backgroundColor: '#ff6f00',
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
  },
  kalchakraAntarCard: {
    backgroundColor: '#e8f5e8',
    borderRadius: 6,
    padding: 8,
    marginRight: 6,
    minWidth: 70,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#4caf50',
    position: 'relative',
  },
  selectedKalchakraAntarCard: {
    backgroundColor: '#4caf50',
    borderColor: '#4caf50',
  },
  currentKalchakraAntarCard: {
    backgroundColor: '#388e3c',
    borderColor: '#388e3c',
  },
  kalchakraAntarPlanet: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4caf50',
    textAlign: 'center',
  },
  selectedKalchakraAntarPlanet: {
    color: COLORS.white,
  },
  currentKalchakraAntarPlanet: {
    color: COLORS.white,
  },
  kalchakraAntarPeriod: {
    fontSize: 9,
    color: '#4caf50',
    textAlign: 'center',
    marginTop: 1,
    fontWeight: '600',
  },
  selectedKalchakraAntarPeriod: {
    color: COLORS.white,
  },
  currentKalchakraAntarPeriod: {
    color: COLORS.white,
  },
  kalchakraAntarDates: {
    fontSize: 8,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 1,
  },
  selectedKalchakraAntarDates: {
    color: COLORS.white,
  },
  currentKalchakraAntarDates: {
    color: COLORS.white,
  },
  kalchakraAntarProgressBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 2,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderBottomLeftRadius: 6,
    borderBottomRightRadius: 6,
  },
  kalchakraAntarProgressFill: {
    height: '100%',
    backgroundColor: '#ff6f00',
    borderBottomLeftRadius: 6,
    borderBottomRightRadius: 6,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  systemInfoModal: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    maxHeight: '80%',
    width: '100%',
    maxWidth: 400,
  },
  systemInfoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  systemInfoTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#9c27b0',
  },
  modalCloseIcon: {
    fontSize: 18,
    color: COLORS.textSecondary,
    padding: 4,
  },
  systemInfoContent: {
    padding: 20,
  },
  systemInfoSubtitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  systemInfoDescription: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 16,
    lineHeight: 20,
  },
  systemInfoSection: {
    marginBottom: 16,
  },
  systemInfoSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#9c27b0',
    marginBottom: 8,
  },

  jaiminiInfoCard: {
    backgroundColor: '#e8f5e8',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#4caf50',
  },
  jaiminiInfoTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#2e7d32',
    marginBottom: 8,
    textAlign: 'center',
  },
  jaiminiInfoText: {
    fontSize: 12,
    color: '#388e3c',
    textAlign: 'center',
    marginBottom: 4,
  },
  reversalInfo: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#a5d6a7',
  },
  reversalTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#d32f2f',
    marginBottom: 4,
  },
  reversalText: {
    fontSize: 10,
    color: '#d32f2f',
    marginBottom: 2,
  },
  jumpInfo: {
    marginTop: 6,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#a5d6a7',
  },
  jumpTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#e65100',
    marginBottom: 4,
  },
  jumpText: {
    fontSize: 10,
    color: '#bf360c',
    marginBottom: 2,
  },
  predictionInfo: {
    marginTop: 6,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: '#a5d6a7',
  },
  predictionTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#1976d2',
    marginBottom: 4,
  },
  predictionText: {
    fontSize: 10,
    color: '#1976d2',
    marginBottom: 2,
  },
  predictionCardsSection: {
    marginTop: 16,
    marginBottom: 16,
  },
  predictionSectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 12,
    textAlign: 'center',
  },
  cardsContainer: {
    marginTop: 8,
  },
  statusCard: {
    backgroundColor: '#e3f2fd',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#2196f3',
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1976d2',
    marginBottom: 8,
    textAlign: 'center',
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusSign: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1976d2',
  },
  statusScore: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1976d2',
  },
  progressBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#bbdefb',
    borderRadius: 4,
    marginRight: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#2196f3',
    borderRadius: 4,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#1976d2',
    minWidth: 35,
  },
  timeRemaining: {
    fontSize: 12,
    color: '#424242',
    textAlign: 'center',
    marginBottom: 4,
  },
  chakraInfo: {
    fontSize: 11,
    color: '#757575',
    textAlign: 'center',
  },
  focusCard: {
    backgroundColor: '#f3e5f5',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#9c27b0',
  },
  focusTheme: {
    fontSize: 13,
    color: '#424242',
    marginBottom: 8,
    lineHeight: 18,
  },
  energyStyle: {
    fontSize: 12,
    color: '#7b1fa2',
    marginBottom: 6,
    fontWeight: '600',
  },
  keyAreas: {
    fontSize: 12,
    color: '#7b1fa2',
    marginBottom: 8,
    fontWeight: '600',
  },
  keywordsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  keywordTag: {
    backgroundColor: '#e1bee7',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  keywordText: {
    fontSize: 10,
    color: '#4a148c',
    fontWeight: '600',
  },
  timelineCard: {
    backgroundColor: '#fff3e0',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#ff9800',
  },
  currentPeriodInfo: {
    marginBottom: 12,
  },
  currentPeriodName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#e65100',
    textAlign: 'center',
  },
  currentPeriodDates: {
    fontSize: 11,
    color: '#bf360c',
    textAlign: 'center',
    marginTop: 4,
  },
  nextEventsContainer: {
    borderTopWidth: 1,
    borderTopColor: '#ffcc02',
    paddingTop: 8,
  },
  nextEventsTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#e65100',
    marginBottom: 6,
  },
  nextEventText: {
    fontSize: 11,
    color: '#424242',
    marginBottom: 2,
  },
  predictionsCard: {
    backgroundColor: '#e8f5e8',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#4caf50',
  },
  predictionSection: {
    marginBottom: 10,
  },
  predictionSectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2e7d32',
    marginBottom: 4,
  },
  predictionText: {
    fontSize: 11,
    color: '#424242',
    marginBottom: 2,
    lineHeight: 15,
  },
  strengthCard: {
    backgroundColor: '#fce4ec',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e91e63',
  },
  strengthComparison: {
    marginBottom: 12,
  },
  strengthItem: {
    marginBottom: 8,
  },
  strengthLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#ad1457',
    marginBottom: 4,
  },
  strengthBar: {
    height: 6,
    backgroundColor: '#f8bbd9',
    borderRadius: 3,
    marginBottom: 4,
  },
  strengthFill: {
    height: '100%',
    backgroundColor: '#e91e63',
    borderRadius: 3,
  },
  strengthValue: {
    fontSize: 10,
    color: '#ad1457',
    fontWeight: '600',
  },
  guidanceContainer: {
    borderRadius: 8,
    padding: 10,
  },
  guidanceText: {
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
    lineHeight: 16,
  },
  jaiminiCard: {
    borderRadius: 8,
    padding: 10,
    marginRight: 8,
    minWidth: 90,
    alignItems: 'center',
    borderWidth: 1,
    position: 'relative',
  },
  jaiminiChakra1Card: {
    backgroundColor: '#e8f5e8',
    borderColor: '#4caf50',
  },
  jaiminiChakra2Card: {
    backgroundColor: '#fff3e0',
    borderColor: '#ff9800',
  },
  currentJaiminiCard: {
    backgroundColor: '#1976d2',
    borderColor: '#1976d2',
  },
  jaiminiSign: {
    fontSize: 14,
    fontWeight: '700',
    textAlign: 'center',
  },
  currentJaiminiSign: {
    color: COLORS.white,
  },
  jaiminiPeriod: {
    fontSize: 11,
    textAlign: 'center',
    marginTop: 2,
    fontWeight: '600',
  },
  currentJaiminiPeriod: {
    color: COLORS.white,
  },
  jaiminiChakra: {
    fontSize: 9,
    textAlign: 'center',
    marginTop: 1,
    fontWeight: '600',
  },
  currentJaiminiChakra: {
    color: COLORS.white,
  },
  jaiminiDates: {
    fontSize: 8,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 2,
    lineHeight: 10,
  },
  currentJaiminiDates: {
    color: COLORS.white,
  },
  jaiminiProgressBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 3,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
  },
  jaiminiProgressFill: {
    height: '100%',
    backgroundColor: '#ff6f00',
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
  },
  selectedJaiminiCard: {
    backgroundColor: '#2196f3',
    borderColor: '#2196f3',
  },
  jaiminiStatusCard: {
    backgroundColor: '#f3e5f5',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#9c27b0',
  },
  jaiminiStatusTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#9c27b0',
    marginBottom: 12,
    textAlign: 'center',
  },
  jaiminiSelectedInfo: {
    alignItems: 'center',
  },
  jaiminiSelectedSign: {
    fontSize: 20,
    fontWeight: '700',
    color: '#673ab7',
    marginBottom: 4,
  },
  jaiminiSelectedDetails: {
    fontSize: 12,
    color: '#9c27b0',
    marginBottom: 4,
  },
  jaiminiSelectedDates: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  jaiminiAntarCard: {
    backgroundColor: '#e8f5e8',
    borderRadius: 6,
    padding: 8,
    marginRight: 6,
    minWidth: 70,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#4caf50',
    position: 'relative',
  },
  currentJaiminiAntarCard: {
    backgroundColor: '#388e3c',
    borderColor: '#388e3c',
  },
  jaiminiAntarSign: {
    fontSize: 12,
    fontWeight: '600',
    color: '#4caf50',
    textAlign: 'center',
  },
  currentJaiminiAntarSign: {
    color: COLORS.white,
  },
  jaiminiAntarPeriod: {
    fontSize: 9,
    color: '#4caf50',
    textAlign: 'center',
    marginTop: 1,
    fontWeight: '600',
  },
  currentJaiminiAntarPeriod: {
    color: COLORS.white,
  },
  jaiminiAntarDates: {
    fontSize: 8,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 1,
  },
  currentJaiminiAntarDates: {
    color: COLORS.white,
  },
  jaiminiAntarProgressBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 2,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderBottomLeftRadius: 6,
    borderBottomRightRadius: 6,
  },
  jaiminiAntarProgressFill: {
    height: '100%',
    backgroundColor: '#ff6f00',
    borderBottomLeftRadius: 6,
    borderBottomRightRadius: 6,
  },
  selectedJaiminiAntarCard: {
    backgroundColor: '#2e7d32',
    borderColor: '#2e7d32',
  },
  selectedJaiminiText: {
    color: COLORS.white,
  },
  jaiminiTabSelector: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    borderRadius: 8,
    padding: 4,
    marginBottom: 12,
  },
  jaiminiTab: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  activeJaiminiTab: {
    backgroundColor: '#4caf50',
  },
  jaiminiTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  activeJaiminiTabText: {
    color: COLORS.white,
  },
});

export default CascadingDashaBrowser;
