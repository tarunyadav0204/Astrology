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
import { chartAPI } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import JaiminiKalachakraHomeRN from './JaiminiKalachakraHomeRN';
import YoginiDashaTab from './YoginiDashaTab';
import CharaDashaTab from './CharaDashaTab';
import Svg, { Circle, Path, Text as SvgText, G, Defs, LinearGradient, Stop } from 'react-native-svg';
import DateNavigator from '../Common/DateNavigator';

const { width: SCREEN_WIDTH } = Dimensions.get('window');


const CascadingDashaBrowser = ({ visible, onClose, birthData }) => {
  const insets = useSafeAreaInsets();
  const [cascadingData, setCascadingData] = useState(null);
  const [kalchakraData, setKalchakraData] = useState(null);
  const [kalchakraAntarData, setKalchakraAntarData] = useState(null);
  const [kalchakraSystemInfo, setKalchakraSystemInfo] = useState(null);
  const [jaiminiData, setJaiminiData] = useState(null);
  const [jaiminiAntarData, setJaiminiAntarData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [transitDate, setTransitDate] = useState(new Date());
  const [selectedDashas, setSelectedDashas] = useState({});
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [dashaType, setDashaType] = useState('vimshottari'); // 'vimshottari', 'kalchakra', 'jaimini', or 'yogini'
  const [yoginiData, setYoginiData] = useState(null);
  const [showSystemInfo, setShowSystemInfo] = useState(false);
  const [showKalachakraViz, setShowKalachakraViz] = useState(false);
  const [kalchakraViewMode, setKalchakraViewMode] = useState('chips'); // 'chips', 'wheel', 'timeline'

  const [jaiminiTab, setJaiminiTab] = useState('home'); // 'home', 'periods', 'analysis'

  const formatPeriodDuration = (years) => {
    if (!years) return '';
    
    const totalDays = years * 365.25;
    const totalMonths = years * 12;
    
    if (totalDays < 90) { // Less than 3 months
      return `${Math.round(totalDays)}d`;
    } else if (totalMonths < 12) { // Less than 1 year
      return `${Math.round(totalMonths)}m`;
    } else {
      const wholeYears = Math.floor(years);
      const remainingMonths = Math.round((years - wholeYears) * 12);
      
      if (remainingMonths === 0) {
        return `${wholeYears}y`;
      } else {
        return `${wholeYears}y ${remainingMonths}m`;
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
      setLoading(true);
      setError(null);
      
      const targetDate = transitDate.toISOString().split('T')[0];
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        place: birthData.place || 'Unknown'
      };
      
      
      const response = await chartAPI.calculateCascadingDashas(formattedBirthData, targetDate);
      
      if (response.data.error) {
        setError(`Vimshottari calculation failed: ${response.data.error}`);
        return;
      }
      
      // Check if we have maha_dashas in the response
      const mahadashas = response.data.maha_dashas || [];
      
      if (mahadashas.length === 0) {
        setError('Vimshottari calculation returned no dasha periods.');
        return;
      }
      
      setCascadingData(response.data);
    } catch (err) {
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

  // ... rest of the component remains the same
  // (all the other functions and render methods)

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="fullScreen">
      {/* Component JSX remains the same */}
    </Modal>
  );
};

export default CascadingDashaBrowser;