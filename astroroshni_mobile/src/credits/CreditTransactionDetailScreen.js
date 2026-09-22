import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import * as Clipboard from 'expo-clipboard';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../context/ThemeContext';
import { appLocaleForI18n } from '../utils/appLocale';
import { typographyTokens } from '../theme/tokens';
import FocusedStatusBar from '../components/Common/FocusedStatusBar';

const FEATURE_KEYS = {
  chat_question: 'chat_question',
  instant_chat: 'instant_chat',
  instant_chat_minutes: 'instant_chat',
  speech_chat: 'speech_chat',
  speech_chat_minutes: 'speech_chat',
  partnership_analysis: 'partnership_analysis',
  partnership_report: 'partnership_report',
  marriage_analysis: 'marriage_analysis',
  wealth_analysis: 'wealth_analysis',
  wealth_report: 'wealth_report',
  career_analysis: 'career_analysis',
  career_report: 'career_report',
  health_analysis: 'health_analysis',
  health_report: 'health_report',
  education_analysis: 'education_analysis',
  progeny_analysis: 'progeny_analysis',
  progeny_report: 'progeny_report',
  event_timeline: 'event_timeline',
  trading_daily: 'trading_daily',
  trading_calendar: 'trading_calendar',
  prashna_analysis: 'prashna_analysis',
  ashtakavarga_oracle_insight: 'ashtakavarga_oracle_insight',
  ashtakavarga_life_predictions: 'ashtakavarga_life_predictions',
  karma_analysis: 'karma_analysis',
  mundane_analysis: 'mundane_analysis',
  podcast: 'podcast',
  janam_kundli_report: 'janam_kundli_report',
  compatibility_premium_report: 'compatibility_premium_report',
  vehicle_purchase: 'vehicle_purchase',
  griha_pravesh: 'griha_pravesh',
  gold_purchase: 'gold_purchase',
  business_opening: 'business_opening',
  childbirth_planner: 'childbirth_planner',
  childbirth: 'childbirth_planner',
};

const SOURCE_KEYS = {
  first_purchase_bonus: 'first_purchase_bonus',
  pack_bonus: 'pack_bonus',
  purchase_discount: 'purchase_discount',
  web_topup_bonus: 'web_topup_bonus',
  purchase_promo: 'purchase_promo',
  credit_campaign_bonus: 'credit_campaign_bonus',
  promo_code: 'promo_code',
  admin_adjustment: 'admin_adjustment',
};

function transactionKind(item) {
  const source = item?.source || '';
  if (source === 'google_play_refund' || source === 'razorpay_refund' || source === 'refund' || item?.type === 'refund') {
    return 'refund';
  }
  if (source === 'admin_adjustment') return 'adjustment';
  if (source === 'google_play' || source === 'razorpay') return 'purchase';
  if (source === 'feature_usage' || item?.type === 'spent') return 'spend';
  return 'credit';
}

function packCredits(productId) {
  const match = /^credits_(\d+)$/.exec(String(productId || ''));
  return match ? Number(match[1]) : null;
}

function formatWhen(value, locale) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value ? String(value) : '';
  return date.toLocaleString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function formatMoney(amount, currency, locale) {
  const value = Number(amount);
  if (!Number.isFinite(value)) return '';
  try {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency || 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  } catch (_) {
    return `${currency || ''} ${value.toFixed(2)}`.trim();
  }
}

function taxPercentLabel(rate) {
  const percent = Number(rate) * 100;
  if (!Number.isFinite(percent)) return '';
  return Number.isInteger(percent) ? String(percent) : String(Math.round(percent * 10) / 10);
}

