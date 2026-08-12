import React, { useEffect, useRef, useState } from 'react';
import { Animated, FlatList, Modal, Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../../context/ThemeContext';
import { authAPI } from '../../../services/api';
import { apiErrorMessage } from '../../../utils/apiErrorMessage';
import { COUNTRY_CODES, getNationalPhoneMaxLength, isNationalPhoneValid } from '../countryCodes';
import AuthKeyboardScreen from './AuthKeyboardScreen';
import AppAlertModal from '../../Common/AppAlertModal';

export default function ForgotPasswordScreen({ formData, updateFormData, navigateToScreen }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [appAlert, setAppAlert] = useState(null);
  const [country, setCountry] = useState(() => COUNTRY_CODES.find((item) => item.code === (formData.countryCode || '+91')) || COUNTRY_CODES[2]);
  const entrance = useRef(new Animated.Value(0)).current;
  const digits = String(formData.phone || '').replace(/\D/g, '');
  const fullPhone = `${country.code}${digits}`;
  const phoneValid = isNationalPhoneValid(country.code, digits);
  const indiaSms = country.code === '+91';
  const emailPresent = Boolean(String(formData.email || '').trim());
  const stepValid = step === 1 ? phoneValid && (indiaSms || emailPresent) : step === 2 ? String(formData.resetCode || '').length === 6 : newPassword.length >= 8 && /\d/.test(newPassword);

  useEffect(() => {
    Animated.timing(entrance, { toValue: 1, duration: 380, useNativeDriver: true }).start();
  }, [entrance, step]);

  const sendCode = async () => {
    if (!stepValid) return;
    setLoading(true);
    const buildPayload = (phone) => ({ phone, ...(!indiaSms ? { email: String(formData.email || '').trim() } : {}) });
    try {
      try {
        await authAPI.sendResetCode(buildPayload(fullPhone));
      } catch (error) {
        if (error?.response?.status === 404 && fullPhone !== digits) await authAPI.sendResetCode(buildPayload(digits));
        else throw error;
      }
      setAppAlert({ variant: 'success', title: t('authDeep.codeSentTitle', 'Code sent'), message: indiaSms ? t('authDeep.resetSmsSent', 'Check your phone for the reset code.') : t('authDeep.resetEmailSent', 'Check your email for the reset code.') });
      entrance.setValue(0);
      setStep(2);
    } catch (error) {
      setAppAlert({ variant: 'error', title: t('common.error', 'Error'), message: apiErrorMessage(error, t('authDeep.accountNotFound', 'We could not find that account.')) });
    } finally { setLoading(false); }
  };

  const verifyCode = async () => {
    if (!stepValid) return;
    setLoading(true);
    try {
      const response = await authAPI.verifyResetCode({ phone: fullPhone, code: formData.resetCode });
      setResetToken(response.data.reset_token);
      setNewPassword('');
      entrance.setValue(0);
      setStep(3);
    } catch (error) {
      setAppAlert({ variant: 'error', title: t('common.error', 'Error'), message: apiErrorMessage(error, t('authDeep.resetCodeInvalid', 'That code is invalid or has expired.')) });
    } finally { setLoading(false); }
  };

  const resetPassword = async () => {
    if (!stepValid) return;
    setLoading(true);
    try {
      await authAPI.resetPasswordWithToken({ token: resetToken, new_password: newPassword });
      setAppAlert({ variant: 'success', title: t('authDeep.passwordChangedTitle', 'Password changed'), message: t('authDeep.passwordChangedBody', 'Your new password is ready. You can sign in now.'), primaryText: t('authDeep.returnToSignIn', 'Return to sign in'), onPrimaryPress: () => navigateToScreen('phone', 'back') });
    } catch (error) {
      setAppAlert({ variant: 'error', title: t('common.error', 'Error'), message: apiErrorMessage(error, t('authDeep.resetFailed', 'We could not reset your password.')) });
    } finally { setLoading(false); }
  };

  const meta = step === 1
    ? { title: t('authDeep.resetTitle', 'Recover your account'), subtitle: indiaSms ? t('authDeep.resetPhoneSubtitle', 'We’ll send a secure reset code to your phone') : t('authDeep.resetEmailPhoneSubtitle', 'Confirm your phone and email to receive a secure reset code'), action: t('authDeep.sendCode', 'Send reset code') }
    : step === 2
      ? { title: t('authDeep.resetCodeTitle', 'Enter reset code'), subtitle: t('authDeep.resetCodeSubtitle', { destination: indiaSms ? fullPhone : formData.email, defaultValue: 'Enter the 6-digit code sent to {{destination}}' }), action: t('authDeep.verifyCode', 'Verify code') }
      : { title: t('authDeep.newPasswordTitle', 'Create a new password'), subtitle: t('authDeep.newPasswordSubtitle', 'Use at least 8 characters and include one number'), action: t('authDeep.savePassword', 'Save new password') };

  const back = () => {
    if (step === 1) navigateToScreen('password', 'back');
    else { entrance.setValue(0); setStep(step - 1); }
  };

  return (
    <>
      <AuthKeyboardScreen
        emoji="✦"
        title={meta.title}
        subtitle={meta.subtitle}
        onBack={back}
        action={<TouchableOpacity style={[styles.action, { backgroundColor: stepValid ? colors.accent : colors.surfaceMuted }]} onPress={step === 1 ? sendCode : step === 2 ? verifyCode : resetPassword} disabled={!stepValid || loading}><Text style={[styles.actionText, { color: stepValid ? colors.onAccent : colors.textTertiary }]}>{loading ? t('authDeep.pleaseWait', 'Please wait…') : meta.action}</Text><Ionicons name="arrow-forward" size={19} color={stepValid ? colors.onAccent : colors.textTertiary} /></TouchableOpacity>}
      >
        <Animated.View style={{ opacity: entrance, transform: [{ translateY: entrance.interpolate({ inputRange: [0, 1], outputRange: [20, 0] }) }] }}>
          {step === 1 && <>
            <View style={[styles.inputWrap, { backgroundColor: colors.cosmicRaised, borderColor: phoneValid ? colors.accent : colors.cosmicLine }]}>
              <TouchableOpacity style={[styles.countryButton, { borderRightColor: colors.cosmicLine }]} onPress={() => setShowCountryPicker(true)}><Text style={[styles.countryLabel, { color: colors.textInverse }]}>{country.flag} {country.code}</Text><Ionicons name="chevron-down" size={15} color={colors.textInverseMuted} /></TouchableOpacity>
              <TextInput style={[styles.input, { color: colors.textInverse }]} value={formData.phone} onChangeText={(value) => updateFormData('phone', value.replace(/\D/g, '').slice(0, getNationalPhoneMaxLength(country.code)))} placeholder={t('authDeep.phonePlaceholder', 'Phone number')} placeholderTextColor={colors.textInverseMuted} keyboardType="phone-pad" autoFocus />
              {phoneValid && <Ionicons name="checkmark-circle" size={22} color={colors.accent} />}
            </View>
            {!indiaSms && <View style={[styles.inputWrap, styles.secondInput, { backgroundColor: colors.cosmicRaised, borderColor: emailPresent ? colors.accent : colors.cosmicLine }]}><Ionicons name="mail-outline" size={20} color={colors.textInverseMuted} /><TextInput style={[styles.input, { color: colors.textInverse }]} value={formData.email} onChangeText={(value) => updateFormData('email', value)} placeholder={t('authDeep.emailPlaceholder', 'Email address')} placeholderTextColor={colors.textInverseMuted} keyboardType="email-address" autoCapitalize="none" /></View>}
          </>}
          {step === 2 && <View style={[styles.inputWrap, { backgroundColor: colors.cosmicRaised, borderColor: stepValid ? colors.accent : colors.cosmicLine }]}><Ionicons name="keypad-outline" size={20} color={colors.textInverseMuted} /><TextInput style={[styles.input, styles.codeInput, { color: colors.textInverse }]} value={formData.resetCode} onChangeText={(value) => updateFormData('resetCode', value.replace(/\D/g, '').slice(0, 6))} placeholder="••••••" placeholderTextColor={colors.textInverseMuted} keyboardType="number-pad" autoFocus maxLength={6} /></View>}
          {step === 3 && <View style={[styles.inputWrap, { backgroundColor: colors.cosmicRaised, borderColor: stepValid ? colors.accent : colors.cosmicLine }]}><Ionicons name="lock-closed-outline" size={20} color={colors.textInverseMuted} /><TextInput style={[styles.input, { color: colors.textInverse }]} value={newPassword} onChangeText={setNewPassword} placeholder={t('authDeep.newPasswordPlaceholder', 'New password')} placeholderTextColor={colors.textInverseMuted} secureTextEntry={!showPassword} autoFocus /><TouchableOpacity onPress={() => setShowPassword((value) => !value)}><Ionicons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={20} color={colors.textInverseMuted} /></TouchableOpacity></View>}
          <View style={styles.stepRow}>{[1, 2, 3].map((value) => <View key={value} style={[styles.stepDot, { backgroundColor: value <= step ? colors.accent : colors.cosmicLine }]} />)}</View>
        </Animated.View>
      </AuthKeyboardScreen>

      <Modal visible={showCountryPicker} transparent animationType="slide" onRequestClose={() => setShowCountryPicker(false)}>
        <View style={[styles.overlay, { backgroundColor: colors.overlay }]}>
          <View style={[styles.sheet, { backgroundColor: colors.surfaceInverse, borderColor: colors.cosmicLine }]}>
            <View style={[styles.sheetHeader, { borderBottomColor: colors.cosmicLine }]}><Text style={[styles.sheetTitle, { color: colors.textInverse }]}>{t('authDeep.selectCountry', 'Select country')}</Text><TouchableOpacity onPress={() => setShowCountryPicker(false)}><Ionicons name="close" size={23} color={colors.textInverse} /></TouchableOpacity></View>
            <FlatList data={COUNTRY_CODES} keyExtractor={(item) => item.code} renderItem={({ item }) => <TouchableOpacity style={[styles.countryRow, { borderBottomColor: colors.cosmicLine }]} onPress={() => { setCountry(item); updateFormData('countryCode', item.code); updateFormData('phone', digits.slice(0, getNationalPhoneMaxLength(item.code))); setShowCountryPicker(false); }}><Text style={styles.flag}>{item.flag}</Text><View style={styles.countryCopy}><Text style={[styles.countryName, { color: colors.textInverse }]}>{item.name}</Text><Text style={[styles.countryDial, { color: colors.textInverseMuted }]}>{item.code}</Text></View>{country.code === item.code && <Ionicons name="checkmark-circle" size={22} color={colors.accent} />}</TouchableOpacity>} />
          </View>
        </View>
      </Modal>
      <AppAlertModal
        visible={appAlert != null}
        variant={appAlert?.variant || 'info'}
        title={appAlert?.title || ''}
        message={appAlert?.message || ''}
        primaryText={appAlert?.primaryText || t('common.ok', 'OK')}
        onPrimaryPress={() => {
          const next = appAlert?.onPrimaryPress;
          setAppAlert(null);
          next?.();
        }}
        onRequestClose={() => setAppAlert(null)}
      />
    </>
  );
}

const styles = StyleSheet.create({
  inputWrap: { minHeight: 66, borderRadius: 19, borderWidth: 1, paddingHorizontal: 15, flexDirection: 'row', alignItems: 'center', gap: 10 },
  secondInput: { marginTop: 11 },
  input: { flex: 1, fontSize: 17, paddingVertical: 14, ...(Platform.OS === 'web' ? { outlineStyle: 'none' } : null) },
  codeInput: { textAlign: 'center', letterSpacing: 7, fontSize: 24, fontWeight: '700' },
  countryButton: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingRight: 11, borderRightWidth: 1 },
  countryLabel: { fontSize: 15, fontWeight: '700' },
  action: { minHeight: 58, borderRadius: 999, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  actionText: { fontSize: 16, fontWeight: '800' },
  stepRow: { flexDirection: 'row', justifyContent: 'center', gap: 7, marginTop: 22 },
  stepDot: { width: 26, height: 3, borderRadius: 2 },
  overlay: { flex: 1, justifyContent: 'flex-end' },
  sheet: { maxHeight: '74%', borderTopLeftRadius: 28, borderTopRightRadius: 28, borderWidth: 1, paddingBottom: 18 },
  sheetHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 20, borderBottomWidth: 1 },
  sheetTitle: { fontSize: 23, fontFamily: 'serif', fontWeight: '600' },
  countryRow: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 14, borderBottomWidth: StyleSheet.hairlineWidth },
  flag: { fontSize: 25, marginRight: 13 },
  countryCopy: { flex: 1 },
  countryName: { fontSize: 16, fontWeight: '700' },
  countryDial: { fontSize: 13, marginTop: 2 },
});
