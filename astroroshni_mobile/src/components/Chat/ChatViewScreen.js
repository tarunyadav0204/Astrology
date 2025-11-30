import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Share,
  StatusBar,
  Animated,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from '@expo/vector-icons/Ionicons';
import { SafeAreaView } from 'react-native-safe-area-context';
import MessageBubble from './MessageBubble';
import { COLORS } from '../../utils/constants';

const { width } = Dimensions.get('window');

export default function ChatViewScreen({ route, navigation }) {
  const { session } = route.params;
  const [messages] = useState(session.messages || []);
  
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const starAnims = useRef([...Array(15)].map(() => new Animated.Value(0))).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 8,
        useNativeDriver: true,
      }),
    ]).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1500,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1500,
          useNativeDriver: true,
        }),
      ])
    ).start();

    starAnims.forEach((anim, index) => {
      Animated.loop(
        Animated.sequence([
          Animated.delay(index * 150),
          Animated.timing(anim, {
            toValue: 1,
            duration: 2000,
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0,
            duration: 2000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    });
  }, []);

  const getRelativeTime = (date) => {
    const now = new Date();
    const then = new Date(date);
    const diffMs = now - then;
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return then.toLocaleDateString();
  };

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
    navigation.navigate('Chat');
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a0033" translucent={false} />
      <LinearGradient colors={['#1a0033', '#2d1b4e', '#4a2c6d', '#ff6b35']} style={styles.gradient}>
        
        {/* Twinkling Stars */}
        {starAnims.map((anim, index) => {
          const top = Math.random() * 100;
          const left = Math.random() * 100;
          return (
            <Animated.View
              key={index}
              style={[
                styles.star,
                {
                  top: `${top}%`,
                  left: `${left}%`,
                  opacity: anim,
                },
              ]}
            >
              <Text style={styles.starText}>✨</Text>
            </Animated.View>
          );
        })}

        <SafeAreaView style={styles.safeArea}>
          
          {/* Header */}
          <Animated.View style={[styles.header, { opacity: fadeAnim }]}>
            <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
              <Icon name="arrow-back" size={24} color={COLORS.white} />
            </TouchableOpacity>
            
            <View style={styles.headerInfo}>
              <View style={styles.headerIconContainer}>
                <LinearGradient
                  colors={['#ff6b35', '#ff8c5a']}
                  style={styles.headerIconGradient}
                >
                  <Text style={styles.headerIcon}>💬</Text>
                </LinearGradient>
              </View>
              <View style={styles.headerTextContainer}>
                <Text style={styles.headerTitle}>
                  {getRelativeTime(session.created_at)}
                </Text>
                <Text style={styles.headerSubtitle}>
                  {Array.isArray(messages) ? messages.length : 0} messages
                </Text>
              </View>
            </View>
            
            <TouchableOpacity style={styles.shareButton} onPress={shareChat}>
              <Icon name="share-outline" size={24} color={COLORS.white} />
            </TouchableOpacity>
          </Animated.View>

          {/* Info Card */}
          <Animated.View style={[styles.infoCard, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
            <LinearGradient
              colors={['rgba(255, 255, 255, 0.15)', 'rgba(255, 255, 255, 0.05)']}
              style={styles.infoGradient}
            >
              <View style={styles.infoItem}>
                <Icon name="calendar-outline" size={16} color="rgba(255, 255, 255, 0.8)" />
                <Text style={styles.infoText}>
                  {new Date(session.created_at).toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric', 
                    year: 'numeric' 
                  })}
                </Text>
              </View>
              <View style={styles.infoDivider} />
              <View style={styles.infoItem}>
                <Icon name="time-outline" size={16} color="rgba(255, 255, 255, 0.8)" />
                <Text style={styles.infoText}>
                  {new Date(session.created_at).toLocaleTimeString('en-US', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </Text>
              </View>
              <View style={styles.infoDivider} />
              <View style={styles.infoItem}>
                <Icon name="chatbubbles-outline" size={16} color="rgba(255, 255, 255, 0.8)" />
                <Text style={styles.infoText}>{messages.length}</Text>
              </View>
            </LinearGradient>
          </Animated.View>

          {/* Messages */}
          <ScrollView 
            style={styles.messagesContainer}
            contentContainerStyle={styles.messagesContent}
            showsVerticalScrollIndicator={false}
          >
            {Array.isArray(messages) && messages.length > 0 ? (
              messages.map((message, index) => {
                const MessageCard = () => {
                  const msgAnim = useRef(new Animated.Value(0)).current;

                  useEffect(() => {
                    Animated.spring(msgAnim, {
                      toValue: 1,
                      delay: index * 100,
                      tension: 50,
                      friction: 7,
                      useNativeDriver: true,
                    }).start();
                  }, []);

                  return (
                    <Animated.View
                      style={{
                        opacity: msgAnim,
                        transform: [
                          {
                            translateY: msgAnim.interpolate({
                              inputRange: [0, 1],
                              outputRange: [30, 0],
                            }),
                          },
                        ],
                      }}
                    >
                      <MessageBubble 
                        message={message} 
                        language="english"
                      />
                    </Animated.View>
                  );
                };

                return <MessageCard key={`${message.timestamp}_${index}`} />;
              })
            ) : (
              <Animated.View style={[styles.emptyState, { opacity: fadeAnim }]}>
                <Text style={styles.emptyIcon}>💬</Text>
                <Text style={styles.emptyText}>No messages to display</Text>
              </Animated.View>
            )}
          </ScrollView>

          {/* Floating Action Buttons */}
          <Animated.View style={[styles.floatingButtons, { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }]}>
            <TouchableOpacity style={styles.floatingButtonSecondary} onPress={shareChat}>
              <LinearGradient
                colors={['rgba(255, 107, 53, 0.6)', 'rgba(255, 140, 90, 0.5)']}
                style={styles.floatingButtonGradient}
              >
                <Icon name="share-outline" size={20} color={COLORS.white} />
                <Text style={styles.floatingButtonText}>Share</Text>
              </LinearGradient>
            </TouchableOpacity>

            <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
              <TouchableOpacity style={styles.floatingButtonPrimary} onPress={continueConversation}>
                <LinearGradient
                  colors={['#ff6b35', '#ff8c5a']}
                  style={styles.floatingButtonGradient}
                >
                  <Icon name="chatbubbles" size={20} color={COLORS.white} />
                  <Text style={styles.floatingButtonTextPrimary}>Continue Chat</Text>
                  <Icon name="arrow-forward" size={20} color={COLORS.white} />
                </LinearGradient>
              </TouchableOpacity>
            </Animated.View>
          </Animated.View>

        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  gradient: { flex: 1 },
  safeArea: { flex: 1 },
  star: { position: 'absolute' },
  starText: { fontSize: 10 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
  },
  headerIconContainer: {
    marginRight: 12,
  },
  headerIconGradient: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  headerIcon: { fontSize: 22 },
  headerTextContainer: { flex: 1 },
  headerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
  },
  headerSubtitle: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 2,
  },
  shareButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoCard: {
    marginHorizontal: 20,
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  infoGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 16,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  infoText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.9)',
    fontWeight: '600',
  },
  infoDivider: {
    width: 1,
    height: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  messagesContainer: {
    flex: 1,
    paddingHorizontal: 4,
  },
  messagesContent: {
    paddingVertical: 16,
    paddingHorizontal: 12,
    paddingBottom: 100,
    flexGrow: 1,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
  },
  floatingButtons: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    flexDirection: 'row',
    gap: 12,
  },
  floatingButtonSecondary: {
    flex: 1,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  floatingButtonPrimary: {
    flex: 2,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.6,
    shadowRadius: 12,
    elevation: 8,
  },
  floatingButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    gap: 8,
  },
  floatingButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
  floatingButtonTextPrimary: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.white,
  },
});
