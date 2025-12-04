import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { storage } from '../services/storage';

export default function PanchangWidget({ transitDate }) {
  const [panchangData, setPanchangData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const fetchPanchangData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Get birth details for location
      const birthDetails = await storage.getBirthDetails();
      if (!birthDetails) {
        setError('Birth details not found');
        return;
      }

      const dateStr = transitDate.toISOString().split('T')[0];
      
      const requestData = {
        birth_data: {
          name: birthDetails.name || 'User',
          date: birthDetails.date,
          time: birthDetails.time,
          latitude: birthDetails.latitude,
          longitude: birthDetails.longitude,
          timezone: birthDetails.timezone || 'UTC+5:30',
          place: birthDetails.place || ''
        },
        transit_date: dateStr
      };

      console.log('Fetching panchang for:', dateStr);
      
      const response = await fetch('https://astrovishnu.com/api/calculate-panchang', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('Panchang data received:', data);
      
      // Log individual components for debugging
      console.log('Nakshatra data:', data.nakshatra);
      console.log('Tithi data:', data.tithi);
      console.log('Yoga data:', data.yoga);
      console.log('Karana data:', data.karana);
      
      setPanchangData(data);
    } catch (err) {
      console.error('Error fetching panchang data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPanchangData();
  }, [transitDate]);

  if (loading) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>📅 Panchang</Text>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color="#e91e63" />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>📅 Panchang</Text>
        <Text style={styles.errorText}>Error: {error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>📅 Panchang</Text>
      <Text style={styles.date}>{formatDate(transitDate)}</Text>
      
      <View style={styles.content}>
        <View style={styles.panchangItem}>
          <Text style={styles.panchangLabel}>Tithi:</Text>
          <Text style={styles.panchangValue}>
            {panchangData?.tithi?.name || 'Loading...'}
          </Text>
        </View>
        <View style={styles.panchangItem}>
          <Text style={styles.panchangLabel}>Vara:</Text>
          <Text style={styles.panchangValue}>
            {panchangData?.vara?.name || 'Loading...'}
          </Text>
        </View>
        <View style={styles.panchangItem}>
          <Text style={styles.panchangLabel}>Nakshatra:</Text>
          <Text style={styles.panchangValue}>
            {panchangData?.nakshatra?.name || 'Loading...'}
          </Text>
        </View>
        <View style={styles.panchangItem}>
          <Text style={styles.panchangLabel}>Yoga:</Text>
          <Text style={styles.panchangValue}>
            {panchangData?.yoga?.name || 'Loading...'}
          </Text>
        </View>
        <View style={styles.panchangItem}>
          <Text style={styles.panchangLabel}>Karana:</Text>
          <Text style={styles.panchangValue}>
            {panchangData?.karana?.name || 'Loading...'}
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'white',
    borderRadius: 8,
    margin: 10,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#e91e63',
    textAlign: 'center',
    marginBottom: 10,
  },
  date: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginBottom: 15,
  },
  content: {
    gap: 8,
  },
  panchangItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  panchangLabel: {
    fontSize: 14,
    color: '#666',
  },
  panchangValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    marginLeft: 10,
    fontSize: 14,
    color: '#666',
  },
  errorText: {
    fontSize: 14,
    color: '#e91e63',
    textAlign: 'center',
    paddingVertical: 20,
  },
});