import React from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const PeriodsModal = ({ visible, onClose, type, data, colors }) => {
  const periods = type === 'good' ? data.good_periods : data.vulnerable_periods;
  
  const getStatusColor = (vulnerabilityScore) => {
    if (vulnerabilityScore >= 6) return colors.error;
    if (vulnerabilityScore >= 3) return colors.warning;
    return colors.success;
  };

  const renderPeriodItem = ({ item }) => (
    <View style={[styles.periodCard, { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder }]}>
      <View style={styles.periodHeader}>
        <Text style={[styles.monthName, { color: colors.text }]}>
          {item.month_name}
        </Text>
        <View style={[styles.scoreBadge, { backgroundColor: getStatusColor(item.vulnerability_score) }]}>
          <Text style={styles.scoreText}>
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
      <LinearGradient colors={[colors.gradientStart, colors.gradientEnd]} style={styles.container}>
        <View style={styles.header}>
          <Text style={[styles.title, { color: colors.text }]}>
            {type === 'good' ? '🟢 Protected Periods' : '🔴 Vulnerable Periods'}
          </Text>
          <Text style={[styles.subtitle, { color: colors.textSecondary }]}>
            Year {data.year}
          </Text>
          
          <TouchableOpacity
            style={[styles.closeButton, { backgroundColor: colors.primary }]}
            onPress={onClose}
          >
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
        </View>

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

        <View style={styles.footer}>
          <View style={styles.legendContainer}>
            <Text style={[styles.legendTitle, { color: colors.text }]}>
              Vulnerability Scale:
            </Text>
            <View style={styles.legendItems}>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: colors.success }]} />
                <Text style={[styles.legendText, { color: colors.textSecondary }]}>
                  0-2: Protected
                </Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: colors.warning }]} />
                <Text style={[styles.legendText, { color: colors.textSecondary }]}>
                  3-5: Caution
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
        </View>
      </LinearGradient>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 20,
    paddingTop: 60,
    alignItems: 'center',
    position: 'relative',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  closeButton: {
    position: 'absolute',
    top: 60,
    right: 20,
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  listContainer: {
    padding: 16,
    paddingBottom: 100,
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
    color: '#ffffff',
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
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
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