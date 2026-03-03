import React, { useState, useEffect, useCallback } from 'react';
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

const CATEGORIES = ['family', 'career', 'health', 'education', 'finance', 'personal', 'relationship', 'other'];

const FactsScreen = ({ route, navigation }) => {
  const params = route.params || {};
  const { birthChartId: paramChartId, nativeName: paramNativeName, birthData: paramBirthData } = params;
  const { theme, colors } = useTheme();
  const [selectedBirthData, setSelectedBirthData] = useState(null);
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
      fetchFacts();
    } else {
      setFacts([]);
      setLoading(false);
    }
  }, [selectedBirthData?.id]);

  const fetchFacts = async () => {
    const chartId = selectedBirthData?.id;
    if (!chartId) {
      setFacts([]);
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('authToken');
      const response = await axios.get(`${API_BASE_URL}/api/facts/${chartId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        const sortedFacts = (response.data.facts || []).sort((a, b) =>
          new Date(b.extracted_at) - new Date(a.extracted_at)
        );
        setFacts(sortedFacts);
      } else {
        setFacts([]);
      }
    } catch (error) {
      console.error('Error fetching facts:', error);
      Alert.alert('Error', 'Failed to load facts');
      setFacts([]);
    } finally {
      setLoading(false);
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
    <View style={[styles.factCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
      <View style={styles.factHeader}>
        <View style={[styles.categoryBadge, { backgroundColor: colors.primary + '20' }]}>
          <Text style={[styles.categoryText, { color: colors.primary }]}>{item.category}</Text>
        </View>
        <Text style={[styles.dateText, { color: colors.textSecondary }]}>
          {new Date(item.extracted_at).toLocaleDateString()}
        </Text>
      </View>
      <Text style={[styles.factText, { color: colors.text }]}>{item.fact}</Text>
      <View style={styles.actions}>
        <TouchableOpacity onPress={() => openEditModal(item)} style={styles.actionButton}>
          <Text style={[styles.actionText, { color: colors.primary }]}>Edit</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => handleDelete(item)} style={styles.actionButton}>
          <Text style={[styles.actionText, { color: '#ef4444' }]}>Delete</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  const nativeName = selectedBirthData?.name || 'Native';

  if (loading && selectedBirthData?.id) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            {selectedBirthData ? (
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
          <View style={styles.addButtonPlaceholder} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          {selectedBirthData ? (
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
          style={[styles.addButton, { backgroundColor: selectedBirthData?.id ? colors.primary : colors.border }]}
        >
          <Text style={styles.addButtonText}>+ Add</Text>
        </TouchableOpacity>
      </View>

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
        ListEmptyComponent={
          <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
            No facts yet for this native. Add your first fact!
          </Text>
        }
      />
      )}

      <Modal visible={modalVisible} animationType="slide" transparent>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 40 : 0}
          style={styles.modalOverlay}
        >
          <View style={styles.modalOverlay}>
            <View style={[styles.modalContent, { backgroundColor: colors.card }]}>
              <ScrollView
                contentContainerStyle={styles.modalScrollContent}
                keyboardShouldPersistTaps="handled"
              >
                <Text style={[styles.modalTitle, { color: colors.text }]}>
                  {editingFact ? 'Edit Fact' : 'Add Fact'}
                </Text>

                <Text style={[styles.label, { color: colors.text }]}>Category</Text>
                <View style={styles.categoryGrid}>
                  {CATEGORIES.map((cat) => (
                    <TouchableOpacity
                      key={cat}
                      onPress={() => setFormData({ ...formData, category: cat })}
                      style={[
                        styles.categoryChip,
                        { borderColor: colors.border },
                        formData.category === cat && { backgroundColor: colors.primary, borderColor: colors.primary },
                      ]}
                    >
                      <Text
                        style={[
                          styles.categoryChipText,
                          { color: colors.text },
                          formData.category === cat && { color: '#fff' },
                        ]}
                      >
                        {cat}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>

                <Text style={[styles.label, { color: colors.text }]}>Fact</Text>
                <TextInput
                  style={[styles.input, { backgroundColor: colors.background, color: colors.text, borderColor: colors.border }]}
                  value={formData.fact}
                  onChangeText={(text) => setFormData({ ...formData, fact: text })}
                  placeholder="Enter fact..."
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
                    style={[styles.modalButton, { backgroundColor: colors.border }]}
                  >
                    <Text style={[styles.modalButtonText, { color: colors.text }]}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={handleSave} style={[styles.modalButton, { backgroundColor: colors.primary }]}>
                    <Text style={styles.modalButtonText}>Save</Text>
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
  container: {
    flex: 1,
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
  header: {
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.08)',
  },
  backButton: { padding: 4 },
  headerCenter: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  addButtonPlaceholder: { width: 52 },
  addButton: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 },
  addButtonText: { color: '#fff', fontWeight: '600' },
  selectNativeChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    gap: 6,
  },
  selectNativeChipText: { fontSize: 14, fontWeight: '600' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emptyState: { flex: 1, justifyContent: 'center', padding: 24, alignItems: 'center' },
  emptyStateText: { fontSize: 16, textAlign: 'center', lineHeight: 24 },
  list: { padding: 16 },
  factCard: { padding: 16, borderRadius: 12, marginBottom: 12, borderWidth: 1 },
  factHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  categoryBadge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  categoryText: { fontSize: 12, fontWeight: '600', textTransform: 'capitalize' },
  dateText: { fontSize: 12 },
  factText: { fontSize: 15, lineHeight: 22, marginBottom: 12 },
  actions: { flexDirection: 'row', gap: 16 },
  actionButton: { paddingVertical: 4 },
  actionText: { fontSize: 14, fontWeight: '600' },
  emptyText: { textAlign: 'center', marginTop: 40, fontSize: 16 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.8)', justifyContent: 'center', padding: 20 },
  modalContent: { borderRadius: 16, padding: 20 },
  modalScrollContent: {
    paddingBottom: 16,
  },
  modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 20 },
  label: { fontSize: 14, fontWeight: '600', marginBottom: 8, marginTop: 12 },
  categoryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  categoryChip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, borderWidth: 1 },
  categoryChipText: { fontSize: 13, textTransform: 'capitalize' },
  input: { borderWidth: 1, borderRadius: 8, padding: 12, fontSize: 15, textAlignVertical: 'top' },
  modalActions: { flexDirection: 'row', gap: 12, marginTop: 20 },
  modalButton: { flex: 1, paddingVertical: 12, borderRadius: 8, alignItems: 'center' },
  modalButtonText: { color: '#fff', fontWeight: '600', fontSize: 16 },
});

export default FactsScreen;
