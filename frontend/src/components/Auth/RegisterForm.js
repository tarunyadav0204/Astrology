import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { authService } from '../../services/authService';
import PhoneWithCountrySelect from './PhoneWithCountrySelect';
import { buildFullPhone, isNationalPhoneValid } from '../../utils/countryCodes';
import './RegisterForm.css';

const RegisterForm = ({ onRegister, onSwitchToLogin }) => {
  const [countryCode, setCountryCode] = useState('+91');
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    otpCode: '',
    password: '',
    confirmPassword: ''
  });
  const [loading, setLoading] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [verifyingOtp, setVerifyingOtp] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpVerified, setOtpVerified] = useState(false);
  const [verifiedPhone, setVerifiedPhone] = useState('');
  const [otpToken, setOtpToken] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (name === 'email') {
      setOtpSent(false);
      setOtpVerified(false);
      setVerifiedPhone('');
      setOtpToken('');
    }
  };

  const clearOtpState = () => {
    setOtpSent(false);
    setOtpVerified(false);
    setVerifiedPhone('');
    setOtpToken('');
  };

  const handleCountryCodeChange = (code) => {
    setCountryCode(code);
    clearOtpState();
  };

  const handleNationalPhoneChange = (digits) => {
    setFormData((prev) => ({ ...prev, phone: digits }));
    clearOtpState();
  };

  const isValidEmail = (value) => {
    const v = (value || '').trim();
    if (!v) return false;
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
  };

  const handleSendOtp = async () => {
    const national = formData.phone.trim();
    const fullPhone = buildFullPhone(countryCode, national);
    const email = formData.email.trim();
    if (!fullPhone || !isNationalPhoneValid(countryCode, national)) {
      toast.error('Please enter a valid phone number for the selected country');
      return;
    }
    if (!email) {
      toast.error('Please enter your email address');
      return;
    }
    if (!isValidEmail(email)) {
      toast.error('Please enter a valid email address');
      return;
    }

    setSendingOtp(true);
    try {
      const payload = { phone: fullPhone, email };
      const response = await authService.sendRegistrationOtp(payload);
      setOtpSent(true);
      setOtpVerified(false);
      setVerifiedPhone('');
      setOtpToken('');
      toast.success(response.message || 'OTP sent');
      if (response.dev_code) {
        toast.info(`Code: ${response.dev_code}`, { autoClose: 10000 });
      }
    } catch (error) {
      toast.error(error.message || 'Failed to send OTP');
    } finally {
      setSendingOtp(false);
    }
  };

  const handleVerifyOtp = async () => {
    const national = formData.phone.trim();
    const fullPhone = buildFullPhone(countryCode, national);
    const otpCode = formData.otpCode.trim();
    if (!fullPhone || !otpCode) {
      toast.error('Please enter phone and OTP code');
      return;
    }
    setVerifyingOtp(true);
    try {
      const response = await authService.verifyResetCode({ phone: fullPhone, code: otpCode });
      setOtpVerified(true);
      setVerifiedPhone(fullPhone);
      setOtpToken(response?.reset_token || '');
      toast.success('OTP verified successfully');
    } catch (error) {
      setOtpVerified(false);
      setOtpToken('');
      toast.error(error.message || 'Invalid or expired OTP');
    } finally {
      setVerifyingOtp(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    const registerFullPhone = buildFullPhone(countryCode, formData.phone.trim());
    if (!otpVerified || verifiedPhone !== registerFullPhone) {
      toast.error('Please verify OTP before creating your account');
      return;
    }
    if (!otpToken) {
      toast.error('Verified OTP token missing. Please verify OTP again.');
      return;
    }
    const emailTrim = formData.email.trim();
    if (!emailTrim) {
      toast.error('Email is required');
      return;
    }
    if (!isValidEmail(emailTrim)) {
      toast.error('Please enter a valid email address');
      return;
    }

    setLoading(true);

    try {
      const response = await authService.register({
        name: formData.name,
        phone: registerFullPhone,
        email: emailTrim,
        otp_token: otpToken,
        password: formData.password,
        signup_client: 'web',
      });
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      toast.success('Registration successful!');
      onRegister(response.user);
    } catch (error) {
      toast.error(error.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      boxSizing: 'border-box',
      width: '100%',
      maxWidth: 'min(400px, 100%)',
      margin: '0 auto',
      padding: 'clamp(1rem, 4vw, 2rem)',
      background: 'rgba(255, 255, 255, 0.95)',
      borderRadius: '20px',
      boxShadow: '0 10px 40px rgba(0, 0, 0, 0.1)',
      backdropFilter: 'blur(20px)',
      border: '2px solid rgba(255, 255, 255, 0.3)'
    }}>
      <h2 style={{
        textAlign: 'center',
        color: '#e91e63',
        marginBottom: '2rem',
        fontWeight: '700'
      }}>
        🌟 Join AstroRoshni
      </h2>

      <form onSubmit={handleSubmit} autoComplete="off">
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            marginBottom: '0.5rem',
            color: '#e91e63',
            fontWeight: '600'
          }}>
            Full Name
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            placeholder="Enter your full name"
            required
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '2px solid rgba(233, 30, 99, 0.2)',
              borderRadius: '12px',
              fontSize: '1rem',
              background: 'rgba(255, 255, 255, 0.8)'
            }}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            marginBottom: '0.5rem',
            color: '#e91e63',
            fontWeight: '600'
          }}>
            Phone Number
          </label>
          <PhoneWithCountrySelect
            countryCode={countryCode}
            onCountryCodeChange={handleCountryCodeChange}
            nationalDigits={formData.phone}
            onNationalDigitsChange={handleNationalPhoneChange}
            disabled={loading || sendingOtp || verifyingOtp}
            inputName="phone"
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            marginBottom: '0.5rem',
            color: '#e91e63',
            fontWeight: '600'
          }}>
            Password
          </label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            placeholder="Enter password (min 6 characters)"
            required
            minLength="6"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '2px solid rgba(233, 30, 99, 0.2)',
              borderRadius: '12px',
              fontSize: '1rem',
              background: 'rgba(255, 255, 255, 0.8)'
            }}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            marginBottom: '0.5rem',
            color: '#e91e63',
            fontWeight: '600'
          }}>
            Confirm Password
          </label>
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleInputChange}
            placeholder="Confirm your password"
            required
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '2px solid rgba(233, 30, 99, 0.2)',
              borderRadius: '12px',
              fontSize: '1rem',
              background: 'rgba(255, 255, 255, 0.8)'
            }}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            marginBottom: '0.5rem',
            color: '#e91e63',
            fontWeight: '600'
          }}>
            Email (required)
          </label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            placeholder="Enter your email"
            required
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '2px solid rgba(233, 30, 99, 0.2)',
              borderRadius: '12px',
              fontSize: '1rem',
              background: 'rgba(255, 255, 255, 0.8)'
            }}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={{
            display: 'block',
            marginBottom: '0.5rem',
            color: '#e91e63',
            fontWeight: '600'
          }}>
            OTP Verification
          </label>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', width: '100%', minWidth: 0 }}>
            <button
              type="button"
              onClick={handleSendOtp}
              disabled={sendingOtp || loading}
              style={{
                flex: 1,
                minWidth: 0,
                padding: '0.65rem',
                background: 'linear-gradient(135deg, #e91e63 0%, #ff6f00 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                fontWeight: '700',
                cursor: sendingOtp || loading ? 'not-allowed' : 'pointer',
                opacity: sendingOtp || loading ? 0.6 : 1
              }}
            >
              {sendingOtp ? 'Sending OTP...' : (otpSent ? 'Resend OTP' : 'Send OTP')}
            </button>
          </div>
          <div className="register-otp-row">
            <input
              type="text"
              name="otpCode"
              value={formData.otpCode}
              onChange={(e) => setFormData(prev => ({ ...prev, otpCode: e.target.value.replace(/[^0-9]/g, '').slice(0, 6) }))}
              placeholder="Enter 6-digit OTP"
              maxLength="6"
              autoComplete="one-time-code"
              inputMode="numeric"
              autoCorrect="off"
              spellCheck={false}
              autoCapitalize="off"
              style={{
                minWidth: 0,
                width: '100%',
                maxWidth: '100%',
                padding: '0.75rem',
                border: '2px solid rgba(233, 30, 99, 0.2)',
                borderRadius: '12px',
                fontSize: '1rem',
                background: 'rgba(255, 255, 255, 0.8)',
                letterSpacing: '0.2em',
                textAlign: 'center',
                boxSizing: 'border-box',
              }}
            />
            <button
              type="button"
              className="register-otp-verify"
              onClick={handleVerifyOtp}
              disabled={!otpSent || verifyingOtp || loading}
              style={{
                padding: '0.75rem 0.65rem',
                background: otpVerified ? '#2e7d32' : 'linear-gradient(135deg, #e91e63 0%, #ff6f00 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                fontWeight: '700',
                fontSize: 'clamp(0.8rem, 2.8vw, 1rem)',
                cursor: !otpSent || verifyingOtp || loading ? 'not-allowed' : 'pointer',
                opacity: !otpSent || verifyingOtp || loading ? 0.6 : 1,
                whiteSpace: 'nowrap',
                maxWidth: '100%',
                boxSizing: 'border-box',
              }}
            >
              {otpVerified ? 'Verified' : (verifyingOtp ? 'Verifying...' : 'Verify')}
            </button>
          </div>
          <div style={{ marginTop: '8px', fontSize: '12px', color: otpVerified ? '#2e7d32' : '#666' }}>
            {otpVerified
              ? 'OTP verified. You can now create your account.'
              : 'Send OTP, enter code, and verify before registration.'}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || !otpVerified}
          style={{
            width: '100%',
            padding: '1rem',
            background: 'linear-gradient(135deg, #e91e63 0%, #ff6f00 100%)',
            color: 'white',
            border: 'none',
            borderRadius: '12px',
            fontSize: '1.1rem',
            fontWeight: '700',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1,
            marginBottom: '1rem'
          }}
        >
          {loading ? 'Creating Account...' : '🚀 Create Account'}
        </button>

        <p style={{ textAlign: 'center', color: '#666' }}>
          Already have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            style={{
              background: 'none',
              border: 'none',
              color: '#e91e63',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontWeight: '600'
            }}
          >
            Login here
          </button>
        </p>
      </form>
    </div>
  );
};

export default RegisterForm;