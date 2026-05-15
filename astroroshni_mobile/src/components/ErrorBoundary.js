import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as Sentry from '@sentry/react-native';
import { useTheme } from '../context/ThemeContext';
import { recordRuntimeIssue } from '../services/runtimeGuard';

class InnerErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    recordRuntimeIssue(error, {
      fatal: false,
      source: 'react_error_boundary',
      metadata: info,
    }).catch(() => {});

    try {
      Sentry.captureException(error, { contexts: { react: { componentStack: info?.componentStack } } });
    } catch (_) {
      /* never let Sentry break the error UI */
    }

    if (__DEV__) {
      console.error('[ErrorBoundary] Caught error:', error, info);
    }
  }
  
  handleReload = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    const { hasError } = this.state;
    const { children, colors } = this.props;

    if (!hasError) return children;

    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}>
          <Text style={[styles.title, { color: colors.text }]}>Something went wrong</Text>
          <Text style={[styles.message, { color: colors.textSecondary }]}>
            An unexpected error occurred. Please try again.
          </Text>
          <TouchableOpacity style={styles.button} onPress={this.handleReload}>
            <Text style={styles.buttonText}>Go back</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }
}

export default function ErrorBoundary({ children }) {
  const { colors } = useTheme();
  return <InnerErrorBoundary colors={colors}>{children}</InnerErrorBoundary>;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  card: {
    width: '100%',
    maxWidth: 380,
    padding: 24,
    borderRadius: 18,
    borderWidth: 1,
    alignItems: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    marginBottom: 8,
  },
  message: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#f97316',
    borderRadius: 999,
    paddingHorizontal: 20,
    paddingVertical: 10,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
});
