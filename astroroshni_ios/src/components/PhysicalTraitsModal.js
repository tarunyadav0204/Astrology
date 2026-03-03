import React from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';

const { width, height } = Dimensions.get('window');

const getTraitIcon = (iconType) => {
  const iconMap = {
    'eyes': 'eye-outline',
    'hair': 'cut-outline',
    'face': 'happy-outline',
    'body': 'body-outline',
    'mark': 'radio-button-on-outline',
    'skin': 'color-palette-outline',
    'build': 'fitness-outline',
    'height': 'resize-outline',
    'nose': 'triangle-outline',
    'teeth': 'medical-outline',
    'hands': 'hand-left-outline',
    'default': 'star-outline'
  };
  return iconMap[iconType] || iconMap.default;
};

const getTraitColor = (iconType) => {
  const colorMap = {
    'eyes': '#4FC3F7',
    'hair': '#8D6E63',
    'face': '#FFB74D',
    'body': '#81C784',
    'mark': '#E57373',
    'skin': '#F06292',
    'build': '#9575CD',
    'height': '#64B5F6',
    'nose': '#FFD54F',
    'teeth': '#A1C181',
    'hands': '#FFAB91',
    'default': '#FFD700'
  };
  return colorMap[iconType] || colorMap.default;
};

export const PhysicalTraitsModal = ({ visible, traits, onClose, onFeedback, hasFeedback = false }) => {
  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          <LinearGradient
            colors={['#1a0033', '#2d1b4e', '#4a2c6d']}
            style={styles.gradient}
          >
            {/* Header */}
            <View style={styles.header}>
              <View style={styles.headerIcon}>
                <Ionicons name="scan-outline" size={24} color="#FFD700" />
              </View>
              <Text style={styles.headerTitle}>Physical Traits Revealed</Text>
              <Text style={styles.headerSubtitle}>
                Your cosmic blueprint shows these distinctive features
              </Text>
            </View>

            {/* Traits List */}
            <ScrollView style={styles.traitsContainer} showsVerticalScrollIndicator={false}>
              {traits.map((trait, index) => (
                <View key={index} style={styles.traitCard}>
                  <LinearGradient
                    colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']}
                    style={styles.traitGradient}
                  >
                    <View style={[styles.traitIconContainer, { backgroundColor: getTraitColor(trait.icon) + '20' }]}>
                      <Ionicons 
                        name={getTraitIcon(trait.icon)} 
                        size={24} 
                        color={getTraitColor(trait.icon)} 
                      />
                    </View>
                    
                    <View style={styles.traitContent}>
                      <Text style={styles.traitLabel}>{trait.label}</Text>
                      <Text style={styles.traitSource}>Source: {trait.source}</Text>
                    </View>
                    
                    <View style={styles.confidenceContainer}>
                      <Text style={styles.confidenceText}>
                        {trait.confidence ? `${trait.confidence}%` : '85%'}
                      </Text>
                    </View>
                  </LinearGradient>
                </View>
              ))}
            </ScrollView>

            {/* Verification Section */}
            {!hasFeedback && (
              <View style={styles.verificationSection}>
                <Text style={styles.verificationTitle}>
                  Do these traits match your appearance?
                </Text>
                
                <View style={styles.buttonContainer}>
                  <TouchableOpacity
                    style={styles.feedbackButton}
                    onPress={() => onFeedback('accurate')}
                  >
                    <LinearGradient
                      colors={['#4CAF50', '#45a049']}
                      style={styles.buttonGradient}
                    >
                      <Ionicons name="checkmark-circle" size={20} color="#fff" />
                      <Text style={styles.buttonText}>Very Accurate!</Text>
                    </LinearGradient>
                  </TouchableOpacity>
                  
                  <TouchableOpacity
                    style={styles.feedbackButton}
                    onPress={() => onFeedback('inaccurate')}
                  >
                    <LinearGradient
                      colors={['#f44336', '#d32f2f']}
                      style={styles.buttonGradient}
                    >
                      <Ionicons name="close-circle" size={20} color="#fff" />
                      <Text style={styles.buttonText}>Not Accurate</Text>
                    </LinearGradient>
                  </TouchableOpacity>
                </View>
              </View>
            )}
            
            {hasFeedback && (
              <View style={styles.verificationSection}>
                <Text style={[styles.verificationTitle, { color: 'rgba(255, 255, 255, 0.6)' }]}>
                  ✓ Feedback already provided
                </Text>
              </View>
            )}

            {/* Close Button */}
            <TouchableOpacity style={styles.closeButton} onPress={onClose}>
              <Ionicons name="close" size={24} color="rgba(255, 255, 255, 0.7)" />
            </TouchableOpacity>
          </LinearGradient>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 10,
  },
  modalContainer: {
    width: width * 0.95,
    height: height * 0.85,
    borderRadius: 20,
    overflow: 'hidden',
  },
  gradient: {
    flex: 1,
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  headerIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    lineHeight: 20,
  },
  traitsContainer: {
    flex: 1,
    marginBottom: 20,
  },
  traitCard: {
    marginBottom: 12,
    borderRadius: 16,
    overflow: 'hidden',
  },
  traitGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  traitIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  traitContent: {
    flex: 1,
  },
  traitLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 4,
    lineHeight: 22,
  },
  traitSource: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.6)',
    fontStyle: 'italic',
  },
  confidenceContainer: {
    backgroundColor: 'rgba(255, 215, 0, 0.2)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.3)',
  },
  confidenceText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFD700',
  },
  verificationSection: {
    alignItems: 'center',
    marginTop: 10,
  },
  verificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 16,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  feedbackButton: {
    flex: 1,
    borderRadius: 12,
    overflow: 'hidden',
  },
  buttonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    marginLeft: 8,
  },
  closeButton: {
    position: 'absolute',
    top: 15,
    right: 15,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
});