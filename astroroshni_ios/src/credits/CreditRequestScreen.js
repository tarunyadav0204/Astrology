import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { creditAPI } from '../services/api';

const CreditRequestScreen = ({ navigation }) => {
  const [requestAmount, setRequestAmount] = useState('');
  const [requestReason, setRequestReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [myRequests, setMyRequests] = useState([]);

  useEffect(() => {
    loadMyRequests();
  }, []);

  const validateReason = (reason) => {
    return reason
      .replace(/<[^>]*>/g, '')
      .replace(/[<>'"]/g, '')
      .trim()
      .substring(0, 500);
  };

  const loadMyRequests = async () => {
    try {
      const response = await creditAPI.getMyRequests();
      setMyRequests(response.data.requests || []);
    } catch (error) {
      console.error('Error loading requests:', error);
    }
  };

  const handleSubmitRequest = async () => {
    if (!requestAmount || !requestReason.trim()) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    const sanitizedReason = validateReason(requestReason);
    if (sanitizedReason.length < 10) {
      Alert.alert('Error', 'Reason must be at least 10 characters');
      return;
    }

    const amountToRequest = parseInt(requestAmount);
    setLoading(true);

    try {
      const response = await creditAPI.requestCredits(
        amountToRequest,
        sanitizedReason
      );

      if (response.data.success) {
        Alert.alert('Success', response.data.message);
        setRequestAmount('');
        setRequestReason('');
        loadMyRequests();
      } else {
        Alert.alert('Error', response.data.message);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to submit request';
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'approved': return '#4CAF50';
      case 'rejected': return '#f44336';
      default: return '#ff9800';
    }
  };

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#fafafa', '#f5f5f5']} style={styles.backgroundGradient}>
        <SafeAreaView style={styles.safeArea}>
          <KeyboardAvoidingView 
            style={styles.keyboardView}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          >
            {/* Header */}
            <View style={styles.header}>
              <TouchableOpacity 
                onPress={() => navigation.goBack()}
                style={styles.backButton}
              >
                <Ionicons name="arrow-back" size={24} color="#333" />
              </TouchableOpacity>
              <Text style={styles.headerTitle}>Request Credits</Text>
            </View>

            <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
              {/* Request Form */}
              <View style={styles.formCard}>
                <Text style={styles.sectionTitle}>🙋‍♂️ Request Credits</Text>
                
                <View style={styles.inputContainer}>
                  <Text style={styles.inputLabel}>Credits Needed</Text>
                  <TextInput
                    style={styles.input}
                    value={requestAmount}
                    onChangeText={(text) => {
                      // Only allow numeric input and ensure it doesn't exceed 9999
                      const numericValue = text.replace(/[^0-9]/g, '');
                      if (parseInt(numericValue) <= 9999 || numericValue === '') {
                        setRequestAmount(numericValue);
                      }
                    }}
                    placeholder="Enter amount (1-9999)"
                    keyboardType="numeric"
                    maxLength={4}
                  />
                </View>

                <View style={styles.inputContainer}>
                  <Text style={styles.inputLabel}>Reason for Request</Text>
                  <TextInput
                    style={[styles.input, styles.textArea]}
                    value={requestReason}
                    onChangeText={setRequestReason}
                    placeholder="e.g., student discount, financial hardship"
                    multiline
                    numberOfLines={4}
                    maxLength={500}
                    textAlignVertical="top"
                  />
                  <Text style={styles.charCount}>{requestReason.length}/500</Text>
                </View>

                <TouchableOpacity
                  style={[styles.submitButton, loading && styles.buttonDisabled]}
                  onPress={handleSubmitRequest}
                  disabled={loading || !requestAmount || !requestReason.trim()}
                >
                  <LinearGradient
                    colors={loading ? ['#ccc', '#999'] : ['#28a745', '#34ce57']}
                    style={styles.buttonGradient}
                  >
                    <Text style={styles.buttonText}>
                      {loading ? 'Submitting...' : 'Submit Request'}
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              </View>

              {/* My Requests */}
              {myRequests.length > 0 && (
                <View style={styles.requestsCard}>
                  <Text style={styles.sectionTitle}>📋 My Requests</Text>
                  {myRequests.slice(0, 5).map((request) => (
                    <View key={request.id} style={styles.requestItem}>
                      <View style={styles.requestHeader}>
                        <Text style={styles.requestAmount}>{request.requested_amount} credits</Text>
                        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(request.status) }]}>
                          <Text style={styles.statusText}>{request.status.toUpperCase()}</Text>
                        </View>
                      </View>
                      <Text style={styles.requestReason}>{request.reason}</Text>
                      {request.admin_notes && (
                        <Text style={styles.adminNotes}>Admin: {request.admin_notes}</Text>
                      )}
                      <Text style={styles.requestDate}>
                        {new Date(request.created_at).toLocaleDateString()}
                      </Text>
                    </View>
                  ))}
                </View>
              )}
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  backgroundGradient: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  backButton: {
    marginRight: 15,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#333',
  },
  scrollView: {
    flex: 1,
    padding: 20,
  },
  formCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 20,
  },
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#666',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#f8f9fa',
    color: '#333',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  charCount: {
    fontSize: 12,
    color: '#999',
    textAlign: 'right',
    marginTop: 5,
  },
  submitButton: {
    borderRadius: 8,
    overflow: 'hidden',
  },
  buttonGradient: {
    paddingVertical: 15,
    alignItems: 'center',
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  requestsCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  requestItem: {
    backgroundColor: '#f8f9fa',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  requestHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  requestAmount: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '600',
    color: 'white',
  },
  requestReason: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  adminNotes: {
    fontSize: 13,
    color: '#007bff',
    fontStyle: 'italic',
    marginBottom: 5,
  },
  requestDate: {
    fontSize: 12,
    color: '#999',
  },
});

export default CreditRequestScreen;