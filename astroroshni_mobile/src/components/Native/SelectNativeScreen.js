import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  Alert,
  Modal,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { formatBirthDateForDisplay } from '../../utils/birthDateUtils';
import { storage } from '../../services/storage';
import { chartAPI } from '../../services/api';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { trackAstrologyEvent } from '../../utils/analytics';
import { DISPLAY_FONT_FAMILY } from '../../theme/tokens';

const FAMILY_RELATION_ORDER = ['self', 'father', 'mother', 'spouse', 'child', 'sibling', 'friend', 'shared', 'other'];

const getChartId = (profile) => {
  const value = profile?.id
    ?? profile?._id
    ?? profile?.birth_chart_id
    ?? profile?.birthChartId
    ?? profile?.chart_id;
  if (value == null || value === '' || String(value).toLowerCase() === 'self') return null;
  return String(value);
};

const normalizeBirthDate = (value) => {
  const raw = String(value || '').trim();
  const isoDate = raw.match(/\d{4}-\d{2}-\d{2}/)?.[0];
  return isoDate || raw.toLowerCase();
};

const normalizeBirthTime = (value) => {
  const raw = String(value || '').trim();
  const time = raw.match(/(?:T|^)(\d{2}:\d{2}(?::\d{2})?)/)?.[1];
  return (time || raw).slice(0, 8).toLowerCase();
};

// IDs are authoritative. The fingerprint keeps older/local saved charts working
// without ever treating a display name as a unique chart identity.
const getChartSelectionKey = (profile) => {
  const id = getChartId(profile);
  if (id) return `id:${id}`;

  if (!profile) return null;
  const latitude = profile.latitude ?? profile.lat ?? '';
  const longitude = profile.longitude ?? profile.lon ?? profile.lng ?? '';
  return [
    'birth',
    String(profile.name || '').trim().toLowerCase(),
    normalizeBirthDate(profile.date ?? profile.birth_date),
    normalizeBirthTime(profile.time ?? profile.birth_time),
    String(profile.place || profile.birth_place || '').trim().toLowerCase(),
    String(latitude),
    String(longitude),
  ].join('|');
};

const getRelationDisplay = (profile) => {
  const relation = String(profile?.relation || 'other').toLowerCase();
  if (profile?.relation_label) return profile.relation_label;
  if (relation === 'self') return 'You';
  if (relation === 'father') return 'Father';
  if (relation === 'mother') return 'Mother';
  if (relation === 'spouse') return 'Spouse / Partner';
  if (relation === 'child') {
    const order = Number(profile?.relation_order);
    if (order === 1) return '1st child';
    if (order === 2) return '2nd child';
    if (order === 3) return '3rd child';
    return 'Child';
  }
  if (relation === 'sibling') {
    const order = Number(profile?.relation_order);
    if (order < 0) return 'Elder sibling';
    if (order > 0) return 'Younger sibling';
    return 'Sibling';
  }
  if (relation === 'friend') return 'Friend';
  if (relation === 'colleague') return 'Colleague';
  if (relation === 'shared') return 'Shared';
  return 'Other';
};

const getRelationGroupTitle = (relation) => {
  if (relation === 'self') return 'You';
  if (relation === 'father' || relation === 'mother') return 'Parents';
  if (relation === 'spouse') return 'Partner';
  if (relation === 'child') return 'Children';
  if (relation === 'sibling') return 'Siblings';
  if (relation === 'friend') return 'Friends';
  if (relation === 'shared') return 'Shared charts';
  return 'Other charts';
};

const groupProfilesByRelation = (profiles) => {
  const groups = new Map();
  profiles.forEach((profile) => {
    const relation = String(profile?.relation || 'other').toLowerCase();
    const groupKey = relation === 'father' || relation === 'mother' ? 'parents' : relation;
    if (!groups.has(groupKey)) {
      groups.set(groupKey, {
        key: groupKey,
        title: relation === 'father' || relation === 'mother' ? 'Parents' : getRelationGroupTitle(relation),
        sort: FAMILY_RELATION_ORDER.indexOf(relation) >= 0 ? FAMILY_RELATION_ORDER.indexOf(relation) : FAMILY_RELATION_ORDER.length,
        items: [],
      });
    }
    groups.get(groupKey).items.push(profile);
  });
  return Array.from(groups.values()).sort((a, b) => a.sort - b.sort);
};

