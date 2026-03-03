import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { COLORS } from '../utils/constants';
import { useCredits } from './CreditContext';
import { CREDIT_COSTS } from './creditService';

const PremiumFeatureExample = ({ birthData }) => {
  const { credits, spendCredits } = useCredits();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const ANALYSIS_COST = CREDIT_COSTS.PREMIUM_ANALYSIS;

  const handlePremiumAnalysis = async () => {
    if (credits < ANALYSIS_COST) {
      Alert.alert(
        'Insufficient Credits',
        `You need ${ANALYSIS_COST} credits for premium analysis. You have ${credits} credits.`,
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Get Credits', onPress: () => {/* Navigate to credit screen */} }
        ]
      );
      return;
    }

    Alert.alert(
      'Premium Analysis',
      `Use ${ANALYSIS_COST} credits for detailed chart analysis?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          onPress: async () => {
            setLoading(true);
            const success = await spendCredits(
              ANALYSIS_COST, 
              'premium_analysis', 
              'Premium Chart Analysis'
            );
            
            if (success) {
              // Simulate API call for premium analysis
              setTimeout(() => {
                setAnalysis({
                  title: 'Premium Analysis Complete',
                  content: 'Your detailed chart analysis reveals...',
                  insights: [
                    'Strong Jupiter placement indicates good fortune',
                    'Mars in 10th house suggests career success',
                    'Venus aspects Moon for harmonious relationships'
                  ]
                });
                setLoading(false);
              }, 2000);
            } else {
              setLoading(false);
              Alert.alert('Error', 'Failed to process payment');
            }
          }
        }
      ]
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Premium Chart Analysis</Text>
        <Text style={styles.subtitle}>
          Get detailed insights with advanced calculations
        </Text>
      </View>

      <View style={styles.creditInfo}>
        <Text style={styles.costText}>Cost: {ANALYSIS_COST} credits</Text>
        <Text style={styles.balanceText}>Your balance: {credits} credits</Text>
      </View>

      {!analysis ? (
        <TouchableOpacity
          style={[
            styles.analyzeButton,
            (credits < ANALYSIS_COST || loading) && styles.buttonDisabled
          ]}
          onPress={handlePremiumAnalysis}
          disabled={credits < ANALYSIS_COST || loading}
        >
          <Text style={styles.buttonText}>
            {loading ? 'Processing...' : 
             credits < ANALYSIS_COST ? 'Insufficient Credits' : 'Get Premium Analysis'}
          </Text>
        </TouchableOpacity>
      ) : (
        <View style={styles.analysisResult}>
          <Text style={styles.analysisTitle}>{analysis.title}</Text>
          <Text style={styles.analysisContent}>{analysis.content}</Text>
          
          <View style={styles.insightsContainer}>
            <Text style={styles.insightsTitle}>Key Insights:</Text>
            {analysis.insights.map((insight, index) => (
              <Text key={index} style={styles.insightItem}>
                • {insight}
              </Text>
            ))}
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    margin: 16,
  },
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  creditInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
    padding: 12,
    backgroundColor: COLORS.lightGray,
    borderRadius: 8,
  },
  costText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
  balanceText: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  analyzeButton: {
    backgroundColor: COLORS.primary,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: COLORS.gray,
  },
  buttonText: {
    color: COLORS.white,
    fontWeight: '600',
    fontSize: 16,
  },
  analysisResult: {
    marginTop: 16,
  },
  analysisTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.primary,
    marginBottom: 8,
  },
  analysisContent: {
    fontSize: 16,
    color: COLORS.textPrimary,
    marginBottom: 16,
  },
  insightsContainer: {
    backgroundColor: COLORS.lightGray,
    padding: 12,
    borderRadius: 8,
  },
  insightsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  insightItem: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
});

export default PremiumFeatureExample;