import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../../utils/constants';

const OpportunityCard = ({ opportunity, onPress }) => (
  <TouchableOpacity onPress={onPress} style={styles.oppCard}>
    <View style={styles.oppHeader}>
      <View style={styles.oppLeft}>
        <Ionicons name="flame" size={20} color="#ef4444" />
        <Text style={styles.oppSector}>{opportunity.sector}</Text>
      </View>
      <View style={styles.intensityBadge}>
        <Text style={styles.intensityText}>{opportunity.intensity}</Text>
      </View>
    </View>

    <View style={styles.oppDates}>
      <Ionicons name="calendar" size={14} color="#10b981" />
      <Text style={styles.oppDateText}>
        {opportunity.start_date} → {opportunity.end_date}
      </Text>
    </View>

    <Text style={styles.oppReason}>{opportunity.reason}</Text>

    <View style={styles.oppFooter}>
      <Text style={styles.oppDuration}>📅 {opportunity.duration_days} days</Text>
      <Ionicons name="arrow-forward-circle" size={20} color="#6366f1" />
    </View>
  </TouchableOpacity>
);

export default function AllOpportunitiesScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [opportunities, setOpportunities] = useState([]);
  const [filter, setFilter] = useState('High');

  useEffect(() => {
    fetchOpportunities();
  }, [filter]);

  const fetchOpportunities = async () => {
    try {
      setLoading(true);
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(
        `${API_BASE_URL}/api/financial/hot-opportunities?intensity=${filter}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      const json = await response.json();
      setOpportunities(json.opportunities);
    } catch (error) {
      console.error('Error fetching opportunities:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#0f0c29', '#302b63', '#24243e']} style={styles.bg}>
        <SafeAreaView style={styles.safeArea}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Ionicons name="arrow-back" size={24} color="#fff" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Hot Opportunities</Text>
            <TouchableOpacity onPress={fetchOpportunities}>
              <Ionicons name="refresh" size={24} color="#fff" />
            </TouchableOpacity>
          </View>

          {/* Filter Tabs */}
          <View style={styles.filterContainer}>
            {['High', 'Medium', 'Low'].map((intensity) => (
              <TouchableOpacity
                key={intensity}
                style={[styles.filterTab, filter === intensity && styles.filterTabActive]}
                onPress={() => setFilter(intensity)}
              >
                <Text style={[styles.filterText, filter === intensity && styles.filterTextActive]}>
                  {intensity}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {loading ? (
            <View style={styles.centerContainer}>
              <ActivityIndicator size="large" color="#10b981" />
              <Text style={styles.loadingText}>Loading opportunities...</Text>
            </View>
          ) : (
            <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
              <View style={styles.countBadge}>
                <Ionicons name="flash" size={16} color="#fbbf24" />
                <Text style={styles.countText}>
                  {opportunities.length} {filter} Intensity Opportunities
                </Text>
              </View>

              {opportunities.length === 0 ? (
                <View style={styles.emptyContainer}>
                  <Ionicons name="search" size={48} color="#666" />
                  <Text style={styles.emptyText}>No opportunities found</Text>
                  <Text style={styles.emptySubtext}>Try a different intensity filter</Text>
                </View>
              ) : (
                opportunities.map((opp, idx) => (
                  <OpportunityCard
                    key={idx}
                    opportunity={opp}
                    onPress={() => navigation.navigate('SectorDetail', { sector: opp.sector })}
                  />
                ))
              )}
            </ScrollView>
          )}
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  bg: { flex: 1, width: '100%', height: '100%' },
  safeArea: { flex: 1 },
  centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { color: '#fff', marginTop: 16, fontSize: 16 },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
  },
  headerTitle: { color: '#fff', fontSize: 20, fontWeight: 'bold' },

  filterContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 20,
    gap: 12,
  },
  filterTab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
  },
  filterTabActive: {
    backgroundColor: '#6366f1',
  },
  filterText: { color: '#888', fontSize: 14, fontWeight: '600' },
  filterTextActive: { color: '#fff' },

  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 30,
  },

  countBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(251,191,36,0.2)',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    alignSelf: 'flex-start',
    marginBottom: 20,
  },
  countText: { color: '#fbbf24', fontSize: 14, fontWeight: 'bold' },

  oppCard: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.3)',
  },
  oppHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  oppLeft: { flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1 },
  oppSector: { color: '#fff', fontSize: 16, fontWeight: 'bold', flex: 1 },
  intensityBadge: {
    backgroundColor: 'rgba(239,68,68,0.2)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  intensityText: { color: '#ef4444', fontSize: 12, fontWeight: 'bold' },

  oppDates: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
  },
  oppDateText: { color: '#10b981', fontSize: 14, fontWeight: '600' },

  oppReason: {
    color: '#ccc',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },

  oppFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  oppDuration: { color: '#888', fontSize: 13 },

  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: { color: '#fff', fontSize: 18, fontWeight: 'bold', marginTop: 16 },
  emptySubtext: { color: '#888', fontSize: 14, marginTop: 8 },
});
