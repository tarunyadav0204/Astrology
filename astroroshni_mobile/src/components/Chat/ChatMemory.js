import React, { useEffect, useState, useCallback } from 'react';
import { Modal, View, Text, TouchableOpacity } from 'react-native';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import FactsScreen from '../Facts/FactsScreen';

export default function ChatMemory({ birthData, navigation }) {
  const { colors } = useTheme();
  const [open, setOpen] = useState(false);
  const [count, setCount] = useState(null);
  const refresh = useCallback(async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const { data } = await axios.get(`${API_BASE_URL}/api/facts/${birthData.id}?limit=1`, { headers: { Authorization: `Bearer ${token}` } });
      setCount(data.total ?? (data.facts || []).length);
    } catch (_) { setCount(null); }
  }, [birthData.id]);
  useEffect(() => { refresh(); }, [refresh]);
  return <>
    <TouchableOpacity accessibilityRole="button" accessibilityLabel={`Memory for ${birthData.name}${count !== null ? `, ${count} saved details` : ''}`} accessibilityHint="Review, edit or remove remembered details" hitSlop={{ top: 8, bottom: 8, left: 2, right: 8 }} onPress={() => setOpen(true)} style={{ flexDirection: 'row', alignItems: 'center', gap: 3, paddingHorizontal: 4, minHeight: 24, flexShrink: 0 }}>
      <Ionicons name="bookmarks-outline" size={16} color={colors.textInverseMuted} />
      {count !== null && <Text style={{ color: colors.textInverseMuted, fontSize: 11 }}>{count}</Text>}
    </TouchableOpacity>
    <Modal visible={open} transparent animationType="slide" onRequestClose={() => { setOpen(false); refresh(); }}>
      <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: colors.overlay }}>
        <View accessibilityViewIsModal style={{ height: '85%', borderTopLeftRadius: 20, borderTopRightRadius: 20, overflow: 'hidden', backgroundColor: colors.background }}>
          <FactsScreen route={{ params: { birthData, memory: true, onFactsChanged: (facts, total) => setCount(total ?? facts.length) } }} navigation={{ ...navigation, goBack: () => { setOpen(false); refresh(); } }} />
        </View>
      </View>
    </Modal>
  </>;
}
