import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { authService } from '../../services/authService';
import PhoneWithCountrySelect from './PhoneWithCountrySelect';
import { buildFullPhone, isNationalPhoneValid } from '../../utils/countryCodes';

// Get app name based on domain
const getAppName = () => {
  const hostname = window.location.hostname;
  if (hostname.includes('astroroshni')) {
    return 'AstroRoshni';
  } else if (hostname.includes('astrovishnu')) {
    return 'AstroVishnu';
  }
  // Default fallback
  return 'AstroRoshni';
};

const LoginForm = ({ onLogin, onSwitchToRegister }) => {
  const [countryCode, setCountryCode] = useState('+91');
  const [formData, setFormData] = useState({
    phone: '', // national digits only (no country code)
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetCountryCode, setResetCountryCode] = useState('+91');
  const [resetData, setResetData] = useState({ phone: '', email: '', code: '', newPassword: '' });
  const [resetStep, setResetStep] = useState(1);
  const [resetToken, setResetToken] = useState('');
  /** Non-India: reset / registration OTP is also sent by email (backend requires it). */
  const isOtpEmailRequired = () => resetCountryCode !== '+91';

  const [biometricSupported, setBiometricSupported] = useState(false);
  
  React.useEffect(() => {
    // Check if biometric authentication is supported
    const checkBiometric = async () => {
      if (window.PublicKeyCredential && navigator.credentials) {
        try {
          const available = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
          setBiometricSupported(available);
        } catch (error) {
          setBiometricSupported(false);
        }
      }
    };
    checkBiometric();
  }, []);

  const handleInputChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const fullPhone = buildFullPhone(countryCode, formData.phone);
    if (!fullPhone || !isNationalPhoneValid(countryCode, formData.phone)) {
      toast.error('Please enter a valid phone number for the selected country');
      return;
    }
    setLoading(true);

    try {
      const response = await authService.login({ phone: fullPhone, password: formData.password });
      
      // Check if user is admin (you can modify this condition as needed)
      const isAdmin = response.user?.role === 'admin';
      const userWithAdmin = { ...response.user, isAdmin };
      
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(userWithAdmin));
      
      // Save user data for biometric login if supported
      if (biometricSupported && /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        localStorage.setItem('biometric_user', JSON.stringify({
          ...userWithAdmin,
          token: response.access_token,
          phone: fullPhone
        }));
      }
      
      toast.success('Login successful!');
      onLogin(userWithAdmin);
    } catch (error) {
      toast.error(error.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSendCode = async (e) => {
    e.preventDefault();
    const fullPhone = buildFullPhone(resetCountryCode, resetData.phone);
    if (!fullPhone || !isNationalPhoneValid(resetCountryCode, resetData.phone)) {
      toast.error('Please enter a valid phone number for the selected country');
      return;
    }
    setLoading(true);

    try {
      if (isOtpEmailRequired() && !(resetData.email || '').trim()) {
        throw new Error('Email is required for non-India numbers');
      }
      const payload = { phone: fullPhone };
      if ((resetData.email || '').trim()) payload.email = resetData.email.trim();
      const response = await authService.sendResetCode(payload);
      toast.success(response.message);
      // Show code if SMS service is unavailable (testing mode)
      if (response.code) {
        console.log('Reset code:', response.code);
        toast.info(`Code: ${response.code}`, { autoClose: 10000 });
      }
      setResetStep(2);
    } catch (error) {
      toast.error(error.message || 'Phone number not found');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (e) => {
    e.preventDefault();
    const fullPhone = buildFullPhone(resetCountryCode, resetData.phone);
    setLoading(true);

    try {
      const response = await authService.verifyResetCode({
        phone: fullPhone,
        code: resetData.code
      });
      setResetToken(response.reset_token);
      toast.success('Code verified! Enter new password.');
      setResetStep(3);
    } catch (error) {
      toast.error(error.message || 'Invalid or expired code');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await authService.resetPasswordWithToken({
        token: resetToken,
        new_password: resetData.newPassword
      });
      toast.success('Password reset successfully!');
      setShowForgotPassword(false);
      setResetStep(1);
      setResetData({ phone: '', email: '', code: '', newPassword: '' });
      setResetCountryCode('+91');
      setResetToken('');
    } catch (error) {
      toast.error(error.message || 'Password reset failed');
    } finally {
      setLoading(false);
    }
  };
  
  const handleBiometricLogin = async () => {
    setLoading(true);
    
    try {
      // Check if user has saved credentials
      const savedUser = localStorage.getItem('biometric_user');
      if (!savedUser) {
        toast.error('Please login with password first to enable biometric authentication');
        setLoading(false);
        return;
      }
      
      const userData = JSON.parse(savedUser);
      
      // Create credential request
      const credential = await navigator.credentials.create({
        publicKey: {
          challenge: new Uint8Array(32),
          rp: {
            name: getAppName(),
            id: window.location.hostname
          },
          user: {
            id: new TextEncoder().encode(userData.phone),
            name: userData.phone,
            displayName: userData.name || userData.phone
          },
          pubKeyCredParams: [{ alg: -7, type: 'public-key' }],
          authenticatorSelection: {
            authenticatorAttachment: 'platform',
            userVerification: 'required'
          },
          timeout: 60000,
          attestation: 'direct'
        }
      });
      
      if (credential) {
        // Store biometric credential
        localStorage.setItem('biometric_credential', JSON.stringify({
          id: credential.id,
          rawId: Array.from(new Uint8Array(credential.rawId)),
          type: credential.type
        }));
        
        // Auto-login with saved user data
        localStorage.setItem('token', userData.token);
        localStorage.setItem('user', JSON.stringify(userData));
        toast.success('Biometric login successful!');
        onLogin(userData);
      }
    } catch (error) {
      if (error.name === 'NotAllowedError') {
        toast.error('Biometric authentication was cancelled');
      } else if (error.name === 'NotSupportedError') {
        toast.error('Biometric authentication not supported on this device');
      } else {
        toast.error('Biometric authentication failed');
      }
    } finally {
      setLoading(false);
    }
  };

  if (showForgotPassword) {
    return (
      <div style={{
        maxWidth: '400px',
        margin: '0 auto',
        padding: '2rem',
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
          🔐 Reset Password
        </h2>

        {resetStep === 1 ? (
          <form onSubmit={handleSendCode}>
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
                countryCode={resetCountryCode}
                onCountryCodeChange={setResetCountryCode}
                nationalDigits={resetData.phone}
                onNationalDigitsChange={(digits) =>
                  setResetData((prev) => ({ ...prev, phone: digits }))
                }
                disabled={loading}
              />
            </div>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{
                display: 'block',
                marginBottom: '0.5rem',
                color: '#e91e63',
                fontWeight: '600'
              }}>
                Email {isOtpEmailRequired() ? '(required for non-India numbers)' : '(optional)'}
              </label>
              <input
                type="email"
                value={resetData.email}
                onChange={(e) => setResetData(prev => ({ ...prev, email: e.target.value }))}
                placeholder="Enter your email"
                required={isOtpEmailRequired()}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '2px solid rgba(233, 30, 99, 0.2)',
                  borderRadius: '12px',
                  fontSize: '16px',
                  background: 'rgba(255, 255, 255, 0.8)'
                }}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
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
              {loading ? 'Sending...' : 'Send Code'}
            </button>
          </form>
        ) : resetStep === 2 ? (
          <form onSubmit={handleVerifyCode}>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{
                display: 'block',
                marginBottom: '0.5rem',
                color: '#e91e63',
                fontWeight: '600'
              }}>
                Enter 6-digit Code
              </label>
              <input
                type="text"
                value={resetData.code}
                onChange={(e) => setResetData(prev => ({ ...prev, code: e.target.value }))}
                placeholder="Enter verification code"
                maxLength="6"
                required
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '2px solid rgba(233, 30, 99, 0.2)',
                  borderRadius: '12px',
                  fontSize: '16px',
                  background: 'rgba(255, 255, 255, 0.8)',
                  textAlign: 'center',
                  letterSpacing: '0.2em'
                }}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
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
              {loading ? 'Verifying...' : 'Verify Code'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleResetPassword}>
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{
                display: 'block',
                marginBottom: '0.5rem',
                color: '#e91e63',
                fontWeight: '600'
              }}>
                New Password
              </label>
              <input
                type="password"
                value={resetData.newPassword}
                onChange={(e) => setResetData(prev => ({ ...prev, newPassword: e.target.value }))}
                placeholder="Enter new password"
                required
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '2px solid rgba(233, 30, 99, 0.2)',
                  borderRadius: '12px',
                  fontSize: '16px',
                  background: 'rgba(255, 255, 255, 0.8)'
                }}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
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
              {loading ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        )}

        <p style={{ textAlign: 'center', color: '#666' }}>
          <button
            type="button"
            onClick={() => {
              setShowForgotPassword(false);
              setResetStep(1);
              setResetData({ phone: '', email: '', code: '', newPassword: '' });
              setResetCountryCode('+91');
              setResetToken('');
            }}
            style={{
              background: 'none',
              border: 'none',
              color: '#e91e63',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontWeight: '600'
            }}
          >
            Back to Login
          </button>
        </p>
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: '400px',
      margin: '0 auto',
      padding: '2rem',
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
        ✨ Login to {getAppName()}
      </h2>

      <form onSubmit={handleSubmit}>
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
            onCountryCodeChange={setCountryCode}
            nationalDigits={formData.phone}
            onNationalDigitsChange={(digits) =>
              setFormData((prev) => ({ ...prev, phone: digits }))
            }
            disabled={loading}
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
          <div style={{ position: 'relative' }}>
            <input
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
              style={{
                width: '100%',
                padding: '0.75rem 3rem 0.75rem 0.75rem',
                border: '2px solid rgba(233, 30, 99, 0.2)',
                borderRadius: '12px',
                fontSize: '16px',
                background: 'rgba(255, 255, 255, 0.8)',
                WebkitAppearance: 'none',
                WebkitUserSelect: 'text',
                WebkitTouchCallout: 'default'
              }}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              style={{
                position: 'absolute',
                right: '0.75rem',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1.2rem',
                color: '#666'
              }}
            >
              {showPassword ? '🙈' : '👁️'}
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
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
          {loading ? 'Logging in...' : '🚀 Login'}
        </button>
        
        {biometricSupported && /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) && (
          <button
            type="button"
            onClick={handleBiometricLogin}
            disabled={loading}
            style={{
              width: '100%',
              padding: '1rem',
              background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
              marginBottom: '1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            {/iPhone|iPad|iPod/i.test(navigator.userAgent) ? '🔐 Face ID / Touch ID' : '🔐 Fingerprint / Face Login'}
          </button>
        )}

        <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
          <button
            type="button"
            onClick={() => setShowForgotPassword(true)}
            style={{
              background: 'none',
              border: 'none',
              color: '#e91e63',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontWeight: '600',
              fontSize: '14px'
            }}
          >
            Forgot Password?
          </button>
        </div>

        <p style={{ textAlign: 'center', color: '#666' }}>
          Don't have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            style={{
              background: 'none',
              border: 'none',
              color: '#e91e63',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontWeight: '600'
            }}
          >
            Register here
          </button>
        </p>
      </form>
    </div>
  );
};

export default LoginForm;