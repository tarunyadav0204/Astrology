import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS } from '../../../utils/constants';

export default function GenderScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>Gender Screen - Coming Soon</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  text: { color: COLORS.white, fontSize: 18 },
});