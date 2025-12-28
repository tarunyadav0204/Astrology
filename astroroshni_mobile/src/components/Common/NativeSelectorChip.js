import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { COLORS } from '../../utils/constants';
import Ionicons from '@expo/vector-icons/Ionicons';

const NativeSelectorChip = ({ 
  birthData, 
  onPress, 
  style, 
  textStyle,
  maxLength = 12,
  showIcon = true 
}) => {
  if (!birthData) return null;

  const displayName = birthData.name?.slice(0, maxLength) + 
    (birthData.name?.length > maxLength ? '...' : '');

  return (
    <TouchableOpacity 
      onPress={onPress} 
      style={[styles.nameChip, style]}
      activeOpacity={0.7}
    >
      {showIcon && <Text style={styles.chipIcon}>👤</Text>}
      <Text style={[styles.nameChipText, textStyle]}>
        {displayName}
      </Text>
      <Ionicons name="chevron-down" size={12} color="rgba(255, 255, 255, 0.7)" style={styles.dropdownIcon} />
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  nameChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  chipIcon: {
    fontSize: 12,
    marginRight: 4,
  },
  nameChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.9)',
  },
  dropdownIcon: {
    marginLeft: 4,
  },
});

export default NativeSelectorChip;