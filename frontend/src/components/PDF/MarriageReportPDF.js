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
    color: '#2C3E50',
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
    color: '#2C3E50',
  },
  answerText: {
    marginBottom: 10,
    textAlign: 'justify',
  },
  highlightBox: {
    backgroundColor: '#E8F6F3',
    padding: 12,
    marginBottom: 20,
    borderRadius: 5,
    borderLeftWidth: 4,
    borderLeftColor: '#1ABC9C',
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

export const MarriageReportPDF = ({ data, userName }) => {
  // Handle both old and new data formats
  const analysis = data?.marriage_analysis?.json_response || data?.analysis || {};
  
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.title}>Vedic Marriage Analysis</Text>
          <Text style={styles.meta}>
            Prepared for: {userName || 'User'} • Date: {new Date().toLocaleDateString()}
          </Text>
        </View>

        {analysis.quick_answer && (
          <View style={styles.highlightBox}>
            <Text style={{ fontWeight: 'bold', marginBottom: 5 }}>Executive Summary:</Text>
            <Text>{cleanText(analysis.quick_answer)}</Text>
          </View>
        )}

        {analysis.detailed_analysis && analysis.detailed_analysis.map((item, index) => (
          <View key={index} style={styles.section}>
            <Text style={styles.questionText}>{index + 1}. {cleanText(item.question)}</Text>
            <Text style={styles.answerText}>{cleanText(item.answer)}</Text>
          </View>
        ))}

        {analysis.final_thoughts && (
          <View style={{ marginTop: 10 }}>
            <Text style={{ fontSize: 14, fontWeight: 'bold', color: '#2980B9', marginBottom: 8 }}>Final Thoughts</Text>
            <Text style={styles.answerText}>{cleanText(analysis.final_thoughts)}</Text>
          </View>
        )}

        <Text style={styles.disclaimer}>
          Astrology is a guidance tool. This report is based on Vedic principles but should not replace professional advice.
        </Text>
      </Page>
    </Document>
  );
};