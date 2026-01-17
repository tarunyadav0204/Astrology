import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { COLORS } from '../../utils/constants';
import { useTheme } from '../../context/ThemeContext';
import Ionicons from '@expo/vector-icons/Ionicons';

const NativeSelectorChip = ({ 
  birthData, 
  onPress, 
  style, 
  textStyle,
  maxLength = 12,
  showIcon = true 
}) => {
  const { theme, colors } = useTheme();
  if (!birthData) return null;

  const displayName = birthData.name?.slice(0, maxLength) + 
    (birthData.name?.length > maxLength ? '...' : '');

  return (
    <TouchableOpacity 
      onPress={onPress} 
      style={[
        styles.nameChip,
        {
          backgroundColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.15)' : 'rgba(249, 115, 22, 0.15)',
          borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(249, 115, 22, 0.2)'
        },
        style
      ]}
      activeOpacity={0.7}
    >
      {showIcon && <Text style={styles.chipIcon}>👤</Text>}
      <Text style={[styles.nameChipText, { color: colors.textSecondary }, textStyle]}>
        {displayName}
      </Text>
      <Ionicons name="chevron-down" size={12} color={colors.textTertiary} style={styles.dropdownIcon} />
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
  },
  dropdownIcon: {
    marginLeft: 4,
  },
});

export default NativeSelectorChip;