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
  Dimensions,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, API_BASE_URL, getEndpoint, VOICE_CONFIG } from '../../utils/constants';
import { generatePDF, sharePDFOnWhatsApp } from '../../utils/pdfGenerator';
import { textToSpeech } from '../../utils/textToSpeech';
import { useTranslation } from 'react-i18next';

export default function MessageBubble({ message, language, onFollowUpClick, partnership, onDelete, onRestart }) {
  const { t } = useTranslation();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const isPartnership = partnership || message.partnership_mode;
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [tooltipModal, setTooltipModal] = useState({ show: false, term: '', definition: '' });
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showVoicePicker, setShowVoicePicker] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const [showImageModal, setShowImageModal] = useState(false);
  const [isImageLoading, setIsImageLoading] = useState(true);
  const skeletonAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (message.summary_image && isImageLoading) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(skeletonAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(skeletonAnim, {
            toValue: 0,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [message.summary_image, isImageLoading]);

  // Animated loader for typing indicator
  const dot1Anim = useRef(new Animated.Value(0)).current;
  const dot2Anim = useRef(new Animated.Value(0)).current;
  const dot3Anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    let animationRef = null;
    
    if (message.isTyping) {
      const animateLoader = () => {
        animationRef = Animated.sequence([
          Animated.timing(dot1Anim, { toValue: 1, duration: 400, useNativeDriver: true }),
          Animated.timing(dot2Anim, { toValue: 1, duration: 400, useNativeDriver: true }),
          Animated.timing(dot3Anim, { toValue: 1, duration: 400, useNativeDriver: true }),
          Animated.timing(dot1Anim, { toValue: 0.3, duration: 400, useNativeDriver: true }),
          Animated.timing(dot2Anim, { toValue: 0.3, duration: 400, useNativeDriver: true }),
          Animated.timing(dot3Anim, { toValue: 0.3, duration: 400, useNativeDriver: true }),
        ]);
        animationRef.start((finished) => {
          if (finished && message.isTyping) {
            animateLoader();
          }
        });
      };
      animateLoader();
    }
    
    return () => {
      if (animationRef) {
        animationRef.stop();
      }
    };
  }, [message.isTyping]);



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
      textToSpeech.stop();
      setIsSpeaking(false);
      return;
    }

    try {
      setIsSpeaking(true);
      const cleanText = message.content
        .replace(/<[^>]*>/g, '')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/&quot;/g, '"')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&#39;/g, "'")
        .replace(/&nbsp;/g, ' ')
        .trim();

      textToSpeech.speak(cleanText, {
        voice: selectedVoice?.identifier,
        onDone: () => setIsSpeaking(false),
        onError: () => setIsSpeaking(false),
      });
    } catch (error) {
      setIsSpeaking(false);
    }
  };

  const showVoiceSelector = async () => {
    try {
      const voices = await textToSpeech.getAvailableVoices();
      const filteredVoices = voices.filter(v => v.language.startsWith('en') || v.language.startsWith('hi'));
      setAvailableVoices(filteredVoices);
      setShowVoicePicker(true);
    } catch (error) {
      Alert.alert('Error', 'Could not load voices');
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

      const shareText = `☀️ AstroRoshni Prediction\n\n${cleanText}\n\nShared from AstroRoshni App`;
      
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
    
    // First decode HTML entities AGGRESSIVELY
    let formatted = content;
    
    // Multiple passes to handle nested encoding
    for (let i = 0; i < 3; i++) {
      formatted = formatted
        .replace(/&quot;/g, '"')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&#39;/g, "'")
        .replace(/&nbsp;/g, ' ');
    }
    
    // Remove glossary JSON blocks that shouldn't be displayed
    formatted = formatted.replace(/GLOSSARY_START[\s\S]*?GLOSSARY_END/g, '');
    formatted = formatted.replace(/```json[\s\S]*?```/g, '');
    formatted = formatted.replace(/\{\s*"[^"]+"\s*:\s*"[^"]*"[\s\S]*?\}/g, '');
    // Remove glossary headers
    formatted = formatted.replace(/#### Glossary[\s\S]*?(?=####|$)/gi, '');
    formatted = formatted.replace(/### Glossary[\s\S]*?(?=###|$)/gi, '');
    formatted = formatted.replace(/## Glossary[\s\S]*?(?=##|$)/gi, '');
    
    // Remove standalone # at end of lines (trailing markdown artifacts)
    formatted = formatted
      .replace(/\n\s*#+\s*$/gm, '')
      .replace(/\n\s*#+\s*\n/g, '\n')
      .replace(/#+\s*$/, '');
    
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
    formatted = formatted.replace(/\r\n/g, '\n').replace(/\r/g, '\n').replace(/\\n/g, '\n');
    
    // Handle markdown tables - convert to simple format
    formatted = formatted.replace(/\|(.+?)\|\s*\n\s*\|[:\s-|]+\|\s*\n([\s\S]*?)(?=\n\n|\n###|\n##|$)/g, (match, header, rows) => {
      // console.log('Table regex match:', { match, header, rows });
      return `<table>${header.trim()}|||${rows.trim()}</table>`;
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
          const boldRegex = /\*\*(.*?)\*\*/gs;
          const parts = text.split(boldRegex);
          
          return parts.map((part, index) => {
            if (index % 2 === 1) { // Bold text
              return (
                <Text key={`card-bold-${index}`} style={[styles.cardText, { fontWeight: '700' }]}>
                  {part}
                </Text>
              );
            } else if (part) {
              // Handle italics
              const italicRegex = /\*(.*?)\*/gs;
              const italicParts = part.split(italicRegex);
              
              return italicParts.map((italicPart, italicIndex) => {
                if (italicIndex % 2 === 1) { // Italic text
                  return (
                    <Text key={`card-italic-${index}-${italicIndex}`} style={[styles.cardText, { fontStyle: 'italic' }]}>
                      {italicPart}
                    </Text>
                  );
                } else if (italicPart) {
                  return (
                    <Text key={`card-text-${index}-${italicIndex}`} style={styles.cardText}>
                      {italicPart}
                    </Text>
                  );
                }
                return null;
              });
            }
            return null;
          });
        };
        
        elements.push(
          <TouchableOpacity 
            key={`quick-${currentIndex++}`} 
            activeOpacity={0.95}
            style={styles.quickAnswerWrapper}
          >
            <LinearGradient
              colors={Platform.OS === 'android' 
                ? ['rgba(255, 255, 255, 0.98)', 'rgba(255, 248, 225, 0.95)'] 
                : ['rgba(255, 255, 255, 0.25)', 'rgba(255, 255, 255, 0.1)']}
              style={styles.quickAnswerCard}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <LinearGradient
                colors={['rgba(255, 107, 53, 0.1)', 'transparent']}
                style={styles.cardGlow}
                start={{ x: 0, y: 0 }}
                end={{ x: 0.5, y: 0.5 }}
              />
              <View style={styles.cardHeader}>
                <View style={styles.iconCircle}>
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
                </View>
                <View>
                  <Text style={styles.cardTitle}>Quick Answer</Text>
                  <View style={styles.titleUnderline} />
                </View>
              </View>
              <Text style={styles.cardText}>
                {renderCardContent(cardContent)}
              </Text>
              
              {/* Decorative sparkle */}
              <Text style={styles.sparkleIcon}>✨</Text>
            </LinearGradient>
          </TouchableOpacity>
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
          const boldRegex = /\*\*(.*?)\*\*/gs;
          const parts = text.split(boldRegex);
          
          return parts.map((part, index) => {
            if (index % 2 === 1) { // Bold text
              return (
                <Text key={`card-bold-${index}`} style={[styles.cardText, { fontWeight: '700' }]}>
                  {part}
                </Text>
              );
            } else if (part) {
              // Handle italics
              const italicRegex = /\*(.*?)\*/gs;
              const italicParts = part.split(italicRegex);
              
              return italicParts.map((italicPart, italicIndex) => {
                if (italicIndex % 2 === 1) { // Italic text
                  return (
                    <Text key={`card-italic-${index}-${italicIndex}`} style={[styles.cardText, { fontStyle: 'italic' }]}>
                      {italicPart}
                    </Text>
                  );
                } else if (italicPart) {
                  return (
                    <Text key={`card-text-${index}-${italicIndex}`} style={styles.cardText}>
                      {italicPart}
                    </Text>
                  );
                }
                return null;
              });
            }
            return null;
          });
        };
        
        elements.push(
          <TouchableOpacity 
            key={`final-${currentIndex++}`}
            activeOpacity={0.95}
            style={styles.finalThoughtsWrapper}
          >
            <LinearGradient
              colors={Platform.OS === 'android'
                ? ['rgba(240, 249, 255, 0.98)', 'rgba(224, 242, 254, 0.95)']
                : ['rgba(230, 243, 255, 0.25)', 'rgba(176, 224, 230, 0.1)']}
              style={styles.finalThoughtsCard}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <LinearGradient
                colors={['rgba(65, 105, 225, 0.1)', 'transparent']}
                style={styles.cardGlow}
                start={{ x: 1, y: 0 }}
                end={{ x: 0.5, y: 0.5 }}
              />
              <View style={styles.cardHeader}>
                <View style={[styles.iconCircle, { backgroundColor: 'rgba(65, 105, 225, 0.1)', borderColor: 'rgba(65, 105, 225, 0.2)' }]}>
                  <Text style={styles.thoughtIcon}>💭</Text>
                </View>
                <View>
                  <Text style={[styles.cardTitle, { color: '#4169E1' }]}>Final Thoughts</Text>
                  <View style={[styles.titleUnderline, { backgroundColor: '#4169E1' }]} />
                </View>
              </View>
              <Text style={styles.cardText}>
                {renderCardContent(cardContent)}
              </Text>
              <Text style={[styles.sparkleIcon, { color: '#4169E1' }]}>📜</Text>
            </LinearGradient>
          </TouchableOpacity>
        );
      } else if (item.type === 'table') {
        // Parse table data
        const tableContent = item.match[1];
        const parts = tableContent.split('|||');
        if (parts.length >= 2) {
          const headerRow = parts[0].split('|').map(h => h.trim()).filter(h => h);
          const rowsText = parts[1].trim();
          const dataRows = rowsText.split('\n')
            .map(row => row.trim())
            .filter(row => row && row.includes('|') && !row.match(/^\s*\|[\s:-]+\|/))
            .slice(0, 10); // Limit rows to prevent infinite scroll
          
          // console.log('Table debug:', { headerRow, dataRows, rowsText, tableContent });
          
          if (dataRows.length > 0) {
            elements.push(
              <View key={`table-${currentIndex++}`} style={styles.tableContainer}>
                {/* Header */}
                <View style={styles.tableHeaderRow}>
                  {headerRow.map((header, idx) => (
                    <Text key={`th-${idx}`} style={[styles.tableHeaderCell, { flex: 1 }]}>
                      {header.replace(/\*\*/g, '')}
                    </Text>
                  ))}
                </View>
                {/* Rows */}
                {dataRows.map((row, rowIdx) => {
                  const cells = row.split('|').map(c => c.trim()).filter(c => c);
                  if (cells.length === 0) return null;
                  return (
                    <View key={`tr-${rowIdx}`} style={styles.tableRow}>
                      {cells.map((cell, cellIdx) => (
                        <Text key={`td-${rowIdx}-${cellIdx}`} style={[styles.tableCell, { flex: 1 }]}>
                          {cell.replace(/\*\*/g, '')}
                        </Text>
                      ))}
                    </View>
                  );
                }).filter(Boolean)}
              </View>
            );
          }
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
    
    // Handle tooltip tags first
    const tooltipRegex = /<tooltip data-term="([^"]+)" data-definition="([^"]+)">([^<]+)<\/tooltip>/g;
    const parts = text.split(tooltipRegex);
    
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      // Don't skip empty parts here as it breaks the index-based logic (i % 4)
      
      if (i % 4 === 3) { // Tooltip text
        const definition = parts[i - 1]?.replace(/&quot;/g, '"') || '';
        
        elements.push(
          <Text
            key={`tooltip-${startIndex}-${i}`}
            onPress={() => setTooltipModal({ show: true, term: part, definition: definition })}
            style={styles.tooltipText}
          >
            {part} ⓘ
          </Text>
        );
      } else if (i % 4 === 0 && part) { // Regular text
        // Handle markdown bold formatting
        const boldRegex = /\*\*(.*?)\*\*/gs;
        const boldParts = part.split(boldRegex);
        
        boldParts.forEach((boldPart, boldIndex) => {
          if (boldIndex % 2 === 1) { // Odd indices are bold text
            elements.push(
              <Text 
                key={`bold-${startIndex}-${i}-${boldIndex}`} 
                style={[
                  styles.boldText,
                  message.role === 'user' && styles.userText,
                  message.role === 'user' && { fontWeight: '700' }
                ]}
              >
                {boldPart}
              </Text>
            );
          } else if (boldPart) {
            // Handle italics within regular text
            const italicRegex = /\*(.*?)\*/g;
            const italicParts = boldPart.split(italicRegex);
            
            italicParts.forEach((italicPart, italicIndex) => {
              if (italicIndex % 2 === 1) { // Odd indices are italic text
                elements.push(
                  <Text 
                    key={`italic-${startIndex}-${i}-${boldIndex}-${italicIndex}`} 
                    style={[
                      styles.regularText, 
                      { fontStyle: 'italic' },
                      message.role === 'user' && styles.userText
                    ]}
                  >
                    {italicPart}
                  </Text>
                );
              } else if (italicPart) {
                elements.push(
                  <Text 
                    key={`text-${startIndex}-${i}-${boldIndex}-${italicIndex}`} 
                    style={[
                      styles.regularText,
                      message.role === 'user' && styles.userText
                    ]}
                  >
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
      <Text 
        key={`line-${startIndex}`} 
        style={[
          styles.regularText,
          message.role === 'user' && styles.userText
        ]}
      >
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
    if (text.includes('parashari')) return '🏛️';
    if (text.includes('jaimini')) return '🔱';
    if (text.includes('nadi')) return '🧬';
    if (text.includes('kp') || text.includes('stellar')) return '🎯';
    if (text.includes('synthesis')) return '⚛️';
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
    if (text.includes('remedy') || text.includes('solution')) return '☀️';
    if (text.includes('prediction') || text.includes('forecast')) return '🌙';
    if (text.includes('transit') || text.includes('planetary')) return '🪐';
    return '✨'; // Default symbol
  };

  const parseRegularText = (text, startIndex) => {
    const elements = [];
    let currentIndex = startIndex;
    let listCounter = 0;
    
    // Split by headers and paragraphs - include markdown headers up to level 4
    // We use [^:\n]+ to stop at a colon or newline so the content after a header isn't swallowed
    const parts = text.split(/(<h3>.*?<\/h3>|##\s+[^:\n]+|###\s+[^:\n]+|####\s+[^:\n]+|\n\n+)/).filter(part => {
      const trimmed = part.trim();
      // Filter out standalone # symbols
      return trimmed && trimmed !== '#';
    });
    
    for (const part of parts) {
      if (part.match(/<h3>(.*?)<\/h3>/)) {
        listCounter = 0; // Reset counter for new section
        let headerText = part.replace(/<h3>(.*?)<\/h3>/, '$1');
        headerText = headerText.replace(/<tooltip[^>]*>([^<]+)<\/tooltip>/g, '$1');
        const symbol = getHeaderSymbol(headerText);
        elements.push(
          <View key={`header-${currentIndex++}`} style={styles.headerContainer}>
            <AnimatedIcon symbol={symbol} />
            <Text style={styles.headerText}>{headerText}</Text>
          </View>
        );
      } else if (part.match(/^##\s+(.+)$/m) || part.match(/^###\s+(.+)$/m)) {
        listCounter = 0; // Reset counter for new section
        let headerText = part.replace(/^##\s+(.+)$/m, '$1').replace(/^###\s+(.+)$/m, '$1');
        headerText = headerText.replace(/<tooltip[^>]*>([^<]+)<\/tooltip>/g, '$1');
        const symbol = getHeaderSymbol(headerText);
        elements.push(
          <View key={`header-${currentIndex++}`} style={styles.headerContainer}>
            <AnimatedIcon symbol={symbol} />
            <Text style={styles.headerText}>{headerText}</Text>
          </View>
        );
      } else if (part.match(/^####\s+(.+)$/m)) {
        let headerText = part.replace(/^####\s+(.+)$/m, '$1');
        headerText = headerText.replace(/<tooltip[^>]*>([^<]+)<\/tooltip>/g, '$1');
        const symbol = getHeaderSymbol(headerText);
        elements.push(
          <View key={`subheader-${currentIndex++}`} style={styles.subHeaderContainer}>
            <Text style={styles.subHeaderIcon}>{symbol}</Text>
            <Text style={styles.subHeaderText}>{headerText}</Text>
          </View>
        );
      } else if (part.trim()) {
        // Handle lists and regular text
        // Clean up leading colons and whitespace that might be left over from header split
        let cleanPart = part.replace(/^\s*[:：]\s*/, '');
        if (!cleanPart.trim()) continue;

        const lines = cleanPart.split('\n').filter(line => line.trim());
        
        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) continue;
          
          if (trimmedLine.startsWith('•') || trimmedLine.startsWith('-') || trimmedLine.startsWith('* ') || trimmedLine.match(/^\d+\./)) {
            const isNumbered = trimmedLine.match(/^(\d+)\./);
            const number = isNumbered ? isNumbered[1] : null;
            
            listCounter++;
            let cleanListText = trimmedLine
              .replace(/^([•\-\*]|\d+\.)\s*/, '') // Remove exactly one bullet or number and trailing space
              .replace(/&lt;/g, '<')
              .replace(/&gt;/g, '>')
              .replace(/&quot;/g, '"')
              .replace(/&amp;/g, '&')
              .replace(/&#39;/g, "'")
              .replace(/&nbsp;/g, ' ')
              .replace(/<[^>]*>/g, '');
            
            // Process bold formatting in list items
            const boldRegex = /\*\*(.*?)\*\*/gs;
            const listParts = cleanListText.split(boldRegex);
            
            const listElements = listParts.map((listPart, listIndex) => {
              if (listIndex % 2 === 1) { // Odd indices are bold text
                return (
                  <Text key={`list-bold-${currentIndex}-${listIndex}`} style={[styles.listText, styles.boldText]}>
                    {listPart}
                  </Text>
                );
              } else if (listPart) {
                return (
                  <Text key={`list-text-${currentIndex}-${listIndex}`} style={styles.listText}>
                    {listPart}
                  </Text>
                );
              }
              return null;
            });
            
            elements.push(
              <View key={`list-${currentIndex++}`} style={styles.listItem}>
                {isNumbered ? (
                  <View style={styles.numberCircle}>
                    <Text style={styles.numberText}>{number}</Text>
                  </View>
                ) : (
                  <View style={styles.bulletContainer}>
                    <View style={styles.bulletDot} />
                  </View>
                )}
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



  // Check if this is a clarification message
  const isClarification = message.message_type === 'clarification';

  // Handle empty content for non-typing messages
  if (!message.content || message.content.trim() === '') {
    return null;
  }

  const formattedContent = formatContent(message.content);
  const renderedElements = renderFormattedText(formattedContent);

  const BubbleWrapper = ({ children, role, isPartnership, isClarification, timestamp }) => {
    if (role === 'user') {
      return (
        <LinearGradient
          colors={['#dcf0ff', '#bae6fd']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[
            styles.bubble,
            styles.userBubble,
            isPartnership && styles.partnershipBubble
          ]}
        >
          <View style={styles.userHeader}>
            <LinearGradient
              colors={['#3b82f6', '#60a5fa']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.userBadge}
            >
            <Ionicons name="person" size={10} color="#fff" style={styles.userIcon} />
            <Text style={styles.userLabel}>{t('chat.you', 'You')}</Text>
          </LinearGradient>
          </View>
          {children}
          <Text style={[styles.timestamp, { color: 'rgba(30, 58, 138, 0.5)' }]}>
            {new Date(timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </Text>
        </LinearGradient>
      );
    }
    return (
      <View style={[
        styles.bubble,
        styles.assistantBubble,
        isPartnership && styles.partnershipBubble,
        isClarification && styles.clarificationBubble
      ]}>
        {children}
      </View>
    );
  };

  return (
    <Animated.View style={[
      styles.container,
      message.role === 'user' ? styles.userContainer : styles.assistantContainer,
      { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }
    ]}>
      <BubbleWrapper 
        role={message.role} 
        isPartnership={isPartnership} 
        isClarification={isClarification}
        timestamp={message.timestamp}
      >
        {message.role === 'assistant' && (
          <View style={styles.assistantHeader}>
            <LinearGradient
              colors={['#ff6b35', '#ff8c5a']}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.verifiedBadge}
            >
            <Ionicons name="checkmark-circle" size={12} color="#fff" style={styles.verifiedIcon} />
            <Text style={styles.assistantLabel}>
              {isClarification ? t('chat.inquiry', 'AstroRoshni Inquiry') : t('chat.verified', 'AstroRoshni Verified')}
            </Text>
          </LinearGradient>
            {message.isTyping && (
              <View style={styles.typingIndicatorBadge}>
                <Text style={styles.typingIndicatorText}>Analyzing Chart...</Text>
              </View>
            )}
          </View>
        )}
        
        {/* Beta Notice for Timeline Predictions */}
        {message.role === 'assistant' && !isClarification && (
          <View style={styles.betaNotice}>
            <Text style={styles.betaNoticeText}>{t('chat.betaNotice', '⚠️ BETA: Timeline predictions are experimental. Use logic and discretion.')}</Text>
          </View>
        )}
        
        {/* Legal Disclaimer */}
        {message.role === 'assistant' && !isClarification && (
          <View style={styles.disclaimerNotice}>
            <Text style={styles.disclaimerNoticeText}>
              {t('chat.disclaimerNotice', '⚖️ DISCLAIMER: Astrology is a probabilistic tool for guidance. Not a substitute for medical, legal, financial, or mental health advice. Consult qualified professionals for important decisions.')}
            </Text>
          </View>
        )}
        
        {/* Summary Image */}
        {message.summary_image && (
          <TouchableOpacity 
            style={styles.imageContainer}
            onPress={() => setShowImageModal(true)}
            activeOpacity={0.8}
          >
            {isImageLoading && (
              <View style={styles.skeletonWrapper}>
                <Animated.View 
                  style={[
                    styles.skeletonGradient,
                    {
                      opacity: skeletonAnim.interpolate({
                        inputRange: [0, 1],
                        outputRange: [0.3, 0.7]
                      })
                    }
                  ]} 
                />
                <View style={styles.skeletonContent}>
                  <Ionicons name="image-outline" size={32} color="rgba(255, 107, 53, 0.2)" />
                  <Text style={styles.skeletonText}>Preparing Chart...</Text>
                </View>
              </View>
            )}
            <Image 
              source={{ uri: message.summary_image }}
              style={[
                styles.summaryImage,
                isImageLoading && { position: 'absolute', opacity: 0 }
              ]}
              resizeMode="contain"
              onError={(e) => {
                console.log('❌ Image load error:', e.nativeEvent.error);
                setIsImageLoading(false);
              }}
              onLoad={() => {
                console.log('✅ Image loaded successfully');
                setIsImageLoading(false);
              }}
            />
            {!isImageLoading && (
              <Text style={styles.tapToEnlarge}>Tap to enlarge</Text>
            )}
          </TouchableOpacity>
        )}
        
        <View style={styles.messageContent}>
          {renderedElements}
        </View>

        {/* NEW: Render Follow-up Questions from the dedicated prop */}
        {message.follow_up_questions && message.follow_up_questions.length > 0 && (
          <View style={styles.followUpContainer}>
            {message.follow_up_questions.map((question, index) => {
              const cleanQuestion = question
                .replace(/^[\s☀️🌟⭐💫✨📅💼🍎📚🧘*•-]+/, '')
                .trim();
              if (cleanQuestion.length < 5) return null;
              return (
                <TouchableOpacity
                  key={`followup-prop-${index}`}
                  style={styles.followUpButton}
                  onPress={() => onFollowUpClick && onFollowUpClick(cleanQuestion)}
                >
                  <Text style={styles.followUpText}>{cleanQuestion}</Text>
                </TouchableOpacity>
              );
            }).filter(Boolean)}
          </View>
        )}

        {!message.isTyping && message.messageId && message.role === 'assistant' && (
          <View style={styles.actionButtons}>
            {/* Restart Button for timeout messages */}
            {message.showRestartButton && (
              <TouchableOpacity
                style={[styles.actionButton, styles.restartButton]}
                onPress={() => onRestart && onRestart(message.messageId)}
              >
                <Ionicons name="refresh" size={16} color="#ff6b35" />
              </TouchableOpacity>
            )}
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
              <Ionicons name="copy-outline" size={16} color="#666" />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={shareMessage}
            >
              <Ionicons name="share-social-outline" size={16} color="#666" />
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
                  <Ionicons name="document-text-outline" size={16} color="#666" />
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
              <Ionicons name="trash-outline" size={16} color="#666" />
            </TouchableOpacity>
          </View>
        )}

        {!message.isTyping && message.messageId && message.role === 'user' && (
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={styles.actionButton}
              onPress={copyToClipboard}
            >
              <Ionicons name="copy-outline" size={16} color="#666" />
            </TouchableOpacity>
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
              <Ionicons name="trash-outline" size={16} color="#666" />
            </TouchableOpacity>
          </View>
        )}

        {message.role === 'assistant' && (
          <Text style={styles.timestamp}>
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </Text>
        )}
      </BubbleWrapper>
      
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
        <TouchableOpacity 
          style={styles.tooltipModalOverlay} 
          activeOpacity={1} 
          onPress={() => setTooltipModal({ show: false, term: '', definition: '' })}
        >
          <Animated.View style={styles.tooltipModalContent}>
            <LinearGradient
              colors={Platform.OS === 'android' 
                ? ['rgba(0, 0, 0, 0.9)', 'rgba(20, 20, 20, 0.85)'] 
                : ['rgba(255, 255, 255, 0.98)', 'rgba(255, 248, 240, 0.95)']}
              style={styles.tooltipGradient}
            >
              <View style={styles.tooltipHeader}>
                <View style={styles.tooltipIconCircle}>
                  <Ionicons name="book-outline" size={20} color="#ff6b35" />
                </View>
                <Text style={styles.tooltipModalTitle}>{tooltipModal.term}</Text>
              </View>
              
              <ScrollView style={styles.tooltipScrollView} showsVerticalScrollIndicator={false}>
                <Text style={styles.tooltipModalDefinition}>{tooltipModal.definition}</Text>
              </ScrollView>

              <TouchableOpacity
                style={styles.tooltipModalClose}
                onPress={() => setTooltipModal({ show: false, term: '', definition: '' })}
              >
                <Text style={styles.tooltipModalCloseText}>{t('languageModal.close', 'Close')}</Text>
              </TouchableOpacity>
            </LinearGradient>
          </Animated.View>
        </TouchableOpacity>
      </Modal>
      
      {/* Image Modal */}
      <Modal
        visible={showImageModal}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowImageModal(false)}
      >
        <TouchableOpacity
          style={styles.imageModalOverlay}
          activeOpacity={1}
          onPress={() => setShowImageModal(false)}
        >
          <View style={styles.imageModalContainer}>
            {message.summary_image && (
              <Image
                source={{ uri: message.summary_image }}
                style={styles.fullScreenImage}
                resizeMode="contain"
              />
            )}
            <TouchableOpacity
              style={styles.closeImageButton}
              onPress={() => setShowImageModal(false)}
            >
              <Text style={styles.closeImageButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
        </TouchableOpacity>
      </Modal>
    </Animated.View>
  );
};

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
    maxWidth: '98%',
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
    borderBottomRightRadius: 4,
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.15)',
    shadowColor: '#3b82f6',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
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
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    gap: 8,
  },
  userHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  userBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
    shadowColor: '#3b82f6',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  userIcon: {
    marginRight: 4,
  },
  userLabel: {
    fontSize: 9,
    fontWeight: '800',
    color: '#fff',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  imageContainer: {
    marginBottom: 15,
    alignItems: 'center',
    width: '100%',
    height: 250,
    borderRadius: 12,
    overflow: 'hidden',
  },
  summaryImage: {
    width: '100%',
    maxWidth: 400,
    height: 250,
    borderRadius: 12,
  },
  skeletonWrapper: {
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(255, 107, 53, 0.05)',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  },
  skeletonGradient: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(255, 107, 53, 0.15)',
  },
  skeletonContent: {
    alignItems: 'center',
    gap: 8,
  },
  skeletonText: {
    fontSize: 12,
    color: 'rgba(255, 107, 53, 0.4)',
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  tapToEnlarge: {
    fontSize: 11,
    color: '#666',
    marginTop: 4,
  },
  verifiedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  verifiedIcon: {
    marginRight: 4,
  },
  assistantLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: '#fff',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  typingIndicatorBadge: {
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    borderWidth: 0.5,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  typingIndicatorText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#ff6b35',
    textTransform: 'uppercase',
  },
  messageContent: {
    paddingBottom: 4,
  },
  regularText: {
    fontSize: 15,
    lineHeight: 22,
    marginVertical: 2,
    color: '#2c3e50',
    flexShrink: 1,
  },
  userText: {
    color: '#1e3a8a',
    fontWeight: '500',
  },
  boldText: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '700',
    color: '#2c3e50',
    flexShrink: 1,
  },
  headerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
    backgroundColor: Platform.OS === 'android' ? 'rgba(255, 107, 53, 0.1)' : 'rgba(255, 107, 53, 0.06)',
    borderRadius: 25,
    alignSelf: 'flex-start',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(255, 107, 53, 0.3)',
  },
  headerIcon: {
    fontSize: 18,
    marginRight: 10,
  },
  headerText: {
    fontSize: 15,
    fontWeight: '800',
    color: '#ff6b35',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  subHeaderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: Platform.OS === 'android' ? 'rgba(255, 107, 53, 0.05)' : 'rgba(255, 107, 53, 0.03)',
    borderRadius: 12,
    borderLeftWidth: 3,
    borderLeftColor: 'rgba(255, 107, 53, 0.5)',
  },
  subHeaderIcon: {
    fontSize: 16,
    marginRight: 10,
  },
  subHeaderText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#ff6b35',
    letterSpacing: 0.2,
    flex: 1,
  },
  listItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginVertical: 6,
  },
  numberCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#ff6b35',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 10,
    marginTop: 2,
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 3,
  },
  numberText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '800',
  },
  bulletContainer: {
    width: 20,
    alignItems: 'center',
    justifyContent: 'flex-start',
    paddingTop: 8,
    marginRight: 8,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#ff6b35',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 3,
    elevation: 2,
  },
  bullet: {
    color: '#ff6b35',
    fontSize: 20,
    marginRight: 8,
  },
  listContent: {
    flex: 1,
    marginLeft: -2,
  },
  listText: {
    fontSize: 15,
    lineHeight: 22,
    color: '#2c3e50',
    flexShrink: 1,
  },
  quickAnswerWrapper: {
    marginVertical: 12,
    width: '100%',
  },
  quickAnswerCard: {
    borderRadius: 24,
    padding: 20,
    borderWidth: StyleSheet.hairlineWidth * 2,
    borderColor: 'rgba(255, 107, 53, 0.2)',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.15,
    shadowRadius: 15,
    elevation: 5,
    overflow: 'hidden',
    position: 'relative',
  },
  cardGlow: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 100,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
  },
  titleUnderline: {
    height: 2,
    width: 40,
    backgroundColor: '#ff6b35',
    marginTop: 2,
    borderRadius: 1,
    opacity: 0.4,
  },
  sparkleIcon: {
    position: 'absolute',
    bottom: 10,
    right: 15,
    fontSize: 16,
    opacity: 0.6,
    color: '#ff6b35',
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
  finalThoughtsWrapper: {
    marginVertical: 12,
    width: '100%',
  },
  finalThoughtsCard: {
    borderRadius: 24,
    padding: 20,
    borderWidth: StyleSheet.hairlineWidth * 2,
    borderColor: 'rgba(65, 105, 225, 0.2)',
    shadowColor: '#4169E1',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.15,
    shadowRadius: 15,
    elevation: 5,
    overflow: 'hidden',
    position: 'relative',
  },
  thoughtIcon: {
    fontSize: 18,
    color: '#4169E1',
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: Platform.OS === 'android' ? '#ff6b35' : '#2c3e50',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  cardText: {
    fontSize: 15,
    color: Platform.OS === 'android' ? '#2c3e50' : '#2c3e50',
    lineHeight: 22,
    zIndex: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 8,
    gap: 8,
  },
  actionButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 10,
    width: 36,
    height: 36,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  pdfButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderColor: 'rgba(59, 130, 246, 0.2)',
  },
  deleteButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderColor: 'rgba(239, 68, 68, 0.2)',
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
    backgroundColor: Platform.OS === 'android' ? 'rgba(255, 107, 53, 0.18)' : 'rgba(255, 107, 53, 0.12)',
    borderRadius: 25,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginBottom: 8,
    borderWidth: 1.5,
    borderColor: Platform.OS === 'android' ? 'rgba(255, 107, 53, 0.4)' : 'rgba(255, 107, 53, 0.3)',
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
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  typingText: {
    fontSize: 15,
    color: '#2c3e50',
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
  typingBubble: {
    maxWidth: '88%',
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
    color: '#ff6b35',
    fontWeight: '700',
    backgroundColor: 'rgba(255, 107, 53, 0.08)',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderWidth: 0.5,
    borderColor: 'rgba(255, 107, 53, 0.3)',
    textDecorationLine: 'underline',
    textDecorationStyle: 'dashed',
    overflow: 'hidden',
  },
  tooltipModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  tooltipModalContent: {
    width: '90%',
    maxWidth: 400,
    borderRadius: 24,
    overflow: 'hidden',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  tooltipGradient: {
    padding: 24,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: Platform.OS === 'android' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 107, 53, 0.1)',
  },
  tooltipHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
  },
  tooltipIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 107, 53, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.2)',
  },
  tooltipModalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#ff6b35',
    flex: 1,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  tooltipScrollView: {
    maxHeight: 300,
    marginBottom: 20,
  },
  tooltipModalDefinition: {
    fontSize: 15,
    lineHeight: 22,
    color: Platform.OS === 'android' ? '#ecf0f1' : '#2c3e50',
  },
  tooltipModalClose: {
    backgroundColor: '#ff6b35',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 25,
    alignSelf: 'center',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  tooltipModalCloseText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  tableContainer: {
    marginVertical: 12,
    borderRadius: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 53, 0.15)',
    backgroundColor: '#fff',
    shadowColor: '#ff6b35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  tableHeaderRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 107, 53, 0.08)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 107, 53, 0.15)',
    paddingVertical: 12,
    paddingHorizontal: 8,
  },
  tableHeaderCell: {
    fontSize: 12,
    fontWeight: '800',
    color: '#ff6b35',
    textAlign: 'center',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    paddingHorizontal: 4,
  },
  tableRow: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 0, 0, 0.03)',
    paddingVertical: 10,
    paddingHorizontal: 8,
    alignItems: 'center',
  },
  tableCell: {
    fontSize: 13,
    color: '#2c3e50',
    textAlign: 'center',
    fontWeight: '500',
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
  disclaimerNotice: {
    backgroundColor: 'rgba(156, 39, 176, 0.08)',
    borderLeftWidth: 3,
    borderLeftColor: '#9C27B0',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  disclaimerNoticeText: {
    fontSize: 11,
    color: '#6A1B9A',
    fontWeight: '600',
    lineHeight: 16,
  },
  imageModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.95)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  imageModalCloseButton: {
    position: 'absolute',
    top: 50,
    right: 20,
    zIndex: 10,
  },
  imageModalImage: {
    width: Dimensions.get('window').width,
    height: Dimensions.get('window').height * 0.8,
  },
});
