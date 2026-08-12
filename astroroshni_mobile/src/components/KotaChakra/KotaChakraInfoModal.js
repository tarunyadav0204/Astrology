import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
} from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { typographyTokens } from '../../theme/tokens';

const KotaChakraInfoModal = ({ visible, onClose, colors }) => {
  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <View style={[styles.modalOverlay, { backgroundColor: colors.overlay }]}>
        <View style={[styles.modalContent, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
          <View style={[styles.modalHeader, { borderBottomColor: colors.cardBorder }]}>
            <View>
              <Text style={[styles.eyebrow, { color: colors.primary }]}>CLASSICAL METHOD</Text>
              <Text style={[styles.modalTitle, { color: colors.text }]}>About Kota Chakra</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={[styles.closeButton, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]} accessibilityLabel="Close">
              <Ionicons name="close" size={21} color={colors.text} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
            <Text style={[styles.sectionTitle, { color: colors.primary }]}>What is Kota Chakra?</Text>
            <Text style={[styles.sectionText, { color: colors.text }]}>
              Kota Chakra is a classical Vedic astrology system from Uttara Kalamrita that analyzes planetary siege patterns around your birth nakshatra. It creates a fortress-like grid to assess vulnerability and protection periods.
            </Text>

            <Text style={[styles.sectionTitle, { color: colors.primary, marginTop: 18 }]}>Fortress structure</Text>
            <Text style={[styles.sectionText, { color: colors.text }]}>
              The fortress has 4 concentric zones, each containing 7 nakshatras:
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Stambha (Inner Pillar) - Core self, health, legal matters
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Madhya (Middle Fort) - Resources, family, stability
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Prakaara (Boundary Wall) - Social image, reputation
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Bahya (Outer Zone) - External relations, travel
            </Text>

            <Text style={[styles.sectionTitle, { color: colors.primary, marginTop: 18 }]}>Key players</Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Kota Swami (Gold) - Lord of Moon's sign, fortress ruler
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Kota Paala (Blue) - Nakshatra lord, fortress guard
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Malefics (Red) - Saturn, Mars, Rahu, Ketu create siege
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Benefics (Green) - Jupiter, Venus provide protection
            </Text>

            <Text style={[styles.sectionTitle, { color: colors.primary, marginTop: 18 }]}>Classical rules</Text>
            <Text style={[styles.sectionText, { color: colors.text }]}>
              According to Uttara Kalamrita:
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Any malefic in Stambha creates vulnerability
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Benefics in Stambha act as guardians
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Strong Kota Swami enhances protection
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Free Kota Paala ensures active guarding
            </Text>

            <Text style={[styles.sectionTitle, { color: colors.primary, marginTop: 18 }]}>How to use it</Text>
            <Text style={[styles.sectionText, { color: colors.text }]}>
              1. Check current fortress status for any date
            </Text>
            <Text style={[styles.sectionText, { color: colors.text }]}>
              2. Avoid important decisions during high vulnerability
            </Text>
            <Text style={[styles.sectionText, { color: colors.text }]}>
              3. Use protected periods for new ventures
            </Text>
            <Text style={[styles.sectionText, { color: colors.text }]}>
              4. Apply remedies when malefics occupy Stambha
            </Text>

            <Text style={[styles.sectionTitle, { color: colors.primary, marginTop: 18 }]}>Timing applications</Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Health treatments during protected periods
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Legal matters when Stambha is clear
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
              • Financial decisions during Madhya protection
            </Text>
            <Text style={[styles.bulletText, { color: colors.textSecondary }]}>
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
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    width: '100%',
    height: '86%',
    borderRadius: 24,
    padding: 18,
    borderWidth: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 15,
    marginBottom: 15,
    borderBottomWidth: 1,
  },
  eyebrow: {
    ...typographyTokens.eyebrow,
    marginBottom: 4,
  },
  modalTitle: {
    ...typographyTokens.sectionTitle,
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalBody: {
    flex: 1,
  },
  sectionTitle: {
    ...typographyTokens.display,
    fontSize: 19,
    lineHeight: 23,
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
