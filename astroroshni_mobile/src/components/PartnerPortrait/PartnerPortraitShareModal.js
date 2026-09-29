import React, { useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Image, Modal, Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View, useWindowDimensions } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import { useTranslation } from 'react-i18next';

import { useTheme } from '../../context/ThemeContext';
import { sharePartnerPortraitCard } from '../../platform/sharePartnerPortrait';
import { trackEvent } from '../../utils/analytics';

const SHARE_URL = 'astroroshni.com/mobile/partner-portrait';

export default function PartnerPortraitShareModal({ visible, onClose, portraitUrl, traits = [] }) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const { height } = useWindowDimensions();
  const [format, setFormat] = useState('story');
  const [sharing, setSharing] = useState(false);
  const [error, setError] = useState('');
  const cardRef = useRef(null);
  const story = format === 'story';
  const previewWidth = story ? Math.min(248, Math.max(190, (height - 290) * 9 / 16)) : Math.min(310, height - 330);
  const cleanTraits = useMemo(() => traits.filter(Boolean).slice(0, 3), [traits]);

  const share = async () => {
    try {
      setSharing(true);
      setError('');
      trackEvent('partner_portrait_share_started', { format });
      await sharePartnerPortraitCard(cardRef, format, {
        title: t('partnerPortrait.shareSheetTitle', 'My Partner Portrait from AstroRoshni'),
        text: t('partnerPortrait.shareSheetText', 'One possible partner appearance suggested by my birth chart. Create yours with AstroRoshni.'),
      });
      trackEvent('partner_portrait_shared', { format });
    } catch (shareError) {
      if (!['AbortError', 'NotAllowedError'].includes(shareError?.name)) {
        setError(t('partnerPortrait.shareFailed', 'The share card could not be created. Please try again.'));
      }
    } finally {
      setSharing(false);
    }
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={[styles.sheet, { backgroundColor: colors.surfaceRaised, borderColor: colors.cardBorder }]}> 
          <View style={styles.header}>
            <View style={styles.headerCopy}>
              <Text style={[styles.title, { color: colors.text }]}>{t('partnerPortrait.shareTitle', 'Share your Partner Portrait')}</Text>
              <Text style={[styles.subtitle, { color: colors.textSecondary }]}>{t('partnerPortrait.sharePrivacy', 'Your name and birth details are never added.')}</Text>
            </View>
            <TouchableOpacity onPress={onClose} style={styles.close}><Ionicons name="close" size={22} color={colors.text} /></TouchableOpacity>
          </View>
          <View style={[styles.formatRow, { backgroundColor: colors.background }]}> 
            {[
              ['story', t('partnerPortrait.storyFormat', 'Story · 9:16')],
              ['square', t('partnerPortrait.squareFormat', 'Post · 1:1')],
            ].map(([value, label]) => (
              <TouchableOpacity
                key={value}
                onPress={() => setFormat(value)}
                style={[styles.formatButton, format === value && { backgroundColor: colors.surfaceRaised, borderColor: colors.primary }]}
              >
                <Text style={[styles.formatText, { color: format === value ? colors.primary : colors.textSecondary }]}>{label}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <ScrollView contentContainerStyle={styles.previewWrap} showsVerticalScrollIndicator={false}>
            <View
              ref={cardRef}
              collapsable={false}
              style={[styles.shareCard, { width: previewWidth, aspectRatio: story ? 9 / 16 : 1 }]}
            >
              <Image source={{ uri: portraitUrl }} style={styles.shareImage} resizeMode="cover" />
              <LinearGradient colors={['rgba(23,3,14,0.05)', 'rgba(23,3,14,0.96)']} style={styles.shareShade} />
              <View style={styles.shareTop}>
                <Text style={styles.shareBrand}>ASTROROSHNI</Text>
                <Text style={styles.shareBadge}>{t('partnerPortrait.shareClassicalBadge', 'CLASSICAL CHART PORTRAIT')}</Text>
              </View>
              <View style={styles.shareBottom}>
                <Text style={[styles.shareHeadline, !story && styles.shareHeadlineSquare]}>{t('partnerPortrait.shareHeadline', 'My birth chart’s Partner Portrait')}</Text>
                <Text style={styles.shareQualifier}>{t('partnerPortrait.shareQualifier', 'One possible appearance suggested by repeated chart indications')}</Text>
                {cleanTraits.length ? (
                  <View style={styles.shareTraits}>
                    {cleanTraits.map((trait) => <Text key={trait} style={styles.shareTrait}>✦ {trait}</Text>)}
                  </View>
                ) : null}
                <View style={styles.shareFooter}>
                  <Text style={styles.shareCta}>{t('partnerPortrait.shareCreateYours', 'Create yours')}</Text>
                  <Text style={styles.shareUrl}>{SHARE_URL}</Text>
                </View>
              </View>
            </View>
          </ScrollView>
          {error ? <Text style={[styles.error, { color: colors.error }]}>{error}</Text> : null}
          <TouchableOpacity disabled={sharing || !portraitUrl} onPress={share} style={[styles.shareButton, { backgroundColor: colors.primary }]}> 
            {sharing ? <ActivityIndicator color={colors.onPrimary} /> : <Ionicons name="share-social-outline" size={19} color={colors.onPrimary} />}
            <Text style={[styles.shareButtonText, { color: colors.onPrimary }]}>{sharing ? t('partnerPortrait.preparingShare', 'Preparing…') : t('partnerPortrait.shareNow', 'Share portrait')}</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(15,3,10,0.68)', justifyContent: 'flex-end' },
  sheet: { maxHeight: '94%', borderTopLeftRadius: 28, borderTopRightRadius: 28, borderWidth: 1, padding: 18, paddingBottom: Platform.OS === 'ios' ? 30 : 20 },
  header: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  headerCopy: { flex: 1 },
  title: { fontSize: 20, lineHeight: 26, fontWeight: '900' },
  subtitle: { marginTop: 3, fontSize: 12, lineHeight: 17 },
  close: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center' },
  formatRow: { marginTop: 14, borderRadius: 15, padding: 4, flexDirection: 'row', gap: 4 },
  formatButton: { flex: 1, minHeight: 39, borderWidth: 1, borderColor: 'transparent', borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  formatText: { fontSize: 12, fontWeight: '800' },
  previewWrap: { alignItems: 'center', paddingVertical: 14 },
  shareCard: { backgroundColor: '#260817', overflow: 'hidden', borderRadius: 18 },
  shareImage: { ...StyleSheet.absoluteFillObject, width: '100%', height: '100%' },
  shareShade: { ...StyleSheet.absoluteFillObject },
  shareTop: { position: 'absolute', top: 0, left: 0, right: 0, padding: 15, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  shareBrand: { color: '#FFF8EB', fontSize: 11, fontWeight: '900', letterSpacing: 1.5 },
  shareBadge: { flexShrink: 1, color: '#F4D89B', fontSize: 7, fontWeight: '900', letterSpacing: 0.7, textAlign: 'right' },
  shareBottom: { position: 'absolute', left: 0, right: 0, bottom: 0, padding: 17 },
  shareHeadline: { color: '#FFF8EB', fontFamily: Platform.select({ web: 'Georgia', ios: 'Georgia', android: 'serif' }), fontSize: 24, lineHeight: 28, fontWeight: '800' },
  shareHeadlineSquare: { fontSize: 19, lineHeight: 22 },
  shareQualifier: { color: '#E8D5DD', marginTop: 7, fontSize: 9, lineHeight: 13 },
  shareTraits: { marginTop: 10, gap: 3 },
  shareTrait: { color: '#FFF8EB', fontSize: 9, lineHeight: 13, fontWeight: '700' },
  shareFooter: { marginTop: 12, paddingTop: 9, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: 'rgba(244,216,155,0.55)', flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  shareCta: { color: '#F4D89B', fontSize: 9, fontWeight: '900', textTransform: 'uppercase' },
  shareUrl: { color: '#FFF8EB', fontSize: 8, fontWeight: '700' },
  error: { textAlign: 'center', fontSize: 12, lineHeight: 17, marginBottom: 8 },
  shareButton: { minHeight: 54, borderRadius: 17, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  shareButtonText: { fontSize: 15, fontWeight: '900' },
});
