import React from 'react';
import { Modal, View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const PremiumAnalysisModal = ({ visible, onClose, premiumCost, standardCost }) => {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          <ScrollView showsVerticalScrollIndicator={false}>
            {/* Header */}
            <LinearGradient
              colors={['#ff6b35', '#ffd700']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.header}
            >
              <Text style={styles.headerIcon}>⚡</Text>
              <Text style={styles.headerTitle}>Premium Deep Analysis</Text>
              <Text style={styles.headerSubtitle}>Advanced Astrological Insights</Text>
            </LinearGradient>

            {/* Content */}
            <View style={styles.content}>
              {/* What You Get */}
              <Text style={styles.sectionTitle}>What You Get:</Text>
              
              <View style={styles.featureItem}>
                <Text style={styles.featureIcon}>🧠</Text>
                <View style={styles.featureText}>
                  <Text style={styles.featureTitle}>Deep Thinking AI</Text>
                  <Text style={styles.featureDescription}>
                    Advanced AI model that analyzes charts with highest level of accuracy
                  </Text>
                </View>
              </View>

              <View style={styles.featureItem}>
                <Text style={styles.featureIcon}>✨</Text>
                <View style={styles.featureText}>
                  <Text style={styles.featureTitle}>Deeper Insights</Text>
                  <Text style={styles.featureDescription}>
                    Advanced astrological calculations beyond basic analysis
                  </Text>
                </View>
              </View>

              <View style={styles.featureItem}>
                <Text style={styles.featureIcon}>🎯</Text>
                <View style={styles.featureText}>
                  <Text style={styles.featureTitle}>Precise Predictions</Text>
                  <Text style={styles.featureDescription}>
                    Uses divisional charts (D9, D10, D12) for accuracy
                  </Text>
                </View>
              </View>

              <View style={styles.featureItem}>
                <Text style={styles.featureIcon}>📊</Text>
                <View style={styles.featureText}>
                  <Text style={styles.featureTitle}>Multi-System Analysis</Text>
                  <Text style={styles.featureDescription}>
                    Combines Vimshottari, Chara, and Yogini Dashas
                  </Text>
                </View>
              </View>

              <View style={styles.featureItem}>
                <Text style={styles.featureIcon}>🔮</Text>
                <View style={styles.featureText}>
                  <Text style={styles.featureTitle}>Comprehensive Context</Text>
                  <Text style={styles.featureDescription}>
                    Analyzes planetary strengths, yogas, and aspects
                  </Text>
                </View>
              </View>

              <View style={styles.featureItem}>
                <Text style={styles.featureIcon}>⏱️</Text>
                <View style={styles.featureText}>
                  <Text style={styles.featureTitle}>Better Timing</Text>
                  <Text style={styles.featureDescription}>
                    Includes transit activations and dasha-bhukti periods
                  </Text>
                </View>
              </View>

              <View style={styles.featureItem}>
                <Text style={styles.featureIcon}>💎</Text>
                <View style={styles.featureText}>
                  <Text style={styles.featureTitle}>Classical References</Text>
                  <Text style={styles.featureDescription}>
                    Traditional wisdom from BPHS, Jataka Parijata, Saravali, Phaladeepika, Hora Sara, Uttara Kalamrita, Jaimini Sutras, Laghu Parashari, Chamatkar Chintamani, and Mansagari
                  </Text>
                </View>
              </View>

              {/* Comparison */}
              <View style={styles.comparisonContainer}>
                <Text style={styles.comparisonTitle}>Example Comparison:</Text>
                
                <View style={styles.comparisonBox}>
                  <Text style={styles.comparisonLabel}>Standard Analysis:</Text>
                  <Text style={styles.comparisonText}>
                    "Your career looks promising in the next 2 years"
                  </Text>
                </View>

                <View style={[styles.comparisonBox, styles.premiumBox]}>
                  <Text style={[styles.comparisonLabel, styles.premiumLabel]}>Premium Analysis:</Text>
                  <Text style={styles.comparisonText}>
                    "Your 10th lord Jupiter in D10 chart shows strong career potential. During Jupiter-Venus dasha (Mar 2024 - Jul 2026), with Jupiter transiting your 10th house, expect promotion or business growth. Your Gajakesari yoga activates, bringing recognition."
                  </Text>
                </View>
              </View>

              {/* Cost */}
              <View style={styles.costContainer}>
                <Text style={styles.costLabel}>Cost:</Text>
                <View style={styles.costRow}>
                  <View style={styles.costItem}>
                    <Text style={styles.costType}>Standard</Text>
                    <Text style={styles.costValue}>{standardCost} credit</Text>
                  </View>
                  <Text style={styles.costVs}>vs</Text>
                  <View style={[styles.costItem, styles.premiumCostItem]}>
                    <Text style={[styles.costType, styles.premiumCostType]}>Premium</Text>
                    <Text style={[styles.costValue, styles.premiumCostValue]}>{premiumCost} credits</Text>
                  </View>
                </View>
              </View>

              {/* Perfect For */}
              <View style={styles.perfectForContainer}>
                <Text style={styles.perfectForTitle}>Perfect for:</Text>
                <Text style={styles.perfectForText}>
                  Career timing • Marriage compatibility • Health analysis • Wealth predictions • Important life decisions
                </Text>
              </View>
            </View>

            {/* Close Button */}
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <Text style={styles.closeButtonText}>Got it!</Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContainer: {
    backgroundColor: '#fff',
    borderRadius: 20,
    width: '100%',
    maxWidth: 500,
    maxHeight: '90%',
    overflow: 'hidden',
  },
  header: {
    padding: 24,
    alignItems: 'center',
  },
  headerIcon: {
    fontSize: 48,
    marginBottom: 8,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  content: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 16,
  },
  featureItem: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-start',
  },
  featureIcon: {
    fontSize: 24,
    marginRight: 12,
    marginTop: 2,
  },
  featureText: {
    flex: 1,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 2,
  },
  featureDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
  comparisonContainer: {
    marginTop: 24,
    marginBottom: 20,
  },
  comparisonTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 12,
  },
  comparisonBox: {
    backgroundColor: '#f5f5f5',
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
  },
  premiumBox: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  comparisonLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 6,
  },
  premiumLabel: {
    color: '#ff6b35',
  },
  comparisonText: {
    fontSize: 13,
    color: '#333',
    lineHeight: 18,
  },
  costContainer: {
    backgroundColor: '#f9f9f9',
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
  },
  costLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
    marginBottom: 12,
    textAlign: 'center',
  },
  costRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  costItem: {
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  premiumCostItem: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    paddingVertical: 8,
    paddingHorizontal: 20,
    borderRadius: 12,
  },
  costType: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  premiumCostType: {
    color: '#ff6b35',
    fontWeight: '600',
  },
  costValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  premiumCostValue: {
    color: '#ff6b35',
    fontSize: 18,
  },
  costVs: {
    fontSize: 14,
    color: '#999',
    marginHorizontal: 12,
  },
  perfectForContainer: {
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  perfectForTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
  },
  perfectForText: {
    fontSize: 13,
    color: '#666',
    lineHeight: 18,
  },
  closeButton: {
    backgroundColor: '#ff6b35',
    margin: 20,
    marginTop: 0,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default PremiumAnalysisModal;
