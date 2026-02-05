import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ScrollView,
} from 'react-native';

const PlanetDetailsModal = ({ visible, onClose, planetDetails, colors }) => {
  console.log('PlanetDetailsModal received:', planetDetails);
  
  if (!planetDetails) {
    console.log('No planet details provided');
    return null;
  }

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
              {planetDetails.role_icon} {planetDetails.planet}
            </Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Text style={[styles.closeButtonText, { color: colors?.text || '#ffffff' }]}>×</Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalBody} showsVerticalScrollIndicator={false}>
            <Text style={[styles.sectionTitle, { color: colors?.primary || '#007AFF' }]}>Role</Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              {planetDetails.role}
            </Text>

            <Text style={[styles.sectionTitle, { color: colors?.primary || '#007AFF', marginTop: 16 }]}>Current Position</Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              {planetDetails.position}
            </Text>
            <Text style={[styles.subText, { color: colors?.textSecondary || '#cccccc' }]}>
              Nakshatra: {planetDetails.nakshatra} • Motion: {planetDetails.motion}
            </Text>

            <Text style={[styles.sectionTitle, { color: colors?.primary || '#007AFF', marginTop: 16 }]}>Fortress Location</Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              {planetDetails.fortress_location}
            </Text>

            <Text style={[styles.sectionTitle, { color: colors?.primary || '#007AFF', marginTop: 16 }]}>Current Effect</Text>
            <Text style={[styles.sectionText, { color: colors?.text || '#ffffff' }]}>
              {planetDetails.effect}
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
    height: '80%',
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
  detailSection: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
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