import { APP_CONFIG } from '../config/app.config';

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? APP_CONFIG.api.prod 
  : APP_CONFIG.api.dev;

const getEndpoint = (path) => {
  if (API_BASE_URL.includes('localhost')) {
    return `${API_BASE_URL}/api${path}`;
  }
  return `/api${path}`;
};

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
};

export const adminService = {
  async getAllUsers() {
    const response = await fetch(getEndpoint('/admin/users'), {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch users');
    }

    return response.json();
  },

  async updateUser(phone, updates) {
    const response = await fetch(getEndpoint(`/admin/users/${phone}`), {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      throw new Error('Failed to update user');
    }

    return response.json();
  },

  async getAllCharts() {
    const response = await fetch(getEndpoint('/admin/charts'), {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch charts');
    }

    return response.json();
  },

  async deleteChart(chartId) {
    const response = await fetch(getEndpoint(`/admin/charts/${chartId}`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to delete chart');
    }

    return response.json();
  },

  async updateUserSubscription(userId, subscriptionData) {
    const response = await fetch(getEndpoint(`/admin/users/${userId}/subscription`), {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(subscriptionData),
    });

    if (!response.ok) {
      throw new Error('Failed to update subscription');
    }

    return response.json();
  },

  async getSubscriptionPlans() {
    const response = await fetch(getEndpoint('/admin/subscription-plans'), {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch subscription plans');
    }

    return response.json();
  }
};