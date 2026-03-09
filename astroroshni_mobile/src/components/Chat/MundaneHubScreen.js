import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  TextInput,
  Platform,
  KeyboardAvoidingView,
  Modal,
  FlatList,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { useCredits } from '../../credits/CreditContext';
import { useAnalytics } from '../../hooks/useAnalytics';
import { useTranslation } from 'react-i18next';
import DateTimePicker from '@react-native-community/datetimepicker';
import { COUNTRIES } from '../../utils/mundaneConstants';

const { width } = Dimensions.get('window');

const MUNDANE_CATEGORIES = [
  {
    id: 'sports',
    title: 'Sports & Competition',
    icon: '🏏',
    gradient: ['#F59E0B', '#D97706'],
    description: 'Predict match outcomes, tournaments, and player performance.',
    fields: ['event_name', 'entities', 'event_date', 'event_time']
  },
  {
    id: 'markets',
    title: 'Markets & Finance',
    icon: '📈',
    gradient: ['#10B981', '#059669'],
    description: 'Analyze stock markets, commodities, and economic trends.',
    fields: ['event_name', 'entities', 'event_date', 'period']
  },
  {
    id: 'politics',
    title: 'Politics & Elections',
    icon: '🗳️',
    gradient: ['#6366F1', '#4F46E5'],
    description: 'Forecast election results, regime changes, and policy impacts.',
    fields: ['event_name', 'entities', 'event_date']
  },
  {
    id: 'war',
    title: 'War & Geopolitics',
    icon: '🛡️',
    gradient: ['#EF4444', '#DC2626'],
    description: 'Evaluate border tensions, conflict risks, and global stability.',
    fields: ['event_name', 'entities', 'event_date']
  },
  {
    id: 'general',
    title: 'General Events',
    icon: '🌍',
    gradient: ['#6B7280', '#4B5563'],
    description: 'Natural events, launches, or any major world occurrence.',
    fields: ['event_name', 'event_date', 'event_time']
  }
];

