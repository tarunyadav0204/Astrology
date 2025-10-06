import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { authService } from '../../services/authService';

const LoginForm = ({ onLogin, onSwitchToRegister }) => {
  const [formData, setFormData] = useState({
    phone: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await authService.login(formData);
      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      toast.success('Login successful!');
      onLogin(response.user);
    } catch (error) {
      toast.error(error.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

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
        ✨ Login to Astrology App
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
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleInputChange}
            placeholder="Enter your phone number"
            required
            autoComplete="tel"
            inputMode="numeric"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '2px solid rgba(233, 30, 99, 0.2)',
              borderRadius: '12px',
              fontSize: '16px',
              background: 'rgba(255, 255, 255, 0.8)',
              WebkitAppearance: 'none',
              WebkitUserSelect: 'text',
              WebkitTouchCallout: 'default'
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
            Password
          </label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            placeholder="Enter your password"
            required
            autoComplete="current-password"
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '2px solid rgba(233, 30, 99, 0.2)',
              borderRadius: '12px',
              fontSize: '16px',
              background: 'rgba(255, 255, 255, 0.8)',
              WebkitAppearance: 'none',
              WebkitUserSelect: 'text',
              WebkitTouchCallout: 'default'
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
          {loading ? 'Logging in...' : '🚀 Login'}
        </button>

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