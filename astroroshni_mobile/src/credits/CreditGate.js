import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { COLORS } from '../utils/constants';
import { useCredits } from './CreditContext';

const CreditGate = ({ 
  children, 
  cost, 
  feature, 
  description, 
  onPurchase,
  showBalance = true 
}) => {
  const { credits, spendCredits } = useCredits();

  const handlePurchase = async () => {
    if (credits < cost) {
      Alert.alert(
        'Insufficient Credits',
        `You need ${cost} credits for this feature. You have ${credits} credits.`,
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Get Credits', onPress: () => {/* Navigate to credit screen */} }
        ]
      );
      return;
    }

    Alert.alert(
      'Confirm Purchase',
      `Use ${cost} credits for ${description}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          onPress: async () => {
            const success = await spendCredits(cost, feature, description);
            if (success && onPurchase) {
              onPurchase();
            }
          }
        }
      ]
    );
  };

  const hasEnoughCredits = credits >= cost;

  return (
    <View style={styles.container}>
      {showBalance && (
        <View style={styles.balanceInfo}>
          <Text style={styles.balanceText}>Balance: {credits} credits</Text>
        </View>
      )}
      
      <View style={styles.featureInfo}>
        <Text style={styles.featureTitle}>{description}</Text>
        <Text style={styles.costText}>Cost: {cost} credits</Text>
      </View>

      <TouchableOpacity
        style={[
          styles.purchaseButton,
          !hasEnoughCredits && styles.buttonDisabled
        ]}
        onPress={handlePurchase}
        disabled={!hasEnoughCredits}
      >
        <Text style={styles.buttonText}>
          {hasEnoughCredits ? 'Use Credits' : 'Insufficient Credits'}
        </Text>
      </TouchableOpacity>

      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    margin: 16,
  },
  balanceInfo: {
    alignItems: 'center',
    marginBottom: 12,
  },
  balanceText: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  featureInfo: {
    alignItems: 'center',
    marginBottom: 16,
  },
  featureTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  costText: {
    fontSize: 16,
    color: COLORS.primary,
    fontWeight: '500',
  },
  purchaseButton: {
    backgroundColor: COLORS.primary,
    padding: 12,
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
});

export default CreditGate;