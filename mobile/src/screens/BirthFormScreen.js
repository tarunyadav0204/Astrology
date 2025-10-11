import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';

export default function BirthFormScreen({ navigation }) {
  const [formData, setFormData] = useState({
    name: '',
    date: '',
    time: '',
    place: '',
    latitude: '',
    longitude: '',
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.date || !formData.time || !formData.place) {
      Alert.alert('Error', 'Please fill all required fields');
      return;
    }
    
    try {
      // Add default coordinates if not provided
      const birthData = {
        ...formData,
        latitude: formData.latitude || '28.6139',
        longitude: formData.longitude || '77.2090',
        timezone: 'UTC+5:30'
      };
      
      // Navigate to main app with birth data
      navigation.navigate('Dashboard', { birthData });
    } catch (error) {
      Alert.alert('Error', 'Failed to process birth data');
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={['#e91e63', '#ff6f00']}
        style={styles.gradient}
      >
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <View style={styles.header}>
              <TouchableOpacity 
                style={styles.backButton}
                onPress={() => navigation.goBack()}
              >
                <Text style={styles.backButtonText}>← Back</Text>
              </TouchableOpacity>
              <Text style={styles.title}>🔮 Birth Details</Text>
              <Text style={styles.subtitle}>Enter your birth information for accurate calculations</Text>
            </View>
            
            <View style={styles.form}>
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Name *</Text>
            <TextInput
              style={styles.input}
              value={formData.name}
              onChangeText={(value) => handleInputChange('name', value)}
              placeholder="Enter your name"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Date of Birth *</Text>
            <TextInput
              style={styles.input}
              value={formData.date}
              onChangeText={(value) => handleInputChange('date', value)}
              placeholder="YYYY-MM-DD"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Time of Birth *</Text>
            <TextInput
              style={styles.input}
              value={formData.time}
              onChangeText={(value) => handleInputChange('time', value)}
              placeholder="HH:MM (24-hour format)"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Place of Birth *</Text>
            <TextInput
              style={styles.input}
              value={formData.place}
              onChangeText={(value) => handleInputChange('place', value)}
              placeholder="City, Country"
            />
          </View>

          <View style={styles.row}>
            <View style={[styles.inputGroup, styles.halfWidth]}>
              <Text style={styles.label}>Latitude</Text>
              <TextInput
                style={styles.input}
                value={formData.latitude}
                onChangeText={(value) => handleInputChange('latitude', value)}
                placeholder="0.0000"
                keyboardType="numeric"
              />
            </View>

            <View style={[styles.inputGroup, styles.halfWidth]}>
              <Text style={styles.label}>Longitude</Text>
              <TextInput
                style={styles.input}
                value={formData.longitude}
                onChangeText={(value) => handleInputChange('longitude', value)}
                placeholder="0.0000"
                keyboardType="numeric"
              />
            </View>
          </View>

              <TouchableOpacity 
                style={styles.submitButton} 
                onPress={handleSubmit}
              >
                <Text style={styles.submitButtonText}>
                  Calculate Birth Chart
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
    position: 'relative',
  },
  backButton: {
    position: 'absolute',
    top: 0,
    left: 0,
    padding: 10,
    zIndex: 1,
  },
  backButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: 'white',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
    textAlign: 'center',
  },
  form: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 20,
    padding: 25,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
    marginBottom: 8,
  },
  input: {
    backgroundColor: 'rgba(255,255,255,0.9)',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    color: '#333',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  halfWidth: {
    width: '48%',
  },
  submitButton: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    marginTop: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 5,
  },
  disabledButton: {
    opacity: 0.7,
  },
  submitButtonText: {
    color: '#e91e63',
    fontSize: 18,
    fontWeight: 'bold',
  },
});