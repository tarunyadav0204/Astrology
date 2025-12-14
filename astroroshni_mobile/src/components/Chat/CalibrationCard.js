import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

const CalibrationCard = ({ data, onConfirm, onReject }) => {
  const getIcon = (type) => {
    if (type === 'relationship') return '💍';
    if (type === 'career') return '💼';
    return '⭐';
  };

  return (
    <View style={styles.card}>
      <Text style={styles.header}>🔮 TIMELINE CALIBRATION</Text>
      
      <View style={styles.content}>
        <Text style={styles.year}>📅 {data.year} (Age {data.age})</Text>
        <Text style={styles.type}>{getIcon(data.type)} {data.label}</Text>
        <Text style={styles.confidence}>⭐ Confidence: {data.confidence}</Text>
        <Text style={styles.reason}>{data.reason}</Text>
      </View>

      <View style={styles.buttons}>
        <TouchableOpacity style={styles.yesBtn} onPress={onConfirm}>
          <Text style={styles.btnText}>✓ YES</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.noBtn} onPress={onReject}>
          <Text style={styles.btnText}>✗ NO</Text>
        </TouchableOpacity>
      </View>
      
      <Text style={styles.question}>
        Did you experience this event that year?
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 8,
    borderWidth: 2,
    borderColor: '#FFD700',
  },
  header: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#FFD700',
    marginBottom: 12,
  },
  content: {
    marginBottom: 16,
  },
  year: { 
    fontSize: 16, 
    color: '#fff', 
    marginBottom: 4 
  },
  type: { 
    fontSize: 16, 
    color: '#fff', 
    marginBottom: 4 
  },
  confidence: { 
    fontSize: 14, 
    color: '#FFD700', 
    marginBottom: 8 
  },
  reason: { 
    fontSize: 12, 
    color: '#aaa', 
    fontStyle: 'italic' 
  },
  buttons: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  yesBtn: {
    flex: 1,
    backgroundColor: '#4CAF50',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  noBtn: {
    flex: 1,
    backgroundColor: '#f44336',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  question: {
    fontSize: 12,
    color: '#ccc',
    textAlign: 'center',
  },
});

export default CalibrationCard;
