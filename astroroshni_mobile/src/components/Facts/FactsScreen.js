import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  Modal,
  Alert,
  ActivityIndicator,
  SafeAreaView,
  Platform,
  StatusBar,
  KeyboardAvoidingView,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../context/ThemeContext';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../../utils/constants';
import { storage } from '../../services/storage';
import NativeSelectorChip from '../Common/NativeSelectorChip';
import { typographyTokens } from '../../theme/tokens';

const CATEGORIES = ['family', 'career', 'health', 'education', 'finance', 'personal', 'relationship', 'other'];

const FactsScreen = ({ route, navigation }) => {
  const params = route.params || {};
  const { birthChartId: paramChartId, nativeName: paramNativeName, birthData: paramBirthData } = params;
  const [memoryNotice, setMemoryNotice] = useState('');
  const { colors } = useTheme();
  const [selectedBirthData, setSelectedBirthData] = useState(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [matched, setMatched] = useState(0);
  const requestId = useRef(0);
  const [facts, setFacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingFact, setEditingFact] = useState(null);
  const [formData, setFormData] = useState({ category: 'personal', fact: '' });

  const loadSelectedNative = useCallback(async (fromStorageOnly = false) => {
    if (fromStorageOnly) {
      const details = await storage.getBirthDetails();
      setSelectedBirthData(details || null);
      return details;
    }
    if (paramChartId || paramBirthData?.id) {
      const id = paramChartId || paramBirthData?.id;
      const name = paramNativeName || paramBirthData?.name || 'Native';
      const data = paramBirthData ? { ...paramBirthData, id, name } : { id, name };
      setSelectedBirthData(data);
      return data;
    }
    const details = await storage.getBirthDetails();
    setSelectedBirthData(details || null);
    return details;
  }, [paramChartId, paramNativeName]);

  useEffect(() => {
    loadSelectedNative();
  }, [loadSelectedNative]);

  useEffect(() => {
    // If screen was opened with an explicit chart (e.g. from Profile "My Facts"),
    // keep using that native instead of overriding from storage on focus.
    if (paramChartId || paramBirthData?.id) {
      return;
    }
    const unsubscribe = navigation.addListener('focus', async () => {
      const details = await storage.getBirthDetails();
      setSelectedBirthData(details || null);
    });
    return unsubscribe;
  }, [navigation, paramChartId, paramBirthData]);

  useEffect(() => {
    if (selectedBirthData?.id) {
      const timer = setTimeout(() => fetchFacts(), 250);
      return () => { clearTimeout(timer); requestId.current += 1; };
    } else {
      setFacts([]);
      setLoading(false);
    }
  }, [selectedBirthData?.id, search, page]);

  const fetchFacts = async () => {
    const chartId = selectedBirthData?.id;
    if (!chartId) {
      setFacts([]);
      setLoading(false);
      return;
    }
    const currentRequest = ++requestId.current;
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('authToken');
      const response = await axios.get(`${API_BASE_URL}/api/facts/${chartId}?q=${encodeURIComponent(search)}&page=${page}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (currentRequest !== requestId.current) return;
      if (response.data.success) {
        const sortedFacts = response.data.facts || [];
        setFacts(sortedFacts);
        setHasMore(Boolean(response.data.has_more));
        setMatched(response.data.matched ?? sortedFacts.length);
        params.onFactsChanged?.(sortedFacts, response.data.total);
      } else {
        setFacts([]);
      }
    } catch (error) {
      if (currentRequest !== requestId.current) return;
      console.error('Error fetching facts:', error);
      Alert.alert('Error', 'Failed to load facts');
      setFacts([]);
    } finally {
      if (currentRequest === requestId.current) setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!formData.fact.trim()) {
      Alert.alert('Error', 'Please enter a fact');
      return;
    }

    try {
      console.log('Saving fact:', formData);
      const token = await AsyncStorage.getItem('authToken');
      if (editingFact) {
        await axios.put(`${API_BASE_URL}/api/facts/${editingFact.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } else {
        const chartId = selectedBirthData?.id;
        if (!chartId) {
          Alert.alert('Error', 'Please select a native first.');
          return;
        }
        await axios.post(`${API_BASE_URL}/api/facts`, { ...formData, birth_chart_id: chartId }, {
          headers: { Authorization: `Bearer ${token}` }
        });
      }
      setMemoryNotice('Memory updated. Future answers can use your saved details.');
      setModalVisible(false);
      setEditingFact(null);
      setFormData({ category: 'personal', fact: '' });
      fetchFacts();
    } catch (error) {
      console.error('Error saving fact:', error);
      console.error('Error details:', error.response?.data);
      Alert.alert('Error', 'Failed to save fact');
    }
  };

  const handleDelete = (fact) => {
    Alert.alert('Delete Fact', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            console.log('Deleting fact:', fact.id);
            const token = await AsyncStorage.getItem('authToken');
            await axios.delete(`${API_BASE_URL}/api/facts/${fact.id}`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            setMemoryNotice('Detail removed from saved memory. Conversation history remains.');
            fetchFacts();
          } catch (error) {
            console.error('Error deleting fact:', error);
            console.error('Error details:', error.response?.data);
            Alert.alert('Error', 'Failed to delete fact');
          }
        },
      },
    ]);
  };

  const openEditModal = (fact) => {
    setEditingFact(fact);
    setFormData({ category: fact.category, fact: fact.fact });
    setModalVisible(true);
  };

  const openAddModal = () => {
    setEditingFact(null);
    setFormData({ category: 'personal', fact: '' });
    setModalVisible(true);
  };

  const renderFact = ({ item }) => (
    <View style={[styles.factCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
      <View style={styles.factHeader}>
        <View style={[styles.categoryBadge, { backgroundColor: colors.surfaceMuted }]}>
          <Ionicons name="bookmark-outline" size={12} color={colors.primary} />
          <Text style={[styles.categoryText, { color: colors.primary }]}>{item.category}</Text>
        </View>
        <Text style={[styles.dateText, { color: colors.textSecondary }]}>
          {new Date(item.extracted_at).toLocaleDateString()}
        </Text>
      </View>
      <Text style={[styles.factText, { color: colors.text }]}>{item.fact}</Text>
      <View style={[styles.actions, { borderTopColor: colors.cardBorder }]}>
        <TouchableOpacity onPress={() => openEditModal(item)} accessibilityRole="button" style={[styles.actionButton, { backgroundColor: colors.surfaceMuted }]}>
          <Ionicons name="create-outline" size={16} color={colors.primary} /><Text style={[styles.actionText, { color: colors.primary }]}>Edit</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => handleDelete(item)} accessibilityRole="button" style={styles.actionButton}>
          <Ionicons name="trash-outline" size={16} color={colors.error} /><Text style={[styles.actionText, { color: colors.error }]}>Delete</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const nativeName = selectedBirthData?.name || paramNativeName || paramBirthData?.name || 'Native';


  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }, params.memory && styles.sheetContainer]}>
      <View style={[styles.header, { backgroundColor: colors.cardBackground, borderBottomColor: colors.cardBorder }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} accessibilityRole="button" style={[styles.backButton, { backgroundColor: colors.surfaceMuted }]}>
          <Ionicons name={params.memory ? "close" : "arrow-back"} size={20} color={colors.text} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          {params.memory ? <><Text style={[styles.headerEyebrow, { color: colors.textSecondary }]}>Remembered about</Text><Text style={[styles.memoryTitle, { color: colors.text }]} numberOfLines={2} ellipsizeMode="tail">{nativeName}</Text></> : selectedBirthData ? (
            <NativeSelectorChip
              birthData={selectedBirthData}
              onPress={() => navigation.navigate('SelectNative', { returnTo: 'Facts' })}
              maxLength={10}
              showIcon={false}
            />
          ) : (
            <TouchableOpacity
              style={[styles.selectNativeChip, { backgroundColor: colors.primary + '25', borderColor: colors.primary + '50' }]}
              onPress={() => navigation.navigate('SelectNative', { returnTo: 'Facts' })}
            >
              <Text style={[styles.selectNativeChipText, { color: colors.primary }]}>Select native</Text>
              <Ionicons name="chevron-down" size={16} color={colors.primary} />
            </TouchableOpacity>
          )}
        </View>
        <TouchableOpacity
          onPress={openAddModal}
          disabled={!selectedBirthData?.id}
          accessibilityRole="button"
          style={[styles.addButton, { backgroundColor: selectedBirthData?.id ? colors.primary : colors.surfaceMuted }]}
        >
          <Ionicons name="add" size={18} color={selectedBirthData?.id ? colors.onPrimary : colors.textSecondary} /><Text style={[styles.addButtonText, { color: selectedBirthData?.id ? colors.onPrimary : colors.textSecondary }]}>Add</Text>
        </TouchableOpacity>
      </View>

      {params.memory && <View style={[styles.memoryHelp, { backgroundColor: colors.surfaceMuted }]}>
        <Ionicons name="sparkles-outline" size={18} color={colors.primary} />
        <View style={styles.helpCopy}>
          <Text style={[styles.helpText, { color: colors.text }]}>These details help personalize future answers. You can correct or remove them anytime.</Text>
          <Text style={[styles.historyNote, { color: colors.textSecondary }]}>Editing memory does not change your conversation history.</Text>
        </View>
      </View>}
      {memoryNotice ? <View style={[styles.notice, { backgroundColor: colors.surfaceMuted }]}><Ionicons name="checkmark-circle-outline" size={18} color={colors.success} /><Text accessibilityLiveRegion="polite" style={[styles.noticeText, { color: colors.text }]}>{memoryNotice}</Text></View> : null}
      {selectedBirthData?.id && <View style={styles.searchArea}>
        <View style={[styles.searchBox, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
          <Ionicons name="search-outline" size={18} color={colors.textSecondary} />
          <TextInput accessibilityLabel="Search memory facts" value={search} onChangeText={value => { setSearch(value); setPage(1); }} placeholder="Search facts, e.g. career or studying abroad" placeholderTextColor={colors.textSecondary} style={[styles.searchInput, { color: colors.text }]} returnKeyType="search" />
        </View>
        <View style={styles.searchMeta}><Text style={[styles.resultCount, { color: colors.textSecondary }]}>{matched} {search ? 'matching facts' : 'facts'}</Text>{loading && <ActivityIndicator size="small" color={colors.primary} />}</View>
      </View>}
      {!selectedBirthData?.id ? (
        <View style={styles.emptyState}>
          <Text style={[styles.emptyStateText, { color: colors.textSecondary }]}>
            Select a native above to view and manage facts for that chart.
          </Text>
        </View>
      ) : (
      <FlatList
        data={facts}
        renderItem={renderFact}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        ListFooterComponent={<View style={styles.pagination}>{page > 1 && <TouchableOpacity style={[styles.pageButton, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]} disabled={loading} onPress={() => setPage(value => value - 1)}><Ionicons name="chevron-back" size={16} color={colors.primary} /><Text style={[styles.actionText, { color: colors.primary }]}>Previous</Text></TouchableOpacity>}{hasMore && <TouchableOpacity style={[styles.pageButton, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]} disabled={loading} onPress={() => setPage(value => value + 1)}><Text style={[styles.actionText, { color: colors.primary }]}>Next</Text><Ionicons name="chevron-forward" size={16} color={colors.primary} /></TouchableOpacity>}</View>}
        ListEmptyComponent={
          <View style={styles.listEmpty}>
            {loading ? <ActivityIndicator color={colors.primary} /> : <><View style={[styles.emptyIcon, { backgroundColor: colors.surfaceMuted }]}><Ionicons name={search ? "search-outline" : "bookmarks-outline"} size={28} color={colors.primary} /></View><Text style={[styles.emptyText, { color: colors.textSecondary }]}>{search ? 'No facts match your search.' : 'No facts yet for this native. Add your first fact!'}</Text></>}
          </View>
        }
      />
      )}

      <Modal visible={modalVisible} animationType="slide" transparent onRequestClose={() => setModalVisible(false)}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 40 : 0}
          style={[styles.modalOverlay, { backgroundColor: colors.overlay }]}
        >
          <View style={styles.modalLayout}>
            <View style={[styles.modalContent, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
              <ScrollView
                contentContainerStyle={styles.modalScrollContent}
                keyboardShouldPersistTaps="handled"
              >
                <View style={styles.editorHeader}><View style={[styles.editorIcon, { backgroundColor: colors.surfaceMuted }]}><Ionicons name={editingFact ? "create-outline" : "add-outline"} size={22} color={colors.primary} /></View><Text style={[styles.modalTitle, { color: colors.text }]}>{editingFact ? 'Edit Fact' : 'Add Fact'}</Text></View>

                <Text style={[styles.label, { color: colors.text }]}>Category</Text>
                <View style={styles.categoryGrid}>
                  {CATEGORIES.map((cat) => (
                    <TouchableOpacity
                      key={cat}
                      onPress={() => setFormData({ ...formData, category: cat })}
                      style={[
                        styles.categoryChip,
                        { borderColor: colors.cardBorder },
                        formData.category === cat && { backgroundColor: colors.primary, borderColor: colors.primary },
                      ]}
                    >
                      <Text
                        style={[
                          styles.categoryChipText,
                          { color: colors.text },
                          formData.category === cat && { color: colors.onPrimary },
                        ]}
                      >
                        {cat}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>

                <Text style={[styles.label, { color: colors.text }]}>Fact</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: colors.background, color: colors.text, borderColor: colors.cardBorder }]}
                  value={formData.fact}
                  onChangeText={(text) => setFormData({ ...formData, fact: text })}
                  placeholder="For example: Considering a master’s abroad"
                  accessibilityLabel="Remembered detail"
                  placeholderTextColor={colors.textSecondary}
                  multiline
                  numberOfLines={4}
                />

                <View style={styles.modalActions}>
                  <TouchableOpacity
                    onPress={() => {
                      setModalVisible(false);
                      setEditingFact(null);
                    }}
                    style={[styles.modalButton, { backgroundColor: colors.surfaceMuted }]}
                  >
                    <Text style={[styles.modalButtonText, { color: colors.text }]}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={handleSave} disabled={!formData.fact.trim()} style={[styles.modalButton, { backgroundColor: formData.fact.trim() ? colors.primary : colors.surfaceMuted }]}><Ionicons name="checkmark" size={18} color={formData.fact.trim() ? colors.onPrimary : colors.textSecondary} />
                    <Text style={[styles.modalButtonText, { color: formData.fact.trim() ? colors.onPrimary : colors.textSecondary }]}>Save</Text>
                  </TouchableOpacity>
                </View>
              </ScrollView>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0 },
  sheetContainer: { paddingTop: 0 },
  header: { paddingHorizontal: 18, paddingVertical: 16, flexDirection: 'row', alignItems: 'center', gap: 12, borderBottomWidth: StyleSheet.hairlineWidth },
  backButton: { width: 40, height: 40, borderRadius: 20, flexShrink: 0, alignItems: 'center', justifyContent: 'center' },
  headerCenter: { flex: 1, minWidth: 0, flexShrink: 1, justifyContent: 'center' },
  headerEyebrow: { fontSize: 11, fontWeight: '600', marginBottom: 3 },
  memoryTitle: { width: '100%', flexShrink: 1, ...typographyTokens.display, fontSize: 20, lineHeight: 25 },
  addButton: { paddingHorizontal: 14, minHeight: 42, borderRadius: 21, flexShrink: 0, flexDirection: 'row', gap: 4, alignItems: 'center', justifyContent: 'center' },
  addButtonText: { fontSize: 14, fontWeight: '600' },
  selectNativeChip: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1, gap: 6 },
  selectNativeChipText: { fontSize: 14, fontWeight: '600' },
  memoryHelp: { marginHorizontal: 18, marginTop: 16, padding: 12, borderRadius: 14, flexDirection: 'row', gap: 10, alignItems: 'flex-start' },
  helpCopy: { flex: 1, minWidth: 0 },
  helpText: { fontSize: 13, lineHeight: 19 },
  historyNote: { fontSize: 11, lineHeight: 16, marginTop: 5 },
  notice: { marginHorizontal: 18, marginTop: 10, padding: 12, borderRadius: 12, flexDirection: 'row', gap: 8 },
  noticeText: { flex: 1, fontSize: 13, lineHeight: 19 },
  searchArea: { paddingHorizontal: 18, paddingTop: 16, paddingBottom: 4 },
  searchBox: { flexDirection: 'row', gap: 10, alignItems: 'center', borderWidth: 1, borderRadius: 14, paddingHorizontal: 12 },
  searchInput: { flex: 1, minWidth: 0, paddingVertical: 13, fontSize: 13 },
  searchMeta: { minHeight: 28, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 6 },
  resultCount: { fontSize: 11, fontWeight: '600' },
  emptyState: { flex: 1, justifyContent: 'center', padding: 24, alignItems: 'center' },
  emptyStateText: { fontSize: 15, textAlign: 'center', lineHeight: 23 },
  list: { paddingHorizontal: 18, paddingTop: 8, paddingBottom: 28 },
  factCard: { padding: 16, borderRadius: 18, marginBottom: 12, borderWidth: 1 },
  factHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  categoryBadge: { flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12, flexShrink: 1 },
  categoryText: { fontSize: 11, fontWeight: '600', textTransform: 'capitalize', flexShrink: 1 },
  dateText: { fontSize: 11 },
  factText: { fontSize: 16, lineHeight: 24, marginBottom: 14 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 10 },
  actionButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, minHeight: 40, paddingHorizontal: 12, borderRadius: 20 },
  actionText: { fontSize: 13, fontWeight: '600' },
  pagination: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 8, paddingVertical: 12 },
  pageButton: { flexDirection: 'row', alignItems: 'center', gap: 5, minHeight: 42, paddingHorizontal: 14, borderRadius: 21, borderWidth: 1 },
  listEmpty: { alignItems: 'center', paddingHorizontal: 20, paddingVertical: 36, gap: 14 },
  emptyIcon: { width: 64, height: 64, borderRadius: 32, justifyContent: 'center', alignItems: 'center' },
  emptyText: { textAlign: 'center', fontSize: 14, lineHeight: 22 },
  modalOverlay: { flex: 1, justifyContent: 'center' },
  modalLayout: { flex: 1, justifyContent: 'center', padding: 20 },
  modalContent: { borderRadius: 24, borderWidth: 1, padding: 20, width: '100%', maxWidth: 520, maxHeight: '90%', alignSelf: 'center' },
  modalScrollContent: { paddingBottom: 4 },
  editorHeader: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 12 },
  editorIcon: { width: 44, height: 44, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  modalTitle: { ...typographyTokens.display, fontSize: 25, lineHeight: 30, flexShrink: 1 },
  label: { fontSize: 12, fontWeight: '600', marginBottom: 10, marginTop: 16 },
  categoryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  categoryChip: { paddingHorizontal: 14, minHeight: 40, justifyContent: 'center', borderRadius: 20, borderWidth: 1 },
  categoryChipText: { fontSize: 13, textTransform: 'capitalize' },
  input: { borderWidth: 1, borderRadius: 14, padding: 14, minHeight: 120, fontSize: 16, lineHeight: 24, textAlignVertical: 'top' },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 24 },
  modalButton: { flex: 1, minHeight: 48, borderRadius: 14, flexDirection: 'row', gap: 6, justifyContent: 'center', alignItems: 'center' },
  modalButtonText: { fontWeight: '600', fontSize: 15 },
});

export default FactsScreen;
