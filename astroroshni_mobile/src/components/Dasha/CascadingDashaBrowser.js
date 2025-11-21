import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  Modal,
  SafeAreaView,
  Platform,
  StatusBar,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import Icon from 'react-native-vector-icons/Ionicons';
import { COLORS, API_BASE_URL } from '../../utils/constants';
import { chartAPI } from '../../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

const CascadingDashaBrowser = ({ visible, onClose, birthData }) => {
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
  const [dashaType, setDashaType] = useState('vimshottari'); // 'vimshottari', 'kalchakra', or 'jaimini'
  const [showSystemInfo, setShowSystemInfo] = useState(false);
  const [manushyaRule, setManushyaRule] = useState('always-reverse'); // 'always-reverse' or 'pada-based'

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
      }
    }
  }, [visible, birthData, transitDate, dashaType, manushyaRule]);

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
        const selectedIndex = options.findIndex(d => d.planet === selectedValue);
        if (selectedIndex > 0) {
          const scrollX = dashaType.includes('kalchakra') ? selectedIndex * 98 : selectedIndex * 78;
          setTimeout(() => {
            scrollRef.current?.scrollTo({ x: scrollX, animated: true });
          }, 100);
        }
      }
    });
  }, [selectedDashas, cascadingData, kalchakraData]);

  // Auto-scroll to current Kalchakra dasha on load
  useEffect(() => {
    if (dashaType === 'kalchakra' && kalchakraData?.periods && scrollRefs.kalchakra_maha?.current) {
      const currentDate = new Date();
      const currentIndex = kalchakraData.periods.findIndex(period => {
        const startDate = new Date(period.start_date);
        const endDate = new Date(period.end_date);
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
      const token = await AsyncStorage.getItem('authToken');
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 'Asia/Kolkata',
        location: birthData.place || 'Unknown'
      };
      
      const response = await fetch(`${API_BASE_URL}/api/calculate-cascading-dashas`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          birth_data: formattedBirthData,
          target_date: targetDate
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const cascadingData = await response.json();
      setCascadingData(cascadingData);
    } catch (err) {
      console.error('Cascading fetch error:', err);
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
        timezone: birthData.timezone || 5.5,
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
      console.error('Jaimini antardasha fetch error:', err);
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
        timezone: birthData.timezone || 5.5,
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
      setJaiminiData(jaiminiData);
      
    } catch (err) {
      console.error('Jaimini Kalchakra fetch error:', err);
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
        timezone: birthData.timezone || 5.5,
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
          birth_data: formattedBirthData,
          manushya_rule: manushyaRule
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const kalchakraData = await response.json();
      setKalchakraData(kalchakraData);
      
      // Fetch system info
      try {
        const infoResponse = await fetch(`${API_BASE_URL}/api/kalchakra-dasha-info`);
        if (infoResponse.ok) {
          const systemInfo = await infoResponse.json();
          setKalchakraSystemInfo(systemInfo);
        }
      } catch (infoErr) {
        console.log('System info fetch failed:', infoErr);
      }
      
    } catch (err) {
      console.error('Kalchakra fetch error:', err);
      setError('Failed to load Kalchakra dasha data');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchKalchakraAntardasha = async (mahaPlanet) => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      
      const formattedBirthData = {
        name: birthData.name,
        date: birthData.date.includes('T') ? birthData.date.split('T')[0] : birthData.date,
        time: birthData.time.includes('T') ? new Date(birthData.time).toTimeString().slice(0, 5) : birthData.time,
        latitude: parseFloat(birthData.latitude),
        longitude: parseFloat(birthData.longitude),
        timezone: birthData.timezone || 5.5,
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
          maha_planet: mahaPlanet,
          target_date: new Date().toISOString().split('T')[0]
        })
      });
      
      if (response.ok) {
        const antarData = await response.json();
        setKalchakraAntarData(antarData);
      }
    } catch (err) {
      console.error('Kalchakra antardasha fetch error:', err);
    }
  };

  const autoSelectCurrentDashas = () => {
    if (!cascadingData) return;
    
    const currentSelections = {};
    
    const currentMaha = cascadingData.maha_dashas?.find(d => d.current);
    if (currentMaha) currentSelections.maha = currentMaha.planet;
    
    const currentAntar = cascadingData.antar_dashas?.find(d => d.current);
    if (currentAntar) currentSelections.antar = currentAntar.planet;
    
    const currentPratyantar = cascadingData.pratyantar_dashas?.find(d => d.current);
    if (currentPratyantar) currentSelections.pratyantar = currentPratyantar.planet;
    
    const currentSookshma = cascadingData.sookshma_dashas?.find(d => d.current);
    if (currentSookshma) currentSelections.sookshma = currentSookshma.planet;
    
    const currentPrana = cascadingData.prana_dashas?.find(d => d.current);
    if (currentPrana) currentSelections.prana = currentPrana.planet;
    
    setSelectedDashas(currentSelections);
  };

  const autoSelectCurrentJaiminiDashas = () => {
    if (!jaiminiData?.periods) {
      console.log('No jaimini periods data', jaiminiData);
      return;
    }
    
    if (jaiminiData.periods.length === 0) {
      console.log('Jaimini periods array is empty');
      return;
    }
    
    console.log('Jaimini periods:', jaiminiData.periods);
    
    // Find the period marked as current by backend
    const currentPeriod = jaiminiData.periods.find(period => period.current === true);
    
    console.log('Current period found:', currentPeriod);
    
    if (currentPeriod) {
      console.log('Selecting current period:', currentPeriod.sign || currentPeriod.planet);
      setSelectedDashas({ jaimini_maha: currentPeriod.id || currentPeriod.sign || currentPeriod.planet });
      fetchJaiminiAntardasha(currentPeriod.sign || currentPeriod.planet);
    } else if (jaiminiData.periods.length > 0) {
      // Fallback: select first period
      const firstPeriod = jaiminiData.periods[0];
      console.log('Fallback: selecting first period:', firstPeriod.sign);
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
    if (!kalchakraData?.periods) return;
    
    // Use the current flag set by backend
    const currentPeriod = kalchakraData.periods.find(period => period.current === true);
    
    if (currentPeriod) {
      setSelectedDashas({ kalchakra_maha: currentPeriod.planet });
      // Fetch antardasha for current mahadasha
      fetchKalchakraAntardasha(currentPeriod.planet);
    }
  };
  
  const handleKalchakraMahaSelection = (planet) => {
    setSelectedDashas({ kalchakra_maha: planet });
    fetchKalchakraAntardasha(planet);
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
    
    if (diffMs <= 0) return 'Completed';
    
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffYears = Math.floor(diffDays / 365);
    const remainingDays = diffDays % 365;
    const diffMonths = Math.floor(remainingDays / 30);
    const finalDays = remainingDays % 30;
    
    if (diffYears > 0) {
      return `${diffYears}y ${diffMonths}m remaining`;
    } else if (diffMonths > 0) {
      return `${diffMonths}m ${finalDays}d remaining`;
    } else {
      return `${finalDays}d remaining`;
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
        return kalchakraData?.periods || [];
      } else if (dashaLevel === 'kalchakra_antar') {
        return kalchakraAntarData?.antar_periods || [];
      }
      return [];
    }
    
    if (!cascadingData) return [];
    
    switch (dashaLevel) {
      case 'maha':
        return cascadingData.maha_dashas || [];
      case 'antar':
        return cascadingData.antar_dashas || [];
      case 'pratyantar':
        return cascadingData.pratyantar_dashas || [];
      case 'sookshma':
        return cascadingData.sookshma_dashas || [];
      case 'prana':
        return cascadingData.prana_dashas || [];
      default:
        return [];
    }
  };



  const renderDashaTypeSelector = () => (
    <View style={styles.dashaTypeSelector}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabScrollView}>
        <TouchableOpacity
          style={[styles.dashaTypeTab, dashaType === 'vimshottari' && styles.activeDashaTypeTab]}
          onPress={() => {
            setDashaType('vimshottari');
            setSelectedDashas({});
            setKalchakraAntarData(null);
            setJaiminiData(null);
          }}
        >
          <Text style={[styles.dashaTypeTabText, dashaType === 'vimshottari' && styles.activeDashaTypeTabText]} numberOfLines={1}>
            Vimshottari
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.dashaTypeTab, dashaType === 'kalchakra' && styles.activeDashaTypeTab]}
          onPress={() => {
            setDashaType('kalchakra');
            setSelectedDashas({});
            setKalchakraAntarData(null);
            setJaiminiData(null);
          }}
        >
          <View style={styles.tabContent}>
            <Text style={[styles.dashaTypeTabText, dashaType === 'kalchakra' && styles.activeDashaTypeTabText]} numberOfLines={1}>
              BPHS Kalchakra
            </Text>
            {kalchakraSystemInfo && (
              <TouchableOpacity 
                style={styles.infoButton}
                onPress={() => setShowSystemInfo(true)}
              >
                <Text style={styles.infoIcon}>ℹ️</Text>
              </TouchableOpacity>
            )}
          </View>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.dashaTypeTab, dashaType === 'jaimini' && styles.activeDashaTypeTab]}
          onPress={() => {
            setDashaType('jaimini');
            setSelectedDashas({});
            setKalchakraAntarData(null);
            setJaiminiData(null);
          }}
        >
          <Text style={[styles.dashaTypeTabText, dashaType === 'jaimini' && styles.activeDashaTypeTabText]} numberOfLines={1}>
            Jaimini Kalchakra
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );

  const renderDateNavigation = () => (
    <View style={styles.dateNav}>
      <View style={styles.compactNavRow}>
        <View style={styles.navButtonGroup}>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(-30)}>
            <Text style={styles.compactNavText}>-1M</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(-7)}>
            <Text style={styles.compactNavText}>-1W</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(-1)}>
            <Text style={styles.compactNavText}>-1D</Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity style={styles.compactDateButton} onPress={() => setTransitDate(new Date())}>
          <Text style={styles.compactDateText}>{transitDate.toLocaleDateString('en-US', {month: 'short', day: 'numeric'})}</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.compactCalendarButton} onPress={() => setShowDatePicker(true)}>
          <Text style={styles.calendarIcon}>📅</Text>
        </TouchableOpacity>
        
        <View style={styles.navButtonGroup}>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(1)}>
            <Text style={styles.compactNavText}>+1D</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(7)}>
            <Text style={styles.compactNavText}>+1W</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.compactNavButton} onPress={() => adjustDate(30)}>
            <Text style={styles.compactNavText}>+1M</Text>
          </TouchableOpacity>
        </View>
      </View>
      
      {showDatePicker && (
        <View>
          <DateTimePicker
            value={transitDate}
            mode="date"
            display={Platform.OS === 'ios' ? 'spinner' : 'default'}
            onChange={(event, selectedDate) => {
              if (Platform.OS === 'android') {
                setShowDatePicker(false);
                if (selectedDate) {
                  setTransitDate(selectedDate);
                }
              } else {
                if (selectedDate) {
                  setTransitDate(selectedDate);
                }
              }
            }}
          />
          {Platform.OS === 'ios' && (
            <TouchableOpacity 
              style={styles.doneButton} 
              onPress={() => setShowDatePicker(false)}
            >
              <Text style={styles.doneButtonText}>Done</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
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
    
    const currentMaha = kalchakraData.periods?.find(period => {
      const startDate = new Date(period.start_date);
      const endDate = new Date(period.end_date);
      const now = new Date();
      return now >= startDate && now <= endDate;
    });
    
    const currentAntar = kalchakraAntarData?.antar_periods?.find(period => period.current);
    
    if (!currentMaha) return null;
    
    const mahaProgress = calculateProgress(currentMaha.start_date, currentMaha.end_date);
    const antarProgress = currentAntar ? calculateProgress(currentAntar.start_date, currentAntar.end_date) : 0;
    
    return (
      <View style={styles.currentStatusCard}>
        <Text style={styles.currentStatusTitle}>Current Kalchakra Periods</Text>
        
        <View style={styles.currentPeriodRow}>
          <View style={styles.currentPeriodInfo}>
            <Text style={styles.currentPeriodLabel}>Mahadasha</Text>
            <Text style={styles.currentPeriodPlanet}>{currentMaha.planet}</Text>
            <Text style={styles.currentPeriodTime}>{getRemainingTime(currentMaha.end_date)}</Text>
          </View>
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: `${mahaProgress}%` }]} />
            </View>
            <Text style={styles.progressText}>{Math.round(mahaProgress)}%</Text>
          </View>
        </View>
        
        {currentAntar && (
          <View style={styles.currentPeriodRow}>
            <View style={styles.currentPeriodInfo}>
              <Text style={styles.currentPeriodLabel}>Antardasha</Text>
              <Text style={styles.currentPeriodPlanet}>{currentAntar.planet}</Text>
              <Text style={styles.currentPeriodTime}>{getRemainingTime(currentAntar.end_date)}</Text>
            </View>
            <View style={styles.progressContainer}>
              <View style={styles.progressBar}>
                <View style={[styles.progressFill, styles.antarProgressFill, { width: `${antarProgress}%` }]} />
              </View>
              <Text style={styles.progressText}>{Math.round(antarProgress)}%</Text>
            </View>
          </View>
        )}
        
        <View style={styles.systemInfoRow}>
          <Text style={styles.systemInfoText}>120-year cycle • {kalchakraData.sequence_direction} sequence</Text>
          <Text style={styles.systemInfoText}>Moon: {kalchakraData.moon_nakshatra} Pada {kalchakraData.moon_pada} ({kalchakraData.nakshatra_deity})</Text>
        </View>
      </View>
    );
  };
  
  const renderBreadcrumb = () => {
    if (dashaType === 'kalchakra') {
      return renderKalchakraCurrentStatus();
    } else if (dashaType === 'jaimini') {
      return renderJaiminiCurrentStatus();
    }
    
    if (!cascadingData) {
      return (
        <View style={styles.breadcrumb}>
          <Text style={styles.breadcrumbText}>Select dashas to see hierarchy</Text>
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
    
    return (
      <View style={styles.breadcrumb}>
        {breadcrumbItems.length === 0 ? (
          <Text style={styles.breadcrumbText}>Select dashas to see hierarchy</Text>
        ) : (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.breadcrumbScroll}>
            {breadcrumbItems.map((item, index) => (
              <View key={`breadcrumb-${item.planet}-${index}`} style={styles.breadcrumbRow}>
                <View style={styles.breadcrumbCard}>
                  <Text style={styles.breadcrumbPlanet}>{item.planet}</Text>
                  {item.details && (
                    <>
                      <Text style={styles.breadcrumbPeriod}>{formatPeriodDuration(item.details.years)}</Text>
                      <Text style={styles.breadcrumbDates}>
                        {new Date(item.details.start).toLocaleDateString('en-US', {month: 'short', year: '2-digit'})} - {new Date(item.details.end).toLocaleDateString('en-US', {month: 'short', year: '2-digit'})}
                      </Text>
                    </>
                  )}
                </View>
                {index < breadcrumbItems.length - 1 && (
                  <Text style={styles.breadcrumbArrow}>→</Text>
                )}
              </View>
            ))}
          </ScrollView>
        )}
      </View>
    );
  };

  const renderManushyaRuleSelector = () => (
    <View style={styles.manushyaRuleSelector}>
      <Text style={styles.manushyaRuleLabel}>Manushya Nakshatra Rule:</Text>
      <View style={styles.manushyaRuleOptions}>
        <TouchableOpacity
          style={[styles.manushyaRuleOption, manushyaRule === 'always-reverse' && styles.activeManushyaRule]}
          onPress={() => {
            setManushyaRule('always-reverse');
            setKalchakraData(null);
            setKalchakraAntarData(null);
          }}
        >
          <Text style={[styles.manushyaRuleText, manushyaRule === 'always-reverse' && styles.activeManushyaRuleText]}>
            BPHS Authentic
          </Text>
          <Text style={[styles.manushyaRuleSubtext, manushyaRule === 'always-reverse' && styles.activeManushyaRuleSubtext]}>All Manushya: Backward</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.manushyaRuleOption, manushyaRule === 'pada-based' && styles.activeManushyaRule]}
          onPress={() => {
            setManushyaRule('pada-based');
            setKalchakraData(null);
            setKalchakraAntarData(null);
          }}
        >
          <Text style={[styles.manushyaRuleText, manushyaRule === 'pada-based' && styles.activeManushyaRuleText]}>
            Modern Variant
          </Text>
          <Text style={[styles.manushyaRuleSubtext, manushyaRule === 'pada-based' && styles.activeManushyaRuleSubtext]}>Pada 1-2: Forward, 3-4: Backward</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const renderJaiminiKalchakraDashaList = () => {
    if (!jaiminiData) {
      return (
        <View style={styles.selectorContainer}>
          <Text style={styles.selectorLabel}>Jaimini Kalchakra Dasha</Text>
          <View style={[styles.optionCard, styles.disabledOption]}>
            <Text style={styles.disabledOptionText}>Loading...</Text>
          </View>
        </View>
      );
    }
    
    if (jaiminiData.error) {
      return (
        <View style={styles.selectorContainer}>
          <Text style={styles.selectorLabel}>Jaimini Kalchakra Dasha</Text>
          <View style={[styles.optionCard, styles.disabledOption]}>
            <Text style={styles.disabledOptionText}>Error: {jaiminiData.error}</Text>
          </View>
        </View>
      );
    }
    
    if (!jaiminiData.periods || jaiminiData.periods.length === 0) {
      return (
        <View style={styles.selectorContainer}>
          <Text style={styles.selectorLabel}>Jaimini Kalchakra Dasha</Text>
          <View style={[styles.optionCard, styles.disabledOption]}>
            <Text style={styles.disabledOptionText}>No periods calculated</Text>
          </View>
        </View>
      );
    }

    return (
      <>
        <View style={styles.jaiminiInfoCard}>
          <Text style={styles.jaiminiInfoTitle}>Jaimini Kalchakra System</Text>
          <Text style={styles.jaiminiInfoText}>Janma Rashi: {jaiminiData.janma_rashi}</Text>
          <Text style={styles.jaiminiInfoText}>Chakra 1: {jaiminiData.chakra1_direction} • Chakra 2: {jaiminiData.chakra2_direction}</Text>
          <Text style={styles.jaiminiInfoText}>Total Cycle: {jaiminiData.total_cycle_years} years</Text>
          
          {jaiminiData.reversals && jaiminiData.reversals.length > 0 && (
            <View style={styles.reversalInfo}>
              <Text style={styles.reversalTitle}>🔄 Direction Reversals:</Text>
              {jaiminiData.reversals.map((reversal, index) => (
                <Text key={index} style={styles.reversalText}>
                  {reversal.type}: {reversal.from_direction} → {reversal.to_direction}
                </Text>
              ))}
            </View>
          )}
          
          {jaiminiData.jumps && jaiminiData.jumps.length > 0 && (
            <View style={styles.jumpInfo}>
              <Text style={styles.jumpTitle}>⚡ Sign Jumps:</Text>
              {jaiminiData.jumps.map((jump, index) => (
                <Text key={index} style={styles.jumpText}>
                  Skipped: {jump.skipped_sign} ({jump.reason})
                </Text>
              ))}
            </View>
          )}
          
          {jaiminiData.predictions && (
            <View style={styles.predictionInfo}>
              <Text style={styles.predictionTitle}>🔮 Upcoming Events:</Text>
              
              {jaiminiData.predictions.cycle_progress && (
                <Text style={styles.predictionText}>
                  Cycle Progress: {jaiminiData.predictions.cycle_progress}% complete
                </Text>
              )}
              
              {jaiminiData.predictions.next_reversal && (
                <Text style={styles.predictionText}>
                  Next Reversal: {jaiminiData.predictions.next_reversal.significance} in {jaiminiData.predictions.next_reversal.years_until} years
                </Text>
              )}
              
              {jaiminiData.predictions.next_cycle_reset && (
                <Text style={styles.predictionText}>
                  Cycle Reset: {jaiminiData.predictions.next_cycle_reset.years_until} years (Cycle {jaiminiData.predictions.next_cycle_reset.cycle_number})
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
          <Text style={styles.selectorLabel}>Jaimini Kalchakra Mahadasha</Text>
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
                  }}
                >
                  <Text style={[
                    styles.jaiminiSign,
                    isActuallyCurrent && styles.currentJaiminiSign,
                    selectedDashas.jaimini_maha === (period.id || period.sign) && styles.selectedJaiminiText
                  ]}>
                    {period.sign}
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
                    C{period.chakra} {period.direction === 'Forward' ? '→' : '←'}
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
            <Text style={styles.selectorLabel}>Jaimini Antardasha ({jaiminiAntarData.maha_sign})</Text>
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
                    }}
                  >
                    <Text style={[
                      styles.jaiminiAntarSign,
                      isActuallyCurrent && styles.currentJaiminiAntarSign,
                      selectedDashas.jaimini_antar === period.sign && styles.selectedJaiminiText
                    ]}>
                      {period.sign}
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
        
        {/* Prediction Cards - Show at the end */}
        {jaiminiData.cards && (
          <View style={styles.predictionCardsSection}>
            <Text style={styles.predictionSectionTitle}>📊 Jaimini Predictions</Text>
            <ScrollView style={styles.cardsContainer} showsVerticalScrollIndicator={false}>
              {/* Status Card */}
              {jaiminiData.cards.status_card && (
                <View style={styles.statusCard}>
                  <Text style={styles.cardTitle}>Current Status</Text>
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
                  <Text style={styles.cardTitle}>🎯 Life Focus</Text>
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
                  <Text style={styles.cardTitle}>📅 Timeline</Text>
                  <View style={styles.currentPeriodInfo}>
                    <Text style={styles.currentPeriodName}>{jaiminiData.cards.timeline_card.current_period.name}</Text>
                    <Text style={styles.currentPeriodDates}>
                      {new Date(jaiminiData.cards.timeline_card.current_period.start).toLocaleDateString()} - 
                      {new Date(jaiminiData.cards.timeline_card.current_period.end).toLocaleDateString()}
                    </Text>
                  </View>
                  {jaiminiData.cards.timeline_card.next_events.length > 0 && (
                    <View style={styles.nextEventsContainer}>
                      <Text style={styles.nextEventsTitle}>Upcoming Events:</Text>
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
                  <Text style={styles.cardTitle}>🔮 Predictions</Text>
                  {jaiminiData.cards.predictions_card.next_6_months.length > 0 && (
                    <View style={styles.predictionSection}>
                      <Text style={styles.predictionSectionTitle}>Next 6 months:</Text>
                      {jaiminiData.cards.predictions_card.next_6_months.map((event, index) => (
                        <Text key={index} style={styles.predictionText}>• {event}</Text>
                      ))}
                    </View>
                  )}
                  {jaiminiData.cards.predictions_card.next_2_years.length > 0 && (
                    <View style={styles.predictionSection}>
                      <Text style={styles.predictionSectionTitle}>Next 2 years:</Text>
                      {jaiminiData.cards.predictions_card.next_2_years.map((theme, index) => (
                        <Text key={index} style={styles.predictionText}>• {theme}</Text>
                      ))}
                    </View>
                  )}
                  {jaiminiData.cards.predictions_card.jump_effects.length > 0 && (
                    <View style={styles.predictionSection}>
                      <Text style={styles.predictionSectionTitle}>Jump Effects:</Text>
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
                  <Text style={styles.cardTitle}>💪 Strength Comparison</Text>
                  <View style={styles.strengthComparison}>
                    <View style={styles.strengthItem}>
                      <Text style={styles.strengthLabel}>Current</Text>
                      <View style={styles.strengthBar}>
                        <View style={[styles.strengthFill, { width: `${jaiminiData.cards.strength_card.current_strength}%` }]} />
                      </View>
                      <Text style={styles.strengthValue}>{jaiminiData.cards.strength_card.current_strength}/100</Text>
                    </View>
                    <View style={styles.strengthItem}>
                      <Text style={styles.strengthLabel}>Next ({jaiminiData.cards.strength_card.next_sign_name})</Text>
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
        )}
      </>
    );
  };

  const renderKalchakraDashaList = () => {
    const mahaOptions = getDashaOptions('kalchakra_maha');
    const antarOptions = getDashaOptions('kalchakra_antar');
    
    return (
      <>
        <View style={styles.selectorContainer}>
          <Text style={styles.selectorLabel}>Kalchakra Mahadasha (BPHS Authentic)</Text>
          <ScrollView 
            ref={scrollRefs.kalchakra_maha}
            horizontal 
            showsHorizontalScrollIndicator={false} 
            style={styles.optionsScroll}
          >
            {mahaOptions.length === 0 ? (
              <View style={[styles.optionCard, styles.disabledOption]}>
                <Text style={styles.disabledOptionText}>No periods available</Text>
              </View>
            ) : (
              mahaOptions.map((period, index) => {
                const isSelected = selectedDashas.kalchakra_maha === period.planet;
                const currentDate = new Date();
                const startDate = new Date(period.start_date);
                const endDate = new Date(period.end_date);
                const isActuallyCurrent = currentDate >= startDate && currentDate <= endDate;
                const progress = calculateProgress(period.start_date, period.end_date);
                
                return (
                  <TouchableOpacity
                    key={`${period.planet}-${index}`}
                    style={[
                      styles.kalchakraCard,
                      isSelected && styles.selectedKalchakraCard,
                      isActuallyCurrent && styles.currentKalchakraCard
                    ]}
                    onPress={() => handleKalchakraMahaSelection(period.planet)}
                  >
                    <Text style={[
                      styles.kalchakraPlanet,
                      isSelected && styles.selectedKalchakraPlanet,
                      isActuallyCurrent && styles.currentKalchakraPlanet
                    ]}>
                      {period.planet}
                    </Text>
                    <Text style={[
                      styles.kalchakraPeriod,
                      isSelected && styles.selectedKalchakraPeriod,
                      isActuallyCurrent && styles.currentKalchakraPeriod
                    ]}>
                      {formatPeriodDuration(period.duration_years)}
                    </Text>
                    <Text style={[
                      styles.kalchakraSequence,
                      isSelected && styles.selectedKalchakraSequence,
                      isActuallyCurrent && styles.currentKalchakraSequence
                    ]}>
                      {period.sequence_direction === 'forward' ? '→' : '←'} C{period.cycle_number || 1}
                    </Text>
                    <Text style={[
                      styles.kalchakraDates,
                      isSelected && styles.selectedKalchakraDates,
                      isActuallyCurrent && styles.currentKalchakraDates
                    ]}>
                      {new Date(period.start_date).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})} - {new Date(period.end_date).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})}
                    </Text>
                    {isActuallyCurrent && (
                      <View style={styles.kalchakraProgressBar}>
                        <View style={[styles.kalchakraProgressFill, { width: `${progress}%` }]} />
                      </View>
                    )}
                  </TouchableOpacity>
                );
              })
            )}
          </ScrollView>
        </View>
        
        {selectedDashas.kalchakra_maha && antarOptions.length > 0 && (
          <View style={styles.selectorContainer}>
            <Text style={styles.selectorLabel}>Kalchakra Antardasha ({selectedDashas.kalchakra_maha})</Text>
            <ScrollView 
              ref={scrollRefs.kalchakra_antar}
              horizontal 
              showsHorizontalScrollIndicator={false} 
              style={styles.optionsScroll}
            >
              {antarOptions.map((period, index) => {
                const isSelected = selectedDashas.kalchakra_antar === period.planet;
                const isActuallyCurrent = period.current;
                const progress = calculateProgress(period.start_date, period.end_date);
                
                return (
                  <TouchableOpacity
                    key={`antar-${period.planet}-${index}`}
                    style={[
                      styles.kalchakraAntarCard,
                      isSelected && styles.selectedKalchakraAntarCard,
                      isActuallyCurrent && styles.currentKalchakraAntarCard
                    ]}
                    onPress={() => {
                      setSelectedDashas(prev => ({ ...prev, kalchakra_antar: period.planet }));
                    }}
                  >
                    <Text style={[
                      styles.kalchakraAntarPlanet,
                      isSelected && styles.selectedKalchakraAntarPlanet,
                      isActuallyCurrent && styles.currentKalchakraAntarPlanet
                    ]}>
                      {period.planet}
                    </Text>
                    <Text style={[
                      styles.kalchakraAntarPeriod,
                      isSelected && styles.selectedKalchakraAntarPeriod,
                      isActuallyCurrent && styles.currentKalchakraAntarPeriod
                    ]}>
                      {formatPeriodDuration(period.years)}
                    </Text>
                    <Text style={[
                      styles.kalchakraAntarDates,
                      isSelected && styles.selectedKalchakraAntarDates,
                      isActuallyCurrent && styles.currentKalchakraAntarDates
                    ]}>
                      {new Date(period.start_date).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})} - {new Date(period.end_date).toLocaleDateString('en-US', {day: 'numeric', month: 'short', year: '2-digit'})}
                    </Text>
                    {isActuallyCurrent && (
                      <View style={styles.kalchakraAntarProgressBar}>
                        <View style={[styles.kalchakraAntarProgressFill, { width: `${progress}%` }]} />
                      </View>
                    )}
                  </TouchableOpacity>
                );
              })}
            </ScrollView>
          </View>
        )}
      </>
    );
  };
  
  const renderSystemInfoModal = () => (
    <Modal visible={showSystemInfo} animationType="slide" transparent>
      <View style={styles.modalOverlay}>
        <View style={styles.systemInfoModal}>
          <View style={styles.systemInfoHeader}>
            <Text style={styles.systemInfoTitle}>BPHS Kalchakra Dasha</Text>
            <TouchableOpacity onPress={() => setShowSystemInfo(false)}>
              <Text style={styles.modalCloseIcon}>✕</Text>
            </TouchableOpacity>
          </View>
          
          {kalchakraSystemInfo && (
            <ScrollView style={styles.systemInfoContent}>
              <Text style={styles.systemInfoSubtitle}>{kalchakraSystemInfo.system_name}</Text>
              <Text style={styles.systemInfoDescription}>{kalchakraSystemInfo.specialty}</Text>
              
              <View style={styles.systemInfoSection}>
                <Text style={styles.systemInfoSectionTitle}>Source</Text>
                <Text style={styles.systemInfoText}>{kalchakraSystemInfo.source}</Text>
              </View>
              
              <View style={styles.systemInfoSection}>
                <Text style={styles.systemInfoSectionTitle}>Key Features</Text>
                <Text style={styles.systemInfoText}>• {kalchakraSystemInfo.total_combinations} nakshatra-pada combinations</Text>
                <Text style={styles.systemInfoText}>• {kalchakraSystemInfo.cycle_length_years}-year complete cycle</Text>
                <Text style={styles.systemInfoText}>• {kalchakraSystemInfo.based_on}</Text>
                <Text style={styles.systemInfoText}>• {kalchakraSystemInfo.timing_method}</Text>
              </View>
              
              <View style={styles.systemInfoSection}>
                <Text style={styles.systemInfoSectionTitle}>Authenticity</Text>
                <Text style={styles.systemInfoText}>{kalchakraSystemInfo.authenticity}</Text>
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
    
    return (
      <View style={styles.selectorContainer}>
        <Text style={styles.selectorLabel}>{title}</Text>
        <ScrollView ref={scrollRefs[dashaLevel]} horizontal showsHorizontalScrollIndicator={false} style={styles.optionsScroll}>
          {options.length === 0 ? (
            <View style={[styles.optionCard, styles.disabledOption]}>
              <Text style={styles.disabledOptionText}>No options available</Text>
            </View>
          ) : (
            options.map((dasha, index) => {
              const isSelected = selectedValue === dasha.planet;
              const isCurrent = dasha.current;
              const currentDate = transitDate;
              const startDate = new Date(dasha.start);
              const endDate = new Date(dasha.end);
              const isActuallyCurrent = currentDate >= startDate && currentDate <= endDate;
              
              return (
                <TouchableOpacity
                  key={`${dasha.planet}-${index}`}
                  style={[
                    styles.optionCard,
                    isSelected && styles.selectedOptionCard,
                    isActuallyCurrent && styles.currentOptionCard
                  ]}
                  onPress={() => {
                    handleDashaSelection(dashaLevel, dasha.planet);
                  }}
                >
                  <Text style={[
                    styles.optionPlanet,
                    isSelected && styles.selectedOptionPlanet,
                    isActuallyCurrent && styles.currentOptionPlanet
                  ]}>
                    {dasha.planet}
                  </Text>
                  <Text style={[
                    styles.optionPeriod,
                    isSelected && styles.selectedOptionPeriod,
                    isActuallyCurrent && styles.currentOptionPeriod
                  ]}>
                    {formatPeriodDuration(dasha.years)}
                  </Text>
                  <Text style={[
                    styles.optionDates,
                    isSelected && styles.selectedOptionDates,
                    isActuallyCurrent && styles.currentOptionDates
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

  if (loading) {
    return (
      <Modal visible={visible} animationType="slide">
        <StatusBar barStyle="light-content" backgroundColor="#ff6f00" translucent={false} />
        <SafeAreaView style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeIcon}>✕</Text>
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Dasha Browser</Text>
            <View style={styles.placeholder} />
          </View>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={COLORS.accent} />
            <Text style={styles.loadingText}>Loading Dasha Data...</Text>
          </View>
        </SafeAreaView>
      </Modal>
    );
  }

  if (error) {
    return (
      <Modal visible={visible} animationType="slide">
        <StatusBar barStyle="light-content" backgroundColor="#ff6f00" translucent={false} />
        <SafeAreaView style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={styles.closeIcon}>✕</Text>
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Dasha Browser</Text>
            <View style={styles.placeholder} />
          </View>
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={fetchCascadingDashas}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    );
  }

  return (
    <Modal visible={visible} animationType="slide">
      <StatusBar barStyle="light-content" backgroundColor="#ff6f00" translucent={false} />
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Text style={styles.closeIcon}>✕</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Dashas for {birthData?.name || 'User'}</Text>
          <View style={styles.placeholder} />
        </View>
        
        <ScrollView style={styles.content}>
          {renderDashaTypeSelector()}
          {dashaType === 'vimshottari' && renderDateNavigation()}
          {renderBreadcrumb()}
          
          <View style={styles.selectorsContainer}>
            {dashaType === 'vimshottari' ? (
              <>
                {renderDashaSelector('maha', 'Maha Dasha')}
                {renderDashaSelector('antar', 'Antar Dasha')}
                {renderDashaSelector('pratyantar', 'Pratyantar Dasha')}
                {renderDashaSelector('sookshma', 'Sookshma Dasha')}
                {renderDashaSelector('prana', 'Prana Dasha')}
              </>
            ) : dashaType === 'kalchakra' ? (
              <>
                {renderManushyaRuleSelector()}
                {renderKalchakraDashaList()}
              </>
            ) : (
              <>
                {renderJaiminiKalchakraDashaList()}
              </>
            )}
          </View>
        </ScrollView>
        
        {renderSystemInfoModal()}
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
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
    marginRight: 4,
    minWidth: 100,
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
  infoButton: {
    marginLeft: 4,
    padding: 2,
  },
  infoIcon: {
    fontSize: 16,
    color: COLORS.white,
  },
  currentStatusCard: {
    backgroundColor: '#f3e5f5',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#9c27b0',
  },
  currentStatusTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#9c27b0',
    marginBottom: 12,
    textAlign: 'center',
  },
  currentPeriodRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  currentPeriodInfo: {
    flex: 1,
  },
  currentPeriodLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  currentPeriodPlanet: {
    fontSize: 16,
    fontWeight: '700',
    color: '#9c27b0',
  },
  currentPeriodTime: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  progressContainer: {
    alignItems: 'center',
    minWidth: 60,
  },
  progressBar: {
    width: 50,
    height: 6,
    backgroundColor: COLORS.lightGray,
    borderRadius: 3,
    marginBottom: 4,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#9c27b0',
    borderRadius: 3,
  },
  antarProgressFill: {
    backgroundColor: '#673ab7',
  },
  progressText: {
    fontSize: 10,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  systemInfoRow: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#e1bee7',
  },
  systemInfoText: {
    fontSize: 11,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 2,
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
  manushyaRuleSelector: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#e1bee7',
  },
  manushyaRuleLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#9c27b0',
    marginBottom: 8,
    textAlign: 'center',
  },
  manushyaRuleOptions: {
    flexDirection: 'row',
    gap: 8,
  },
  manushyaRuleOption: {
    flex: 1,
    backgroundColor: COLORS.lightGray,
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  activeManushyaRule: {
    backgroundColor: '#9c27b0',
    borderColor: '#9c27b0',
  },
  manushyaRuleText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textPrimary,
    textAlign: 'center',
  },
  activeManushyaRuleText: {
    color: COLORS.white,
  },
  manushyaRuleSubtext: {
    fontSize: 9,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginTop: 2,
    lineHeight: 11,
  },
  activeManushyaRuleSubtext: {
    color: 'rgba(255,255,255,0.8)',
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
    color: '#ff9800',
    marginBottom: 4,
  },
  jumpText: {
    fontSize: 10,
    color: '#ff9800',
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
});

export default CascadingDashaBrowser;