export default function CreditTransactionDetailScreen({ navigation, route }) {
  const item = route?.params?.transaction || null;
  const { t, i18n } = useTranslation();
  const { colors, androidLightCardFixStyle } = useTheme();
  const dateLocale = appLocaleForI18n(i18n.language);
  const [copiedKey, setCopiedKey] = useState('');

  const copyValue = async (key, value) => {
    if (!value) return;
    await Clipboard.setStringAsync(String(value));
    setCopiedKey(key);
    setTimeout(() => setCopiedKey((current) => (current === key ? '' : current)), 1600);
  };

  const bgGradient = [colors.background, colors.backgroundSecondary, colors.background];
  const cardStyle = [
    styles.card,
    androidLightCardFixStyle,
    { backgroundColor: colors.cardBackground, borderColor: colors.cardBorder },
  ];

  if (!item) {
    return (
      <View style={styles.container}>
        <FocusedStatusBar backgroundColor={colors.background} barStyle={colors.statusBarStyle || 'dark-content'} />
        <LinearGradient colors={bgGradient} style={styles.backgroundGradient}>
          <SafeAreaView style={styles.safeArea}>
            <View style={styles.header}>
              <TouchableOpacity
                onPress={() => navigation.goBack()}
                style={[styles.backButton, { backgroundColor: colors.surfaceMuted }]}
                accessibilityRole="button"
              >
                <Ionicons name="arrow-back" size={24} color={colors.text} />
              </TouchableOpacity>
              <Text style={[styles.headerTitle, { color: colors.text }]}>{t('credits.page.transactionDetail.title')}</Text>
            </View>
          </SafeAreaView>
        </LinearGradient>
      </View>
    );
  }

  const kind = transactionKind(item);
  const amount = Number(item.amount);
  const signedAmount = amount > 0 ? `+${amount}` : String(amount);
  const amountColor = amount > 0 ? colors.success : colors.primary;
  const featureKey = FEATURE_KEYS[item.reference_id];
  const featureTitle = featureKey
    ? t(`credits.page.transactionDetail.features.${featureKey}`)
    : '';
  const sourceTitle = SOURCE_KEYS[item.source]
    ? t(`credits.page.transactionDetail.sources.${SOURCE_KEYS[item.source]}`)
    : '';
  const creditsFromPack = packCredits(item.product_id);
  const kindTitle = {
    spend: t('credits.page.transactionDetail.creditsUsed'),
    purchase: t('credits.page.transactionDetail.creditsAdded'),
    refund: t('credits.page.transactionDetail.refund'),
    adjustment: t('credits.page.transactionDetail.adjustment'),
    credit: t('credits.page.transactionDetail.creditsAdded'),
  }[kind];
  const whatTitle = kind === 'spend'
    ? (featureTitle || t('credits.page.transactionDetail.feature'))
    : kind === 'purchase'
      ? (creditsFromPack
        ? t('credits.page.creditsCount', { count: creditsFromPack })
        : t('credits.page.transactionDetail.purchase'))
      : kind === 'refund'
        ? t('credits.page.transactionDetail.refund')
        : (sourceTitle || t('credits.page.transactionDetail.creditsAdded'));

  const description = String(item.description || '').trim();
  const rawPurchase = /^(Google Play|Razorpay):\s*credits_\d+$/i.test(description);
  const showDescription = Boolean(
    description
    && description !== item.source
    && description !== whatTitle
    && !rawPurchase,
  );
  const money = item.money || null;
  const paidLabel = money?.amount_paid != null
    ? formatMoney(money.amount_paid, money.currency, dateLocale)
    : (money?.amount_paid_label || '');
  const showPayment = Boolean(item.payment_method || paidLabel);
  const showOrder = (kind === 'purchase' || kind === 'refund') && item.reference_id;
  const whenLabel = formatWhen(item.date, dateLocale);
  const paymentName = item.payment_method === 'google_play'
    ? t('credits.page.transactionDetail.googlePlay')
    : item.payment_method === 'razorpay'
      ? t('credits.page.transactionDetail.razorpay')
      : '';

  const chatLink = item.feature_link?.kind === 'chat' && item.feature_link?.session_id
    ? item.feature_link
    : null;
  const eventLink = item.feature_link?.kind === 'event_timeline' && item.feature_link?.year
    ? item.feature_link
    : null;
  const analysisLink = item.feature_link?.kind === 'analysis'
    && ['career', 'wealth', 'health', 'marriage', 'education', 'progeny'].includes(item.feature_link?.analysis)
    && Number(item.feature_link?.birth_chart_id) > 0
    ? item.feature_link
    : null;
  const podcastLink = item.feature_link?.kind === 'podcast'
    && item.feature_link?.message_id
    && (item.feature_link?.lang === 'en' || item.feature_link?.lang === 'hi')
    ? item.feature_link
    : null;
  const speechLink = item.feature_link?.kind === 'speech' && item.feature_link?.session_id
    ? item.feature_link
    : null;
  const prashnaLink = item.feature_link?.kind === 'prashna' && Number(item.feature_link?.reading_id) > 0
    ? item.feature_link
    : null;
  const karmaLink = item.feature_link?.kind === 'karma' && Number(item.feature_link?.birth_chart_id) > 0
    ? item.feature_link
    : null;
  const ashtakavargaLink = item.feature_link?.kind === 'ashtakavarga'
    && (
      (item.feature_link?.scope === 'oracle' && Number(item.feature_link?.analysis_id) > 0)
      || (item.feature_link?.scope === 'life' && item.feature_link?.date && item.feature_link?.time)
    )
    ? item.feature_link
    : null;

  const openChat = () => {
    if (!chatLink?.session_id) return;
    navigation.navigate('ChatView', {
      session: {
        session_id: String(chatLink.session_id),
        session_ids: [String(chatLink.session_id)],
        messages: [],
        native_name: null,
        created_at: item.date,
      },
    });
  };

  const openAnalysis = () => {
    if (!analysisLink?.analysis) return;
    navigation.navigate('AnalysisDetail', {
      analysisType: analysisLink.analysis,
      title: t(`home.analysis.${analysisLink.analysis}.title`),
      openSaved: true,
      birthChartId: Number(analysisLink.birth_chart_id),
      analysisFocus: analysisLink.analysis_focus,
      childrenCount: analysisLink.children_count,
    });
  };

  const openPodcast = () => {
    if (!podcastLink?.message_id) return;
    navigation.navigate('PodcastHistory', {
      openMessageId: String(podcastLink.message_id),
      openLang: podcastLink.lang,
      openSessionId: podcastLink.session_id || undefined,
      openBirthChartId: Number(podcastLink.birth_chart_id) > 0 ? Number(podcastLink.birth_chart_id) : undefined,
    });
  };

  const openSpeechCall = () => {
    if (!speechLink?.session_id) return;
    navigation.navigate('ChatView', {
      session: {
        session_id: String(speechLink.session_id),
        session_ids: [String(speechLink.session_id)],
        messages: [],
        native_name: null,
        created_at: item.date,
      },
    });
  };

  const openPrashna = () => {
    if (!prashnaLink?.reading_id) return;
    navigation.navigate('Prashna', { readingId: Number(prashnaLink.reading_id) });
  };

  const openKarma = () => {
    if (!karmaLink?.birth_chart_id) return;
    navigation.navigate('KarmaAnalysis', { chartId: Number(karmaLink.birth_chart_id) });
  };

  const openAshtakavarga = () => {
    if (!ashtakavargaLink) return;
    if (ashtakavargaLink.scope === 'oracle') {
      navigation.navigate('AshtakvargaHistoryDetail', { analysisId: Number(ashtakavargaLink.analysis_id) });
      return;
    }
    navigation.navigate('AshtakvargaStudy', {
      exactBirth: true,
      birthData: {
        date: ashtakavargaLink.date,
        time: ashtakavargaLink.time,
        latitude: Number(ashtakavargaLink.latitude),
        longitude: Number(ashtakavargaLink.longitude),
      },
    });
  };

  const openEventReport = () => {
    if (!eventLink?.year) return;
    const birthChartId = Number(eventLink.birth_chart_id) > 0 ? Number(eventLink.birth_chart_id) : undefined;
    if (eventLink.scope === 'monthly' && eventLink.month) {
      navigation.navigate('MonthlyDeepScreen', {
        year: Number(eventLink.year),
        month: Number(eventLink.month),
        birthChartId,
      });
      return;
    }
    navigation.navigate('EventScreen', {
      year: Number(eventLink.year),
      openSaved: true,
      birthChartId,
    });
  };

  const openSupport = () => {
    navigation.navigate('Support', {
      draftSubject: t('credits.page.transactionDetail.supportSubject', { id: item.id }),
      draftBody: t('credits.page.transactionDetail.supportBody', {
        id: item.id,
        description: description || whatTitle,
        amount: signedAmount,
        date: whenLabel,
      }),
    });
  };

  return (
    <View style={styles.container}>
      <FocusedStatusBar backgroundColor={colors.background} barStyle={colors.statusBarStyle || 'dark-content'} />
      <LinearGradient colors={bgGradient} style={styles.backgroundGradient}>
        <SafeAreaView style={styles.safeArea}>
          <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
            <View style={styles.header}>
              <TouchableOpacity
                onPress={() => navigation.goBack()}
                style={[styles.backButton, { backgroundColor: colors.surfaceMuted }]}
                accessibilityRole="button"
                accessibilityLabel={t('credits.page.transactionDetail.title')}
              >
                <Ionicons name="arrow-back" size={24} color={colors.text} />
              </TouchableOpacity>
              <Text style={[styles.headerEyebrow, { color: colors.primary }]}>{kindTitle}</Text>
              <Text style={[styles.amount, { color: amountColor }]}>{signedAmount}</Text>
              <Text style={[styles.headerSubtitle, { color: colors.textSecondary }]}>
                {t('credits.page.creditsLabel')}
              </Text>
            </View>

            <View style={cardStyle}>
              <DetailRow
                label={t('credits.page.transactionDetail.when')}
                value={whenLabel}
                colors={colors}
              />
              <DetailRow
                label={t('credits.page.transactionDetail.balanceAfter')}
                value={item.balance_after != null ? String(item.balance_after) : ''}
                colors={colors}
              />
            </View>

            <Text style={[styles.sectionTitle, { color: colors.text }]}>
              {t('credits.page.transactionDetail.whatThisWas')}
            </Text>
            <View style={cardStyle}>
              <Text style={[styles.whatTitle, { color: colors.text, paddingBottom: showDescription ? 0 : 12 }]}>{whatTitle}</Text>
              {showDescription ? (
                <Text style={[styles.whatBody, { color: colors.textSecondary }]}>{description}</Text>
              ) : null}
            </View>

            {chatLink ? (
              <TouchableOpacity
                style={[styles.helpButton, { backgroundColor: colors.primary, marginBottom: 8 }]}
                onPress={openChat}
                accessibilityRole="button"
              >
                <Ionicons name="chatbubbles-outline" size={18} color={colors.onPrimary} />
                <Text style={[styles.helpButtonText, { color: colors.onPrimary }]}>
                  {t('credits.page.transactionDetail.openChat')}
                </Text>
              </TouchableOpacity>
            ) : null}
            {analysisLink ? (
              <TouchableOpacity
                style={[styles.helpButton, { backgroundColor: colors.primary, marginBottom: 8 }]}
                onPress={openAnalysis}
                accessibilityRole="button"
              >
                <Ionicons name="document-text-outline" size={18} color={colors.onPrimary} />
                <Text style={[styles.helpButtonText, { color: colors.onPrimary }]}>
                  {t('credits.page.transactionDetail.openAnalysis')}
                </Text>
              </TouchableOpacity>
            ) : null}
            {podcastLink ? (
              <TouchableOpacity
                style={[styles.helpButton, { backgroundColor: colors.primary, marginBottom: 8 }]}
                onPress={openPodcast}
                accessibilityRole="button"
              >
                <Ionicons name="headset-outline" size={18} color={colors.onPrimary} />
                <Text style={[styles.helpButtonText, { color: colors.onPrimary }]}>
                  {t('credits.page.transactionDetail.openPodcast')}
                </Text>
              </TouchableOpacity>
            ) : null}
            {speechLink ? (
              <TouchableOpacity
                style={[styles.helpButton, { backgroundColor: colors.primary, marginBottom: 8 }]}
                onPress={openSpeechCall}
                accessibilityRole="button"
              >
                <Ionicons name="mic-outline" size={18} color={colors.onPrimary} />
                <Text style={[styles.helpButtonText, { color: colors.onPrimary }]}>
                  {t('credits.page.transactionDetail.openCall')}
                </Text>
              </TouchableOpacity>
            ) : null}
            {prashnaLink ? (
              <TouchableOpacity
                style={[styles.helpButton, { backgroundColor: colors.primary, marginBottom: 8 }]}
                onPress={openPrashna}
                accessibilityRole="button"
              >
                <Ionicons name="help-circle-outline" size={18} color={colors.onPrimary} />
                <Text style={[styles.helpButtonText, { color: colors.onPrimary }]}>
                  {t('credits.page.transactionDetail.openPrashna')}
                </Text>
              </TouchableOpacity>
            ) : null}
            {ashtakavargaLink ? (
              <TouchableOpacity
                style={[styles.helpButton, { backgroundColor: colors.primary, marginBottom: 8 }]}
                onPress={openAshtakavarga}
                accessibilityRole="button"
              >
                <Ionicons name="grid-outline" size={18} color={colors.onPrimary} />
                <Text style={[styles.helpButtonText, { color: colors.onPrimary }]}>
                  {t('credits.page.transactionDetail.openAshtakavarga')}
                </Text>
              </TouchableOpacity>
            ) : null}
            {karmaLink ? (
              <TouchableOpacity
                style={[styles.helpButton, { backgroundColor: colors.primary, marginBottom: 8 }]}
                onPress={openKarma}
                accessibilityRole="button"
              >
                <Ionicons name="infinite-outline" size={18} color={colors.onPrimary} />
                <Text style={[styles.helpButtonText, { color: colors.onPrimary }]}>
                  {t('credits.page.transactionDetail.openKarma')}
                </Text>
              </TouchableOpacity>
            ) : null}
            {eventLink ? (
              <TouchableOpacity
                style={[styles.helpButton, { backgroundColor: colors.primary, marginBottom: 8 }]}
                onPress={openEventReport}
                accessibilityRole="button"
              >
                <Ionicons name="calendar-outline" size={18} color={colors.onPrimary} />
                <Text style={[styles.helpButtonText, { color: colors.onPrimary }]}>
                  {eventLink.scope === 'monthly'
                    ? t('credits.page.transactionDetail.openMonth')
                    : t('credits.page.transactionDetail.openYear')}
                </Text>
              </TouchableOpacity>
            ) : null}

            {showPayment ? (
              <>
                <Text style={[styles.sectionTitle, { color: colors.text }]}>
                  {t('credits.page.transactionDetail.payment')}
                </Text>
                <View style={cardStyle}>
                  {paymentName ? (
                    <DetailRow
                      label={t('credits.page.transactionDetail.paidWith')}
                      value={paymentName}
                      colors={colors}
                    />
                  ) : null}
                  {paidLabel ? (
                    <DetailRow
                      label={kind === 'refund'
                        ? t('credits.page.transactionDetail.amountRefunded')
                        : t('credits.page.transactionDetail.amountPaid')}
                      value={paidLabel}
                      colors={colors}
                    />
                  ) : null}
                  {money?.tax_amount != null ? (
                    <>
                      <DetailRow
                        label={t('credits.page.transactionDetail.gstIncluded', {
                          percent: taxPercentLabel(money.tax_rate),
                        })}
                        value={formatMoney(money.tax_amount, money.currency, dateLocale)}
                        colors={colors}
                      />
                      <DetailRow
                        label={t('credits.page.transactionDetail.beforeGst')}
                        value={formatMoney(money.pretax_amount, money.currency, dateLocale)}
                        colors={colors}
                      />
                      <Text style={[styles.taxNote, { color: colors.textTertiary }]}>
                        {t('credits.page.transactionDetail.gstNote')}
                      </Text>
                    </>
                  ) : null}
                </View>
              </>
            ) : null}

            <View style={cardStyle}>
              {showOrder ? (
                <CopyRow
                  label={t('credits.page.transactionDetail.orderId')}
                  value={String(item.reference_id)}
                  copied={copiedKey === 'order'}
                  onCopy={() => copyValue('order', item.reference_id)}
                  colors={colors}
                  t={t}
                />
              ) : null}
              <CopyRow
                label={t('credits.page.transactionDetail.transactionId')}
                value={item.id != null ? String(item.id) : ''}
                copied={copiedKey === 'id'}
                onCopy={() => copyValue('id', item.id)}
                colors={colors}
                t={t}
              />
            </View>

            {kind === 'purchase' && item?.id != null ? (
              <TouchableOpacity
                style={[styles.helpButton, { backgroundColor: colors.primary }]}
                onPress={() => navigation.navigate('CreditInvoice', { transactionId: item.id })}
                accessibilityRole="button"
              >
                <Ionicons name="document-text-outline" size={18} color={colors.onPrimary} />
                <Text style={[styles.helpButtonText, { color: colors.onPrimary }]}>
                  {t('credits.page.transactionDetail.viewInvoice')}
                </Text>
              </TouchableOpacity>
            ) : null}

            <TouchableOpacity
              style={[styles.helpButton, { backgroundColor: colors.primary }]}
              onPress={openSupport}
              accessibilityRole="button"
            >
              <Ionicons name="chatbubble-ellipses-outline" size={18} color={colors.onPrimary} />
              <Text style={[styles.helpButtonText, { color: colors.onPrimary }]}>
                {t('credits.page.transactionDetail.needHelp')}
              </Text>
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

function DetailRow({ label, value, colors }) {
  if (!value) return null;
  return (
    <View style={styles.detailRow}>
      <Text style={[styles.rowLabel, { color: colors.textSecondary }]}>{label}</Text>
      <Text style={[styles.rowValue, { color: colors.text }]}>{value}</Text>
    </View>
  );
}

function CopyRow({ label, value, copied, onCopy, colors, t }) {
  if (!value) return null;
  return (
    <View style={styles.row}>
      <View style={styles.copyText}>
        <Text style={[styles.rowLabel, { color: colors.textSecondary }]}>{label}</Text>
        <Text style={[styles.rowValue, { color: colors.text }]} selectable>{value}</Text>
      </View>
      <TouchableOpacity
        onPress={onCopy}
        style={[styles.copyButton, { backgroundColor: colors.surfaceMuted }]}
        accessibilityRole="button"
        accessibilityLabel={t('credits.page.transactionDetail.copy')}
      >
        <Text style={[styles.copyButtonText, { color: colors.primary }]}>
          {copied ? t('credits.page.transactionDetail.copied') : t('credits.page.transactionDetail.copy')}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  backgroundGradient: { flex: 1 },
  safeArea: { flex: 1 },
  scrollContent: { paddingBottom: 40 },
  header: {
    paddingHorizontal: 24,
    paddingTop: 18,
    paddingBottom: 8,
  },
  backButton: {
    width: 46,
    height: 46,
    borderRadius: 23,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  headerEyebrow: {
    ...typographyTokens.eyebrow,
    marginBottom: 8,
  },
  headerTitle: {
    ...typographyTokens.title,
    fontSize: 32,
    lineHeight: 36,
  },
  amount: {
    fontSize: 42,
    lineHeight: 48,
    fontWeight: '700',
  },
  headerSubtitle: {
    ...typographyTokens.bodyMd,
    fontSize: 15,
    marginTop: 2,
    marginBottom: 16,
  },
  sectionTitle: {
    ...typographyTokens.sectionTitle,
    fontSize: 18,
    marginHorizontal: 24,
    marginBottom: 10,
    marginTop: 8,
  },
  card: {
    marginHorizontal: 24,
    marginBottom: 16,
    borderRadius: 22,
    borderWidth: 1,
    paddingHorizontal: 18,
    paddingVertical: 8,
  },
  whatTitle: {
    fontSize: 17,
    fontWeight: '700',
    paddingTop: 12,
  },
  whatBody: {
    fontSize: 15,
    lineHeight: 22,
    paddingTop: 8,
    paddingBottom: 12,
  },
  detailRow: {
    paddingVertical: 12,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    paddingVertical: 12,
  },
  rowLabel: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
  },
  rowValue: {
    fontSize: 16,
    fontWeight: '600',
    flexShrink: 1,
  },
  copyText: { flex: 1, minWidth: 0 },
  copyButton: {
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  copyButtonText: {
    fontSize: 13,
    fontWeight: '700',
  },
  taxNote: {
    fontSize: 13,
    lineHeight: 18,
    paddingBottom: 12,
  },
  helpButton: {
    marginHorizontal: 24,
    marginTop: 8,
    borderRadius: 16,
    minHeight: 52,
    paddingHorizontal: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  helpButtonText: {
    fontSize: 16,
    fontWeight: '700',
  },
});
