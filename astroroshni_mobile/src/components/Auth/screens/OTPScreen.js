import React, { useEffect, useRef, useState } from 'react';
import { Animated, Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../../../context/ThemeContext';
import { authAPI } from '../../../services/api';
import { trackAcquisitionFunnelEvent } from '../../../services/acquisitionTracking';
import { registrationEmailRequiredForCountry } from '../countryCodes';
import AuthKeyboardScreen from './AuthKeyboardScreen';
import AppAlertModal from '../../Common/AppAlertModal';

export default function OTPScreen({ formData, updateFormData, navigateToScreen, isLogin }) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [resendTimer, setResendTimer] = useState(30);
  const [devOtpCode, setDevOtpCode] = useState(formData.devOtpCode || null);
  const [appAlert, setAppAlert] = useState(null);
  const inputAnim = useRef(new Animated.Value(0)).current;
  const lastAutoVerifyCodeRef = useRef('');
  const code = String(formData.otpCode || '');
  const isValid = code.length === 6;
  const otpSentToEmail = formData?.otpDelivery?.registration_otp_channel === 'email';
  const destination = otpSentToEmail && formData.email ? formData.email : `${formData.countryCode} ${formData.phone}`;
  const emailRequired = registrationEmailRequiredForCountry(formData.countryCode || '+91');

  useEffect(() => {
    trackAcquisitionFunnelEvent('registration_otp_screen_viewed', { mode: isLogin ? 'login' : 'register' }, { screenName: 'OTPScreen' }).catch(() => {});
    Animated.timing(inputAnim, { toValue: 1, duration: 420, useNativeDriver: true }).start();
    const timer = setInterval(() => setResendTimer((value) => Math.max(0, value - 1)), 1000);
    return () => clearInterval(timer);
  }, [inputAnim, isLogin]);

  const verify = async (override) => {
    const submitted = String(override ?? code).replace(/\D/g, '').slice(0, 6);
    if (submitted.length !== 6 || loading) return;
    setLoading(true);
    try {
      trackAcquisitionFunnelEvent('registration_otp_verify_submitted', { source: 'otp_screen' }, { status: 'started', screenName: 'OTPScreen' }).catch(() => {});
      const response = await authAPI.verifyResetCode({ phone: `${formData.countryCode || ''}${formData.phone}`, code: submitted });
      updateFormData('otpToken', response?.data?.reset_token || '');
      trackAcquisitionFunnelEvent('registration_otp_verified', { source: 'otp_screen' }, { status: 'success', screenName: 'OTPScreen' }).catch(() => {});
      navigateToScreen('name');
    } catch (error) {
      lastAutoVerifyCodeRef.current = '';
      trackAcquisitionFunnelEvent('registration_otp_verify_failed', { source: 'otp_screen' }, { status: 'failed', screenName: 'OTPScreen' }).catch(() => {});
      setAppAlert({ variant: 'error', title: t('common.error', 'Error'), message: t('authDeep.otpInvalid', 'That code is not valid. Check it and try again.') });
    } finally {
      setLoading(false);
    }
  };

  const changeCode = (value) => {
    const digits = value.replace(/\D/g, '').slice(0, 6);
    updateFormData('otpCode', digits);
    if (digits.length === 6 && !loading && lastAutoVerifyCodeRef.current !== digits) {
      lastAutoVerifyCodeRef.current = digits;
      setTimeout(() => verify(digits), 80);
    }
  };

  const resend = async () => {
    if (resendTimer > 0 || resending) return;
    setResending(true);
    try {
      const payload = { phone: `${formData.countryCode || ''}${formData.phone}` };
      if ((formData.email || '').trim()) payload.email = formData.email.trim();
      const response = await authAPI.sendRegistrationOtp(payload);
      updateFormData('otpDelivery', response?.data?.delivery || formData.otpDelivery || null);
      if (response?.data?.dev_code) setDevOtpCode(response.data.dev_code);
      setResendTimer(30);
      setAppAlert({ variant: 'success', title: t('authDeep.codeSentTitle', 'Code sent'), message: t('authDeep.codeSentBody', 'A new verification code is on its way.') });
    } catch (error) {
      setAppAlert({ variant: 'error', title: t('common.error', 'Error'), message: t('authDeep.resendFailed', 'We could not resend the code. Please try again.') });
    } finally {
      setResending(false);
    }
  };

  return (
    <>
    <AuthKeyboardScreen
      emoji="✦"
      title={t('authDeep.otpTitle', 'Enter verification code')}
      subtitle={t('authDeep.otpSubtitle', { destination, defaultValue: 'We sent a 6-digit code to {{destination}}' })}
      onBack={() => navigateToScreen(emailRequired ? 'email' : 'phone', 'back')}
      headerExtra={devOtpCode ? <View style={[styles.devCode, { backgroundColor: colors.cosmicRaised, borderColor: colors.cosmicLine }]}><Text style={[styles.devLabel, { color: colors.accent }]}>{t('authDeep.developmentCode', 'DEVELOPMENT CODE')}</Text><Text style={[styles.devValue, { color: colors.textInverse }]}>{devOtpCode}</Text></View> : null}
      action={
        <TouchableOpacity style={[styles.action, { backgroundColor: isValid ? colors.accent : colors.surfaceMuted }]} onPress={() => verify()} disabled={!isValid || loading}>
          <Text style={[styles.actionText, { color: isValid ? colors.onAccent : colors.textTertiary }]}>{loading ? t('authDeep.verifying', 'Verifying…') : t('authDeep.verifyCode', 'Verify code')}</Text>
          <Ionicons name="arrow-forward" size={19} color={isValid ? colors.onAccent : colors.textTertiary} />
        </TouchableOpacity>
      }
    >
      <Animated.View style={{ opacity: inputAnim, transform: [{ translateY: inputAnim.interpolate({ inputRange: [0, 1], outputRange: [22, 0] }) }] }}>
        <View style={[styles.inputWrap, { backgroundColor: colors.cosmicRaised, borderColor: isValid ? colors.accent : colors.cosmicLine }]}>
          <TextInput style={[styles.input, { color: colors.textInverse }]} placeholder="••••••" placeholderTextColor={colors.textInverseMuted} value={code} onChangeText={changeCode} keyboardType="number-pad" inputMode="numeric" textContentType="oneTimeCode" autoComplete="sms-otp" autoFocus maxLength={6} />
          {isValid && <Ionicons name="checkmark-circle" size={23} color={colors.accent} />}
        </View>
        <View style={styles.resendRow}>
          <Text style={[styles.helper, { color: colors.textInverseMuted }]}>{t('authDeep.didNotReceive', 'Didn’t receive it?')}</Text>
          <TouchableOpacity onPress={resend} disabled={resendTimer > 0 || resending}>
            <Text style={[styles.resend, { color: resendTimer > 0 ? colors.textInverseMuted : colors.accent }]}>{resending ? t('authDeep.sending', 'Sending…') : resendTimer > 0 ? t('authDeep.resendIn', { seconds: resendTimer, defaultValue: 'Resend in {{seconds}}s' }) : t('authDeep.resend', 'Resend code')}</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
    </AuthKeyboardScreen>
    <AppAlertModal
      visible={appAlert != null}
      variant={appAlert?.variant || 'info'}
      title={appAlert?.title || ''}
      message={appAlert?.message || ''}
      primaryText={t('common.ok', 'OK')}
      onPrimaryPress={() => setAppAlert(null)}
      onRequestClose={() => setAppAlert(null)}
    />
    </>
  );
}

const styles = StyleSheet.create({
  inputWrap: { minHeight: 70, borderWidth: 1, borderRadius: 20, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center' },
  input: { flex: 1, fontSize: 28, letterSpacing: 8, fontWeight: '700', textAlign: 'center', paddingVertical: 15, ...(Platform.OS === 'web' ? { outlineStyle: 'none' } : null) },
  resendRow: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 7, marginTop: 18 },
  helper: { fontSize: 13 },
  resend: { fontSize: 13, fontWeight: '800' },
  action: { minHeight: 58, borderRadius: 999, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  actionText: { fontSize: 16, fontWeight: '800' },
  devCode: { marginTop: 16, borderRadius: 14, borderWidth: 1, paddingHorizontal: 18, paddingVertical: 10, alignItems: 'center' },
  devLabel: { fontSize: 10, letterSpacing: 1.5, fontWeight: '800' },
  devValue: { fontSize: 20, letterSpacing: 5, fontWeight: '800', marginTop: 3 },
});
