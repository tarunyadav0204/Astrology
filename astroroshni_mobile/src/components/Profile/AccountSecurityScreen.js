import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { authAPI, chatAPI } from '../../services/api';
import { storage } from '../../services/storage';
import AppAlertModal from '../Common/AppAlertModal';
import FocusedStatusBar from '../Common/FocusedStatusBar';

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
  const { colors } = useTheme();
  const { t } = useTranslation();

  const [loading, setLoading] = useState(true);
  const [savingPw, setSavingPw] = useState(false);
  const [savingEmail, setSavingEmail] = useState(false);
  const [savingGender, setSavingGender] = useState(false);
  const [deletingChatHistory, setDeletingChatHistory] = useState(false);
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

  const confirmAccountDeletion = () => {
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

  const deleteAllChatHistory = async () => {
    setDeletingChatHistory(true);
    try {
      const { data } = await chatAPI.clearHistory();
      await storage.clearChatHistory();
      const deletedMessages = Number(data?.deleted_messages || 0);
      setAppAlert({
        variant: 'success',
        title: t('accountSecurity.chatHistoryDeletedTitle', 'Chat history deleted'),
        message:
          deletedMessages > 0
            ? t(
                'accountSecurity.chatHistoryDeletedCount',
                {
                  count: deletedMessages,
                  defaultValue:
                    '{{count}} chat messages have been permanently deleted. Your account, charts and credits are unchanged.',
                }
              )
            : t(
                'accountSecurity.chatHistoryAlreadyEmpty',
                'Your chat history is already empty. Your account, charts and credits are unchanged.'
              ),
        primaryText: t('common.ok', 'OK'),
      });
    } catch (e) {
      setAppAlert({
        variant: 'error',
        title: t('accountSecurity.chatHistoryDeleteFailedTitle', 'Could not delete chat history'),
        message: formatApiError(e, t),
        primaryText: t('common.ok', 'OK'),
      });
    } finally {
      setDeletingChatHistory(false);
    }
  };

  const confirmChatHistoryDeletion = () => {
    setAppAlert({
      variant: 'warning',
      title: t('accountSecurity.deleteChatsConfirmTitle', 'Delete all chat history?'),
      message: t(
        'accountSecurity.deleteChatsConfirmBody',
        'Every question and answer in your chat history will be permanently deleted. Your account, birth charts and credits will remain available.'
      ),
      secondaryText: t('common.cancel', 'Cancel'),
      primaryText: t('accountSecurity.deleteAllChats', 'Delete All Chats'),
      onPrimaryPress: deleteAllChatHistory,
    });
  };

  const onDeleteAccount = () => {
    setAppAlert({
      variant: 'info',
      title: t('accountSecurity.deleteChoiceTitle', 'Delete account or only chats?'),
      message: t(
        'accountSecurity.deleteChoiceBody',
        'If you only want to remove your conversations, you do not need to delete your account. Choose Delete All Chat History to keep your account, birth charts, subscriptions and credits.\n\nContinue Account Deletion only if you want to permanently remove your entire account and associated data.'
      ),
      secondaryText: t('accountSecurity.continueAccountDeletion', 'Continue Account Deletion'),
      primaryText: t('accountSecurity.deleteAllChatHistory', 'Delete All Chat History'),
      stackButtons: true,
      showCloseButton: true,
      onSecondaryPress: confirmAccountDeletion,
      onPrimaryPress: confirmChatHistoryDeletion,
    });
  };

  const handleAppAlertPrimary = () => {
    const fn = appAlert?.onPrimaryPress;
    dismissAppAlert();
    if (typeof fn === 'function') {
      void Promise.resolve(fn()).catch(() => {});
    }
  };

  const handleAppAlertSecondary = () => {
    const fn = appAlert?.onSecondaryPress;
    dismissAppAlert();
    if (typeof fn === 'function') {
      void Promise.resolve(fn()).catch(() => {});
    }
  };

  const bg = colors.background;
  const cardBg = colors.surfaceRaised;
  const borderCol = colors.cardBorder;
  const inputBg = colors.surfaceMuted;

  const SectionHeader = ({ icon, title, detail }) => (
    <View style={styles.sectionHeader}>
      <View style={[styles.sectionIcon, { backgroundColor: colors.accentSoft }]}>
        <Ionicons name={icon} size={18} color={colors.onAccent} />
      </View>
      <View style={styles.sectionHeaderCopy}>
        <Text style={[styles.sectionHeading, { color: colors.text }]}>{title}</Text>
        {!!detail && <Text style={[styles.sectionDetail, { color: colors.textSecondary }]}>{detail}</Text>}
      </View>
    </View>
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.headerSurface }]} edges={['top']}>
      <FocusedStatusBar backgroundColor={colors.headerSurface} barStyle="light-content" />
      <View style={[styles.header, { backgroundColor: colors.headerSurface, borderBottomColor: colors.cosmicLine }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={23} color={colors.textInverse} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: colors.textInverse }]} numberOfLines={1}>
          {t('accountSecurity.title', 'Account & security')}
        </Text>
        <View style={{ width: 40 }} />
      </View>

      <View style={[styles.contentShell, { backgroundColor: bg }]}>
        {loading ? (
          <View style={styles.centered}>
            <ActivityIndicator size="large" color={colors.accent} />
          </View>
        ) : (
          <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <View style={[styles.hero, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine }]}>
            <View style={[styles.heroRing, styles.heroRingLarge, { borderColor: colors.cosmicLine }]} />
            <View style={[styles.heroRing, styles.heroRingSmall, { borderColor: colors.cosmicLine }]} />
            <View style={[styles.heroIcon, { backgroundColor: colors.accentSoft }]}>
              <Ionicons name="shield-checkmark-outline" size={27} color={colors.onAccent} />
            </View>
            <Text style={[styles.heroEyebrow, { color: colors.accent }]}>{t('accountSecurity.title', 'Account & security')}</Text>
            <Text style={[styles.heroTitle, { color: colors.textInverse }]}>{t('accountSecurity.sectionPassword', 'Password')} · {t('accountSecurity.sectionEmail', 'Email')}</Text>
            <View style={styles.heroPills}>
              <View style={[styles.heroPill, { borderColor: colors.cosmicLine }]}><Ionicons name="lock-closed-outline" size={14} color={colors.accent} /><Text style={[styles.heroPillText, { color: colors.textInverseMuted }]}>{t('accountSecurity.sectionPassword', 'Password')}</Text></View>
              <View style={[styles.heroPill, { borderColor: colors.cosmicLine }]}><Ionicons name="person-outline" size={14} color={colors.accent} /><Text style={[styles.heroPillText, { color: colors.textInverseMuted }]}>{t('accountSecurity.sectionGender', 'Gender (account)')}</Text></View>
            </View>
          </View>

          {!!errorBanner && (
            <View style={[styles.banner, { borderColor: colors.error, backgroundColor: colors.surfaceRaised }]}>
              <Ionicons name="alert-circle-outline" size={20} color={colors.error} />
              <Text style={[styles.bannerText, { color: colors.error }]}>{errorBanner}</Text>
            </View>
          )}

          <View style={[styles.card, { backgroundColor: cardBg, borderColor: borderCol }]}>
            <SectionHeader icon="key-outline" title={t('accountSecurity.sectionPassword', 'Password')} detail={t('accountSecurity.newPasswordHint', 'Min. 8 characters, one number')} />
            <Text style={[styles.label, { color: colors.textSecondary }]}>{t('accountSecurity.currentPassword', 'Current password')}</Text>
            <TextInput
              style={[styles.input, { color: colors.text, borderColor: borderCol, backgroundColor: inputBg }]}
              secureTextEntry
              value={curPw}
              onChangeText={setCurPw}
              placeholder="••••••••"
              placeholderTextColor={colors.textSecondary}
            />
            <Text style={[styles.label, { color: colors.textSecondary, marginTop: 12 }]}>{t('accountSecurity.newPassword', 'New password')}</Text>
            <TextInput
              style={[styles.input, { color: colors.text, borderColor: borderCol, backgroundColor: inputBg }]}
              secureTextEntry
              value={newPw}
              onChangeText={setNewPw}
              placeholder={t('accountSecurity.newPasswordHint', 'Min. 8 characters, one number')}
              placeholderTextColor={colors.textSecondary}
            />
            <Text style={[styles.label, { color: colors.textSecondary, marginTop: 12 }]}>{t('accountSecurity.confirmPassword', 'Confirm new password')}</Text>
            <TextInput
              style={[styles.input, { color: colors.text, borderColor: borderCol, backgroundColor: inputBg }]}
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
                <ActivityIndicator color={colors.onPrimary} />
              ) : (
                <Text style={[styles.primaryBtnText, { color: colors.onPrimary }]}>{t('accountSecurity.updatePassword', 'Update password')}</Text>
              )}
            </TouchableOpacity>
          </View>

          <View style={[styles.card, { backgroundColor: cardBg, borderColor: borderCol }]}>
            <SectionHeader icon="mail-outline" title={t('accountSecurity.sectionEmail', 'Email')} />
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
              style={[styles.input, { color: colors.text, borderColor: borderCol, backgroundColor: inputBg }]}
              value={emailDraft}
              onChangeText={setEmailDraft}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              placeholder={t('accountSecurity.emailField', 'Email address')}
              placeholderTextColor={colors.textSecondary}
            />
            <TouchableOpacity
              style={[styles.primaryBtn, { backgroundColor: colors.primary, opacity: savingEmail ? 0.7 : 1, marginTop: 12 }]}
              onPress={onSaveEmail}
              disabled={savingEmail}
            >
              {savingEmail ? (
                <ActivityIndicator color={colors.onPrimary} />
              ) : (
                <Text style={[styles.primaryBtnText, { color: colors.onPrimary }]}>
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

          <View style={[styles.card, { backgroundColor: cardBg, borderColor: borderCol }]}>
            <SectionHeader icon="person-outline" title={t('accountSecurity.sectionGender', 'Gender (account)')} />
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
                        borderColor: active ? colors.selectionBorder : borderCol,
                        backgroundColor: active ? colors.selectionSurface : colors.surfaceMuted,
                      },
                    ]}
                    onPress={() => onPressGenderChip(opt.value)}
                    disabled={savingGender}
                  >
                    <Text style={[styles.chipText, { color: active ? colors.selectionText : colors.text }]}>{t(opt.labelKey, opt.fb)}</Text>
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

          <View style={[styles.dangerCard, { backgroundColor: cardBg, borderColor: colors.error }]}>
            <SectionHeader icon="trash-outline" title={t('accountSecurity.sectionDanger', 'Danger zone')} detail={t('accountSecurity.deleteAllChatHistory', 'Delete All Chat History')} />
            <TouchableOpacity
              style={[styles.dangerBtn, { borderColor: colors.error, opacity: deletingChatHistory ? 0.6 : 1 }]}
              onPress={onDeleteAccount}
              disabled={deletingChatHistory}
            >
              {deletingChatHistory ? (
                <ActivityIndicator color={colors.error} />
              ) : (
              <Text style={[styles.dangerBtnText, { color: colors.error }]}>
                {t('profile.deleteAccountAndData', 'Delete Account & Data')}
              </Text>
              )}
            </TouchableOpacity>
          </View>
          </ScrollView>
        )}
      </View>

      <AppAlertModal
        visible={appAlert != null}
        variant={appAlert?.variant ?? 'info'}
        title={appAlert?.title ?? ''}
        message={appAlert?.message}
        primaryText={appAlert?.primaryText ?? t('common.ok', 'OK')}
        secondaryText={appAlert?.secondaryText}
        stackButtons={appAlert?.stackButtons === true}
        showCloseButton={appAlert?.showCloseButton === true}
        onPrimaryPress={handleAppAlertPrimary}
        onSecondaryPress={handleAppAlertSecondary}
        onRequestClose={dismissAppAlert}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  contentShell: { flex: 1, borderTopLeftRadius: 24, borderTopRightRadius: 24, overflow: 'hidden' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 14, paddingVertical: 12, borderBottomWidth: StyleSheet.hairlineWidth },
  backButton: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { flex: 1, textAlign: 'center', fontSize: 20, fontFamily: 'serif', fontWeight: '600' },
  content: { padding: 18, paddingBottom: 48 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  hero: { minHeight: 218, borderRadius: 28, borderWidth: 1, padding: 24, marginBottom: 18, overflow: 'hidden', justifyContent: 'flex-end' },
  heroRing: { position: 'absolute', borderWidth: 1, borderRadius: 999 },
  heroRingLarge: { width: 220, height: 220, right: -72, top: -96 },
  heroRingSmall: { width: 152, height: 152, right: -31, top: -66 },
  heroIcon: { width: 50, height: 50, borderRadius: 25, alignItems: 'center', justifyContent: 'center', marginBottom: 18 },
  heroEyebrow: { fontSize: 12, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 2.2, marginBottom: 7 },
  heroTitle: { fontSize: 30, lineHeight: 35, fontFamily: 'serif', fontWeight: '600', marginBottom: 16 },
  heroPills: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  heroPill: { flexDirection: 'row', alignItems: 'center', gap: 7, borderWidth: 1, borderRadius: 999, paddingHorizontal: 11, paddingVertical: 7 },
  heroPillText: { fontSize: 12, fontWeight: '700' },
  banner: { flexDirection: 'row', alignItems: 'center', gap: 9, padding: 13, borderRadius: 14, borderWidth: 1, marginBottom: 16 },
  bannerText: { flex: 1, fontSize: 13, lineHeight: 18 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 18 },
  sectionIcon: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center' },
  sectionHeaderCopy: { flex: 1, marginLeft: 12 },
  sectionHeading: { fontSize: 20, fontFamily: 'serif', fontWeight: '600' },
  sectionDetail: { fontSize: 12, marginTop: 2 },
  card: { borderRadius: 22, borderWidth: 1, padding: 18, marginBottom: 14 },
  dangerCard: { borderRadius: 22, borderWidth: 1, padding: 18, marginTop: 2 },
  label: { fontSize: 13, marginBottom: 6 },
  help: { fontSize: 14, lineHeight: 20, marginBottom: 12 },
  input: { borderWidth: 1, borderRadius: 14, paddingHorizontal: 14, paddingVertical: 13, fontSize: 16 },
  primaryBtn: { marginTop: 16, borderRadius: 999, paddingVertical: 14, alignItems: 'center' },
  primaryBtnText: { fontSize: 15, fontWeight: '800' },
  linkRow: { marginTop: 12, alignItems: 'center' },
  linkText: { fontSize: 15, fontWeight: '600' },
  genderRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  chip: { paddingVertical: 10, paddingHorizontal: 14, borderRadius: 999, borderWidth: 1 },
  chipText: { fontSize: 14, fontWeight: '600' },
  dangerBtn: { paddingVertical: 13, alignItems: 'center', borderWidth: 1, borderRadius: 999 },
  dangerBtnText: { fontSize: 16, fontWeight: '700' },
});
