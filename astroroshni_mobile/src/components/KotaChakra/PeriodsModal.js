import React from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { typographyTokens } from '../../theme/tokens';

const PeriodsModal = ({ visible, onClose, type, data, colors }) => {
  const periods = type === 'good' ? data.good_periods : data.vulnerable_periods;

  const getStatusColor = (vulnerabilityScore) => {
    if (vulnerabilityScore >= 6) return colors.error;
    if (vulnerabilityScore >= 3) return colors.warning;
    if (vulnerabilityScore >= 2) return colors.warning; // Score 2 is caution
    return colors.success;
  };

  const getStatusTextColor = (vulnerabilityScore) => (
    vulnerabilityScore >= 2 && vulnerabilityScore < 6 ? colors.onAccent : colors.textInverse
  );

  const renderPeriodItem = ({ item }) => (
    <View style={[styles.periodCard, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}>
      <View style={styles.periodHeader}>
        <Text style={[styles.monthName, { color: colors.text }]}>
          {item.month_name}
        </Text>
        <View style={[styles.scoreBadge, { backgroundColor: getStatusColor(item.vulnerability_score) }]}>
          <Text style={[styles.scoreText, { color: getStatusTextColor(item.vulnerability_score) }]}>
            {item.vulnerability_score}
          </Text>
        </View>
      </View>

      <Text style={[styles.interpretation, { color: colors.textSecondary }]}>
        {item.interpretation}
      </Text>

      {item.malefic_siege && (
        <View style={styles.siegeInfo}>
          {Object.entries(item.malefic_siege).map(([section, planets]) => {
            if (planets.length > 0) {
              return (
                <Text key={section} style={[styles.siegeText, { color: colors.textTertiary }]}>
                  {section}: {planets.map(p => p.planet).join(', ')}
                </Text>
              );
            }
            return null;
          })}
        </View>
      )}
    </View>
  );

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <LinearGradient colors={[colors.background, colors.backgroundSecondary]} style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor={colors.headerSurface} translucent={false} />
        <SafeAreaView edges={['top']} style={{ backgroundColor: colors.headerSurface }}>
          <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
            <View>
              <Text style={[styles.eyebrow, { color: colors.accent }]}>{type === 'good' ? 'PROTECTION WINDOWS' : 'CAUTION WINDOWS'}</Text>
              <Text style={[styles.title, { color: colors.textInverse }]}>{type === 'good' ? 'Protected periods' : 'Vulnerable periods'}</Text>
              <Text style={[styles.subtitle, { color: colors.textInverseMuted }]}>Year {data.year}</Text>
            </View>
            <TouchableOpacity style={[styles.closeButton, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]} onPress={onClose} accessibilityLabel="Close">
              <Ionicons name="close" size={22} color={colors.textInverse} />
            </TouchableOpacity>
          </View>
        </SafeAreaView>

        {periods.length > 0 ? (
          <FlatList
            data={periods}
            renderItem={renderPeriodItem}
            keyExtractor={(item) => item.month.toString()}
            contentContainerStyle={styles.listContainer}
            showsVerticalScrollIndicator={false}
          />
        ) : (
          <View style={styles.emptyContainer}>
            <Text style={[styles.emptyText, { color: colors.textSecondary }]}>
              {type === 'good'
                ? 'No particularly protected periods found this year'
                : 'No highly vulnerable periods found this year'
              }
            </Text>
            <Text style={[styles.emptySubtext, { color: colors.textTertiary }]}>
              This indicates a relatively stable year with moderate protection levels.
            </Text>
          </View>
        )}

        <SafeAreaView edges={['bottom']} style={[styles.footer, { backgroundColor: colors.surfaceRaised, borderTopColor: colors.cardBorder }]}>
          <View style={styles.legendContainer}>
            <Text style={[styles.legendTitle, { color: colors.text }]}>
              Vulnerability scale
            </Text>
            <View style={styles.legendItems}>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: colors.success }]} />
                <Text style={[styles.legendText, { color: colors.textSecondary }]}>
                  0-1: Protected
                </Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: colors.warning }]} />
                <Text style={[styles.legendText, { color: colors.textSecondary }]}>
                  2-5: Caution
                </Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: colors.error }]} />
                <Text style={[styles.legendText, { color: colors.textSecondary }]}>
                  6+: High Risk
                </Text>
              </View>
            </View>
          </View>
        </SafeAreaView>
      </LinearGradient>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  eyebrow: {
    ...typographyTokens.eyebrow,
    marginBottom: 4,
  },
  title: {
    ...typographyTokens.display,
    fontSize: 28,
    lineHeight: 32,
  },
  subtitle: {
    fontSize: 13,
    fontWeight: '500',
    marginTop: 3,
  },
  closeButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContainer: {
    padding: 16,
    paddingBottom: 20,
  },
  periodCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
  },
  periodHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  monthName: {
    fontSize: 18,
    fontWeight: '600',
  },
  scoreBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  scoreText: {
    fontSize: 12,
    fontWeight: '700',
  },
  interpretation: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8,
  },
  siegeInfo: {
    gap: 2,
  },
  siegeText: {
    fontSize: 12,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  footer: {
    padding: 16,
    borderTopWidth: 1,
  },
  legendContainer: {
    alignItems: 'center',
  },
  legendTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  legendItems: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    fontSize: 12,
  },
});

export default PeriodsModal;
