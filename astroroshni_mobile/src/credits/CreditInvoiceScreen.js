import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../context/ThemeContext';
import { appLocaleForI18n } from '../utils/appLocale';
import { typographyTokens } from '../theme/tokens';
import FocusedStatusBar from '../components/Common/FocusedStatusBar';
import { creditAPI } from '../services/api';
import { exportHtmlAsPdf, sharePDFOnWhatsApp } from '../utils/pdfGenerator';

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
  const value = Number(rate);
  if (!Number.isFinite(value)) return '';
  return String(Math.round(value * 100));
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function DetailRow({ label, value, colors }) {
  if (!value) return null;
  return (
    <View style={styles.row}>
      <Text style={[styles.rowLabel, { color: colors.textSecondary }]}>{label}</Text>
      <Text style={[styles.rowValue, { color: colors.text }]}>{value}</Text>
    </View>
  );
}

export default function CreditInvoiceScreen({ navigation, route }) {
  const { t, i18n } = useTranslation();
  const { colors } = useTheme();
  const dateLocale = appLocaleForI18n(i18n.language);
  const transactionId = route?.params?.transactionId;
  const [invoice, setInvoice] = useState(null);
  const [status, setStatus] = useState('loading');
  const [sharing, setSharing] = useState(false);

  const load = useCallback(async () => {
    if (transactionId == null) {
      setStatus('missing');
      return;
    }
    setStatus('loading');
    try {
      const response = await creditAPI.getInvoice(transactionId);
      setInvoice(response?.data || null);
      setStatus(response?.data ? 'ready' : 'missing');
    } catch (error) {
      setStatus(error?.response?.status === 404 ? 'missing' : 'error');
    }
  }, [transactionId]);

  useEffect(() => {
    load();
  }, [load]);

  const money = invoice?.money;
  const paidLabel = money?.amount_paid != null
    ? formatMoney(money.amount_paid, money.currency, dateLocale)
    : money?.amount_paid_label || '';
  const paymentName = invoice?.payment_method === 'google_play'
    ? t('credits.page.transactionDetail.googlePlay')
    : invoice?.payment_method === 'razorpay'
      ? t('credits.page.transactionDetail.razorpay')
      : '';
  const buyerLine = [invoice?.buyer?.name, invoice?.buyer?.phone, invoice?.buyer?.email]
    .filter(Boolean)
    .join('\n');
  const sellerLine = [invoice?.seller?.name, invoice?.seller?.address]
    .filter(Boolean)
    .join('\n');

  const shareInvoice = async () => {
    if (!invoice || sharing) return;
    setSharing(true);
    try {
      const rows = [
        [t('credits.page.transactionDetail.invoiceNumber'), invoice.invoice_number],
        [t('credits.page.transactionDetail.issuedOn'), formatWhen(invoice.issued_at, dateLocale)],
        [t('credits.page.transactionDetail.soldBy'), sellerLine],
        [t('credits.page.transactionDetail.gstin'), invoice?.seller?.gstin],
        [t('credits.page.transactionDetail.billedTo'), buyerLine],
        [t('credits.page.transactionDetail.creditsPurchased'), String(invoice.credits || '')],
        [t('credits.page.transactionDetail.paidWith'), paymentName],
        [t('credits.page.transactionDetail.orderId'), invoice.order_id],
        [t('credits.page.transactionDetail.amountPaid'), paidLabel],
        money?.tax_amount != null
          ? [t('credits.page.transactionDetail.gstIncluded', { percent: taxPercentLabel(money.tax_rate) }), formatMoney(money.tax_amount, money.currency, dateLocale)]
          : null,
        money?.pretax_amount != null
          ? [t('credits.page.transactionDetail.beforeGst'), formatMoney(money.pretax_amount, money.currency, dateLocale)]
          : null,
      ].filter((row) => row && row[1]);
      const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
        body { font-family: -apple-system, sans-serif; color: #1a1a1a; padding: 32px; }
        h1 { font-size: 28px; margin: 0 0 8px; }
        .muted { color: #666; margin-bottom: 24px; }
        table { width: 100%; border-collapse: collapse; }
        td { padding: 10px 0; border-bottom: 1px solid #eee; vertical-align: top; }
        td:first-child { color: #666; width: 42%; }
      </style></head><body>
        <h1>${escapeHtml(t('credits.page.transactionDetail.invoiceTitle'))}</h1>
        <div class="muted">${escapeHtml(invoice.seller?.name || 'AstroRoshni')}</div>
        <table>${rows.map(([label, value]) => `<tr><td>${escapeHtml(label)}</td><td>${escapeHtml(value)}</td></tr>`).join('')}</table>
        ${money?.tax_amount != null ? `<p class="muted">${escapeHtml(t('credits.page.transactionDetail.gstNote'))}</p>` : ''}
      </body></html>`;
      const uri = await exportHtmlAsPdf(html);
      await sharePDFOnWhatsApp(uri, { contentType: 'invoice', source: 'credit_invoice' });
    } catch (_) {
      /* The invoice stays on screen if sharing is cancelled or the PDF cannot be created. */
    } finally {
      setSharing(false);
    }
  };

  const cardStyle = {
    backgroundColor: colors.surface,
    borderColor: colors.border,
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FocusedStatusBar
        backgroundColor={colors.background}
        barStyle={colors.statusBarStyle || 'dark-content'}
      />
      <LinearGradient colors={[colors.background, colors.backgroundSecondary, colors.background]} style={styles.flex}>
        <SafeAreaView style={styles.flex}>
          <View style={styles.header}>
            <TouchableOpacity
              onPress={() => navigation.goBack()}
              accessibilityRole="button"
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="chevron-back" size={26} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: colors.text }]}>
              {t('credits.page.transactionDetail.invoiceTitle')}
            </Text>
            <View style={styles.headerSpacer} />
          </View>
          {status === 'loading' ? (
            <ActivityIndicator color={colors.primary} style={styles.loader} />
          ) : status !== 'ready' || !invoice ? (
            <View style={styles.messageWrap}>
              <TouchableOpacity onPress={status === 'error' ? load : undefined} accessibilityRole="button">
                <Text style={[styles.message, { color: colors.textSecondary }]}>
                  {status === 'error'
                    ? t('credits.page.transactionDetail.invoiceLoadError')
                    : t('credits.page.transactionDetail.invoiceUnavailable')}
                </Text>
              </TouchableOpacity>
            </View>
          ) : (
            <ScrollView contentContainerStyle={styles.content}>
              <Text style={[styles.number, { color: colors.text }]}>{invoice.invoice_number}</Text>
              <Text style={[styles.issued, { color: colors.textSecondary }]}>
                {t('credits.page.transactionDetail.issuedOn')} {formatWhen(invoice.issued_at, dateLocale)}
              </Text>
              <View style={[styles.card, cardStyle]}>
                <DetailRow label={t('credits.page.transactionDetail.soldBy')} value={sellerLine} colors={colors} />
                <DetailRow label={t('credits.page.transactionDetail.gstin')} value={invoice.seller?.gstin} colors={colors} />
                <DetailRow label={t('credits.page.transactionDetail.billedTo')} value={buyerLine} colors={colors} />
              </View>
              <View style={[styles.card, cardStyle]}>
                <DetailRow
                  label={t('credits.page.transactionDetail.creditsPurchased')}
                  value={invoice.credits != null ? String(invoice.credits) : ''}
                  colors={colors}
                />
                <DetailRow label={t('credits.page.transactionDetail.paidWith')} value={paymentName} colors={colors} />
                <DetailRow label={t('credits.page.transactionDetail.orderId')} value={invoice.order_id} colors={colors} />
                <DetailRow label={t('credits.page.transactionDetail.amountPaid')} value={paidLabel} colors={colors} />
                {money?.tax_amount != null ? (
                  <>
                    <DetailRow
                      label={t('credits.page.transactionDetail.gstIncluded', { percent: taxPercentLabel(money.tax_rate) })}
                      value={formatMoney(money.tax_amount, money.currency, dateLocale)}
                      colors={colors}
                    />
                    <DetailRow
                      label={t('credits.page.transactionDetail.beforeGst')}
                      value={formatMoney(money.pretax_amount, money.currency, dateLocale)}
                      colors={colors}
                    />
                    <Text style={[styles.note, { color: colors.textSecondary }]}>
                      {t('credits.page.transactionDetail.gstNote')}
                    </Text>
                  </>
                ) : null}
              </View>
              <TouchableOpacity
                style={[styles.shareButton, { backgroundColor: colors.primary }]}
                onPress={shareInvoice}
                disabled={sharing}
                accessibilityRole="button"
              >
                {sharing ? (
                  <ActivityIndicator color={colors.onPrimary} />
                ) : (
                  <>
                    <Ionicons name="share-outline" size={18} color={colors.onPrimary} />
                    <Text style={[styles.shareButtonText, { color: colors.onPrimary }]}>
                      {t('credits.page.transactionDetail.shareInvoice')}
                    </Text>
                  </>
                )}
              </TouchableOpacity>
            </ScrollView>
          )}
        </SafeAreaView>
      </LinearGradient>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  flex: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  headerTitle: {
    flex: 1,
    textAlign: 'center',
    ...typographyTokens.sectionTitle,
    fontSize: 22,
    lineHeight: 28,
  },
  headerSpacer: { width: 26 },
  loader: { marginTop: 48 },
  content: { padding: 20, paddingBottom: 40 },
  number: {
    ...typographyTokens.title,
    fontSize: 32,
    lineHeight: 36,
  },
  issued: {
    marginTop: 4,
    marginBottom: 16,
    ...typographyTokens.bodyMd,
    fontSize: 14,
  },
  card: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
  },
  row: { marginBottom: 12 },
  rowLabel: {
    ...typographyTokens.label,
    marginBottom: 2,
  },
  rowValue: {
    ...typographyTokens.bodyMd,
    fontSize: 16,
  },
  note: {
    ...typographyTokens.bodyMd,
    fontSize: 13,
    lineHeight: 18,
  },
  shareButton: {
    minHeight: 48,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 8,
    marginTop: 4,
  },
  shareButtonText: {
    ...typographyTokens.bodyMd,
    fontWeight: '700',
    fontSize: 16,
  },
  messageWrap: { padding: 24 },
  message: {
    ...typographyTokens.bodyMd,
    fontSize: 16,
    lineHeight: 22,
  },
});
