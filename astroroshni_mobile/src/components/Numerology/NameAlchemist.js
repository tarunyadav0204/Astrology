import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS, API_BASE_URL, getEndpoint } from '../../utils/constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

const getVerdictClass = (compound) => {
  const lucky = [1, 3, 5, 6, 10, 14, 15, 19, 21, 23, 24, 27, 32, 37, 41, 45, 46, 50];
  const unlucky = [12, 16, 18, 22, 26, 28, 29, 35, 38, 43, 44, 48];
  
  if (lucky.includes(compound)) return 'lucky';
  if (unlucky.includes(compound)) return 'unlucky';
  return 'neutral';
};

export default function NameAlchemist({ data, birthData }) {
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

  return (
    <View style={styles.container}>
      {/* Current Name Analysis */}
      {data?.profile && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>✨ Your Name Analysis</Text>
          <View style={styles.nameCard}>
            <LinearGradient colors={['rgba(79, 172, 254, 0.2)', 'rgba(0, 242, 254, 0.1)']} style={styles.nameGradient}>
              <Text style={styles.currentName}>{birthData?.name}</Text>
              <View style={styles.nameNumbers}>
                <View style={styles.numberItem}>
                  <Text style={styles.numberValue}>{data.profile.expression_number}</Text>
                  <Text style={styles.numberLabel}>Expression</Text>
                </View>
                <View style={styles.numberItem}>
                  <Text style={styles.numberValue}>{data.profile.soul_urge_number}</Text>
                  <Text style={styles.numberLabel}>Soul Urge</Text>
                </View>
                <View style={styles.numberItem}>
                  <Text style={styles.numberValue}>{data.profile.life_path_number}</Text>
                  <Text style={styles.numberLabel}>Life Path</Text>
                </View>
              </View>
            </LinearGradient>
          </View>
        </View>
      )}

      {/* Name Optimizer */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🎯 Name Impact Score</Text>
        <Text style={styles.description}>
          See how your name affects first impressions & opportunities
        </Text>
        
        {/* System Toggle */}
        <View style={styles.systemToggle}>
          <TouchableOpacity 
            style={[styles.toggleBtn, system === 'chaldean' && styles.activeToggle]}
            onPress={() => setSystem('chaldean')}
          >
            <Text style={[styles.toggleText, system === 'chaldean' && styles.activeToggleText]}>Chaldean</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.toggleBtn, system === 'pythagorean' && styles.activeToggle]}
            onPress={() => setSystem('pythagorean')}
          >
            <Text style={[styles.toggleText, system === 'pythagorean' && styles.activeToggleText]}>Pythagorean</Text>
          </TouchableOpacity>
        </View>
        
        <TouchableOpacity 
          style={styles.explanationToggle}
          onPress={() => setShowExplanation(!showExplanation)}
        >
          <Text style={styles.explanationToggleText}>🤔 Why do systems differ?</Text>
        </TouchableOpacity>
        
        {showExplanation && (
          <View style={styles.explanationBox}>
            <Text style={styles.explanationTitle}>Two Different Methods:</Text>
            <Text style={styles.explanationText}>
              • <Text style={styles.bold}>Chaldean:</Text> Ancient system, more spiritual{"\n"}
              • <Text style={styles.bold}>Pythagorean:</Text> Modern system, better for business{"\n"}{"\n"}
              <Text style={styles.bold}>Which to trust?</Text>{"\n"}
              Personal guidance: Chaldean{"\n"}
              Business names: Pythagorean
            </Text>
          </View>
        )}
        
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            placeholder="Enter name to analyze..."
            placeholderTextColor="rgba(255, 255, 255, 0.5)"
            value={customName}
            onChangeText={setCustomName}
            autoCapitalize="words"
          />
          <TouchableOpacity
            style={styles.analyzeButton}
            onPress={analyzeName}
            disabled={loading}
          >
            <LinearGradient colors={['#4facfe', '#00f2fe']} style={styles.buttonGradient}>
              {loading ? (
                <ActivityIndicator size="small" color={COLORS.white} />
              ) : (
                <Text style={styles.buttonText}>Analyze</Text>
              )}
            </LinearGradient>
          </TouchableOpacity>
        </View>

        {/* Analysis Results */}
        {nameAnalysis && (
          <View style={styles.resultsSection}>
            <Text style={styles.resultsTitle}>Analysis Results</Text>
            
            <View style={styles.resultCard}>
              <LinearGradient colors={['rgba(255, 255, 255, 0.1)', 'rgba(255, 255, 255, 0.05)']} style={styles.resultGradient}>
                <Text style={styles.analyzedName}>{customName}</Text>
                
                {nameAnalysis.numbers && (
                  <View style={styles.resultNumbers}>
                    {Object.entries(nameAnalysis.numbers).map(([key, value]) => (
                      <View key={key} style={styles.resultNumberItem}>
                        <Text style={styles.resultNumberValue}>{value}</Text>
                        <Text style={styles.resultNumberLabel}>{key.replace('_', ' ')}</Text>
                      </View>
                    ))}
                  </View>
                )}

                {nameAnalysis.compound_number && (
                  <View style={styles.verdictSection}>
                    <View style={styles.compoundDisplay}>
                      <Text style={styles.compoundNumber}>{nameAnalysis.compound_number}</Text>
                      <Text style={styles.compoundLabel}>Compound</Text>
                    </View>
                    <View style={[styles.verdictBadge, 
                      getVerdictClass(nameAnalysis.compound_number) === 'lucky' && styles.luckyBadge,
                      getVerdictClass(nameAnalysis.compound_number) === 'unlucky' && styles.unluckyBadge,
                      getVerdictClass(nameAnalysis.compound_number) === 'neutral' && styles.neutralBadge
                    ]}>
                      <Text style={styles.verdictStatus}>
                        {getVerdictClass(nameAnalysis.compound_number) === 'lucky' ? '✅ Strong Energy' :
                         getVerdictClass(nameAnalysis.compound_number) === 'unlucky' ? '❌ Challenging' :
                         '⚠️ Neutral Energy'}
                      </Text>
                    </View>
                    <Text style={styles.verdictReason}>
                      {getVerdictClass(nameAnalysis.compound_number) === 'lucky' ? 
                        'Creates positive first impressions and attracts opportunities.' :
                        getVerdictClass(nameAnalysis.compound_number) === 'unlucky' ?
                        'May create obstacles. Consider variations for better energy.' :
                        'Balanced energy. Can be enhanced with modifications.'}
                    </Text>
                  </View>
                )}
              </LinearGradient>
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
    color: COLORS.white,
    marginBottom: 16,
    textAlign: 'center',
  },
  nameCard: {
    marginBottom: 20,
  },
  nameGradient: {
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(79, 172, 254, 0.3)',
    alignItems: 'center',
  },
  currentName: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
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
    color: '#4facfe',
    marginBottom: 4,
  },
  numberLabel: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
  },
  description: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
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
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: COLORS.white,
    fontSize: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  analyzeButton: {
    borderRadius: 12,
    overflow: 'hidden',
  },
  buttonGradient: {
    paddingHorizontal: 20,
    paddingVertical: 12,
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 80,
  },
  buttonText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
  resultsSection: {
    marginTop: 20,
  },
  resultsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 12,
  },
  resultCard: {
    marginBottom: 16,
  },
  resultGradient: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  analyzedName: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.white,
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
    color: '#4facfe',
    marginBottom: 4,
  },
  resultNumberLabel: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    textTransform: 'capitalize',
  },
  verdictSection: {
    marginTop: 12,
  },
  verdictTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 8,
  },
  verdictBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  excellentBadge: {
    backgroundColor: 'rgba(34, 197, 94, 0.3)',
  },
  goodBadge: {
    backgroundColor: 'rgba(59, 130, 246, 0.3)',
  },
  averageBadge: {
    backgroundColor: 'rgba(245, 158, 11, 0.3)',
  },
  challengingBadge: {
    backgroundColor: 'rgba(239, 68, 68, 0.3)',
  },
  verdictStatus: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.white,
    textTransform: 'capitalize',
  },
  verdictReason: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
    lineHeight: 16,
  },
  systemToggle: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
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
  },
  activeToggle: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  toggleText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    fontWeight: '500',
  },
  activeToggleText: {
    color: COLORS.white,
    fontWeight: '600',
  },
  explanationToggle: {
    alignItems: 'center',
    marginBottom: 16,
  },
  explanationToggleText: {
    fontSize: 12,
    color: '#4facfe',
    fontWeight: '500',
  },
  explanationBox: {
    backgroundColor: 'rgba(79, 172, 254, 0.1)',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    borderLeftWidth: 3,
    borderLeftColor: '#4facfe',
  },
  explanationTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.white,
    marginBottom: 6,
  },
  explanationText: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.8)',
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
    color: COLORS.white,
  },
  compoundLabel: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 4,
  },
  luckyBadge: {
    backgroundColor: 'rgba(34, 197, 94, 0.3)',
  },
  unluckyBadge: {
    backgroundColor: 'rgba(239, 68, 68, 0.3)',
  },
  neutralBadge: {
    backgroundColor: 'rgba(245, 158, 11, 0.3)',
  },
});