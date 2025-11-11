import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function ChatScreen({ navigation }) {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    Alert.alert('SUCCESS', 'ChatScreen is working!');
    
    const welcomeMessage = {
      id: 'welcome-1',
      content: 'Hello! Welcome to AstroRoshni. How can I help you today?',
      role: 'assistant'
    };
    
    setMessages([welcomeMessage]);
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>🔮 AstroRoshni</Text>
      </View>
      
      <View style={styles.content}>
        <Text style={styles.debugText}>SIMPLE CHAT SCREEN LOADED</Text>
        <Text style={styles.debugText}>Messages: {messages.length}</Text>
        
        {messages.map((message) => (
          <View key={message.id} style={styles.messageBubble}>
            <Text style={styles.messageText}>{message.content}</Text>
          </View>
        ))}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#ff6b35',
    padding: 16,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  debugText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'red',
    marginBottom: 10,
  },
  messageBubble: {
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  messageText: {
    fontSize: 16,
    color: '#333',
  },
});