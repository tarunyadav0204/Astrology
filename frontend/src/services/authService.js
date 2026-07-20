import { APP_CONFIG } from '../config/app.config';

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? APP_CONFIG.api.prod 
  : APP_CONFIG.api.dev;

// Helper function to add /api prefix for all endpoints
const getEndpoint = (path) => {
  if (API_BASE_URL.includes('localhost')) {
    return `${API_BASE_URL}/api${path}`;
  }
  return `/api${path}`;
};

const FRIENDLY_AUTH_FALLBACKS = {
  sendCode: 'Could not send the reset code. Please check your details and try again.',
  verifyCode: 'That code is invalid or has expired. Please request a new one.',
  resetPassword: 'Could not reset your password. Please try again.',
  network: 'Network error. Please check your connection and try again.',
  generic: 'Something went wrong. Please try again.',
};

/** Pull a plain string out of FastAPI `detail` without exposing raw objects. */
const extractApiDetail = (payload) => {
  const detail = payload?.detail ?? payload?.message;
  if (typeof detail === 'string' && detail.trim()) return detail.trim();
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        // Prefer human msg; skip loc/type noise from Pydantic 422 bodies.
        return item?.msg || item?.message || '';
      })
      .map((part) => String(part || '').trim())
      .filter(Boolean);
    if (parts.length) return parts.join('. ');
  }
  if (detail && typeof detail === 'object' && typeof detail.message === 'string') {
    return detail.message.trim();
  }
  return '';
};

const looksTechnical = (message) => {
  const text = String(message || '');
  if (!text.trim()) return true;
  if (/^HTTP\s*\d+/i.test(text)) return true;
  if (/\[object Object\]/i.test(text)) return true;
  if (/traceback|exception|sql|postgres|psycopg|internal server/i.test(text)) return true;
  if (/value error|typeerror|referenceerror|validation error/i.test(text)) return true;
  if (/body\s*->|field required|not a valid/i.test(text)) return true;
  return false;
};

/** Map known server/auth errors to short user-facing copy. */
export const toUserFriendlyAuthError = (errorOrMessage, fallback = FRIENDLY_AUTH_FALLBACKS.generic) => {
  const raw =
    typeof errorOrMessage === 'string'
      ? errorOrMessage
      : errorOrMessage?.message || extractApiDetail(errorOrMessage) || '';
  const text = String(raw || '').trim();
  const lower = text.toLowerCase();

  if (!text || looksTechnical(text)) return fallback;

  if (lower.includes('invalid or expired reset token') || lower.includes('reset session expired')) {
    return 'Your reset session expired. Please verify the code again.';
  }
  if (lower.includes('invalid or expired code')) {
    return FRIENDLY_AUTH_FALLBACKS.verifyCode;
  }
  if (lower.includes('phone number not found') || lower.includes('account not found')) {
    return 'We could not find an account with those details.';
  }
  if (lower.includes('failed to deliver reset code') || lower.includes('failed to send')) {
    return FRIENDLY_AUTH_FALLBACKS.sendCode;
  }
  if (lower.includes('password must be at least') || lower.includes('password must include')) {
    return text; // already user-facing validation copy from API
  }
  if (lower.includes('network error') || lower.includes('failed to fetch')) {
    return FRIENDLY_AUTH_FALLBACKS.network;
  }
  if (lower.includes('email is required')) {
    return 'Please enter your email address.';
  }

  // Keep short, readable API messages; replace anything that still looks raw.
  if (text.length > 160 || looksTechnical(text)) return fallback;
  return text;
};

const apiErrorMessage = (payload, fallback) =>
  toUserFriendlyAuthError(extractApiDetail(payload) || fallback, fallback);

const throwFriendlyHttpError = async (response, fallback) => {
  let message = fallback;
  try {
    const error = await response.json();
    message = apiErrorMessage(error, fallback);
  } catch {
    message = fallback;
  }
  throw new Error(message);
};

export const authService = {
  async register(userData) {
    const response = await fetch(getEndpoint('/register'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
  },

  async sendRegistrationOtp(data) {
    try {
      const response = await fetch(getEndpoint('/send-registration-otp'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        let errorMessage = 'Failed to send OTP';
        try {
          const error = await response.json();
          errorMessage = error.detail || errorMessage;
        } catch {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Network error - please check your connection');
      }
      throw error;
    }
  },

  async login(userData) {
    try {
      const response = await fetch(getEndpoint('/login'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        let errorMessage = 'Login failed';
        try {
          const error = await response.json();
          errorMessage = error.detail || errorMessage;
        } catch {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Network error - please check your connection');
      }
      throw error;
    }
  },

  async getCurrentUser() {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No token found');
    }

    try {
      const response = await fetch(getEndpoint('/me'), {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Access forbidden - please login again');
        }
        throw new Error('Failed to get user info');
      }

      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Network error - API unavailable');
      }
      throw error;
    }
  },

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  getToken() {
    return localStorage.getItem('token');
  },

  getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  async forgotPassword(data) {
    try {
      const response = await fetch(getEndpoint('/forgot-password'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        await throwFriendlyHttpError(response, 'We could not find an account with those details.');
      }

      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(FRIENDLY_AUTH_FALLBACKS.network);
      }
      throw new Error(toUserFriendlyAuthError(error, 'We could not find an account with those details.'));
    }
  },

  async sendResetCode(data) {
    try {
      const response = await fetch(getEndpoint('/send-reset-code'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        await throwFriendlyHttpError(response, FRIENDLY_AUTH_FALLBACKS.sendCode);
      }

      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(FRIENDLY_AUTH_FALLBACKS.network);
      }
      throw new Error(toUserFriendlyAuthError(error, FRIENDLY_AUTH_FALLBACKS.sendCode));
    }
  },

  async verifyResetCode(data) {
    try {
      const response = await fetch(getEndpoint('/verify-reset-code'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        await throwFriendlyHttpError(response, FRIENDLY_AUTH_FALLBACKS.verifyCode);
      }

      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(FRIENDLY_AUTH_FALLBACKS.network);
      }
      throw new Error(toUserFriendlyAuthError(error, FRIENDLY_AUTH_FALLBACKS.verifyCode));
    }
  },

  async resetPasswordWithToken(data) {
    try {
      const response = await fetch(getEndpoint('/reset-password-with-token'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        await throwFriendlyHttpError(response, FRIENDLY_AUTH_FALLBACKS.resetPassword);
      }

      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(FRIENDLY_AUTH_FALLBACKS.network);
      }
      throw new Error(toUserFriendlyAuthError(error, FRIENDLY_AUTH_FALLBACKS.resetPassword));
    }
  },

  async resetPassword(data) {
    try {
      const response = await fetch(getEndpoint('/reset-password'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        await throwFriendlyHttpError(response, FRIENDLY_AUTH_FALLBACKS.resetPassword);
      }

      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(FRIENDLY_AUTH_FALLBACKS.network);
      }
      throw new Error(toUserFriendlyAuthError(error, FRIENDLY_AUTH_FALLBACKS.resetPassword));
    }
  }
};