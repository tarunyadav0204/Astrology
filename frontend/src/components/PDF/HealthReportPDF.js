import React from 'react';
import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';

const styles = StyleSheet.create({
  page: {
    padding: 40,
    fontFamily: 'Helvetica',
    fontSize: 11,
    lineHeight: 1.5,
    color: '#333'
  },
  header: {
    marginBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    paddingBottom: 10,
  },
  title: {
    fontSize: 24,
    color: '#2E7D32',
    marginBottom: 5,
    fontWeight: 'bold',
  },
  meta: {
    fontSize: 10,
    color: '#7F8C8D',
  },
  section: {
    marginBottom: 15,
    padding: 10,
    backgroundColor: '#F9F9F9',
    borderRadius: 4,
  },
  questionText: {
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 4,
    color: '#2E7D32',
  },
  answerText: {
    marginBottom: 10,
    textAlign: 'justify',
  },
  highlightBox: {
    backgroundColor: '#E8F5E8',
    padding: 12,
    marginBottom: 20,
    borderRadius: 5,
    borderLeftWidth: 4,
    borderLeftColor: '#4CAF50',
  },
  disclaimer: {
    position: 'absolute',
    bottom: 30,
    left: 40,
    right: 40,
    fontSize: 9,
    textAlign: 'center',
    color: '#95A5A6',
    borderTopWidth: 1,
    borderTopColor: '#EEE',
    paddingTop: 10,
  }
});

const cleanText = (html) => {
  if (!html) return '';
  let text = html.replace(/<br\s*\/?>/gi, '\n');
  text = text.replace(/<[^>]+>/g, '');
  return text;
};

export const HealthReportPDF = ({ data, userName }) => {
  // Handle both health_analysis format and direct insights format
  const analysis = data?.health_analysis?.json_response || data?.insights || {};
  const insights = data?.insights || {};
  
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Vedic Health Analysis</Text>
          <Text style={styles.meta}>
            Prepared for: {userName || 'User'} • Date: {new Date().toLocaleDateString()}
          </Text>
        </View>

        {/* Health Overview */}
        {insights.health_overview && (
          <View style={styles.highlightBox}>
            <Text style={{ fontWeight: 'bold', marginBottom: 5 }}>Health Overview:</Text>
            <Text>{cleanText(insights.health_overview)}</Text>
          </View>
        )}

        {/* Constitutional Analysis */}
        {insights.constitutional_analysis && (
          <View style={styles.section}>
            <Text style={styles.questionText}>Constitutional Analysis</Text>
            <Text style={styles.answerText}>{cleanText(insights.constitutional_analysis)}</Text>
          </View>
        )}

        {/* Key Health Areas */}
        {insights.key_health_areas && insights.key_health_areas.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.questionText}>Key Health Areas</Text>
            {insights.key_health_areas.map((area, idx) => (
              <Text key={idx} style={{ fontSize: 10, marginBottom: 2 }}>• {cleanText(area)}</Text>
            ))}
          </View>
        )}

        {/* Lifestyle Recommendations */}
        {insights.lifestyle_recommendations && insights.lifestyle_recommendations.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.questionText}>Lifestyle Recommendations</Text>
            {insights.lifestyle_recommendations.map((rec, idx) => (
              <Text key={idx} style={{ fontSize: 10, marginBottom: 2 }}>• {cleanText(rec)}</Text>
            ))}
          </View>
        )}

        {/* Preventive Measures */}
        {insights.preventive_measures && insights.preventive_measures.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.questionText}>Preventive Measures</Text>
            {insights.preventive_measures.map((measure, idx) => (
              <Text key={idx} style={{ fontSize: 10, marginBottom: 2 }}>• {cleanText(measure)}</Text>
            ))}
          </View>
        )}

        {/* Positive Indicators */}
        {insights.positive_indicators && (
          <View style={styles.section}>
            <Text style={styles.questionText}>Positive Health Indicators</Text>
            <Text style={styles.answerText}>{cleanText(insights.positive_indicators)}</Text>
          </View>
        )}

        {/* Fallback for structured analysis */}
        {analysis.detailed_analysis && analysis.detailed_analysis.map((item, index) => (
          <View key={index} style={styles.section}>
            <Text style={styles.questionText}>{index + 1}. {cleanText(item.question)}</Text>
            <Text style={styles.answerText}>{cleanText(item.answer)}</Text>
            
            {item.key_points && item.key_points.length > 0 && (
              <View style={{ marginTop: 8 }}>
                <Text style={{ fontWeight: 'bold', fontSize: 10, marginBottom: 4 }}>Key Points:</Text>
                {item.key_points.map((point, idx) => (
                  <Text key={idx} style={{ fontSize: 10, marginBottom: 2 }}>• {cleanText(point)}</Text>
                ))}
              </View>
            )}
          </View>
        ))}

        <Text style={styles.disclaimer}>
          This health analysis is based on Vedic astrological principles and is for educational purposes only. 
          Please consult qualified healthcare professionals for any health concerns or medical decisions.
        </Text>
      </Page>
    </Document>
  );
};