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
  Modal,
  Image,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, API_BASE_URL, getEndpoint, VOICE_CONFIG } from '../../utils/constants';
import { generatePDF, sharePDFOnWhatsApp } from '../../utils/pdfGenerator';
import * as Speech from 'expo-speech';

export default function MessageBubble({ message, language, onFollowUpClick, partnership, onDelete }) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const isPartnership = partnership || message.partnership_mode;
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [tooltipModal, setTooltipModal] = useState({ show: false, term: '', definition: '' });
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showVoicePicker, setShowVoicePicker] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);

  // Debug logging
  useEffect(() => {
    if (message.sender === 'ai') {
      console.log('💬 [MessageBubble] Rendering AI message:', {
        has_terms: !!message.terms,
        terms_count: message.terms?.length || 0,
        has_glossary: !!message.glossary,
        glossary_keys: Object.keys(message.glossary || {}).length,
        has_summary_image: !!message.summary_image,
        summary_image_preview: message.summary_image?.substring(0, 100),
        summary_image_length: message.summary_image?.length || 0
      });
    }
  }, [message]);

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
  const speak = async () => {
    if (isSpeaking) {
      Speech.stop();
      setIsSpeaking(false);
      return;
    }

    const cleanText = message.content
      .replace(/<[^>]*>/g, '')
      .replace(/[#*]/g, '')
      .replace(/&quot;/g, '"').replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<').replace(/&gt;/g, '>')
      .trim();

    setIsSpeaking(true);
    const voiceLanguage = language === 'hindi' ? 'hi-IN' : language === 'telugu' ? 'te-IN' : language === 'tamil' ? 'ta-IN' : language === 'gujarati' ? 'gu-IN' : 'en-IN';

    try {
      const voices = await Speech.getAvailableVoicesAsync();
      const languageVoices = voices.filter(v => v.language === voiceLanguage || v.language === 'en-IN');
      
      let preferredVoice = selectedVoice || languageVoices.find(v => v.name === 'Rishi') || languageVoices[0];

      Speech.speak(cleanText, {
        language: voiceLanguage,
        voice: preferredVoice?.identifier,
        rate: 1.0,
        pitch: 1.0,
        onDone: () => setIsSpeaking(false),
        onStopped: () => setIsSpeaking(false),
        onError: () => setIsSpeaking(false)
      });
    } catch (error) {
      console.log('Speech error:', error);
      setIsSpeaking(false);
    }
  };

  const showVoiceSelector = async () => {
    try {
      const voices = await Speech.getAvailableVoicesAsync();
      const voiceLanguage = language === 'hindi' ? 'hi-IN' : language === 'telugu' ? 'te-IN' : language === 'tamil' ? 'ta-IN' : language === 'gujarati' ? 'gu-IN' : 'en-IN';
      
      const languageVoices = voices.filter(v => v.language === voiceLanguage || v.language === 'en-IN' || v.language.startsWith('en-'));
      
      setAvailableVoices(languageVoices);
      setShowVoicePicker(true);
    } catch (error) {
      console.log('Error getting voices:', error);
    }
  };

  const sharePDF = async () => {
    try {
      setIsGeneratingPDF(true);
      console.log('📄 Starting PDF generation...');
      const pdfUri = await generatePDF(message);
      console.log('✅ PDF generated:', pdfUri);
      await sharePDFOnWhatsApp(pdfUri);
      console.log('✅ PDF shared');
    } catch (error) {
      console.error('❌ PDF generation error:', error);
      Alert.alert('Error', `Failed to generate PDF: ${error.message}`);
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  const deleteMessage = async () => {
    try {
      const token = await AsyncStorage.getItem('authToken');
      const deleteUrl = `${API_BASE_URL}${getEndpoint(`/chat-v2/message/${message.messageId}`)}`;
      
      const response = await fetch(deleteUrl, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        Alert.alert('✅ Deleted', 'Message deleted successfully');
        if (onDelete) {
          onDelete(message.messageId);
        }
      } else {
        Alert.alert('❌ Error', 'Failed to delete message');
      }
    } catch (error) {
      Alert.alert('❌ Error', 'Failed to delete message');
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
    
    // First decode HTML entities
    let formatted = content
      .replace(/&quot;/g, '"')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ');
    
    // Process term tooltips FIRST, after HTML entity decoding
    if (message.terms && message.glossary && Object.keys(message.glossary).length > 0) {
      // First try to find existing <term> tags
      let termCount = 0;
      formatted = formatted.replace(/<term\s+id=["']([^"']+)["']\s*>([^<]+)<\/term>/gi, (match, termId, termText) => {
        const normalizedId = termId.toLowerCase().trim();
        if (message.glossary[normalizedId]) {
          termCount++;
          const definition = message.glossary[normalizedId].replace(/"/g, '&quot;');
          return `<tooltip data-term="${normalizedId}" data-definition="${definition}">${termText}</tooltip>`;
        }
        return termText;
      });
      
      // If no tags found, auto-wrap terms from glossary keys
      if (termCount === 0) {
        Object.keys(message.glossary).forEach(termKey => {
          const definition = message.glossary[termKey].replace(/"/g, '&quot;');
          // Create case-insensitive regex for the term
          const termPattern = new RegExp(`\\b(${termKey.replace(/[()]/g, '\\$&')})\\b`, 'gi');
          formatted = formatted.replace(termPattern, (match) => {
            return `<tooltip data-term="${termKey}" data-definition="${definition}">${match}</tooltip>`;
          });
        });
      }
    }
    
    // Normalize line breaks
    formatted = formatted.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    
    // Handle markdown tables - convert to simple format
    formatted = formatted.replace(/\|(.+)\|\n\|[:\s-]+\|\n((?:\|.+\|\n?)+)/g, (match, header, rows) => {
      return `<table>${header}|||${rows}</table>`;
    });
    
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
      { regex: /<followup>(.*?)<\/followup>/gs, type: 'followup' },
      { regex: /<table>(.*?)<\/table>/gs, type: 'table' }
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
          .replace(/Quick Answer\s*:?/g, '')
          .replace(/^\s*:?\s*/, '')
          .replace(/^\n*:/, '')
          .replace(/^\s*:\s*/, '')
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
          .replace(/Final Thoughts\s*:?/g, '')
          .replace(/^\s*:?\s*/, '')
          .replace(/^\n*:/, '')
          .replace(/^\s*:\s*/, '')
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
            <Text style={styles.cardTitle}>💭 Final Thoughts</Text>
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
      } else if (item.type === 'table') {
        // Parse table data
        const tableData = item.match[1].split('|||');
        const headerRow = tableData[0].split('|').map(h => h.trim()).filter(h => h);
        const dataRows = tableData[1].split('\n').filter(r => r.trim() && r.includes('|'));
        
        elements.push(
          <View key={`table-${currentIndex++}`} style={styles.tableContainer}>
            {/* Header */}
            <View style={styles.tableHeaderRow}>
              {headerRow.map((header, idx) => (
                <Text key={`th-${idx}`} style={[styles.tableHeaderCell, { flex: idx === 0 ? 1.5 : 1 }]}>
                  {header.replace(/\*\*/g, '')}
                </Text>
              ))}
            </View>
            {/* Rows */}
            {dataRows.map((row, rowIdx) => {
              const cells = row.split('|').map(c => c.trim()).filter(c => c);
              return (
                <View key={`tr-${rowIdx}`} style={styles.tableRow}>
                  {cells.map((cell, cellIdx) => (
                    <Text key={`td-${rowIdx}-${cellIdx}`} style={[styles.tableCell, { flex: cellIdx === 0 ? 1.5 : 1 }]}>
                      {cell.replace(/\*\*/g, '')}
                    </Text>
                  ))}
                </View>
              );
            })}
          </View>
        );
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
    
    // Handle tooltip tags first
    const tooltipRegex = /<tooltip data-term="([^"]+)" data-definition="([^"]+)">([^<]+)<\/tooltip>/g;
    const parts = text.split(tooltipRegex);
    
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (!part) continue;
      
      if (i % 4 === 3) { // Tooltip text (every 4th element after split)
        const termId = parts[i - 2];
        const definition = parts[i - 1].replace(/&quot;/g, '"');
        
        elements.push(
          <Text
            key={`tooltip-${startIndex}-${i}`}
            onPress={() => setTooltipModal({ show: true, term: part, definition })}
            style={styles.tooltipText}
          >
            {part}
          </Text>
        );
      } else if (i % 4 === 0) { // Regular text
        // Handle markdown bold formatting
        const boldRegex = /\*\*(.*?)\*\*/g;
        const boldParts = part.split(boldRegex);
        
        boldParts.forEach((boldPart, boldIndex) => {
          if (!boldPart) return;
          
          if (boldIndex % 2 === 1) { // Odd indices are bold text
            elements.push(
              <Text key={`bold-${startIndex}-${i}-${boldIndex}`} style={styles.boldText}>
                {boldPart}
              </Text>
            );
          } else if (boldPart.trim()) {
            // Handle italics within regular text
            const italicRegex = /\*(.*?)\*/g;
            const italicParts = boldPart.split(italicRegex);
            
            italicParts.forEach((italicPart, italicIndex) => {
              if (!italicPart) return;
              
              if (italicIndex % 2 === 1) { // Odd indices are italic text
                elements.push(
                  <Text key={`italic-${startIndex}-${i}-${boldIndex}-${italicIndex}`} style={[styles.regularText, { fontStyle: 'italic' }]}>
                    {italicPart}
                  </Text>
                );
              } else if (italicPart.trim()) {
                elements.push(
                  <Text key={`text-${startIndex}-${i}-${boldIndex}-${italicIndex}`} style={styles.regularText}>
                    {italicPart}
                  </Text>
                );
              }
            });
          }
        });
      }
    }
    
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
        let headerText = part.replace(/^##\s+(.+)$/m, '$1').replace(/^###\s+(.+)$/m, '$1');
        // Remove tooltip tags from headers
        headerText = headerText.replace(/<tooltip[^>]*>([^<]+)<\/tooltip>/g, '$1');
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
            
            // Process tooltips after HTML entity decoding
            if (message.terms && message.glossary) {
              processedLine = processedLine.replace(/<term id="([^"]+)">([^<]+)<\/term>/g, (match, termId, termText) => {
                if (message.glossary[termId]) {
                  return `<tooltip data-term="${termId}" data-definition="${message.glossary[termId].replace(/"/g, '&quot;')}">${termText}</tooltip>`;
                }
                return match;
              });
            }
            
            // Remove any remaining term tags that weren't processed
            processedLine = processedLine.replace(/<term id="[^"]+">([^<]+)<\/term>/g, '$1');
            
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
        
        {/* Beta Notice for Timeline Predictions */}
        {message.role === 'assistant' && !isClarification && (
          <View style={styles.betaNotice}>
            <Text style={styles.betaNoticeText}>⚠️ BETA NOTICE: Timeline predictions are experimental. Please use logic and discretion.</Text>
          </View>
        )}
        
        {/* Summary Image */}
        {message.summary_image && (
          <View style={{ marginBottom: 15, alignItems: 'center' }}>
            <Image 
              source={{ uri: message.summary_image }}
              style={{ width: '100%', maxWidth: 400, height: 250, borderRadius: 12 }}
              resizeMode="contain"
              onError={(e) => console.log('❌ Image load error:', e.nativeEvent.error)}
              onLoad={() => console.log('✅ Image loaded successfully')}
            />
          </View>
        )}
        
        <View style={styles.messageContent}>
          {renderedElements}
        </View>

        {!message.isTyping && message.messageId && (
          <View style={styles.actionButtons}>
            {message.role === 'assistant' && (
              <>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={speak}
                >
                  <Ionicons name={isSpeaking ? "stop-circle" : "volume-medium"} size={16} color={isSpeaking ? "#ff6b35" : "#666"} />
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.actionButton}
                  onPress={showVoiceSelector}
                >
                  <Ionicons name="settings" size={16} color="#666" />
                </TouchableOpacity>
              </>
            )}
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
            {message.role === 'assistant' && (
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
            )}
            <TouchableOpacity
              style={[styles.actionButton, styles.deleteButton]}
              onPress={() => {
                Alert.alert(
                  'Delete Message',
                  'Are you sure you want to delete this message?',
                  [
                    { text: 'Cancel', style: 'cancel' },
                    { text: 'Delete', style: 'destructive', onPress: deleteMessage }
                  ]
                );
              }}
            >
              <Text style={styles.actionIcon}>🗑️</Text>
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
      
      {/* Voice Picker Modal */}
      <Modal
        visible={showVoicePicker}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setShowVoicePicker(false)}
      >
        <View style={styles.voiceModalOverlay}>
          <View style={styles.voiceModalContent}>
            <Text style={styles.voiceModalTitle}>Choose Voice</Text>
            <ScrollView style={styles.voiceScrollView} showsVerticalScrollIndicator={true}>
              {availableVoices.map((voice, index) => (
                <TouchableOpacity
                  key={voice.identifier}
                  style={[
                    styles.voiceOption,
                    selectedVoice?.identifier === voice.identifier && styles.selectedVoiceOption
                  ]}
                  onPress={() => {
                    setSelectedVoice(voice);
                    setShowVoicePicker(false);
                  }}
                >
                  <Text style={[
                    styles.voiceOptionText,
                    selectedVoice?.identifier === voice.identifier && styles.selectedVoiceText
                  ]}>
                    {voice.name} ({voice.language})
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
            <TouchableOpacity
              style={styles.voiceModalClose}
              onPress={() => setShowVoicePicker(false)}
            >
              <Text style={styles.voiceModalCloseText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
      
      {/* Tooltip Modal */}
      <Modal
        visible={tooltipModal.show}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setTooltipModal({ show: false, term: '', definition: '' })}
      >
        <View style={styles.tooltipModalOverlay}>
          <View style={styles.tooltipModalContent}>
            <Text style={styles.tooltipModalTitle}>{tooltipModal.term}</Text>
            <Text style={styles.tooltipModalDefinition}>{tooltipModal.definition}</Text>
            <TouchableOpacity
              style={styles.tooltipModalClose}
              onPress={() => setTooltipModal({ show: false, term: '', definition: '' })}
            >
              <Text style={styles.tooltipModalCloseText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
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
  deleteButton: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderColor: 'rgba(239, 68, 68, 0.3)',
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
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
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
  tooltipTerm: {
    backgroundColor: 'rgba(233, 30, 99, 0.15)',
    borderRadius: 4,
    paddingHorizontal: 4,
    borderWidth: 1,
    borderColor: 'rgba(233, 30, 99, 0.3)',
  },
  tooltipText: {
    color: '#e91e63',
    fontWeight: '600',
    textDecorationLine: 'underline',
    textDecorationStyle: 'dotted',
    backgroundColor: 'rgba(233, 30, 99, 0.15)',
    borderRadius: 4,
    paddingHorizontal: 4,
  },
  tooltipModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  tooltipModalContent: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    maxWidth: '90%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  tooltipModalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#e91e63',
    marginBottom: 10,
  },
  tooltipModalDefinition: {
    fontSize: 15,
    lineHeight: 22,
    color: '#333',
    marginBottom: 15,
  },
  tooltipModalClose: {
    backgroundColor: '#e91e63',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    alignSelf: 'flex-end',
  },
  tooltipModalCloseText: {
    color: 'white',
    fontWeight: '600',
  },
  tableContainer: {
    marginVertical: 10,
    borderRadius: 8,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
  },
  tableHeaderRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 107, 53, 0.15)',
    paddingVertical: 8,
    paddingHorizontal: 4,
  },
  tableHeaderCell: {
    fontSize: 12,
    fontWeight: '700',
    color: '#ff6b35',
    paddingHorizontal: 4,
  },
  tableRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.5)',
    paddingVertical: 8,
    paddingHorizontal: 4,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255, 107, 53, 0.1)',
  },
  tableCell: {
    fontSize: 11,
    color: '#2c3e50',
    paddingHorizontal: 4,
  },
  voiceModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  voiceModalContent: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 20,
    maxWidth: '90%',
    maxHeight: '70%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  voiceModalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#ff6b35',
    marginBottom: 15,
    textAlign: 'center',
  },
  voiceScrollView: {
    maxHeight: 300,
    marginBottom: 15,
  },
  voiceOption: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
  },
  selectedVoiceOption: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    borderColor: '#ff6b35',
  },
  voiceOptionText: {
    fontSize: 15,
    color: '#333',
  },
  selectedVoiceText: {
    color: '#ff6b35',
    fontWeight: '600',
  },
  voiceModalClose: {
    backgroundColor: '#ff6b35',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    alignSelf: 'center',
    marginTop: 15,
  },
  voiceModalCloseText: {
    color: 'white',
    fontWeight: '600',
  },
  betaNotice: {
    backgroundColor: 'rgba(255, 152, 0, 0.1)',
    borderLeftWidth: 3,
    borderLeftColor: '#FF9800',
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
  },
  betaNoticeText: {
    fontSize: 12,
    color: '#E65100',
    fontWeight: '600',
    lineHeight: 16,
  },
});