export default function MundaneHubScreen({ navigation }) {
  useAnalytics('MundaneHubScreen');
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const { credits } = useCredits();
  const { t } = useTranslation();

  const [selectedCategory, setSelectedCategory] = useState(null);
  const [formData, setFormData] = useState({
    country: COUNTRIES[0],
    teamACountry: COUNTRIES[0],
    teamBCountry: COUNTRIES[1] || COUNTRIES[0],
    selectedEntities: [], // Array of country objects
    event_name: '',
    entities: '', // Comma separated (for non-sports labels)
    event_date: new Date(),
    event_time: new Date(),
    period: 'This Month'
  });
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [countrySearch, setCountrySearch] = useState('');
  const [countryPickerTarget, setCountryPickerTarget] = useState('location'); // 'location' | 'teamA' | 'teamB'

  const [fadeAnim] = useState(new Animated.Value(0));
  const [slideAnim] = useState(new Animated.Value(30));

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();
  }, [selectedCategory]);

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    // Reset animations for the form
    fadeAnim.setValue(0);
    slideAnim.setValue(20);
  };

  const handleStartAnalysis = () => {
    let entityList = [];
    if (selectedCategory.id === 'sports') {
      entityList = [
        formData.teamACountry?.name,
        formData.teamBCountry?.name,
      ].filter(Boolean);
    } else {
      // Prioritize selected entities (country objects) for chart lookups
      entityList = formData.selectedEntities.map(e => e.name);
      
      // Also include any free-text entities if they aren't duplicates
      const freeTextEntities = formData.entities.split(',').map(e => e.trim()).filter(e => e.length > 0);
      freeTextEntities.forEach(e => {
        if (!entityList.includes(e)) {
          entityList.push(e);
        }
      });
    }

    const context = {
      category: selectedCategory.id,
      country: formData.country.name,
      latitude: formData.country.lat,
      longitude: formData.country.lng,
      event_name: formData.event_name,
      entities: entityList,
      event_date: formData.event_date.toISOString().split('T')[0],
      event_time: formData.event_time.toTimeString().split(' ')[0],
      period: formData.period
    };

    // Construct an initial message based on context
    let initialMessage = "";
    if (selectedCategory.id === 'sports') {
      initialMessage = `Analyze the ${formData.event_name} match between ${entityList.join(' and ')} on ${context.event_date}. Who has the astrological edge?`;
    } else if (selectedCategory.id === 'markets') {
      initialMessage = `Provide a detailed market analysis for ${entityList.join(', ')} focused on the ${formData.event_name || 'current market phase'} for ${formData.period}.`;
    } else if (selectedCategory.id === 'politics') {
      initialMessage = `Analyze the ${formData.event_name} involving ${entityList.join(', ')} on ${context.event_date}. What is the likely political outcome?`;
    } else if (selectedCategory.id === 'war') {
      initialMessage = `Analyze the ${formData.event_name || 'geopolitical tension'} involving ${entityList.join(', ')} as of ${context.event_date}. Assess the risk of conflict escalation.`;
    } else {
      initialMessage = `Analyze the world event: ${formData.event_name} involving ${entityList.join(', ')} on ${context.event_date}.`;
    }

    navigation.navigate('Home', {
      mode: 'mundane',
      startChat: true,
      initialMessage: initialMessage,
      mundaneContext: context
    });
  };

  const renderCategoryList = () => (
    <ScrollView 
      style={styles.scrollView}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
    >
      <View style={styles.heroSection}>
        <Text style={[styles.heroTitle, { color: colors.text }]}>World Events Hub</Text>
        <Text style={[styles.heroSubtitle, { color: colors.textSecondary }]}>
          Select a category to begin your elite mundane analysis
        </Text>
      </View>

      <View style={styles.categoryGrid}>
        {MUNDANE_CATEGORIES.map((cat, index) => (
          <TouchableOpacity
            key={cat.id}
            onPress={() => handleCategorySelect(cat)}
            activeOpacity={0.8}
            style={styles.categoryCard}
          >
            <LinearGradient
              colors={isDark ? ['#1e293b', '#0f172a'] : ['#ffffff', '#f8fafc']}
              style={[styles.cardGradient, { borderColor: isDark ? '#334155' : '#e2e8f0' }]}
            >
              <View style={styles.cardHeader}>
                <LinearGradient colors={cat.gradient} style={styles.iconCircle}>
                  <Text style={styles.iconText}>{cat.icon}</Text>
                </LinearGradient>
                <Ionicons name="chevron-forward" size={20} color={colors.textTertiary} />
              </View>
              <Text style={[styles.catTitle, { color: colors.text }]}>{cat.title}</Text>
              <Text style={[styles.catDesc, { color: colors.textSecondary }]}>{cat.description}</Text>
            </LinearGradient>
          </TouchableOpacity>
        ))}
      </View>
    </ScrollView>
  );

  const renderForm = () => {
    const cat = selectedCategory;
    return (
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex1}
      >
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
        >
          <Animated.View style={[styles.formContainer, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
            <View style={styles.formHeader}>
              <LinearGradient colors={cat.gradient} style={styles.smallIconCircle}>
                <Text style={styles.smallIconText}>{cat.icon}</Text>
              </LinearGradient>
              <Text style={[styles.formTitle, { color: colors.text }]}>{cat.title}</Text>
            </View>

            <View style={styles.inputGroup}>
              <Text style={[styles.label, { color: colors.textSecondary }]}>
                {cat.id === 'sports' ? 'Match location (country)' : 'Primary country of analysis'}
              </Text>
              <TouchableOpacity 
                onPress={() => { setCountryPickerTarget('location'); setShowCountryPicker(true); }}
                style={[styles.input, { backgroundColor: isDark ? '#1e293b' : '#f1f5f9', borderColor: isDark ? '#334155' : '#e2e8f0', justifyContent: 'center' }]}
              >
                <Text style={{ color: colors.text }}>{formData.country.name}</Text>
              </TouchableOpacity>
              <Text style={[styles.helperText, { color: colors.textTertiary }]}>
                {cat.id === 'sports'
                  ? 'This is the country where the match is being played (stadium/host nation).'
                  : 'This sets the nation whose mundane chart and dashas will be used.'}
              </Text>
            </View>

            {cat.fields.includes('event_name') && (
              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: colors.textSecondary }]}>
                  {cat.id === 'sports' ? 'Match / Tournament Name'
                    : cat.id === 'politics' ? 'Election / Political Event'
                    : cat.id === 'war' ? 'Conflict / War / Geopolitical Event'
                    : cat.id === 'markets' ? 'Event / Market Phase'
                    : 'Event Name'}
                </Text>
                <TextInput
                  style={[styles.input, { backgroundColor: isDark ? '#1e293b' : '#f1f5f9', color: colors.text, borderColor: isDark ? '#334155' : '#e2e8f0' }]}
                  placeholder={
                    cat.id === 'sports'
                      ? 'e.g. ICC World Cup Final'
                      : cat.id === 'politics'
                        ? 'e.g. US Presidential Election 2024'
                        : cat.id === 'war'
                          ? 'e.g. US-Israel-Russia Conflict'
                          : cat.id === 'markets'
                            ? 'e.g. Interest Rate Decision, Bull Run Phase'
                            : 'e.g. Solar Eclipse in April, Olympics Opening Ceremony'
                  }
                  placeholderTextColor={colors.textTertiary}
                  value={formData.event_name}
                  onChangeText={(text) => setFormData({...formData, event_name: text})}
                />
              </View>
            )}

            {cat.fields.includes('entities') && (
              cat.id === 'sports' ? (
                <View style={styles.inputGroup}>
                  <Text style={[styles.label, { color: colors.textSecondary }]}>Teams (countries)</Text>
                  
                  <TouchableOpacity 
                    onPress={() => { setCountryPickerTarget('teamA'); setShowCountryPicker(true); }}
                    style={[styles.input, { backgroundColor: isDark ? '#1e293b' : '#f1f5f9', borderColor: isDark ? '#334155' : '#e2e8f0', justifyContent: 'center', marginBottom: 10 }]}
                  >
                    <Text style={{ color: colors.text }}>Team A: {formData.teamACountry.name}</Text>
                  </TouchableOpacity>

                  <TouchableOpacity 
                    onPress={() => { setCountryPickerTarget('teamB'); setShowCountryPicker(true); }}
                    style={[styles.input, { backgroundColor: isDark ? '#1e293b' : '#f1f5f9', borderColor: isDark ? '#334155' : '#e2e8f0', justifyContent: 'center' }]}
                  >
                    <Text style={{ color: colors.text }}>Team B: {formData.teamBCountry.name}</Text>
                  </TouchableOpacity>

                  <Text style={[styles.helperText, { color: colors.textTertiary }]}>
                    These should be the countries / national teams (e.g. India vs New Zealand). Their national charts and dashas will be compared.
                  </Text>
                </View>
              ) : (
                <View style={styles.inputGroup}>
                  <Text style={[styles.label, { color: colors.textSecondary }]}>
                    {cat.id === 'markets'
                      ? 'Involved Nations (MANDATORY)'
                      : cat.id === 'politics'
                        ? 'Involved Nations (MANDATORY)'
                        : cat.id === 'war'
                          ? 'Nations Involved in Conflict (MANDATORY)'
                          : 'Involved Nations / Regions'}
                  </Text>
                  
                  {/* Selected Nations Chips Container */}
                  <View style={[styles.entityChipsContainer, { backgroundColor: isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)' }]}>
                    <View style={styles.entityChips}>
                      {formData.selectedEntities.map((ent) => (
                        <TouchableOpacity 
                          key={ent.name}
                          onPress={() => {
                            setFormData({
                              ...formData,
                              selectedEntities: formData.selectedEntities.filter(e => e.name !== ent.name)
                            });
                          }}
                          style={[styles.entityChip, { backgroundColor: colors.primary + '20', borderColor: colors.primary }]}
                        >
                          <Text style={[styles.entityChipText, { color: colors.text }]}>{ent.name}</Text>
                          <Ionicons name="close-circle" size={18} color={colors.primary} />
                        </TouchableOpacity>
                      ))}
                      <TouchableOpacity 
                        onPress={() => { setCountryPickerTarget('multi'); setShowCountryPicker(true); }}
                        style={[styles.addEntityButton, { borderColor: colors.primary, backgroundColor: isDark ? '#1e293b' : '#fff' }]}
                      >
                        <Ionicons name="add-circle" size={20} color={colors.primary} />
                        <Text style={[styles.addEntityText, { color: colors.primary }]}>Add Involved Nation</Text>
                      </TouchableOpacity>
                    </View>
                  </View>

                  <Text style={[styles.label, { color: colors.textSecondary, marginTop: 15 }]}>
                    Specific Alliances / Blocs / Non-Nation Groups (optional)
                  </Text>
                  <TextInput
                    style={[styles.input, { backgroundColor: isDark ? '#1e293b' : '#f1f5f9', color: colors.text, borderColor: isDark ? '#334155' : '#e2e8f0' }]}
                    placeholder={
                      cat.id === 'markets'
                        ? 'e.g. NIFTY 50, Bank Nifty, S&P 500, Gold'
                        : cat.id === 'politics'
                          ? 'e.g. NATO, EU, G7, BRICS'
                          : cat.id === 'war'
                            ? 'e.g. NATO, EU, Wagner Group'
                            : 'e.g. Global Tech sector'
                    }
                    placeholderTextColor={colors.textTertiary}
                    value={formData.entities}
                    onChangeText={(text) => setFormData({...formData, entities: text})}
                    autoCorrect={false}
                    autoCapitalize="none"
                  />
                  <Text style={[styles.helperText, { color: colors.textTertiary }]}>
                    {cat.id === 'markets'
                      ? 'Pick the specific nations involved in these markets. Their national charts and dashas will be analyzed.'
                      : cat.id === 'politics'
                        ? 'Select the involved nations to load their specific astrological data.'
                        : cat.id === 'war'
                          ? 'MANDATORY: Add every nation involved in this conflict. We need their national charts for a precise prediction.'
                          : 'Select nations involved in this world event.'}
                  </Text>
                </View>
              )
            )}

            {cat.fields.includes('event_date') && (
              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: colors.textSecondary }]}>Date</Text>
                <TouchableOpacity 
                  onPress={() => setShowDatePicker(true)}
                  style={[styles.input, { backgroundColor: isDark ? '#1e293b' : '#f1f5f9', borderColor: isDark ? '#334155' : '#e2e8f0', justifyContent: 'center' }]}
                >
                  <Text style={{ color: colors.text }}>{formData.event_date.toDateString()}</Text>
                </TouchableOpacity>
                {showDatePicker && (
                  <DateTimePicker
                    value={formData.event_date}
                    mode="date"
                    display="default"
                    onChange={(event, date) => {
                      setShowDatePicker(false);
                      if (date) setFormData({...formData, event_date: date});
                    }}
                  />
                )}
              </View>
            )}

            {cat.fields.includes('event_time') && (
              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: colors.textSecondary }]}>Start Time (Approx)</Text>
                <TouchableOpacity 
                  onPress={() => setShowTimePicker(true)}
                  style={[styles.input, { backgroundColor: isDark ? '#1e293b' : '#f1f5f9', borderColor: isDark ? '#334155' : '#e2e8f0', justifyContent: 'center' }]}
                >
                  {(() => {
                    const hours = String(formData.event_time.getHours()).padStart(2, '0');
                    const minutes = String(formData.event_time.getMinutes()).padStart(2, '0');
                    return (
                      <Text style={{ color: colors.text }}>
                        {hours}:{minutes}
                      </Text>
                    );
                  })()}
                </TouchableOpacity>
                {showTimePicker && (
                  <DateTimePicker
                    value={formData.event_time}
                    mode="time"
                    display="default"
                    onChange={(event, time) => {
                      setShowTimePicker(false);
                      if (time) setFormData({...formData, event_time: time});
                    }}
                  />
                )}
              </View>
            )}

            {cat.fields.includes('period') && (
              <View style={styles.inputGroup}>
                <Text style={[styles.label, { color: colors.textSecondary }]}>Timeframe</Text>
                <View style={styles.periodButtons}>
                  {['Today', 'This Week', 'This Month', 'This Year'].map((p) => (
                    <TouchableOpacity
                      key={p}
                      onPress={() => setFormData({...formData, period: p})}
                      style={[
                        styles.periodButton, 
                        { backgroundColor: formData.period === p ? colors.primary : (isDark ? '#1e293b' : '#f1f5f9') }
                      ]}
                    >
                      <Text style={[styles.periodText, { color: formData.period === p ? '#fff' : colors.textSecondary }]}>{p}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}

            <TouchableOpacity
              onPress={handleStartAnalysis}
              style={styles.startButton}
            >
              <LinearGradient
                colors={[colors.primary, colors.secondary]}
                style={styles.startGradient}
              >
                <Text style={styles.startText}>Analyze Astrologically</Text>
                <Ionicons name="sparkles" size={20} color="#fff" />
              </LinearGradient>
            </TouchableOpacity>

            <View style={styles.proTip}>
              <Ionicons name="information-circle-outline" size={20} color={colors.primary} />
              <Text style={[styles.proTipText, { color: colors.textSecondary }]}>
                Elite analysis includes Dual-Chart Comparison, Match-Start Panchang, and Geodetic Risk Assessment.
              </Text>
            </View>
          </Animated.View>
        </ScrollView>
      </KeyboardAvoidingView>
    );
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle={isDark ? "light-content" : "dark-content"} />
      <LinearGradient 
        colors={isDark ? ['#020617', '#0f172a'] : ['#f8fafc', '#f1f5f9']} 
        style={styles.flex1}
      >
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity 
              onPress={() => selectedCategory ? setSelectedCategory(null) : navigation.goBack()}
              style={styles.backButton}
            >
              <Ionicons name="arrow-back" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>
              {selectedCategory ? 'Event Details' : 'Global Markets & Events'}
            </Text>
            <View style={styles.creditBadge}>
              <Text style={styles.creditText}>💳 {credits}</Text>
            </View>
          </View>

          {selectedCategory ? renderForm() : renderCategoryList()}
        </SafeAreaView>

        {/* Country Picker Modal */}
        <Modal
          visible={showCountryPicker}
          animationType="slide"
          transparent={true}
        >
          <View style={[styles.modalOverlay, { backgroundColor: isDark ? 'rgba(0,0,0,0.8)' : 'rgba(0,0,0,0.5)' }]}>
            <View style={[styles.modalContent, { backgroundColor: colors.surface }]}>
              <View style={styles.modalHeader}>
                <Text style={[styles.modalTitle, { color: colors.text }]}>
                  {countryPickerTarget === 'multi' ? 'Add Nations' : 'Select Country'}
                </Text>
                <TouchableOpacity onPress={() => { setShowCountryPicker(false); setCountrySearch(''); }}>
                  <Text style={[styles.doneText, { color: colors.primary }]}>{countryPickerTarget === 'multi' ? 'Done' : ''}</Text>
                  <Ionicons name="close" size={24} color={colors.text} />
                </TouchableOpacity>
              </View>
              
              <View style={[styles.searchBar, { backgroundColor: isDark ? '#1e293b' : '#f1f5f9' }]}>
                <Ionicons name="search" size={20} color={colors.textTertiary} />
                <TextInput
                  style={[styles.searchInput, { color: colors.text }]}
                  placeholder="Search country..."
                  placeholderTextColor={colors.textTertiary}
                  value={countrySearch}
                  onChangeText={setCountrySearch}
                />
              </View>

              <FlatList
                data={COUNTRIES.filter(c => c.name.toLowerCase().includes(countrySearch.toLowerCase()))}
                keyExtractor={(item) => item.name}
                renderItem={({ item }) => {
                  let isSelected = false;
                  if (countryPickerTarget === 'teamA') {
                    isSelected = formData.teamACountry.name === item.name;
                  } else if (countryPickerTarget === 'teamB') {
                    isSelected = formData.teamBCountry.name === item.name;
                  } else if (countryPickerTarget === 'multi') {
                    isSelected = formData.selectedEntities.some(e => e.name === item.name);
                  } else {
                    isSelected = formData.country.name === item.name;
                  }

                  return (
                    <TouchableOpacity
                      style={[styles.countryItem, { borderBottomColor: isDark ? '#1e293b' : '#f1f5f9' }]}
                      onPress={() => {
                        if (countryPickerTarget === 'teamA') {
                          setFormData({ ...formData, teamACountry: item });
                        } else if (countryPickerTarget === 'teamB') {
                          setFormData({ ...formData, teamBCountry: item });
                        } else if (countryPickerTarget === 'multi') {
                          // Toggle selection for multi
                          const isAlreadySelected = formData.selectedEntities.some(e => e.name === item.name);
                          if (isAlreadySelected) {
                            setFormData({
                              ...formData,
                              selectedEntities: formData.selectedEntities.filter(e => e.name !== item.name)
                            });
                          } else {
                            setFormData({
                              ...formData,
                              selectedEntities: [...formData.selectedEntities, item]
                            });
                          }
                          return; // Don't close modal for multi-select
                        } else {
                          setFormData({ ...formData, country: item });
                        }
                        setShowCountryPicker(false);
                        setCountrySearch('');
                      }}
                    >
                      <Text style={[styles.countryText, { color: colors.text }]}>{item.name}</Text>
                      {isSelected && (
                        <Ionicons name="checkmark" size={20} color={colors.primary} />
                      )}
                    </TouchableOpacity>
                  );
                }}
              />
            </View>
          </View>
        </Modal>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  flex1: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
  },
  creditBadge: {
    backgroundColor: 'rgba(245, 158, 11, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  creditText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#D97706',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  heroSection: {
    marginTop: 20,
    marginBottom: 30,
    alignItems: 'center',
  },
  heroTitle: {
    fontSize: 28,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 8,
  },
  heroSubtitle: {
    fontSize: 15,
    textAlign: 'center',
    paddingHorizontal: 20,
    lineHeight: 22,
  },
  categoryGrid: {
    gap: 16,
  },
  categoryCard: {
    borderRadius: 20,
    overflow: 'hidden',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
  },
  cardGradient: {
    padding: 20,
    borderWidth: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  iconCircle: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 24,
  },
  catTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 6,
  },
  catDesc: {
    fontSize: 14,
    lineHeight: 20,
  },
  formContainer: {
    marginTop: 10,
  },
  formHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 25,
    backgroundColor: 'rgba(255,255,255,0.05)',
    padding: 15,
    borderRadius: 15,
  },
  smallIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  smallIconText: {
    fontSize: 20,
  },
  formTitle: {
    fontSize: 22,
    fontWeight: '700',
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    marginLeft: 4,
  },
  input: {
    height: 55,
    borderRadius: 15,
    paddingHorizontal: 16,
    fontSize: 16,
    borderWidth: 1,
  },
  helperText: {
    marginTop: 6,
    fontSize: 12,
  },
  periodButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  periodButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    minWidth: '47%',
    alignItems: 'center',
  },
  periodText: {
    fontSize: 14,
    fontWeight: '600',
  },
  startButton: {
    marginTop: 20,
    borderRadius: 20,
    overflow: 'hidden',
    elevation: 5,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 15,
  },
  startGradient: {
    flexDirection: 'row',
    height: 65,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 10,
  },
  startText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '800',
  },
  modalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  modalContent: {
    height: '80%',
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 15,
    height: 50,
    borderRadius: 15,
    marginBottom: 20,
  },
  searchInput: {
    flex: 1,
    marginLeft: 10,
    fontSize: 16,
  },
  countryItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
  },
  countryText: {
    fontSize: 16,
    fontWeight: '500',
  },
  entityChipsContainer: {
    padding: 12,
    borderRadius: 15,
    minHeight: 60,
    marginBottom: 5,
  },
  entityChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  entityChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    gap: 6,
  },
  entityChipText: {
    fontSize: 14,
    fontWeight: '600',
  },
  addEntityButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderStyle: 'dashed',
    gap: 4,
  },
  addEntityText: {
    fontSize: 14,
    fontWeight: '600',
  },
  doneText: {
    fontSize: 16,
    fontWeight: '700',
    marginRight: 10,
  },
  proTip: {
    flexDirection: 'row',
    marginTop: 25,
    backgroundColor: 'rgba(255,107,53,0.05)',
    padding: 15,
    borderRadius: 12,
    alignItems: 'flex-start',
    gap: 10,
  },
  proTipText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
    fontStyle: 'italic',
  },
});
