import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Share,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';

import MessageBubble from './MessageBubble';
import { COLORS } from '../../utils/constants';

export default function ChatViewScreen({ route, navigation }) {
  const { session } = route.params;
  const [messages] = useState(session.messages || []);

  const shareChat = async () => {
    try {
      if (!Array.isArray(messages) || messages.length === 0) {
        Alert.alert('No Messages', 'There are no messages to share.');
        return;
      }
      
      const chatText = messages
        .map(msg => `${msg.role === 'user' ? 'You' : 'AstroRoshni'}: ${msg.content}`)
        .join('\n\n');
      
      await Share.share({
        message: `🔮 AstroRoshni Chat - ${new Date(session.created_at || Date.now()).toLocaleDateString()}\n\n${chatText}\n\nShared from AstroRoshni App`,
      });
    } catch (error) {
      console.error('Error sharing chat:', error);
    }
  };

  const continueConversation = () => {
    Alert.alert(
      'Continue Conversation',
      'This will take you to the chat screen where you can continue this conversation.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Continue',
          onPress: () => navigation.navigate('Chat')
        }
      ]
    );
  };

  return (
    <LinearGradient colors={[COLORS.gradientStart, COLORS.gradientEnd]} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Ionicons name="arrow-back" size={24} color={COLORS.accent} />
          </TouchableOpacity>
          
          <View style={styles.headerInfo}>
            <Text style={styles.headerTitle}>
              {new Date(session.created_at || Date.now()).toLocaleDateString()}
            </Text>
            <Text style={styles.headerSubtitle}>
              {Array.isArray(messages) ? messages.length : 0} messages
            </Text>
          </View>
          
          <TouchableOpacity
            style={styles.shareButton}
            onPress={shareChat}
          >
            <Ionicons name="share-outline" size={20} color={COLORS.accent} />
          </TouchableOpacity>
        </View>

        {/* Messages */}
        <ScrollView 
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
        >
          {Array.isArray(messages) && messages.length > 0 ? (
            messages.map((message, index) => (
              <MessageBubble 
                key={`${message.timestamp}_${index}`} 
                message={message} 
                language="english"
              />
            ))
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>No messages to display</Text>
            </View>
          )}
        </ScrollView>

        {/* Continue Button */}
        <View style={styles.footer}>
          <TouchableOpacity
            style={styles.continueButton}
            onPress={continueConversation}
          >
            <Ionicons name="chatbubble-ellipses" size={20} color={COLORS.white} />
            <Text style={styles.continueText}>Continue Conversation</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: COLORS.surface,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  backButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: COLORS.lightGray,
  },
  headerInfo: {
    flex: 1,
    alignItems: 'center',
    marginHorizontal: 16,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  headerSubtitle: {
    fontSize: 12,
    color: COLORS.gray,
    marginTop: 2,
  },
  shareButton: {
    padding: 8,
    borderRadius: 20,
    backgroundColor: COLORS.lightGray,
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 4,
  },
  messagesContent: {
    paddingVertical: 16,
    paddingHorizontal: 12,
    flexGrow: 1,
  },
  footer: {
    padding: 16,
    backgroundColor: COLORS.surface,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  continueButton: {
    backgroundColor: COLORS.accent,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 25,
    shadowColor: COLORS.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  continueText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '700',
    marginLeft: 8,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
});