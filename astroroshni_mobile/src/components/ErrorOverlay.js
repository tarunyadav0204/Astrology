import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useError } from '../context/ErrorContext';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../context/ThemeContext';

export default function ErrorOverlay() {
  const { error, clearError } = useError();
  const navigation = useNavigation();
  const { colors, theme } = useTheme();
  const [retrying, setRetrying] = useState(false);

  if (!error) return null;

  const getErrorConfig = () => {
    switch (error.type) {
      case 'network':
        return {
          icon: 'cloud-offline',
          title: 'No Internet Connection',
          message: 'Please check your network connection and try again.',
          showRetry: true
        };
      case 'timeout':
        return {
          icon: 'time-outline',
          title: 'Request Timeout',
          message: 'The request took too long. Please try again.',
          showRetry: true
        };
      case 'server':
        return {
          icon: 'server-outline',
          title: 'Server Unavailable',
          message: 'Our servers are temporarily down. Please try again in a few minutes.',
          showRetry: true
        };
      default:
        return {
          icon: 'alert-circle',
          title: 'Something Went Wrong',
          message: error.message || 'An unexpected error occurred.',
          showRetry: true
        };
    }
  };

  const handleRetry = async () => {
    setRetrying(true);
    
    // Simple retry - just clear error and let user try again
    setTimeout(() => {
      clearError();
      setRetrying(false);
    }, 500);
  };

  const handleGoToProfile = () => {
    clearError();
    navigation.navigate('Profile');
  };

  const config = getErrorConfig();

  return (
    <Modal
      visible={true}
      transparent
      animationType="fade"
      onRequestClose={clearError}
    >
      <View style={styles.overlay}>
        <View style={[styles.container, { backgroundColor: colors.backgroundSecondary, borderColor: colors.cardBorder }]}>
          <View style={[styles.iconContainer, { backgroundColor: colors.surface }]}>
            <Ionicons name={config.icon} size={64} color={colors.error || '#da3633'} />
          </View>
          
          <Text style={[styles.title, { color: colors.text }]}>{config.title}</Text>
          <Text style={[styles.message, { color: colors.textSecondary }]}>{config.message}</Text>

          {config.showRetry && (
            <TouchableOpacity 
              style={styles.retryButton} 
              onPress={handleRetry}
              disabled={retrying}
            >
              <LinearGradient
                colors={[colors.accent, colors.primary]}
                style={styles.retryGradient}
              >
                {retrying ? (
                  <ActivityIndicator color={theme === 'dark' ? colors.background : '#1a1a1a'} />
                ) : (
                  <>
                    <Ionicons name="refresh" size={22} color={theme === 'dark' ? colors.background : '#1a1a1a'} />
                    <Text style={[styles.retryText, { color: theme === 'dark' ? colors.background : '#1a1a1a' }]}>
                      Retry
                    </Text>
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>
          )}

          <TouchableOpacity 
            style={[styles.secondaryButton, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
            onPress={handleGoToProfile}
          >
            <Text style={[styles.secondaryText, { color: colors.text }]}>Go to Profile</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.dismissButton}
            onPress={clearError}
          >
            <Text style={[styles.dismissText, { color: colors.textSecondary }]}>Dismiss</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20
  },
  container: {
    width: '100%',
    maxWidth: 360,
    borderRadius: 24,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 12,
    textAlign: 'center',
    letterSpacing: 0.3
  },
  message: {
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32
  },
  retryButton: {
    width: '100%',
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 12,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4
  },
  retryGradient: {
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10
  },
  retryText: {
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 0.5
  },
  secondaryButton: {
    width: '100%',
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1.5,
    alignItems: 'center',
    marginBottom: 12
  },
  secondaryText: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.3
  },
  dismissButton: {
    paddingVertical: 8
  },
  dismissText: {
    fontSize: 15,
    fontWeight: '500'
  }
});
