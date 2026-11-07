import React, { useEffect, useState } from 'react';
import { Modal, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';

/**
 * Shown after a completed chat answer to offer podcast playback.
 * Premium answers use included copy (no extra credits).
 */
export default function PodcastPromoModal({ visible, onClose, onGenerate, onCreateReel, podcastCost, reelCost, included, colors }) {
  const { t, i18n } = useTranslation();
  const [selectedFormat, setSelectedFormat] = useState(null);
  const cost = podcastCost ?? 2;
  const text = colors?.text ?? '#111';
  const sub = colors?.textSecondary ?? '#666';
  // THEMES.dark.cardBackground is translucent glass — use opaque surfaces so the dialog reads as a solid sheet.
  const cardBg = colors?.backgroundSecondary ?? colors?.background ?? '#fff';
  const border = colors?.cardBorder ?? colors?.strokeMuted ?? '#eee';
  const primary = colors?.primary ?? '#e91e63';
  useEffect(() => { if (!visible) setSelectedFormat(null); }, [visible]);
  const isPodcast = selectedFormat === 'podcast';
  const title = selectedFormat ? t('chat.podcastPromo.languageTitle', 'Choose a language') : t('chat.podcastPromo.mediaTitle', 'Take your reading with you');
  const body = selectedFormat
    ? t('chat.podcastPromo.languageBody', 'Choose the language for your {{format}}.', { format: isPodcast ? t('chat.podcastPromo.listenTitle', 'podcast') : t('chat.podcastPromo.reelTitle', 'reel') })
    : (included ? t('chat.podcastPromo.mediaPremiumBody', 'Listen to the included podcast, or turn this reading into a visual reel.') : t('chat.podcastPromo.mediaBody', 'Listen on the go or create a visual reel you can revisit and share.'));
  const chooseLanguage = (lang) => { if (isPodcast) onGenerate?.(lang); else onCreateReel?.(lang); };

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={[styles.card, { backgroundColor: cardBg, borderColor: border }]}>
          <Text style={[styles.title, { color: text }]}>
            {title}
          </Text>
          <Text style={[styles.body, { color: sub }]}>
            {body}
          </Text>
          {!selectedFormat ? <>
            <TouchableOpacity
              accessibilityRole="button"
              style={[styles.formatOption, { borderColor: primary, backgroundColor: `${primary}0D` }]}
              onPress={() => setSelectedFormat('podcast')}
            >
              <View style={[styles.reelIcon, { backgroundColor: `${primary}1A` }]}><Ionicons name="headset-outline" size={20} color={primary} /></View>
              <View style={styles.reelCopy}><Text style={[styles.reelTitle, { color: text }]}>{t('chat.podcastPromo.listenTitle', 'Listen as a podcast')}</Text><Text style={[styles.reelDescription, { color: sub }]}>{included ? t('chat.podcastPromo.listenIncluded', 'Included with this Premium question.') : t('chat.podcastPromo.listenCost', 'English or Hindi · {{cost}} credits', { cost })}</Text></View>
              <Ionicons name="chevron-forward" size={20} color={primary} />
            </TouchableOpacity>
            <TouchableOpacity
              accessibilityRole="button"
              style={[styles.formatOption, { borderColor: primary, backgroundColor: `${primary}0D` }]}
              onPress={() => onCreateReel?.(i18n.language?.startsWith('hi') ? 'hi' : 'en')}
            >
              <View style={[styles.reelIcon, { backgroundColor: `${primary}1A` }]}><Ionicons name="film-outline" size={20} color={primary} /></View>
              <View style={styles.reelCopy}><Text style={[styles.reelTitle, { color: text }]}>{t('chat.podcastPromo.reelTitle', 'Create a visual reel')}</Text><Text style={[styles.reelDescription, { color: sub }]}>{Number.isFinite(Number(reelCost)) ? t('chat.podcastPromo.reelCost', 'English or Hindi · {{cost}} credits', { cost: reelCost }) : t('chat.podcastPromo.reelCostLoading', 'Checking credits…')}</Text></View>
              <Ionicons name="chevron-forward" size={20} color={primary} />
            </TouchableOpacity>
          </> : <>
            <View style={[styles.mediaSection, { borderColor: border }]}><View style={styles.mediaHeading}><Ionicons name={isPodcast ? 'headset-outline' : 'film-outline'} size={19} color={primary} /><Text style={[styles.mediaTitle, { color: text }]}>{isPodcast ? t('chat.podcastPromo.listenTitle', 'Listen as a podcast') : t('chat.podcastPromo.reelTitle', 'Create a visual reel')}</Text></View></View>
            <View style={styles.options}>
              <TouchableOpacity style={[styles.option, { borderColor: primary, backgroundColor: `${primary}14` }]} onPress={() => chooseLanguage('en')}><Text style={[styles.optionLabel, { color: primary }]}>{t('chat.podcastLanguage.english', 'English')}</Text></TouchableOpacity>
              <TouchableOpacity style={[styles.option, { borderColor: border }]} onPress={() => chooseLanguage('hi')}><Text style={[styles.optionLabel, { color: text }]}>{t('chat.podcastLanguage.hindi', 'हिन्दी')}</Text></TouchableOpacity>
            </View>
            <TouchableOpacity style={styles.back} onPress={() => setSelectedFormat(null)}><Text style={[styles.backText, { color: primary }]}>{t('common.back', 'Back')}</Text></TouchableOpacity>
          </>}
          <TouchableOpacity
            style={[
              styles.btn,
              styles.btnGhost,
              {
                backgroundColor: colors?.backgroundTertiary ?? colors?.surface ?? 'rgba(0,0,0,0.06)',
                borderColor: border,
              },
            ]}
            onPress={onClose}
          >
            <Text style={[styles.btnGhostText, { color: sub }]}>
              {t('chat.podcastPromo.later', 'Maybe later')}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'center',
    padding: 20,
  },
  card: {
    borderRadius: 16,
    padding: 22,
    borderWidth: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 10,
  },
  body: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 16,
  },
  mediaSection: { borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 13 },
  mediaHeading: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  mediaTitle: { fontSize: 15, fontWeight: '700' },
  mediaDescription: { marginTop: 4, fontSize: 12, lineHeight: 17 },
  row: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    flexWrap: 'wrap',
    gap: 10,
  },
  options: {
    gap: 10,
    marginTop: 11,
    marginBottom: 12,
  },
  option: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1.5,
    alignItems: 'center',
  },
  optionLabel: {
    fontSize: 17,
    fontWeight: '700',
  },
  formatOption: { minHeight: 78, marginBottom: 12, padding: 13, borderRadius: 13, borderWidth: 1, flexDirection: 'row', alignItems: 'center', gap: 11 },
  reelIcon: { width: 39, height: 39, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  reelCopy: { flex: 1 },
  reelTitle: { fontSize: 15, fontWeight: '700' },
  reelDescription: { marginTop: 3, fontSize: 12, lineHeight: 17 },
  back: { alignSelf: 'center', paddingVertical: 8, paddingHorizontal: 12, marginBottom: 6 },
  backText: { fontSize: 14, fontWeight: '700' },
  btn: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
  },
  btnGhost: {
    borderWidth: 1,
    alignItems: 'center',
  },
  btnGhostText: {
    fontWeight: '600',
    fontSize: 15,
  },
  btnPrimary: {
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 12,
  },
  btnPrimaryText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 15,
  },
});
