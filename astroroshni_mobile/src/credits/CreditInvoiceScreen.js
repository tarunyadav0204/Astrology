import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
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
import { exportHtmlAsPdf, PDF_PRINT_STYLES, sharePDFOnWhatsApp, userFacingPdfExportError } from '../utils/pdfGenerator';

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
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
    .replace(/\n/g, '<br>');
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
      const rowHtml = rows.map(([label, value]) => (
        `<div class="row"><div class="label">${escapeHtml(label)}</div><div class="value">${escapeHtml(value)}</div></div>`
      )).join('');
      const html = `<!doctype html>
        <html><head><meta charset="utf-8"><style>
          @page { margin: 18mm 15mm; }
          body { margin: 0; color: #272033; background: #fff; font-family: Arial, "Noto Sans", sans-serif; font-size: 11pt; line-height: 1.58; }
          .header { padding-bottom: 20px; margin-bottom: 24px; border-bottom: 3px solid #8b1d4a; }
          .brand { color: #8b1d4a; font-size: 10pt; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; }
          h1 { margin: 7px 0 5px; color: #241322; font-size: 25pt; }
          .meta { color: #6f6671; font-size: 10pt; }
          .row { padding: 10px 0; border-bottom: 1px solid #eee7e3; }
          .label { color: #6f6671; font-size: 10pt; }
          .value { color: #272033; font-size: 12pt; }
          .footer { margin-top: 28px; padding-top: 12px; border-top: 1px solid #ddd; color: #777; font-size: 8.5pt; }
          ${PDF_PRINT_STYLES}
        </style></head><body>
          <header class="header">
            <div class="brand">${escapeHtml(invoice.seller?.name || 'AstroRoshni')}</div>
            <h1>${escapeHtml(t('credits.page.transactionDetail.invoiceTitle'))}</h1>
            <div class="meta">${escapeHtml(invoice.invoice_number || '')}</div>
          </header>
          ${rowHtml}
          ${money?.tax_amount != null ? `<div class="footer">${escapeHtml(t('credits.page.transactionDetail.gstNote'))}</div>` : ''}
        </body></html>`;
      const pdfUri = await exportHtmlAsPdf(html, { timeoutMs: 45000 });
      await sharePDFOnWhatsApp(pdfUri, {
        dialogTitle: t('credits.page.transactionDetail.shareInvoice'),
        reportType: 'credit_invoice',
        source: 'credit_invoice_screen',
      });
    } catch (error) {
      Alert.alert(
        t('credits.page.transactionDetail.shareInvoice'),
        userFacingPdfExportError(error),
      );
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
