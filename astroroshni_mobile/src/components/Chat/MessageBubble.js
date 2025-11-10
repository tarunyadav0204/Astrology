import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Linking,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../../utils/constants';

export default function MessageBubble({ message, language, onFollowUpClick }) {
  const shareToWhatsApp = async () => {
    try {
      const cleanText = message.content
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/###\s*(.*?)$/gm, '$1')
        .replace(/<[^>]*>/g, '')
        .replace(/•\s*/g, '• ')
        .trim();

      const shareText = `🔮 *AstroRoshni Prediction*\n\n${cleanText}\n\n_Shared from AstroRoshni App_`;
      const whatsappUrl = `whatsapp://send?text=${encodeURIComponent(shareText)}`;
      
      const supported = await Linking.canOpenURL(whatsappUrl);
      if (supported) {
        await Linking.openURL(whatsappUrl);
      } else {
        Alert.alert('WhatsApp not installed', 'Please install WhatsApp to share messages');
      }
    } catch (error) {
      console.error('Error sharing to WhatsApp:', error);
    }
  };

  const formatContent = (content) => {
    // First decode HTML entities
    let formatted = content
      .replace(/&quot;/g, '"')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ');
    
    // Then format the content
    formatted = formatted
      .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
      .replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<i>$1</i>')
      .replace(/###\s*(.*?)$/gm, '<h3>$1</h3>')
      .replace(/<div class="quick-answer-card">(.*?)<\/div>/gs, '<quickanswer>$1</quickanswer>')
      .replace(/<div class="final-thoughts-card">(.*?)<\/div>/gs, '<finalthoughts>$1</finalthoughts>')
      .replace(/<div class="follow-up-questions">(.*?)<\/div>/gs, '<followup>$1</followup>');
    
    return formatted;
  };

  const renderFormattedText = (text) => {
    const elements = [];
    let currentIndex = 0;
    let lastIndex = 0;
    
    // Handle all special sections
    const sections = [
      { regex: /<quickanswer>(.*?)<\/quickanswer>/gs, type: 'quick' },
      { regex: /<finalthoughts>(.*?)<\/finalthoughts>/gs, type: 'final' },
      { regex: /<followup>(.*?)<\/followup>/gs, type: 'followup' }
    ];
    
    // Find all matches and sort by position
    const allMatches = [];
    sections.forEach(section => {
      section.regex.lastIndex = 0;
      let match;
      while ((match = section.regex.exec(text)) !== null) {
        allMatches.push({
          type: section.type,
          match: match,
          index: match.index,
          lastIndex: section.regex.lastIndex
        });
      }
    });
    
    allMatches.sort((a, b) => a.index - b.index);
    
    // Process matches in order
    for (const item of allMatches) {
      // Add text before this match
      if (item.index > lastIndex) {
        const beforeText = text.slice(lastIndex, item.index);
        elements.push(...parseRegularText(beforeText, currentIndex));
        currentIndex += 100;
      }
      
      // Add the special section
      if (item.type === 'quick') {
        let cardContent = item.match[1]
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&amp;/g, '&')
          .replace(/<[^>]*>/g, '')
          .replace(/Quick Answer/g, '')
          .trim();
        elements.push(
          <LinearGradient
            key={`quick-${currentIndex++}`}
            colors={['#FFE4B5', '#F0E68C']}
            style={styles.quickAnswerCard}
          >
            <Text style={styles.cardTitle}>⚡ Quick Answer</Text>
            <Text style={styles.cardText}>{cardContent}</Text>
          </LinearGradient>
        );
      } else if (item.type === 'final') {
        let cardContent = item.match[1]
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&amp;/g, '&')
          .replace(/<[^>]*>/g, '')
          .replace(/Final Thoughts/g, '')
          .trim();
        elements.push(
          <LinearGradient
            key={`final-${currentIndex++}`}
            colors={['#E6F3FF', '#B0E0E6']}
            style={styles.finalThoughtsCard}
          >
            <Text style={styles.cardTitle}>◆ Final Thoughts</Text>
            <Text style={styles.cardText}>{cardContent}</Text>
          </LinearGradient>
        );
      } else if (item.type === 'followup') {
        // Parse follow-up questions
        let questionsText = item.match[1]
          .replace(/<[^>]*>/g, '')
          .replace(/&quot;/g, '"')
          .replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&#39;/g, "'")
          .trim();
        
        let questions = [];
        
        // Try different parsing methods
        if (questionsText.match(/[🔮🌟⭐💫✨]/)) {
          questions = questionsText
            .split(/(?=[🔮🌟⭐💫✨])/)
            .map(q => q.trim())
            .filter(q => q.length > 3);
        } else if (questionsText.includes('\n')) {
          questions = questionsText
            .split('\n')
            .map(q => q.trim())
            .filter(q => q.length > 3 && q.includes('?'));
        } else if (questionsText.includes('?') && questionsText.length > 10) {
          questions = [questionsText];
        }
        
        if (questions.length > 0) {
          elements.push(
            <View key={`followup-${currentIndex++}`} style={styles.followUpContainer}>
              {questions.map((question, index) => {
                const cleanQuestion = question
                  .replace(/^[\s🔮🌟⭐💫✨]+/, '')
                  .replace(/&quot;/g, '"')
                  .replace(/&amp;/g, '&')
                  .replace(/&lt;/g, '<')
                  .replace(/&gt;/g, '>')
                  .trim();
                if (cleanQuestion.length < 5) return null;
                return (
                  <TouchableOpacity
                    key={`question-${index}`}
                    style={styles.followUpButton}
                    onPress={() => onFollowUpClick && onFollowUpClick(cleanQuestion)}
                  >
                    <Text style={styles.followUpText}>{cleanQuestion}</Text>
                  </TouchableOpacity>
                );
              }).filter(Boolean)}
            </View>
          );
        }
      }
      
      lastIndex = item.lastIndex;
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      const remainingText = text.slice(lastIndex);
      elements.push(...parseRegularText(remainingText, currentIndex));
    }
    
    return elements;
  };
  
  const renderTextWithBold = (text, startIndex, role) => {
    // First decode HTML entities
    let processedText = text
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&amp;/g, '&');
    
    const elements = [];
    const parts = processedText.split(/(<b>.*?<\/b>)/);
    
    parts.forEach((part, index) => {
      if (part.match(/<b>(.*?)<\/b>/)) {
        const boldText = part.replace(/<b>(.*?)<\/b>/, '$1').replace(/<[^>]*>/g, '');
        elements.push(
          <Text key={`bold-${startIndex}-${index}`} style={[styles.boldText, { color: role === 'user' ? COLORS.black : COLORS.white }]}>
            {boldText}
          </Text>
        );
      } else if (part.trim()) {
        const cleanText = part.replace(/<[^>]*>/g, '');
        if (cleanText) {
          elements.push(
            <Text key={`text-${startIndex}-${index}`} style={[styles.regularText, { color: role === 'user' ? COLORS.black : COLORS.white }]}>
              {cleanText}
            </Text>
          );
        }
      }
    });
    
    return elements.length > 0 ? [
      <Text key={`line-${startIndex}`} style={[styles.regularText, { color: role === 'user' ? COLORS.black : COLORS.white }]}>
        {elements}
      </Text>
    ] : [];
  };

  const parseRegularText = (text, startIndex) => {
    const elements = [];
    let currentIndex = startIndex;
    
    // Split by headers and paragraphs
    const parts = text.split(/(<h3>.*?<\/h3>|\n\n+)/).filter(part => part.trim());
    
    for (const part of parts) {
      if (part.match(/<h3>(.*?)<\/h3>/)) {
        const headerText = part.replace(/<h3>(.*?)<\/h3>/, '$1');
        elements.push(
          <Text key={`header-${currentIndex++}`} style={styles.headerText}>
            ◆ {headerText} ◆
          </Text>
        );
      } else if (part.trim()) {
        // Handle lists and regular text
        const lines = part.split('\n').filter(line => line.trim());
        
        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) continue;
          
          if (trimmedLine.startsWith('•') || trimmedLine.match(/^\d+\./)) {
            const cleanListText = trimmedLine
              .replace(/&lt;/g, '<')
              .replace(/&gt;/g, '>')
              .replace(/&quot;/g, '"')
              .replace(/&amp;/g, '&')
              .replace(/<[^>]*>/g, '');
            elements.push(
              <View key={`list-${currentIndex++}`} style={styles.listItem}>
                <Text style={[styles.listText, { color: message.role === 'user' ? COLORS.black : COLORS.white }]}>
                  {cleanListText}
                </Text>
              </View>
            );
          } else {
            // Regular text with bold formatting
            const textElements = renderTextWithBold(trimmedLine, currentIndex, message.role);
            elements.push(...textElements);
            currentIndex += textElements.length;
          }
        }
      }
    }
    
    return elements;
  };



  if (!message.content || message.content.trim() === '') {
    return null;
  }

  const formattedContent = formatContent(message.content);
  const renderedElements = renderFormattedText(formattedContent);

  return (
    <View style={[
      styles.container,
      message.role === 'user' ? styles.userContainer : styles.assistantContainer
    ]}>
      <View style={[
        styles.bubble,
        message.role === 'user' ? styles.userBubble : styles.assistantBubble
      ]}>
        <View style={styles.messageContent}>
          {renderedElements}
        </View>

        {message.role === 'assistant' && !message.isTyping && (
          <TouchableOpacity
            style={styles.shareButton}
            onPress={shareToWhatsApp}
          >
            <Ionicons name="logo-whatsapp" size={14} color={COLORS.white} />
          </TouchableOpacity>
        )}

        <Text style={styles.timestamp}>
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 4,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  bubble: {
    maxWidth: '85%',
    borderRadius: 12,
    padding: 8,
  },
  userBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderBottomLeftRadius: 4,
  },
  messageContent: {
    paddingRight: 30,
  },
  regularText: {
    fontSize: 15,
    lineHeight: 20,
    marginVertical: 1,
  },
  boldText: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: 'bold',
  },
  headerText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFD700',
    textAlign: 'center',
    marginVertical: 4,
    paddingVertical: 2,
  },
  listItem: {
    marginVertical: 1,
  },
  listText: {
    fontSize: 15,
    lineHeight: 18,
    paddingLeft: 8,
  },
  quickAnswerCard: {
    borderRadius: 8,
    padding: 8,
    marginVertical: 4,
  },
  finalThoughtsCard: {
    borderRadius: 8,
    padding: 8,
    marginVertical: 4,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginBottom: 4,
  },
  cardText: {
    fontSize: 14,
    color: '#2c3e50',
    lineHeight: 18,
  },
  shareButton: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: COLORS.whatsapp,
    borderRadius: 10,
    width: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  timestamp: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'right',
    marginTop: 4,
  },
  followUpContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginVertical: 6,
    gap: 6,
  },
  followUpButton: {
    backgroundColor: 'rgba(248, 250, 252, 0.9)',
    borderRadius: 16,
    paddingHorizontal: 10,
    paddingVertical: 6,
    marginBottom: 4,
  },
  followUpText: {
    color: '#334155',
    fontSize: 12,
    fontWeight: '500',
  },
});