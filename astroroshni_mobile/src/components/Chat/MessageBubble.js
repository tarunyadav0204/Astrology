import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Linking,
  Alert,
  Animated,
  Clipboard,
  Share,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { COLORS } from '../../utils/constants';
import { generatePDF, sharePDFOnWhatsApp } from '../../utils/pdfGenerator';

export default function MessageBubble({ message, language, onFollowUpClick, partnership }) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const isPartnership = partnership || message.partnership_mode;
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);
  const sharePDF = async () => {
    try {
      setIsGeneratingPDF(true);
      const pdfUri = await generatePDF(message);
      await sharePDFOnWhatsApp(pdfUri);
    } catch (error) {
      Alert.alert('Error', 'Failed to generate PDF. Please try again.');
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      const cleanText = message.content
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/###\s*(.*?)$/gm, '$1')
        .replace(/<[^>]*>/g, '')
        .replace(/•\s*/g, '• ')
        .trim();

      await Clipboard.setString(cleanText);
      Alert.alert('Copied!', 'Message copied to clipboard');
    } catch (error) {
      // Error copying to clipboard
    }
  };

  const shareMessage = async () => {
    try {
      const cleanText = message.content
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/###\s*(.*?)$/gm, '$1')
        .replace(/<[^>]*>/g, '')
        .replace(/•\s*/g, '• ')
        .trim();

      const shareText = `🔮 AstroRoshni Prediction\n\n${cleanText}\n\nShared from AstroRoshni App`;
      
      await Share.share({
        message: shareText,
      });
    } catch (error) {
      // Error sharing message
    }
  };

  const formatContent = (content) => {
    if (!content || content.trim() === '') {
      return '';
    }
    
    // DON'T decode HTML entities yet - preserve them for proper formatting
    let formatted = content;
    
    // Normalize line breaks
    formatted = formatted.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    
    // Handle Follow-up Questions section
    formatted = formatted.replace(/<div class="follow-up-questions">([\s\S]*?)<\/div>/g, (match, questions) => {
      return `<followup>${questions}</followup>`;
    });
    
    // Handle Final Thoughts section
    formatted = formatted.replace(/(### Final Thoughts[\s\S]*?)(?=###|$)/g, (match, finalThoughts) => {
      const cleanContent = finalThoughts.replace(/### Final Thoughts\n?/, '').trim();
      return `<finalthoughts>${cleanContent}</finalthoughts>`;
    });
    
    // Handle Quick Answer sections
    formatted = formatted.replace(/<div class="quick-answer-card">(.*?)<\/div>/gs, '<quickanswer>$1</quickanswer>');
    formatted = formatted.replace(/<div class="final-thoughts-card">(.*?)<\/div>/gs, '<finalthoughts>$1</finalthoughts>');
    
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
          .replace(/&#39;/g, "'")
          .replace(/&nbsp;/g, ' ')
          .replace(/<[^>]*>/g, '')
          .replace(/Quick Answer/g, '')
          .replace(/^:\s*/, '')
          .trim();
        
        // Process markdown formatting in card content
        const renderCardContent = (text) => {
          const boldRegex = /\*\*(.*?)\*\*/g;
          const parts = text.split(boldRegex);
          
          return parts.map((part, index) => {
            if (index % 2 === 1) { // Bold text
              return (
                <Text key={`card-bold-${index}`} style={[styles.cardText, { fontWeight: '700' }]}>
                  {part}
                </Text>
              );
            } else {
              // Handle italics
              const italicRegex = /\*(.*?)\*/g;
              const italicParts = part.split(italicRegex);
              
              return italicParts.map((italicPart, italicIndex) => {
                if (italicIndex % 2 === 1) { // Italic text
                  return (
                    <Text key={`card-italic-${index}-${italicIndex}`} style={[styles.cardText, { fontStyle: 'italic' }]}>
                      {italicPart}
                    </Text>
                  );
                } else {
                  return (
                    <Text key={`card-text-${index}-${italicIndex}`} style={styles.cardText}>
                      {italicPart}
                    </Text>
                  );
                }
              });
            }
          });
        };
        
        elements.push(
          <View key={`quick-${currentIndex++}`} style={styles.quickAnswerCard}>
            <View style={styles.glassOverlay} />
            <View style={styles.cardHeader}>
              <Animated.Text style={[
                styles.lightningIcon,
                {
                  transform: [{
                    scale: fadeAnim.interpolate({
                      inputRange: [0, 1],
                      outputRange: [1, 1.2]
                    })
                  }]
                }
              ]}>⚡</Animated.Text>
              <Text style={styles.cardTitle}>Quick Answer</Text>
            </View>
            <Text style={styles.cardText}>
              {renderCardContent(cardContent)}
            </Text>
          </View>
        );
      } else if (item.type === 'final') {
        let cardContent = item.match[1]
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&amp;/g, '&')
          .replace(/&#39;/g, "'")
          .replace(/&nbsp;/g, ' ')
          .replace(/<[^>]*>/g, '')
          .replace(/Final Thoughts/g, '')
          .trim();
        
        // Process markdown formatting in card content
        const renderCardContent = (text) => {
          const boldRegex = /\*\*(.*?)\*\*/g;
          const parts = text.split(boldRegex);
          
          return parts.map((part, index) => {
            if (index % 2 === 1) { // Bold text
              return (
                <Text key={`card-bold-${index}`} style={[styles.cardText, { fontWeight: '700' }]}>
                  {part}
                </Text>
              );
            } else {
              // Handle italics
              const italicRegex = /\*(.*?)\*/g;
              const italicParts = part.split(italicRegex);
              
              return italicParts.map((italicPart, italicIndex) => {
                if (italicIndex % 2 === 1) { // Italic text
                  return (
                    <Text key={`card-italic-${index}-${italicIndex}`} style={[styles.cardText, { fontStyle: 'italic' }]}>
                      {italicPart}
                    </Text>
                  );
                } else {
                  return (
                    <Text key={`card-text-${index}-${italicIndex}`} style={styles.cardText}>
                      {italicPart}
                    </Text>
                  );
                }
              });
            }
          });
        };
        
        elements.push(
          <LinearGradient
            key={`final-${currentIndex++}`}
            colors={['#E6F3FF', '#B0E0E6']}
            style={styles.finalThoughtsCard}
          >
            <Text style={styles.cardTitle}>◆ Final Thoughts</Text>
            <Text style={styles.cardText}>
              {renderCardContent(cardContent)}
            </Text>
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
        
        // Try different parsing methods - handle both emoji and text patterns
        if (questionsText.match(/[🔮🌟⭐💫✨📅💼]/)) {
          questions = questionsText
            .split(/(?=[🔮🌟⭐💫✨📅💼])/)
            .map(q => q.trim())
            .filter(q => q.length > 3);
        } else if (questionsText.includes('\n')) {
          questions = questionsText
            .split('\n')
            .map(q => q.trim())
            .filter(q => q.length > 3 && q.includes('?'));
        } else if (questionsText.includes('?') && questionsText.length > 10) {
          // Split by common question patterns
          const patterns = /(?=When will|What remedies|How to|What should)/g;
          if (questionsText.match(patterns)) {
            questions = questionsText.split(patterns).filter(q => q.trim().length > 3);
          } else {
            questions = [questionsText];
          }
        }
        
        if (questions.length > 0) {
          elements.push(
            <View key={`followup-${currentIndex++}`} style={styles.followUpContainer}>
              {questions.map((question, index) => {
                const cleanQuestion = question
                  .replace(/^[\s🔮🌟⭐💫✨📅💼]+/, '')
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
    const elements = [];
    
    // Handle markdown bold formatting
    const boldRegex = /\*\*(.*?)\*\*/g;
    const parts = text.split(boldRegex);
    
    parts.forEach((part, index) => {
      if (!part) return;
      
      if (index % 2 === 1) { // Odd indices are bold text
        elements.push(
          <Text key={`bold-${startIndex}-${index}`} style={styles.boldText}>
            {part}
          </Text>
        );
      } else if (part.trim()) {
        // Handle italics within regular text
        const italicRegex = /\*(.*?)\*/g;
        const italicParts = part.split(italicRegex);
        
        italicParts.forEach((italicPart, italicIndex) => {
          if (!italicPart) return;
          
          if (italicIndex % 2 === 1) { // Odd indices are italic text
            elements.push(
              <Text key={`italic-${startIndex}-${index}-${italicIndex}`} style={[styles.regularText, { fontStyle: 'italic' }]}>
                {italicPart}
              </Text>
            );
          } else if (italicPart.trim()) {
            elements.push(
              <Text key={`text-${startIndex}-${index}-${italicIndex}`} style={styles.regularText}>
                {italicPart}
              </Text>
            );
          }
        });
      }
    });
    
    return elements.length > 0 ? [
      <Text key={`line-${startIndex}`} style={styles.regularText}>
        {elements}
      </Text>
    ] : [];
  };

  const AnimatedIcon = ({ symbol }) => {
    const rotateAnim = useRef(new Animated.Value(0)).current;
    const scaleAnim = useRef(new Animated.Value(1)).current;
    
    useEffect(() => {
      const rotateAnimation = Animated.loop(
        Animated.timing(rotateAnim, {
          toValue: 1,
          duration: 3000,
          useNativeDriver: true,
        })
      );
      
      const pulseAnimation = Animated.loop(
        Animated.sequence([
          Animated.timing(scaleAnim, {
            toValue: 1.2,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(scaleAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );
      
      rotateAnimation.start();
      pulseAnimation.start();
      
      return () => {
        rotateAnimation.stop();
        pulseAnimation.stop();
      };
    }, []);
    
    const rotate = rotateAnim.interpolate({
      inputRange: [0, 1],
      outputRange: ['0deg', '360deg'],
    });
    
    return (
      <Animated.Text style={[
        styles.headerIcon,
        {
          transform: [
            { rotate },
            { scale: scaleAnim }
          ]
        }
      ]}>
        {symbol}
      </Animated.Text>
    );
  };

  const AnimatedLightning = () => {
    const glowAnim = useRef(new Animated.Value(0)).current;
    const bounceAnim = useRef(new Animated.Value(1)).current;
    
    useEffect(() => {
      const glowAnimation = Animated.loop(
        Animated.sequence([
          Animated.timing(glowAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
          }),
          Animated.timing(glowAnim, {
            toValue: 0,
            duration: 800,
            useNativeDriver: true,
          }),
        ])
      );
      
      const bounceAnimation = Animated.loop(
        Animated.sequence([
          Animated.timing(bounceAnim, {
            toValue: 1.1,
            duration: 600,
            useNativeDriver: true,
          }),
          Animated.timing(bounceAnim, {
            toValue: 1,
            duration: 600,
            useNativeDriver: true,
          }),
        ])
      );
      
      glowAnimation.start();
      bounceAnimation.start();
      
      return () => {
        glowAnimation.stop();
        bounceAnimation.stop();
      };
    }, []);
    
    const glowOpacity = glowAnim.interpolate({
      inputRange: [0, 1],
      outputRange: [0.6, 1],
    });
    
    return (
      <Animated.Text style={[
        styles.lightningIcon,
        {
          opacity: glowOpacity,
          transform: [{ scale: bounceAnim }]
        }
      ]}>
        ⚡
      </Animated.Text>
    );
  };

  const getHeaderSymbol = (headerText) => {
    const text = headerText.toLowerCase();
    if (text.includes('life stage') || text.includes('context')) return '🌱';
    if (text.includes('astrological analysis') || text.includes('analysis')) return '🔍';
    if (text.includes('career') || text.includes('profession')) return '💼';
    if (text.includes('nakshatra') || text.includes('star')) return '⭐';
    if (text.includes('classical authority') || text.includes('authority') || text.includes('classical')) return '📜';
    if (text.includes('timing') && text.includes('guidance')) return '⏰';
    if (text.includes('timing') || text.includes('time')) return '🕐';
    if (text.includes('guidance') || text.includes('advice')) return '🌟';
    if (text.includes('final thoughts') || text.includes('thoughts')) return '💭';
    if (text.includes('relationship') || text.includes('love') || text.includes('marriage')) return '💕';
    if (text.includes('health') || text.includes('wellness')) return '🌿';
    if (text.includes('finance') || text.includes('money') || text.includes('wealth')) return '💰';
    if (text.includes('spiritual') || text.includes('meditation')) return '🕉️';
    if (text.includes('remedy') || text.includes('solution')) return '🔮';
    if (text.includes('prediction') || text.includes('forecast')) return '🌙';
    if (text.includes('transit') || text.includes('planetary')) return '🪐';
    return '✨'; // Default symbol
  };

  const parseRegularText = (text, startIndex) => {
    const elements = [];
    let currentIndex = startIndex;
    let listCounter = 0;
    
    // Split by headers and paragraphs - include markdown headers
    const parts = text.split(/(<h3>.*?<\/h3>|##\s+.+|###\s+.+|\n\n+)/).filter(part => part.trim());
    
    for (const part of parts) {
      if (part.match(/<h3>(.*?)<\/h3>/)) {
        listCounter = 0; // Reset counter for new section
        const headerText = part.replace(/<h3>(.*?)<\/h3>/, '$1');
        const symbol = getHeaderSymbol(headerText);
        elements.push(
          <View key={`header-${currentIndex++}`} style={styles.headerContainer}>
            <AnimatedIcon symbol={symbol} />
            <Text style={styles.headerText}>{headerText}</Text>
          </View>
        );
      } else if (part.match(/^##\s+(.+)$/m) || part.match(/^###\s+(.+)$/m)) {
        listCounter = 0; // Reset counter for new section
        // Handle markdown headers (both ## and ###)
        const headerText = part.replace(/^##\s+(.+)$/m, '$1').replace(/^###\s+(.+)$/m, '$1');
        const symbol = getHeaderSymbol(headerText);
        elements.push(
          <View key={`header-${currentIndex++}`} style={styles.headerContainer}>
            <AnimatedIcon symbol={symbol} />
            <Text style={styles.headerText}>{headerText}</Text>
          </View>
        );
      } else if (part.trim()) {
        // Handle lists and regular text
        const lines = part.split('\n').filter(line => line.trim());
        
        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) continue;
          
          if (trimmedLine.startsWith('•') || trimmedLine.match(/^\d+\./)) {
            listCounter++;
            let cleanListText = trimmedLine
              .replace(/^[•\d+\.\s]+/, '') // Remove bullet or number
              .replace(/&lt;/g, '<')
              .replace(/&gt;/g, '>')
              .replace(/&quot;/g, '"')
              .replace(/&amp;/g, '&')
              .replace(/&#39;/g, "'")
              .replace(/&nbsp;/g, ' ')
              .replace(/<[^>]*>/g, '');
            
            // Process bold formatting in list items
            const boldRegex = /\*\*(.*?)\*\*/g;
            const listParts = cleanListText.split(boldRegex);
            
            const listElements = listParts.map((listPart, listIndex) => {
              if (listIndex % 2 === 1) { // Odd indices are bold text
                return (
                  <Text key={`list-bold-${currentIndex}-${listIndex}`} style={[styles.listText, styles.boldText]}>
                    {listPart}
                  </Text>
                );
              } else {
                return (
                  <Text key={`list-text-${currentIndex}-${listIndex}`} style={styles.listText}>
                    {listPart}
                  </Text>
                );
              }
            });
            
            elements.push(
              <View key={`list-${currentIndex++}`} style={styles.listItem}>
                <View style={styles.numberCircle}>
                  <Text style={styles.numberText}>{listCounter}</Text>
                </View>
                <View style={styles.listContent}>
                  <Text style={styles.listText}>
                    {listElements}
                  </Text>
                </View>
              </View>
            );
          } else {
            // Process markdown formatting first
            let processedLine = trimmedLine
              .replace(/&lt;/g, '<')
              .replace(/&gt;/g, '>')
              .replace(/&quot;/g, '"')
              .replace(/&amp;/g, '&')
              .replace(/&#39;/g, "'")
              .replace(/&nbsp;/g, ' ');
            
            // Regular text with bold formatting
            const textElements = renderTextWithBold(processedLine, currentIndex, message.role);
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

  // Check if this is a clarification message
  const isClarification = message.message_type === 'clarification';

  // Handle typing indicator
  if (message.isTyping) {
    return (
      <Animated.View style={[
        styles.container,
        styles.assistantContainer,
        { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }
      ]}>
        <View style={[styles.bubble, styles.assistantBubble]}>
          <View style={styles.assistantHeader}>
            <Text style={styles.assistantLabel}>🔮 AstroRoshni</Text>
          </View>
          <View style={styles.messageContent}>
            <Text style={styles.typingText}>{message.content}</Text>
          </View>
        </View>
      </Animated.View>
    );
  }

  const formattedContent = formatContent(message.content);
  const renderedElements = renderFormattedText(formattedContent);

  return (
    <Animated.View style={[
      styles.container,
      message.role === 'user' ? styles.userContainer : styles.assistantContainer,
      { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }
    ]}>
      <View style={[
        styles.bubble,
        message.role === 'user' ? styles.userBubble : styles.assistantBubble,
        isPartnership && styles.partnershipBubble,
        isClarification && styles.clarificationBubble
      ]}>
        {message.role === 'assistant' && (
          <View style={styles.assistantHeader}>
            <Text style={styles.assistantLabel}>
              {isClarification ? '❓ Question' : '🔮 AstroRoshni'}
            </Text>
          </View>
        )}
        
        <View style={styles.messageContent}>
          {renderedElements}
        </View>

        {!message.isTyping && (
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={copyToClipboard}
            >
              <Text style={styles.actionIcon}>📋</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={shareMessage}
            >
              <Text style={styles.actionIcon}>↗️</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, styles.pdfButton]}
              onPress={sharePDF}
              disabled={isGeneratingPDF}
            >
              {isGeneratingPDF ? (
                <ActivityIndicator size="small" color={COLORS.primary} />
              ) : (
                <Text style={styles.actionIcon}>📄</Text>
              )}
            </TouchableOpacity>
          </View>
        )}

        <Text style={styles.timestamp}>
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </Text>
      </View>
    </Animated.View>
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
    maxWidth: '88%',
    borderRadius: 20,
    padding: 16,
    marginVertical: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 4,
  },
  userBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.98)',
    borderBottomRightRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
  },
  assistantBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderBottomLeftRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.1)',
    borderLeftWidth: 3,
    borderLeftColor: 'rgba(255, 107, 53, 0.4)',
  },
  assistantHeader: {
    marginBottom: 8,
  },
  assistantLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255, 107, 53, 0.8)',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  messageContent: {
    paddingBottom: 4,
  },
  regularText: {
    fontSize: 15,
    lineHeight: 22,
    marginVertical: 2,
    color: '#2c3e50',
  },
  boldText: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '700',
    color: '#2c3e50',
  },
  headerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(255, 107, 53, 0.08)',
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#ff6b35',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  headerIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  headerText: {
    fontSize: 17,
    fontWeight: '700',
    color: '#ff6b35',
    letterSpacing: 0.5,
    flex: 1,
  },
  listItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginVertical: 6,
  },
  numberCircle: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: '#ff6b35',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
    marginTop: 3,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.3,
    shadowRadius: 2,
    elevation: 2,
  },
  numberText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: '700',
  },
  listContent: {
    flex: 1,
    marginLeft: -2,
  },
  listText: {
    fontSize: 15,
    lineHeight: 22,
    color: '#2c3e50',
  },
  quickAnswerCard: {
    borderRadius: 20,
    padding: 18,
    marginVertical: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    shadowColor: '#FFD700',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 8,
    overflow: 'hidden',
  },
  glassOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    borderRadius: 20,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
    zIndex: 1,
  },
  lightningIcon: {
    fontSize: 18,
    marginRight: 8,
    color: '#FFD700',
  },
  finalThoughtsCard: {
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#4169E1',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
    borderWidth: 1,
    borderColor: 'rgba(65, 105, 225, 0.3)',
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#2c3e50',
    letterSpacing: 0.5,
  },
  cardText: {
    fontSize: 14,
    color: '#2c3e50',
    lineHeight: 20,
    zIndex: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
    gap: 8,
  },
  actionButton: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    borderRadius: 12,
    width: 32,
    height: 32,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
  },
  pdfButton: {
    backgroundColor: 'rgba(249, 115, 22, 0.15)',
    borderColor: 'rgba(249, 115, 22, 0.3)',
  },
  actionIcon: {
    fontSize: 16,
    color: COLORS.accent,
  },
  timestamp: {
    fontSize: 11,
    color: 'rgba(44, 62, 80, 0.6)',
    textAlign: 'right',
    marginTop: 6,
    fontWeight: '500',
  },
  followUpContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginVertical: 6,
    gap: 6,
  },
  followUpButton: {
    backgroundColor: 'rgba(255, 107, 53, 0.12)',
    borderRadius: 25,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginBottom: 8,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  followUpText: {
    color: '#ff6b35',
    fontSize: 13,
    fontWeight: '600',
  },
  typingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  typingText: {
    fontSize: 15,
    color: '#2c3e50',
    flex: 1,
    marginRight: 8,
  },
  typingDots: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#ff6b35',
    marginHorizontal: 2,
  },
  partnershipBubble: {
    borderLeftWidth: 3,
    borderLeftColor: COLORS.partnershipBorder,
  },
  partnershipLabel: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: COLORS.partnershipBorder,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    zIndex: 10,
  },
  partnershipLabelText: {
    color: COLORS.white,
    fontSize: 10,
    fontWeight: '600',
  },
  clarificationBubble: {
    backgroundColor: 'rgba(255, 193, 7, 0.15)',
    borderLeftWidth: 3,
    borderLeftColor: '#FFA726',
    borderWidth: 1,
    borderColor: 'rgba(255, 167, 38, 0.3)',
    shadowColor: '#FFA726',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 5,
  },
});