import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
} from 'react-native';

const KotaChakraInfoModal = ({ visible, onClose, colors }) => {
  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View style={[styles.modalContent, { backgroundColor: colors?.cardBackground || '#1a1a1a' }]}>
          <View style={styles.modalHeader}>
            <Text style={[styles.modalTitle, { color: colors?.text || '#ffffff' }]}>
              🏰 About Kota Chakra
            </Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={[styles.closeButtonText, { color: colors?.text || '#ffffff' }]}>×</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
            <Text style={[styles.sectionTitle, { color: colors?.primary || '#007AFF' }]}>What is Kota Chakra?</Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              Kota Chakra is a classical Vedic astrology system from Uttara Kalamrita that analyzes planetary siege patterns around your birth nakshatra. It creates a fortress-like grid to assess vulnerability and protection periods.
            </Text>

            <Text style={[styles.sectionTitle, { color: colors?.primary || '#007AFF', marginTop: 16 }]}>Fortress Structure</Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              The fortress has 4 concentric zones, each containing 7 nakshatras:
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Stambha (Inner Pillar) - Core self, health, legal matters
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Madhya (Middle Fort) - Resources, family, stability
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Prakaara (Boundary Wall) - Social image, reputation
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Bahya (Outer Zone) - External relations, travel
            </Text>

            <Text style={[styles.sectionTitle, { color: colors?.primary || '#007AFF', marginTop: 16 }]}>Key Players</Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Kota Swami (Gold) - Lord of Moon's sign, fortress ruler
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Kota Paala (Blue) - Nakshatra lord, fortress guard
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Malefics (Red) - Saturn, Mars, Rahu, Ketu create siege
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Benefics (Green) - Jupiter, Venus provide protection
            </Text>

            <Text style={[styles.sectionTitle, { color: colors?.primary || '#007AFF', marginTop: 16 }]}>Classical Rules</Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              According to Uttara Kalamrita:
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Any malefic in Stambha creates vulnerability
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Benefics in Stambha act as guardians
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Strong Kota Swami enhances protection
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Free Kota Paala ensures active guarding
            </Text>

            <Text style={[styles.sectionTitle, { color: colors?.primary || '#007AFF', marginTop: 16 }]}>How to Use</Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              1. Check current fortress status for any date
            </Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              2. Avoid important decisions during high vulnerability
            </Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              3. Use protected periods for new ventures
            </Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              4. Apply remedies when malefics occupy Stambha
            </Text>

            <Text style={[styles.sectionTitle, { color: colors?.primary || '#007AFF', marginTop: 16 }]}>Timing Applications</Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Health treatments during protected periods
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Legal matters when Stambha is clear
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Financial decisions during Madhya protection
            </Text>
            <Text style={[styles.bulletText, { color: colors?.textSecondary || '#cccccc' }]}>
              • Public events when Prakaara is favorable
            </Text>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    width: '100%',
    height: '85%',
    borderRadius: 16,
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
  },
  closeButton: {
    padding: 8,
  },
  closeButtonText: {
    fontSize: 18,
    fontWeight: '600',
  },
  modalBody: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  sectionText: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 4,
  },
  bulletText: {
    fontSize: 13,
    lineHeight: 18,
    marginLeft: 8,
    marginBottom: 2,
  },
});

export default KotaChakraInfoModal;