const ProfileCard = ({ profile, selectedProfileKey, onSelect, onMore, getZodiacSign, colors }) => {
  const selected = selectedProfileKey === getChartSelectionKey(profile);
  const cardBackground = selected ? colors.selectionSurface : colors.surface;
  const primaryText = selected ? colors.selectionText : colors.text;
  const secondaryText = selected ? colors.selectionTextMuted : colors.textSecondary;

  return (
    <View style={styles.profileWrapper}>
      <View
        style={[
          styles.profileCard,
          {
            backgroundColor: cardBackground,
            borderColor: selected ? colors.accent : colors.cardBorder,
          },
        ]}
      >
        <TouchableOpacity
          style={styles.cardTouchable}
          onPress={() => onSelect(profile)}
          activeOpacity={0.86}
          accessibilityRole="button"
          accessibilityLabel={`Use ${profile.name}'s birth chart`}
        >
          <View style={styles.profileInfo}>
            <View
              style={[
                styles.zodiacIcon,
                {
                  backgroundColor: selected ? colors.selectionControl : colors.accentSoft,
                  borderColor: selected ? colors.selectionBorder : colors.accent,
                },
              ]}
            >
              <Text style={[styles.zodiacText, { color: selected ? colors.accent : colors.onAccent }]}>{getZodiacSign(profile)}</Text>
            </View>
            <View style={styles.profileDetails}>
              <Text style={[styles.relationKicker, { color: selected ? colors.selectionText : colors.primary }]}>
                {getRelationDisplay(profile)}
              </Text>
              <View style={styles.nameRow}>
                <Text style={[styles.profileName, { color: primaryText }]} numberOfLines={1}>{profile.name}</Text>
                {profile.isSelf ? (
                  <View style={[styles.selfBadge, { backgroundColor: selected ? colors.accentSoft : colors.surfaceMuted }]}>
                    <Text style={[styles.selfBadgeText, { color: selected ? colors.onAccent : colors.textSecondary }]}>YOU</Text>
                  </View>
                ) : null}
              </View>
              <View style={styles.profileMetaRow}>
                <Ionicons name="calendar-clear-outline" size={13} color={secondaryText} />
                <Text style={[styles.profileDate, { color: secondaryText }]} numberOfLines={1}>
                  {formatBirthDateForDisplay(profile.date, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })} · {profile.time}
                </Text>
              </View>
              {profile.place ? (
                <View style={styles.profileMetaRow}>
                  <Ionicons name="location-outline" size={13} color={secondaryText} />
                  <Text style={[styles.profilePlace, { color: secondaryText }]} numberOfLines={1}>{profile.place}</Text>
                </View>
              ) : null}
            </View>
            <View style={styles.selectionMark}>
              {selected ? (
                <View style={[styles.activeCheck, { backgroundColor: colors.accentSoft }]}>
                  <Ionicons name="checkmark" size={16} color={colors.onAccent} />
                </View>
              ) : (
                <Ionicons name="chevron-forward" size={18} color={colors.textTertiary} />
              )}
            </View>
          </View>
        </TouchableOpacity>
        <TouchableOpacity
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          onPress={() => onMore(profile)}
          style={[styles.menuButton, { backgroundColor: selected ? colors.selectionControl : colors.surfaceMuted }]}
          accessibilityRole="button"
          accessibilityLabel={`More options for ${profile.name}`}
        >
          <Ionicons name="ellipsis-horizontal" size={18} color={secondaryText} />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const normalizeGender = (value) => {
  const normalized = String(value || '').trim().toLowerCase();
  if (normalized.startsWith('m')) return 'male';
  if (normalized.startsWith('f')) return 'female';
  return normalized;
};

const shouldShowForGenderFilter = (profile, genderFilter) => {
  const filter = normalizeGender(genderFilter);
  if (!filter) return true;

  const gender = normalizeGender(profile?.gender);
  if (filter === 'male') return gender !== 'female';
  if (filter === 'female') return gender !== 'male';
  return true;
};

export default function SelectNativeScreen({ navigation, route }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const [profiles, setProfiles] = useState([]);
  const [selectedProfileKey, setSelectedProfileKey] = useState(null);
  const [listLoading, setListLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);
  const [totalCharts, setTotalCharts] = useState(0);
  const [showBottomSheet, setShowBottomSheet] = useState(false);
  const [selectedProfileForMenu, setSelectedProfileForMenu] = useState(null);
  const [showShareModal, setShowShareModal] = useState(false);
  const [localSearchQuery, setLocalSearchQuery] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [sharing, setSharing] = useState(false);
  const shareSearchDebounceRef = useRef(null);
  const fromProfile = route.params?.fromProfile;
  const returnTo = route.params?.returnTo;
  const selectorTarget = route.params?.selectorTarget;
  const nativeGenderFilter = route.params?.nativeGenderFilter;
  const refreshAt = route.params?.refreshAt;
  const returnParams = route.params?.returnParams || {};

  useFocusEffect(
    React.useCallback(() => {
      loadProfiles({ reset: true });
    }, [nativeGenderFilter, refreshAt])
  );

  const PAGE_SIZE = 10;

  const loadProfiles = async ({ reset = false, search = localSearchQuery } = {}) => {
    try {
      if (reset) {
        setListLoading(true);
      } else {
        setLoadingMore(true);
      }
      const currentNative = await storage.getBirthDetails();
      const authToken = await storage.getAuthToken();

      // Guests: local AsyncStorage profiles only (no server list).
      if (!authToken) {
        const savedProfiles = await storage.getBirthProfiles();
        const q = String(search || '').trim().toLowerCase();
        const localList = (savedProfiles || []).filter((profile) => {
          if (!shouldShowForGenderFilter(profile, nativeGenderFilter)) return false;
          if (!q) return true;
          return String(profile.name || '').toLowerCase().includes(q);
        });
        setProfiles(localList);
        setOffset(localList.length);
        setHasMore(false);
        setTotalCharts(localList.length);
        if (currentNative) {
          setSelectedProfileKey(getChartSelectionKey(currentNative));
        }
        return;
      }
      
      // Fetch saved charts from API
      const { chartAPI } = require('../../services/api');
      const nextOffset = reset ? 0 : offset;
      const fetchLimit = nativeGenderFilter ? 50 : PAGE_SIZE;
      const response = await chartAPI.getExistingCharts(search.trim(), fetchLimit, nextOffset);
      const apiCharts = response.data.charts || [];
      
      const profileList = [];
      
      // Add charts from API
      apiCharts.forEach((chart) => {
        const rel = String(chart.relation ?? '')
          .trim()
          .toLowerCase();
        profileList.push({
          id: chart.id || chart._id || chart.birth_chart_id,
          name: chart.name,
          date: chart.date,
          time: chart.time,
          place: chart.place,
          latitude: chart.latitude,
          longitude: chart.longitude,
          gender: chart.gender,
          relation: rel || 'other',
          relation_order: chart.relation_order ?? null,
          relation_side: chart.relation_side || '',
          relation_label: chart.relation_label || '',
          is_family_member: !!chart.is_family_member,
          isSelf: rel === 'self',
          ascendantSign: chart.ascendant_sign,
          ascendantSignName: chart.ascendant_sign_name,
        });
      });
      
      const filteredProfiles = profileList.filter((profile) => shouldShowForGenderFilter(profile, nativeGenderFilter));

      setProfiles(prev => (reset ? filteredProfiles : [...prev, ...filteredProfiles]));
      setOffset(nextOffset + apiCharts.length);
      setHasMore(!!response.data?.has_more);
      setTotalCharts(nativeGenderFilter ? null : (response.data?.total || 0));
      
      if (currentNative) {
        setSelectedProfileKey(getChartSelectionKey(currentNative));
      }
    } catch (error) {
      // Fallback to local storage if API fails
      if (reset) {
        const savedProfiles = await storage.getBirthProfiles();
        const filteredProfiles = (savedProfiles || []).filter((profile) => shouldShowForGenderFilter(profile, nativeGenderFilter));
        setProfiles(filteredProfiles);
        setOffset(savedProfiles.length);
        setHasMore(false);
        setTotalCharts(filteredProfiles.length);
      }
    } finally {
      setListLoading(false);
      setLoadingMore(false);
    }
  };

  const handleLocalSearchChange = (text) => {
    setLocalSearchQuery(text);
    const q = text.trim();
    if (q.length >= 2) {
      trackAstrologyEvent.search(q, 'birth_chart');
    }
    loadProfiles({ reset: true, search: text });
  };

  const syncSelfBirthDetails = async () => {
    try {
      const token = await storage.getAuthToken();
      if (!token) return;
      const { authAPI } = require('../../services/api');
      const response = await authAPI.getSelfBirthChart();
      if (response?.data?.has_self_chart) {
        const bd = {
          ...response.data,
          id: response.data.birth_chart_id, // normalize id field
        };
        await storage.setBirthDetails(bd);
      } else {
        // No chart marked as self after deletion: clear selection
        await storage.clearBirthDetails();
      }
    } catch (e) {
      // Non-fatal; UI will fall back to whatever is in storage/profiles.
    }
  };

  const selectProfile = async (profile) => {
    try {
      // Ensure profile includes id
      const profileWithId = {
        ...profile,
        id: getChartId(profile),
      };
      
      if (fromProfile) {
        // Connect chart to profile and return to Profile screen
        const { chartAPI } = require('../../services/api');
        await chartAPI.setChartAsSelf(profileWithId.id);
        Alert.alert('Success', '✅ Chart connected to your profile!');
        navigation.navigate('Profile');
      } else if (returnTo === 'ChildbirthPlanner') {
        // Set as mother's profile for childbirth planner
        await storage.setBirthDetails(profileWithId);
        setSelectedProfileKey(getChartSelectionKey(profileWithId));
        navigation.navigate('ChildbirthPlanner');
      } else if (returnTo === 'KarmaAnalysis') {
        // Return to Karma Analysis with selected chart
        await storage.setBirthDetails(profileWithId);
        setSelectedProfileKey(getChartSelectionKey(profileWithId));
        navigation.navigate('KarmaAnalysis', { chartId: profileWithId.id });
      } else if (returnTo === 'KP') {
        // Return to KP Screen with selected chart
        await storage.setBirthDetails(profileWithId);
        setSelectedProfileKey(getChartSelectionKey(profileWithId));
        navigation.navigate('KPSystem', { birthDetails: profileWithId });
      } else if (returnTo === 'Yogas') {
        await storage.setBirthDetails(profileWithId);
        setSelectedProfileKey(getChartSelectionKey(profileWithId));
        navigation.navigate('Yogas', { birthDetails: profileWithId });
      } else if (returnTo) {
        // Return to the screen that required a native (Chart, Shadbala, SadeSati, etc.)
        await storage.setBirthDetails(profileWithId);
        setSelectedProfileKey(getChartSelectionKey(profileWithId));
        navigation.navigate(returnTo, {
          ...returnParams,
          birthData: profileWithId,
          birthDetails: profileWithId,
          birthChartId: profileWithId.id,
          selectorTarget,
        });
      } else {
        await storage.setBirthDetails(profileWithId);
        setSelectedProfileKey(getChartSelectionKey(profileWithId));
        navigation.navigate('Home', { resetToGreeting: true, stayOnGreeting: true });
      }
    } catch (error) {
      let errorMessage = '❌ Unable to select profile. Please try again.';
      
      if (error.message?.includes('Network Error')) {
        errorMessage = '❌ Connection failed. Please check your internet.';
      }
      
      Alert.alert('Error', errorMessage);
    }
  };

  const handleEdit = (profile) => {
    console.log('✏️ Edit button pressed for:', profile.name);
    const profileData = {
      ...profile,
      date: profile.date.includes('T') ? profile.date.split('T')[0] : profile.date,
      time: profile.time.includes('T') ? new Date(profile.time).toTimeString().slice(0, 5) : profile.time,
    };
    console.log('📝 Navigating to BirthForm with data:', profileData);
    navigation.navigate('BirthForm', { editProfile: profileData });
  };

  const handleDelete = (profile) => {
    Alert.alert(
      'Delete Profile',
      `Are you sure you want to delete ${profile.name}'s profile?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Delete', 
          style: 'destructive',
          onPress: async () => {
            try {
              const token = await storage.getAuthToken();
              if (token && profile.id && profile.id !== 'self' && !String(profile.id).startsWith('guest_')) {
                await chartAPI.deleteChart(profile.id);
              }
              await storage.removeBirthProfile(profile.name);
              // Prevent stale selected chart: sync "self" from backend.
              await syncSelfBirthDetails();
              loadProfiles({ reset: true });
            } catch (error) {
              Alert.alert('Error', 'Failed to delete profile');
            }
          }
        }
      ]
    );
  };

  const handleConnectToProfile = async (profile) => {
    try {
      const token = await storage.getAuthToken();
      if (!token || String(profile.id || '').startsWith('guest_')) {
        Alert.alert(
          'Sign in required',
          'Sign in to connect this chart to your account profile.',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Sign in', onPress: () => navigation.navigate('Login') },
          ],
        );
        return;
      }
      await chartAPI.setChartAsSelf(profile.id);
      Alert.alert('Success', '✅ Chart connected to your profile!');
      // Must reset list: default loadProfiles() appends next page and never refetches row[0..n], so "You" badge would stay stale.
      loadProfiles({ reset: true });
    } catch (error) {
      let errorMessage = '❌ Something went wrong. Please try again.';
      
      if (error.message?.includes('Network Error') || error.code === 'NETWORK_ERROR') {
        errorMessage = '❌ Connection failed. Please check your internet.';
      } else if (error.response?.status >= 500) {
        errorMessage = '❌ Server error. Please try again later.';
      } else if (error.response?.data?.detail) {
        errorMessage = `❌ ${error.response.data.detail}`;
      }
      
      Alert.alert('Error', errorMessage);
    }
  };

  const handleShare = async (profile) => {
    console.log('Opening share modal for profile:', profile);
    setShowShareModal(true);
  };

  const searchUsers = useCallback(async (query) => {
    if (query.length < 4) {
      setSearchResults([]);
      setSearching(false);
      return;
    }

    setSearching(true);
    try {
      const response = await chartAPI.searchUsers(query);
      const users = response.data?.users || [];
      setSearchResults(users);
      trackAstrologyEvent.search(query, 'user_share');
    } catch (error) {
      console.log('Error response:', error.response);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  /** Debounced: typing was firing API + setState every character → re-renders + Android keyboard resize = visible flicker */
  const onShareSearchChange = useCallback(
    (text) => {
      setSearchQuery(text);
      if (text.length < 4) {
        if (shareSearchDebounceRef.current) {
          clearTimeout(shareSearchDebounceRef.current);
          shareSearchDebounceRef.current = null;
        }
        setSearchResults([]);
        setSearching(false);
        return;
      }
      if (shareSearchDebounceRef.current) {
        clearTimeout(shareSearchDebounceRef.current);
      }
      shareSearchDebounceRef.current = setTimeout(() => {
        shareSearchDebounceRef.current = null;
        searchUsers(text);
      }, 350);
    },
    [searchUsers]
  );

  const handleShareWithUser = async (targetUser) => {
    if (!selectedProfileForMenu) {
      console.log('No profile selected for sharing');
      return;
    }
    
    console.log('Sharing chart:', selectedProfileForMenu.id, 'with user:', targetUser.userid);
    setSharing(true);
    try {
      const response = await chartAPI.shareChart(selectedProfileForMenu.id, targetUser.userid);
      // console.log('Share response:', response);
      Alert.alert('Success', `Chart shared with ${targetUser.name}`);
      setShowShareModal(false);
      setSearchQuery('');
      setSearchResults([]);
    } catch (error) {
      console.log('Share error:', error);
      console.log('Error response:', error.response);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to share chart. Please try again.');
    } finally {
      setSharing(false);
    }
  };

  const handleMore = (profile) => {
    setSelectedProfileForMenu(profile);
    setShowBottomSheet(true);
  };

  const closeBottomSheet = () => {
    setShowBottomSheet(false);
    // Don't clear selectedProfileForMenu here - keep it for share modal
  };

  const handleHeaderBack = () => {
    if (returnTo === 'Home') {
      navigation.navigate(
        'Home',
        returnParams.returnToChat
          ? returnParams
          : { resetToGreeting: true, stayOnGreeting: true }
      );
      return;
    }
    if (returnTo) {
      navigation.navigate(returnTo, returnParams);
      return;
    }
    navigation.goBack();
  };

  const getZodiacSign = (profile) => {
    const icons = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓'];
    const signValue = profile?.ascendantSign ?? profile?.ascendant_sign ?? profile?.lagnaSign ?? profile?.lagna_sign;
    if (typeof signValue === 'number' && signValue >= 0 && signValue < icons.length) {
      return icons[signValue];
    }
    const numericSign = Number(signValue);
    if (Number.isInteger(numericSign) && numericSign >= 0 && numericSign < icons.length) {
      return icons[numericSign];
    }
    if (Number.isInteger(numericSign) && numericSign >= 1 && numericSign <= icons.length) {
      return icons[numericSign - 1];
    }
    const signName = String(profile?.ascendantSignName || profile?.ascendant_sign_name || '').trim().toLowerCase();
    const signIndex = ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo', 'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'].indexOf(signName);
    return signIndex >= 0 ? icons[signIndex] : '✦';
  };

  const selectionPrompt = returnTo === 'ChildbirthPlanner'
    ? 'Select the mother’s chart'
    : returnTo === 'KarmaAnalysis'
      ? t('karmaAnalysis.selectNativePrompt')
      : nativeGenderFilter === 'male'
        ? 'Choose a boy chart for Kundli matching'
        : nativeGenderFilter === 'female'
          ? 'Choose a girl chart for Kundli matching'
          : 'Choose the birth chart you want AstroRoshni to read.';

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={colors.statusBarStyle} backgroundColor={colors.background} translucent={false} />
      <View style={[styles.gradient, { backgroundColor: colors.background }]}>
        <SafeAreaView style={styles.safeArea}>
          <View style={[styles.header, { borderBottomColor: colors.cardBorder }]}>
            <TouchableOpacity onPress={handleHeaderBack} style={[styles.backButton, { backgroundColor: colors.surfaceMuted }]}>
              <Ionicons name="arrow-back" size={20} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>Birth charts</Text>
            <TouchableOpacity 
              onPress={() => navigation.navigate('BirthForm')} 
              style={[styles.addButton, { backgroundColor: colors.accentSoft }]}
            >
              <Ionicons name="add" size={18} color={colors.onAccent} />
              <Text style={[styles.addButtonText, { color: colors.onAccent }]}>New</Text>
            </TouchableOpacity>
          </View>

          <ScrollView 
            style={styles.scrollView}
            contentContainerStyle={styles.scrollContent}
            showsVerticalScrollIndicator={false}
          >
            <View style={[styles.heroCard, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
              <View style={[styles.heroOrbitLarge, { borderColor: colors.cosmicLine }]} />
              <View style={[styles.heroOrbitSmall, { borderColor: colors.cosmicLine }]} />
              <Text style={[styles.heroEyebrow, { color: colors.accent }]}>CHART LIBRARY</Text>
              <Text style={[styles.heroTitle, { color: colors.textInverse }]}>Whose sky are we reading?</Text>
              <Text style={[styles.heroSubtitle, { color: colors.textInverseMuted }]}>{selectionPrompt}</Text>
              <View style={styles.heroFooter}>
                <View style={[styles.chartCountPill, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}>
                  <Ionicons name="albums-outline" size={14} color={colors.accent} />
                  <Text style={[styles.chartCountText, { color: colors.textInverseMuted }]}>
                    {totalCharts ?? profiles.length} saved {Number(totalCharts ?? profiles.length) === 1 ? 'chart' : 'charts'}
                  </Text>
                </View>
                <Text style={[styles.heroHint, { color: colors.textInverseMuted }]}>Tap a chart to continue</Text>
              </View>
            </View>

            {(totalCharts > PAGE_SIZE || localSearchQuery.length > 0 || profiles.length > 0) && (
              <View style={[styles.localSearchContainer, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
                <Ionicons name="search" size={20} color={colors.textSecondary} style={styles.localSearchIcon} />
                <TextInput
                  style={[styles.localSearchInput, { color: colors.text }]}
                  placeholder="Search by name..."
                  placeholderTextColor={colors.textSecondary + '80'}
                  value={localSearchQuery}
                  onChangeText={handleLocalSearchChange}
                  autoCorrect={false}
                />
                {localSearchQuery.length > 0 && (
                  <TouchableOpacity onPress={() => handleLocalSearchChange('')}>
                    <Ionicons name="close-circle" size={20} color={colors.textSecondary} />
                  </TouchableOpacity>
                )}
              </View>
            )}

            {listLoading && profiles.length === 0 ? (
              <View style={[styles.inlineLoader, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
                <ActivityIndicator size="small" color={colors.primary} />
                <Text style={[styles.inlineLoaderText, { color: colors.textSecondary }]}>Preparing your chart library…</Text>
              </View>
            ) : (
              groupProfilesByRelation(profiles).map((group) => (
                <View key={group.key} style={styles.profileGroup}>
                  <View style={styles.profileGroupHeading}>
                    <Text style={[styles.profileGroupTitle, { color: colors.primary }]}>{group.title}</Text>
                    <View style={[styles.groupRule, { backgroundColor: colors.cardBorder }]} />
                  </View>
                  {group.items.map((profile, profileIndex) => (
                    <ProfileCard
                      key={`${getChartSelectionKey(profile)}:${profileIndex}`}
                      profile={profile}
                      selectedProfileKey={selectedProfileKey}
                      onSelect={selectProfile}
                      onMore={handleMore}
                      getZodiacSign={getZodiacSign}
                      colors={colors}
                    />
                  ))}
                </View>
              ))
            )}

            {hasMore && !listLoading && (
              <TouchableOpacity
                style={[styles.loadMoreButton, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
                onPress={() => loadProfiles({ reset: false })}
                disabled={loadingMore}
              >
                {loadingMore ? (
                  <ActivityIndicator size="small" color={colors.primary} />
                ) : (
                  <Text style={[styles.loadMoreText, { color: colors.text }]}>
                    {nativeGenderFilter ? 'Load more matching charts' : `Load more (${profiles.length}/${totalCharts || '?'})`}
                  </Text>
                )}
              </TouchableOpacity>
            )}

            {profiles.length === 0 && (
              <View style={styles.emptyState}>
                <View style={[styles.emptyIcon, { backgroundColor: colors.accentSoft }]}>
                  <Ionicons name="person-add-outline" size={28} color={colors.onAccent} />
                </View>
                <Text style={[styles.emptyTitle, { color: colors.text }]}>
                  {nativeGenderFilter ? 'No Matching Charts Found' : 'No Profiles Found'}
                </Text>
                <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
                  {nativeGenderFilter
                    ? 'Charts without gender are also shown here. Add a new chart or load more if you have many saved charts.'
                    : 'Add your birth details to get started'}
                </Text>
                <TouchableOpacity
                  style={[styles.addProfileButton, { backgroundColor: colors.primary }]}
                  onPress={() => navigation.navigate('BirthForm')}
                >
                  <Text style={[styles.addProfileText, { color: colors.onPrimary }]}>Create birth chart</Text>
                  <Ionicons name="arrow-forward" size={18} color={colors.onPrimary} />
                </TouchableOpacity>
              </View>
            )}
          </ScrollView>
        </SafeAreaView>
      </View>

      <Modal
        visible={showBottomSheet}
        transparent
        animationType="fade"
        onRequestClose={closeBottomSheet}
      >
        <TouchableOpacity 
          style={[styles.modalOverlay, { backgroundColor: colors.overlay }]}
          activeOpacity={1} 
          onPress={closeBottomSheet}
        >
          <View style={[styles.bottomSheet, { backgroundColor: colors.surfaceRaised || colors.surface, borderColor: colors.cardBorder }]}>
            <View style={[styles.bottomSheetHandle, { backgroundColor: colors.borderStrong }]} />
            <Text style={[styles.sheetEyebrow, { color: colors.primary }]}>CHART OPTIONS</Text>
            <Text style={[styles.bottomSheetTitle, { color: colors.text }]} numberOfLines={1}>
              {selectedProfileForMenu?.name || 'Birth chart'}
            </Text>

            <TouchableOpacity
              style={[styles.bottomSheetItem, { backgroundColor: colors.surfaceMuted }]}
              onPress={() => {
                closeBottomSheet();
                if (selectedProfileForMenu) {
                  handleEdit(selectedProfileForMenu);
                }
              }}
            >
              <View style={[styles.sheetItemIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name="pencil-outline" size={18} color={colors.onAccent} /></View>
              <Text style={[styles.bottomSheetItemText, { color: colors.text }]}>Edit birth details</Text>
              <Ionicons name="chevron-forward" size={18} color={colors.textTertiary} />
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.bottomSheetItem, { backgroundColor: colors.surfaceMuted }]}
              onPress={() => {
                closeBottomSheet();
                if (selectedProfileForMenu) {
                  handleConnectToProfile(selectedProfileForMenu);
                }
              }}
            >
              <View style={[styles.sheetItemIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name="person-outline" size={18} color={colors.onAccent} /></View>
              <Text style={[styles.bottomSheetItemText, { color: colors.text }]}>Set as my chart</Text>
              <Ionicons name="chevron-forward" size={18} color={colors.textTertiary} />
            </TouchableOpacity>

            <TouchableOpacity 
              style={[styles.bottomSheetItem, { backgroundColor: colors.surfaceMuted }]}
              onPress={() => {
                closeBottomSheet();
                if (selectedProfileForMenu) {
                  handleShare(selectedProfileForMenu);
                }
              }}
            >
              <View style={[styles.sheetItemIcon, { backgroundColor: colors.accentSoft }]}><Ionicons name="share-social-outline" size={18} color={colors.onAccent} /></View>
              <Text style={[styles.bottomSheetItemText, { color: colors.text }]}>Share chart</Text>
              <Ionicons name="chevron-forward" size={18} color={colors.textTertiary} />
            </TouchableOpacity>

            <TouchableOpacity 
              style={[styles.bottomSheetItem, { backgroundColor: colors.surfaceMuted }]}
              onPress={() => {
                closeBottomSheet();
                if (selectedProfileForMenu) {
                  handleDelete(selectedProfileForMenu);
                }
              }}
            >
              <View style={[styles.sheetItemIcon, { backgroundColor: `${colors.error}18` }]}><Ionicons name="trash-outline" size={18} color={colors.error} /></View>
              <Text style={[styles.bottomSheetItemText, { color: colors.error }]}>Delete chart</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.bottomSheetCancel}
              onPress={closeBottomSheet}
            >
              <Text style={[styles.bottomSheetCancelText, { color: colors.textSecondary }]}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>

      <Modal
        visible={showShareModal}
        transparent
        animationType="slide"
        onRequestClose={() => {
          if (shareSearchDebounceRef.current) {
            clearTimeout(shareSearchDebounceRef.current);
            shareSearchDebounceRef.current = null;
          }
          setShowShareModal(false);
          setSearchQuery('');
          setSearchResults([]);
        }}
      >
        {/* Android: avoid KeyboardAvoidingView + behavior height — fights Modal/window resize and causes full-screen flicker when focusing TextInput */}
        <KeyboardAvoidingView
          style={[styles.shareModalOverlay, { backgroundColor: colors.overlay }]}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          enabled={Platform.OS === 'ios'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 8 : 0}
        >
          <View style={[styles.shareModalContent, { backgroundColor: colors.surfaceRaised || colors.surface, borderColor: colors.cardBorder }]}>
            <View style={styles.shareModalHeader}>
              <View>
                <Text style={[styles.sheetEyebrow, { color: colors.primary }]}>PRIVATE SHARING</Text>
                <Text style={[styles.shareModalTitle, { color: colors.text }]}>Share birth chart</Text>
              </View>
              <TouchableOpacity onPress={() => {
                if (shareSearchDebounceRef.current) {
                  clearTimeout(shareSearchDebounceRef.current);
                  shareSearchDebounceRef.current = null;
                }
                setShowShareModal(false);
                setSearchQuery('');
                setSearchResults([]);
                setSelectedProfileForMenu(null);
              }}>
                <Ionicons name="close" size={24} color={colors.textSecondary} />
              </TouchableOpacity>
            </View>

            <Text style={[styles.shareModalSubtitle, { color: colors.textSecondary }]}>Search user by name or phone (min 4 characters)</Text>

            <View style={[styles.searchInputContainer, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
              <Ionicons name="search" size={20} color={colors.textTertiary} style={styles.searchIcon} />
              <TextInput
                style={[styles.searchInput, { color: colors.text }]}
                placeholder="Type name or phone number..."
                placeholderTextColor={colors.textSecondary}
                value={searchQuery}
                onChangeText={onShareSearchChange}
                autoCorrect={false}
                autoFocus
              />
              {searching && <ActivityIndicator size="small" color={colors.primary} />}
            </View>

            <View style={styles.searchResultsContainer}>
              <ScrollView
                showsVerticalScrollIndicator={false}
                style={styles.searchResultsList}
                keyboardShouldPersistTaps="handled"
                keyboardDismissMode="on-drag"
              >
                {searchQuery.length < 4 && (
                  <Text style={[styles.searchHint, { color: colors.textSecondary }]}>Type at least 4 characters to search</Text>
                )}
                
                {searchQuery.length >= 4 && searchResults.length === 0 && !searching && (
                  <Text style={[styles.noResults, { color: colors.textSecondary }]}>No users found</Text>
                )}

                {searchResults.length > 0 && searchResults.map((user) => (
                  <TouchableOpacity
                    key={user.userid}
                    style={[styles.userResultItem, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}
                    onPress={() => handleShareWithUser(user)}
                    disabled={sharing}
                  >
                    <View style={styles.userResultLeft}>
                      <View style={[styles.userAvatar, { backgroundColor: colors.accentSoft }]}>
                        <Text style={[styles.userAvatarText, { color: colors.onAccent }]}>{user.name.charAt(0).toUpperCase()}</Text>
                      </View>
                      <View>
                        <Text style={[styles.userResultName, { color: colors.text }]}>{user.name}</Text>
                        <Text style={[styles.userResultPhone, { color: colors.textSecondary }]}>****{user.phone}</Text>
                      </View>
                    </View>
                    {sharing ? (
                      <ActivityIndicator size="small" color={colors.primary} />
                    ) : (
                      <Ionicons name="arrow-forward" size={20} color={colors.textTertiary} />
                    )}
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  header: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'space-between', 
    paddingHorizontal: 18,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: { 
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center', 
    justifyContent: 'center' 
  },
  headerTitle: { 
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 20,
    fontWeight: '700',
  },
  addButton: { 
    minWidth: 66,
    height: 38,
    paddingHorizontal: 12,
    borderRadius: 19,
    flexDirection: 'row',
    gap: 5,
    alignItems: 'center', 
    justifyContent: 'center',
  },
  addButtonText: {
    fontSize: 12,
    fontWeight: '800',
  },
  scrollView: { flex: 1 },
  scrollContent: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 44,
  },
  heroCard: {
    minHeight: 220,
    borderRadius: 28,
    borderWidth: 1,
    paddingHorizontal: 22,
    paddingVertical: 24,
    marginBottom: 16,
    overflow: 'hidden',
  },
  heroOrbitLarge: {
    position: 'absolute',
    width: 220,
    height: 220,
    borderRadius: 110,
    borderWidth: 1,
    right: -84,
    top: -104,
    opacity: 0.7,
  },
  heroOrbitSmall: {
    position: 'absolute',
    width: 142,
    height: 142,
    borderRadius: 71,
    borderWidth: 1,
    right: -30,
    top: -76,
    opacity: 0.8,
  },
  heroEyebrow: {
    fontSize: 10,
    lineHeight: 14,
    fontWeight: '900',
    letterSpacing: 2,
  },
  heroTitle: {
    maxWidth: 280,
    marginTop: 12,
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 34,
    lineHeight: 38,
    fontWeight: '700',
  },
  heroSubtitle: {
    maxWidth: 300,
    marginTop: 10,
    fontSize: 14,
    lineHeight: 21,
  },
  heroFooter: {
    marginTop: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  chartCountPill: {
    minHeight: 32,
    paddingHorizontal: 11,
    borderRadius: 16,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },
  chartCountText: {
    fontSize: 10,
    fontWeight: '700',
  },
  heroHint: {
    flex: 1,
    fontSize: 10,
    textAlign: 'right',
  },
  localSearchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 18,
    borderWidth: 1,
    paddingHorizontal: 14,
    marginBottom: 20,
    height: 52,
  },
  localSearchIcon: {
    marginRight: 8,
  },
  localSearchInput: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 8,
  },
  inlineLoader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 84,
    borderRadius: 20,
    borderWidth: 1,
    marginBottom: 16,
    gap: 8,
  },
  inlineLoaderText: {
    fontSize: 14,
  },
  loadMoreButton: {
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 18,
    borderWidth: 1,
    paddingVertical: 14,
    marginTop: 4,
    marginBottom: 8,
  },
  loadMoreText: {
    fontSize: 14,
    fontWeight: '600',
  },
  profileGroup: {
    marginBottom: 8,
  },
  profileGroupHeading: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
    paddingHorizontal: 2,
  },
  profileGroupTitle: {
    fontSize: 10,
    fontWeight: '900',
    textTransform: 'uppercase',
    letterSpacing: 1.5,
  },
  groupRule: {
    flex: 1,
    height: StyleSheet.hairlineWidth,
  },
  profileWrapper: {
    position: 'relative',
    marginBottom: 12,
  },
  profileCard: {
    borderRadius: 22,
    borderWidth: 1,
    overflow: 'hidden',
  },
  cardTouchable: {
    padding: 16,
    paddingRight: 54,
  },
  modalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  bottomSheet: {
    borderWidth: 1,
    borderBottomWidth: 0,
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    paddingHorizontal: 20,
    paddingBottom: 40,
    paddingTop: 12,
  },
  bottomSheetHandle: {
    width: 40,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: 18,
  },
  sheetEyebrow: {
    fontSize: 9,
    lineHeight: 13,
    fontWeight: '900',
    letterSpacing: 1.7,
    marginBottom: 5,
  },
  bottomSheetTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 26,
    lineHeight: 31,
    fontWeight: '700',
    marginBottom: 18,
  },
  bottomSheetItem: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 58,
    paddingVertical: 10,
    paddingHorizontal: 11,
    borderRadius: 17,
    marginBottom: 9,
  },
  sheetItemIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
  },
  bottomSheetItemText: {
    flex: 1,
    fontSize: 14,
    marginLeft: 12,
    fontWeight: '700',
  },
  bottomSheetCancel: {
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  bottomSheetCancelText: {
    fontSize: 16,
    fontWeight: '600',
  },
  shareModalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  shareModalContent: {
    borderWidth: 1,
    borderBottomWidth: 0,
    borderTopLeftRadius: 30,
    borderTopRightRadius: 30,
    paddingHorizontal: 20,
    paddingBottom: 40,
    paddingTop: 20,
    maxHeight: '88%',
    marginTop: '12%',
  },
  shareModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  shareModalTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 26,
    fontWeight: '700',
  },
  shareModalSubtitle: {
    fontSize: 14,
    marginBottom: 16,
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderRadius: 17,
    paddingHorizontal: 12,
    marginBottom: 16,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 16,
  },
  searchResultsContainer: {
    minHeight: 160,
    maxHeight: 320,
  },
  searchResultsList: {
    flexGrow: 1,
  },
  searchHint: {
    textAlign: 'center',
    fontSize: 14,
    marginTop: 20,
  },
  noResults: {
    textAlign: 'center',
    fontSize: 14,
    marginTop: 20,
  },
  userResultItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderRadius: 17,
    marginBottom: 8,
  },
  userResultLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  userAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  userAvatarText: {
    fontSize: 18,
    fontWeight: '700',
  },
  userResultName: {
    fontSize: 16,
    fontWeight: '600',
  },
  userResultPhone: {
    fontSize: 12,
    marginTop: 2,
  },
  profileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  zodiacIcon: {
    width: 54,
    height: 54,
    borderRadius: 27,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  zodiacText: {
    fontSize: 25,
  },
  profileDetails: {
    flex: 1,
  },
  relationKicker: {
    fontSize: 9,
    lineHeight: 12,
    fontWeight: '900',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 3,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  profileName: {
    flexShrink: 1,
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 20,
    lineHeight: 24,
    fontWeight: '700',
    marginRight: 8,
  },
  selfBadge: {
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 10,
  },
  selfBadgeText: {
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 0.7,
  },
  profileMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginTop: 4,
  },
  profileDate: {
    flexShrink: 1,
    fontSize: 11,
    lineHeight: 15,
  },
  profilePlace: {
    flexShrink: 1,
    fontSize: 11,
    lineHeight: 15,
  },
  menuButton: {
    position: 'absolute',
    right: 12,
    top: 12,
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectionMark: {
    width: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
    marginTop: 34,
  },
  activeCheck: {
    width: 26,
    height: 26,
    borderRadius: 13,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 44,
    paddingHorizontal: 24,
  },
  emptyIcon: {
    width: 58,
    height: 58,
    borderRadius: 29,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 18,
  },
  emptyTitle: {
    fontFamily: DISPLAY_FONT_FAMILY,
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 24,
  },
  addProfileButton: {
    minHeight: 48,
    borderRadius: 24,
    paddingHorizontal: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  addProfileText: {
    fontSize: 14,
    fontWeight: '800',
  },
});
