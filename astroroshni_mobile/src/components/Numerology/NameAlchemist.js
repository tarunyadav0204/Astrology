import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { API_BASE_URL } from '../../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useTheme } from '../../context/ThemeContext';

const getVerdictClass = (compound) => {
  const lucky = [1, 3, 5, 6, 10, 14, 15, 19, 21, 23, 24, 27, 32, 37, 41, 45, 46, 50];
  const unlucky = [12, 16, 18, 22, 26, 28, 29, 35, 38, 43, 44, 48];
  
  if (lucky.includes(compound)) return 'lucky';
  if (unlucky.includes(compound)) return 'unlucky';
  return 'neutral';
};

export default function NameAlchemist({ data, birthData }) {
  const { colors } = useTheme();
  const [customName, setCustomName] = useState('');
  const [nameAnalysis, setNameAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [system, setSystem] = useState('chaldean');
  const [showExplanation, setShowExplanation] = useState(false);

  const analyzeName = async () => {
    if (!customName.trim()) {
      Alert.alert('Error', 'Please enter a name to analyze');
      return;
    }

    setLoading(true);
    try {
      const token = await AsyncStorage.getItem('authToken');
      const response = await fetch(`${API_BASE_URL}/api/numerology/optimize-name`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: customName.trim(),
          system: system
        })
      });

      if (response.ok) {
        const result = await response.json();
        setNameAnalysis(result.data);
      } else {
        Alert.alert('Error', 'Failed to analyze name');
      }
    } catch (error) {
      Alert.alert('Error', 'Network error occurred');
    } finally {
      setLoading(false);
    }
  };

  const verdictClass = nameAnalysis?.compound_number != null
    ? getVerdictClass(nameAnalysis.compound_number)
    : null;
  const verdictTone = verdictClass === 'lucky'
    ? colors.success
    : verdictClass === 'unlucky'
      ? colors.error
      : colors.warning;

  return (
    <View style={styles.container}>
      {/* Current Name Analysis */}
      {data?.profile && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.text }]}>✨ Your Name Analysis</Text>
          <View style={[styles.nameCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
              <Text style={[styles.currentName, { color: colors.text }]}>{birthData?.name}</Text>
              <View style={styles.nameNumbers}>
                <View style={styles.numberItem}>
                  <Text style={[styles.numberValue, { color: colors.primary }]}>{data.profile.expression_number}</Text>
                  <Text style={[styles.numberLabel, { color: colors.textSecondary }]}>Expression</Text>
                </View>
                <View style={styles.numberItem}>
                  <Text style={[styles.numberValue, { color: colors.primary }]}>{data.profile.soul_urge_number}</Text>
                  <Text style={[styles.numberLabel, { color: colors.textSecondary }]}>Soul Urge</Text>
                </View>
                <View style={styles.numberItem}>
                  <Text style={[styles.numberValue, { color: colors.primary }]}>{data.profile.life_path_number}</Text>
                  <Text style={[styles.numberLabel, { color: colors.textSecondary }]}>Life Path</Text>
                </View>
              </View>
          </View>
        </View>
      )}

      {/* Name Optimizer */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: colors.text }]}>🎯 Name Impact Score</Text>
        <Text style={[styles.description, { color: colors.textSecondary }]}>
          See how your name affects first impressions & opportunities
        </Text>
        
        {/* System Toggle */}
        <View style={[styles.systemToggle, { backgroundColor: colors.surfaceMuted }]}>
          <TouchableOpacity 
            style={[
              styles.toggleBtn,
              system === 'chaldean' && {
                backgroundColor: colors.selectionSurface,
                borderColor: colors.selectionBorder,
              },
            ]}
            onPress={() => setSystem('chaldean')}
          >
            <Text style={[
              styles.toggleText,
              { color: system === 'chaldean' ? colors.selectionText : colors.textSecondary },
            ]}>Chaldean</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[
              styles.toggleBtn,
              system === 'pythagorean' && {
                backgroundColor: colors.selectionSurface,
                borderColor: colors.selectionBorder,
              },
            ]}
            onPress={() => setSystem('pythagorean')}
          >
            <Text style={[
              styles.toggleText,
              { color: system === 'pythagorean' ? colors.selectionText : colors.textSecondary },
            ]}>Pythagorean</Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity 
          style={styles.explanationToggle}
          onPress={() => setShowExplanation(!showExplanation)}
        >
          <Text style={[styles.explanationToggleText, { color: colors.primary }]}>🤔 Why do systems differ?</Text>
        </TouchableOpacity>
        
        {showExplanation && (
          <View style={[styles.explanationBox, { backgroundColor: colors.surfaceMuted, borderLeftColor: colors.primary }]}>
            <Text style={[styles.explanationTitle, { color: colors.text }]}>Two Different Methods:</Text>
            <Text style={[styles.explanationText, { color: colors.textSecondary }]}>
              • <Text style={[styles.bold, { color: colors.text }]}>Chaldean:</Text> Ancient system, more spiritual{"\n"}
              • <Text style={[styles.bold, { color: colors.text }]}>Pythagorean:</Text> Modern system, better for business{"\n"}{"\n"}
              <Text style={[styles.bold, { color: colors.text }]}>Which to trust?</Text>{"\n"}
              Personal guidance: Chaldean{"\n"}
              Business names: Pythagorean
            </Text>
          </View>
        )}
        
        <View style={styles.inputContainer}>
          <TextInput
            style={[
              styles.textInput,
              {
                backgroundColor: colors.cardBackground,
                color: colors.text,
                borderColor: colors.cardBorder,
              },
            ]}
            placeholder="Enter name to analyze..."
            placeholderTextColor={colors.textTertiary}
            value={customName}
            onChangeText={setCustomName}
            autoCapitalize="words"
          />
          <TouchableOpacity
            style={[styles.analyzeButton, { backgroundColor: colors.primary }]}
            onPress={analyzeName}
            disabled={loading}
          >
              {loading ? (
                <ActivityIndicator size="small" color={colors.onPrimary} />
              ) : (
                <Text style={[styles.buttonText, { color: colors.onPrimary }]}>Analyze</Text>
              )}
          </TouchableOpacity>
        </View>

        {/* Analysis Results */}
        {nameAnalysis && (
          <View style={styles.resultsSection}>
            <Text style={[styles.resultsTitle, { color: colors.text }]}>Analysis Results</Text>
            
            <View style={[styles.resultCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
                <Text style={[styles.analyzedName, { color: colors.text }]}>{customName}</Text>
                
                {nameAnalysis.numbers && (
                  <View style={styles.resultNumbers}>
                    {Object.entries(nameAnalysis.numbers).map(([key, value]) => (
                      <View key={key} style={styles.resultNumberItem}>
                        <Text style={[styles.resultNumberValue, { color: colors.primary }]}>{value}</Text>
                        <Text style={[styles.resultNumberLabel, { color: colors.textSecondary }]}>{key.replace('_', ' ')}</Text>
                      </View>
                    ))}
                  </View>
                )}

                {nameAnalysis.compound_number && (
                  <View style={styles.verdictSection}>
                    <View style={styles.compoundDisplay}>
                      <Text style={[styles.compoundNumber, { color: colors.text }]}>{nameAnalysis.compound_number}</Text>
                      <Text style={[styles.compoundLabel, { color: colors.textSecondary }]}>Compound</Text>
                    </View>
                    <View style={[styles.verdictBadge, { backgroundColor: verdictTone }]}>
                      <Text style={[styles.verdictStatus, { color: colors.onPrimary }]}>
                        {verdictClass === 'lucky' ? '✅ Strong Energy' :
                         verdictClass === 'unlucky' ? '❌ Challenging' :
                         '⚠️ Neutral Energy'}
                      </Text>
                    </View>
                    <Text style={[styles.verdictReason, { color: colors.textSecondary }]}>
                      {verdictClass === 'lucky' ? 
                        'Creates positive first impressions and attracts opportunities.' :
                        verdictClass === 'unlucky' ?
                        'May create obstacles. Consider variations for better energy.' :
                        'Balanced energy. Can be enhanced with modifications.'}
                    </Text>
                  </View>
                )}
            </View>
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingVertical: 20,
  },
  section: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 16,
    textAlign: 'center',
  },
  nameCard: {
    marginBottom: 20,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
  },
  currentName: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 16,
  },
  nameNumbers: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
  },
  numberItem: {
    alignItems: 'center',
  },
  numberValue: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  numberLabel: {
    fontSize: 10,
    textAlign: 'center',
  },
  description: {
    fontSize: 12,
    textAlign: 'center',
    marginBottom: 20,
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    marginBottom: 20,
    gap: 12,
  },
  textInput: {
    flex: 1,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    borderWidth: 1,
  },
  analyzeButton: {
    borderRadius: 12,
    paddingHorizontal: 20,
    paddingVertical: 12,
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 80,
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  resultsSection: {
    marginTop: 20,
  },
  resultsTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  resultCard: {
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  analyzedName: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 16,
  },
  resultNumbers: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  resultNumberItem: {
    alignItems: 'center',
    marginBottom: 8,
    minWidth: '30%',
  },
  resultNumberValue: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 4,
  },
  resultNumberLabel: {
    fontSize: 10,
    textAlign: 'center',
    textTransform: 'capitalize',
  },
  verdictSection: {
    marginTop: 12,
  },
  verdictBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  verdictStatus: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  verdictReason: {
    fontSize: 12,
    lineHeight: 16,
  },
  systemToggle: {
    flexDirection: 'row',
    borderRadius: 20,
    padding: 4,
    marginBottom: 16,
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  toggleText: {
    fontSize: 12,
    fontWeight: '500',
  },
  explanationToggle: {
    alignItems: 'center',
    marginBottom: 16,
  },
  explanationToggleText: {
    fontSize: 12,
    fontWeight: '500',
  },
  explanationBox: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    borderLeftWidth: 3,
  },
  explanationTitle: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 6,
  },
  explanationText: {
    fontSize: 11,
    lineHeight: 14,
  },
  bold: {
    fontWeight: '600',
  },
  compoundDisplay: {
    alignItems: 'center',
    marginBottom: 12,
  },
  compoundNumber: {
    fontSize: 32,
    fontWeight: '700',
  },
  compoundLabel: {
    fontSize: 12,
    marginTop: 4,
  },
});
