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

const PlanetDetailsModal = ({ visible, onClose, planetDetails, colors }) => {
  if (!planetDetails) {
    return null;
  }

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
              <Text style={[styles.eyebrow, { color: colors.primary }]}>PLANET IN THE FORTRESS</Text>
              <Text style={[styles.modalTitle, { color: colors.text }]}>{planetDetails.role_icon} {planetDetails.planet}</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={[styles.closeButton, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]} accessibilityLabel="Close">
              <Ionicons name="close" size={21} color={colors.text} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
            <View style={[styles.detailSection, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
              <Text style={[styles.sectionTitle, { color: colors.primary }]}>ROLE</Text>
              <Text style={[styles.sectionText, { color: colors.text }]}>{planetDetails.role}</Text>
            </View>
            <View style={[styles.detailSection, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
              <Text style={[styles.sectionTitle, { color: colors.primary }]}>CURRENT POSITION</Text>
              <Text style={[styles.sectionText, { color: colors.text }]}>{planetDetails.position}</Text>
              <Text style={[styles.subText, { color: colors.textSecondary }]}>Nakshatra: {planetDetails.nakshatra} · Motion: {planetDetails.motion}</Text>
            </View>
            <View style={[styles.detailSection, { backgroundColor: colors.surfaceMuted, borderColor: colors.cardBorder }]}>
              <Text style={[styles.sectionTitle, { color: colors.primary }]}>FORTRESS LOCATION</Text>
              <Text style={[styles.sectionText, { color: colors.text }]}>{planetDetails.fortress_location}</Text>
            </View>
            <View style={[styles.detailSection, { backgroundColor: colors.cosmicSurface, borderColor: colors.cosmicLine }]}>
              <Text style={[styles.sectionTitle, { color: colors.accent }]}>CURRENT EFFECT</Text>
              <Text style={[styles.sectionText, { color: colors.textInverse }]}>{planetDetails.effect}</Text>
            </View>
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
    height: '80%',
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
  detailSection: {
    marginBottom: 10,
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
  },
  sectionTitle: {
    ...typographyTokens.eyebrow,
    marginBottom: 6,
  },
  sectionText: {
    fontSize: 16,
    lineHeight: 22,
  },
  subText: {
    fontSize: 12,
    marginTop: 4,
  },
});

export default PlanetDetailsModal;
