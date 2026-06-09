import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  StatusBar,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { authAPI } from '../../services/api';
import { storage } from '../../services/storage';
import AppAlertModal from '../Common/AppAlertModal';

function formatApiError(e, t) {
  const d = e.response?.data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((x) => x.msg || String(x)).join(' ');
  return e.message || (t ? t('accountSecurity.requestFailed', 'Request failed') : 'Request failed');
}

const GENDER_OPTIONS = [
  { value: 'male', labelKey: 'accountSecurity.genderMale', fb: 'Male' },
  { value: 'female', labelKey: 'accountSecurity.genderFemale', fb: 'Female' },
  { value: 'other', labelKey: 'accountSecurity.genderOther', fb: 'Other' },
  { value: 'prefer_not_to_say', labelKey: 'accountSecurity.genderPreferNot', fb: 'Prefer not to say' },
];

export default function AccountSecurityScreen({ navigation }) {
  const { theme, colors } = useTheme();
  const { t } = useTranslation();

  const [loading, setLoading] = useState(true);
  const [savingPw, setSavingPw] = useState(false);
  const [savingEmail, setSavingEmail] = useState(false);
  const [savingGender, setSavingGender] = useState(false);
  const [errorBanner, setErrorBanner] = useState('');
  const [appAlert, setAppAlert] = useState(null);

  const [isIndia, setIsIndia] = useState(true);
  const [serverEmail, setServerEmail] = useState('');
  const [emailDraft, setEmailDraft] = useState('');
  const [gender, setGender] = useState(null);

  const [curPw, setCurPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');

  const dismissAppAlert = useCallback(() => setAppAlert(null), []);

  const syncUserStorage = useCallback(async (patch) => {
    const prev = (await storage.getUserData()) || {};
    await storage.setUserData({ ...prev, ...patch });
  }, []);

  const load = useCallback(async () => {
    setErrorBanner('');
    setLoading(true);
    try {
      const { data } = await authAPI.getAccountDetails();
      const em = (data.email || '').trim();
      setServerEmail(em);
      setEmailDraft(em);
      setGender(data.gender || null);
      setIsIndia(data.is_india !== false);
    } catch (e) {
      setErrorBanner(formatApiError(e, t));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    const unsub = navigation.addListener('focus', load);
    return unsub;
  }, [navigation, load]);

  const onSavePassword = async () => {
    setErrorBanner('');
    if (!curPw.trim()) {
      setAppAlert({
        variant: 'warning',
        title: t('common.error', 'Error'),
        message: t('accountSecurity.currentPasswordRequired', 'Enter your current password.'),
        primaryText: t('common.ok', 'OK'),
      });
      return;
    }
    if (newPw.length < 8 || !/\d/.test(newPw)) {
      setAppAlert({
        variant: 'warning',
        title: t('common.error', 'Error'),
        message: t(
          'accountSecurity.passwordRules',
          'New password must be at least 8 characters and include one number.'
        ),
        primaryText: t('common.ok', 'OK'),
      });
      return;
    }
    if (newPw !== confirmPw) {
      setAppAlert({
        variant: 'warning',
        title: t('common.error', 'Error'),
        message: t('accountSecurity.passwordMismatch', 'New password and confirmation do not match.'),
        primaryText: t('common.ok', 'OK'),
      });
      return;
    }
    setSavingPw(true);
    try {
      await authAPI.updateOwnPassword({ current_password: curPw, new_password: newPw });
      setCurPw('');
      setNewPw('');
      setConfirmPw('');
      setAppAlert({
        variant: 'success',
        title: t('accountSecurity.passwordUpdatedTitle', 'Password updated'),
        message: t('accountSecurity.passwordUpdated', 'Your password has been updated.'),
        primaryText: t('common.ok', 'OK'),
      });
    } catch (e) {
      setAppAlert({
        variant: 'error',
        title: t('common.error', 'Error'),
        message: formatApiError(e, t),
        primaryText: t('common.ok', 'OK'),
      });
    } finally {
      setSavingPw(false);
    }
  };

  const onSaveEmail = async () => {
    setErrorBanner('');
    const trimmed = emailDraft.trim();

    if (!trimmed && !serverEmail) {
      setAppAlert({
        variant: 'warning',
        title: t('accountSecurity.emailMissingTitle', 'Enter an email'),
        message: t(
          'accountSecurity.emailMissingBody',
          'Type an email address first, then tap Add email.'
        ),
        primaryText: t('common.ok', 'OK'),
      });
      return;
    }

    if (!trimmed && serverEmail && !isIndia) {
      setAppAlert({
        variant: 'warning',
        title: t('accountSecurity.emailIntlClearTitle', 'Email required'),
        message: t(
          'accountSecurity.emailIntlClearBody',
          'International accounts need an email for password reset. Enter your email or restore the previous one.'
        ),
        primaryText: t('common.ok', 'OK'),
      });
      return;
    }

    if (trimmed && trimmed === serverEmail) {
      setAppAlert({
        variant: 'info',
        title: t('accountSecurity.emailUnchangedTitle', 'No changes'),
        message: t('accountSecurity.emailUnchanged', 'No changes to save.'),
        primaryText: t('common.ok', 'OK'),
      });
      return;
    }

    const hadEmail = !!serverEmail;

    setSavingEmail(true);
    try {
      const { data } = await authAPI.updateOwnEmail({ email: trimmed || null });
      const next = (data.email || '').trim();
      setServerEmail(next);
      setEmailDraft(next);
      await syncUserStorage({ email: next || null });

      if (!next && hadEmail) {
        setAppAlert({
          variant: 'success',
          title: t('accountSecurity.emailRemovedTitle', 'Email removed'),
          message: t('accountSecurity.emailRemovedBody', 'Your account no longer has an email on file.'),
          primaryText: t('common.ok', 'OK'),
        });
      } else if (next) {
        setAppAlert({
          variant: 'success',
          title: t('accountSecurity.emailSavedTitle', 'Email saved'),
          message: t('accountSecurity.emailSavedBody', 'Your account email has been updated.'),
          primaryText: t('common.ok', 'OK'),
        });
      }
    } catch (e) {
      setAppAlert({
        variant: 'error',
        title: t('common.error', 'Error'),
        message: formatApiError(e, t),
        primaryText: t('common.ok', 'OK'),
      });
    } finally {
      setSavingEmail(false);
    }
  };

  const onRemoveEmail = () => {
    if (!isIndia) return;
    setAppAlert({
      variant: 'warning',
      title: t('accountSecurity.removeEmailTitle', 'Remove email?'),
      message: t(
        'accountSecurity.removeEmailBody',
        'Your India account does not require email. You can remove it from your profile.'
      ),
      secondaryText: t('common.cancel', 'Cancel'),
      primaryText: t('accountSecurity.removeEmailConfirm', 'Remove'),
      onPrimaryPress: async () => {
        setSavingEmail(true);
        try {
          const { data } = await authAPI.updateOwnEmail({ email: '' });
          const next = (data.email || '').trim();
          setServerEmail(next);
          setEmailDraft(next);
          await syncUserStorage({ email: next || null });
          setAppAlert({
            variant: 'success',
            title: t('accountSecurity.emailRemovedTitle', 'Email removed'),
            message: t('accountSecurity.emailRemovedBody', 'Your account no longer has an email on file.'),
            primaryText: t('common.ok', 'OK'),
          });
        } catch (e) {
          setAppAlert({
            variant: 'error',
            title: t('common.error', 'Error'),
            message: formatApiError(e, t),
            primaryText: t('common.ok', 'OK'),
          });
        } finally {
          setSavingEmail(false);
        }
      },
    });
  };

  const persistGender = async (genderPayload) => {
    setSavingGender(true);
    try {
      const { data } = await authAPI.updateOwnGender({ gender: genderPayload });
      const g = data.gender ?? null;
      setGender(g);
      await syncUserStorage({ gender: g });
    } catch (e) {
      setAppAlert({
        variant: 'error',
        title: t('common.error', 'Error'),
        message: formatApiError(e, t),
        primaryText: t('common.ok', 'OK'),
      });
    } finally {
      setSavingGender(false);
    }
  };

  const onPressGenderChip = (value) => {
    setErrorBanner('');
    const nextVal = gender === value ? '' : value;
    persistGender(nextVal);
  };

  const onClearGender = () => {
    setAppAlert({
      variant: 'warning',
      title: t('accountSecurity.clearGenderTitle', 'Clear gender?'),
      message: t('accountSecurity.clearGenderBody', 'You can set this again anytime.'),
      secondaryText: t('common.cancel', 'Cancel'),
      primaryText: t('accountSecurity.clear', 'Clear'),
      onPrimaryPress: () => {
        persistGender('');
      },
    });
  };

  const onDeleteAccount = () => {
    setAppAlert({
      variant: 'warning',
      title: t('profile.deleteAccountTitle', 'Delete Account'),
      message: t(
        'profile.deleteAccountConfirmBody',
        'This will permanently delete your account and associated data. This action cannot be undone.\n\nAre you sure you want to continue?'
      ),
      secondaryText: t('common.cancel', 'Cancel'),
      primaryText: t('common.delete', 'Delete'),
      onPrimaryPress: async () => {
        try {
          await authAPI.deleteAccount();
          await storage.clearAll();
          const { replaceWithLogin } = require('../../navigation/replaceWithLogin');
          replaceWithLogin(navigation);
        } catch (e) {
          setAppAlert({
            variant: 'error',
            title: t('common.error', 'Error'),
            message: formatApiError(e, t),
            primaryText: t('common.ok', 'OK'),
          });
        }
      },
    });
  };

  const handleAppAlertPrimary = () => {
    const fn = appAlert?.onPrimaryPress;
    dismissAppAlert();
    if (typeof fn === 'function') {
      void Promise.resolve(fn()).catch(() => {});
    }
  };

  const bg = colors.background;
  const cardBg = theme === 'dark' ? colors.backgroundSecondary : colors.surface;
  const borderCol = colors.cardBorder;

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: bg }]}>
      <StatusBar barStyle={theme === 'dark' ? 'light-content' : 'dark-content'} backgroundColor="#ff6b35" />
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>
          {t('accountSecurity.title', 'Account & security')}
        </Text>
        <View style={{ width: 40 }} />
      </View>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          {!!errorBanner && (
            <View style={[styles.banner, { borderColor: colors.error }]}>
              <Text style={{ color: colors.error }}>{errorBanner}</Text>
            </View>
          )}

          <Text style={[styles.sectionHeading, { color: colors.textSecondary }]}>
            {t('accountSecurity.sectionPassword', 'Password')}
          </Text>
          <View style={[styles.card, { backgroundColor: cardBg, borderColor: borderCol }]}>
            <Text style={[styles.label, { color: colors.textSecondary }]}>{t('accountSecurity.currentPassword', 'Current password')}</Text>
            <TextInput
              style={[styles.input, { color: colors.text, borderColor: borderCol, backgroundColor: theme === 'dark' ? colors.backgroundTertiary : '#fafafa' }]}
              secureTextEntry
              value={curPw}
              onChangeText={setCurPw}
              placeholder="••••••••"
              placeholderTextColor={colors.textSecondary}
            />
            <Text style={[styles.label, { color: colors.textSecondary, marginTop: 12 }]}>{t('accountSecurity.newPassword', 'New password')}</Text>
            <TextInput
              style={[styles.input, { color: colors.text, borderColor: borderCol, backgroundColor: theme === 'dark' ? colors.backgroundTertiary : '#fafafa' }]}
              secureTextEntry
              value={newPw}
              onChangeText={setNewPw}
              placeholder={t('accountSecurity.newPasswordHint', 'Min. 8 characters, one number')}
              placeholderTextColor={colors.textSecondary}
            />
            <Text style={[styles.label, { color: colors.textSecondary, marginTop: 12 }]}>{t('accountSecurity.confirmPassword', 'Confirm new password')}</Text>
            <TextInput
              style={[styles.input, { color: colors.text, borderColor: borderCol, backgroundColor: theme === 'dark' ? colors.backgroundTertiary : '#fafafa' }]}
              secureTextEntry
              value={confirmPw}
              onChangeText={setConfirmPw}
              placeholder="••••••••"
              placeholderTextColor={colors.textSecondary}
            />
            <TouchableOpacity
              style={[styles.primaryBtn, { backgroundColor: colors.primary, opacity: savingPw ? 0.7 : 1 }]}
              onPress={onSavePassword}
              disabled={savingPw}
            >
              {savingPw ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.primaryBtnText}>{t('accountSecurity.updatePassword', 'Update password')}</Text>
              )}
            </TouchableOpacity>
          </View>

          <Text style={[styles.sectionHeading, { color: colors.textSecondary }]}>
            {t('accountSecurity.sectionEmail', 'Email')}
          </Text>
          <View style={[styles.card, { backgroundColor: cardBg, borderColor: borderCol }]}>
            {!serverEmail ? (
              <Text style={[styles.help, { color: colors.textSecondary }]}>
                {isIndia
                  ? t(
                      'accountSecurity.emailHelpIndiaEmpty',
                      'No email on file. Optional for India accounts — add one if you want receipts or backup contact.'
                    )
                  : t(
                      'accountSecurity.emailHelpIntlEmpty',
                      'Add an email so you can reset your password and receive account mail outside India.'
                    )}
              </Text>
            ) : (
              <Text style={[styles.help, { color: colors.textSecondary }]}>
                {isIndia
                  ? t('accountSecurity.emailHelpIndiaSet', 'You can change your email or remove it — India accounts work with phone sign-in.')
                  : t(
                      'accountSecurity.emailHelpIntlSet',
                      'You can update your email. It cannot be removed for international accounts — password reset relies on it.'
                    )}
              </Text>
            )}
            <Text style={[styles.label, { color: colors.textSecondary }]}>{t('accountSecurity.emailField', 'Email address')}</Text>
            <TextInput
              style={[styles.input, { color: colors.text, borderColor: borderCol, backgroundColor: theme === 'dark' ? colors.backgroundTertiary : '#fafafa' }]}
              value={emailDraft}
              onChangeText={setEmailDraft}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              placeholder="name@example.com"
              placeholderTextColor={colors.textSecondary}
            />
            <TouchableOpacity
              style={[styles.primaryBtn, { backgroundColor: colors.primary, opacity: savingEmail ? 0.7 : 1, marginTop: 12 }]}
              onPress={onSaveEmail}
              disabled={savingEmail}
            >
              {savingEmail ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.primaryBtnText}>
                  {serverEmail ? t('accountSecurity.saveEmail', 'Save email') : t('accountSecurity.addEmail', 'Add email')}
                </Text>
              )}
            </TouchableOpacity>
            {isIndia && !!serverEmail && (
              <TouchableOpacity style={styles.linkRow} onPress={onRemoveEmail} disabled={savingEmail}>
                <Text style={[styles.linkText, { color: colors.error }]}>{t('accountSecurity.removeEmail', 'Remove email from account')}</Text>
              </TouchableOpacity>
            )}
          </View>

          <Text style={[styles.sectionHeading, { color: colors.textSecondary }]}>
            {t('accountSecurity.sectionGender', 'Gender (account)')}
          </Text>
          <View style={[styles.card, { backgroundColor: cardBg, borderColor: borderCol }]}>
            <Text style={[styles.help, { color: colors.textSecondary }]}>
              {t(
                'accountSecurity.genderHelp',
                'Optional — not asked at sign-in. Separate from birth-chart gender in Edit birth details.'
              )}
            </Text>
            <View style={styles.genderRow}>
              {GENDER_OPTIONS.map((opt) => {
                const active = gender === opt.value;
                return (
                  <TouchableOpacity
                    key={opt.value}
                    style={[
                      styles.chip,
                      {
                        borderColor: active ? colors.primary : borderCol,
                        backgroundColor: active ? 'rgba(249,115,22,0.12)' : 'transparent',
                      },
                    ]}
                    onPress={() => onPressGenderChip(opt.value)}
                    disabled={savingGender}
                  >
                    <Text style={[styles.chipText, { color: colors.text }]}>{t(opt.labelKey, opt.fb)}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
            {!!gender && (
              <TouchableOpacity style={styles.linkRow} onPress={onClearGender} disabled={savingGender}>
                <Text style={[styles.linkText, { color: colors.textSecondary }]}>{t('accountSecurity.clearGenderLink', 'Clear selection')}</Text>
              </TouchableOpacity>
            )}
          </View>

          <Text style={[styles.sectionHeading, { color: colors.textSecondary }]}>
            {t('accountSecurity.sectionDanger', 'Danger zone')}
          </Text>
          <View style={[styles.card, { backgroundColor: cardBg, borderColor: borderCol }]}>
            <TouchableOpacity style={styles.dangerBtn} onPress={onDeleteAccount}>
              <Text style={[styles.dangerBtnText, { color: theme === 'dark' ? '#fff' : colors.error }]}>
                {t('profile.deleteAccountAndData', 'Delete Account & Data')}
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      )}

      <AppAlertModal
        visible={appAlert != null}
        variant={appAlert?.variant ?? 'info'}
        title={appAlert?.title ?? ''}
        message={appAlert?.message}
        primaryText={appAlert?.primaryText ?? t('common.ok', 'OK')}
        secondaryText={appAlert?.secondaryText}
        onPrimaryPress={handleAppAlertPrimary}
        onRequestClose={dismissAppAlert}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 12, paddingVertical: 8 },
  backButton: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { flex: 1, textAlign: 'center', fontSize: 18, fontWeight: '700' },
  content: { padding: 20, paddingBottom: 40 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  banner: { padding: 12, borderRadius: 12, borderWidth: 1, marginBottom: 16 },
  sectionHeading: { fontSize: 13, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.6, marginTop: 8, marginBottom: 8 },
  card: { borderRadius: 16, borderWidth: 1, padding: 16, marginBottom: 8 },
  label: { fontSize: 13, marginBottom: 6 },
  help: { fontSize: 14, lineHeight: 20, marginBottom: 12 },
  input: { borderWidth: 1, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, fontSize: 16 },
  primaryBtn: { marginTop: 16, borderRadius: 12, paddingVertical: 14, alignItems: 'center' },
  primaryBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  linkRow: { marginTop: 12, alignItems: 'center' },
  linkText: { fontSize: 15, fontWeight: '600' },
  genderRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  chip: { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 999, borderWidth: 1 },
  chipText: { fontSize: 14, fontWeight: '600' },
  dangerBtn: { paddingVertical: 14, alignItems: 'center' },
  dangerBtnText: { fontSize: 16, fontWeight: '700' },
});
