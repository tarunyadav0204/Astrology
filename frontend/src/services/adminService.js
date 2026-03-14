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
  async getAllUsers(params = {}) {
    const sp = new URLSearchParams();
    if (params.phone != null && params.phone !== '') sp.set('phone', params.phone);
    if (params.name != null && params.name !== '') sp.set('name', params.name);
    if (params.role != null && params.role !== '' && params.role !== 'all') sp.set('role', params.role);
    if (params.subscription != null && params.subscription !== '' && params.subscription !== 'all') sp.set('subscription', params.subscription);
    if (params.created_from != null && params.created_from !== '') sp.set('created_from', params.created_from);
    if (params.created_to != null && params.created_to !== '') sp.set('created_to', params.created_to);
    if (params.page != null) sp.set('page', String(params.page));
    if (params.limit != null) sp.set('limit', String(params.limit));
    const qs = sp.toString();
    const url = getEndpoint('/admin/users') + (qs ? `?${qs}` : '');
    const response = await fetch(url, {
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

  async getAllCharts(params = {}) {
    const sp = new URLSearchParams();
    if (params.name != null && params.name !== '') sp.set('name', params.name);
    if (params.phone != null && params.phone !== '') sp.set('phone', params.phone);
    if (params.page != null) sp.set('page', String(params.page));
    if (params.limit != null) sp.set('limit', String(params.limit));
    const qs = sp.toString();
    const url = getEndpoint('/admin/charts') + (qs ? `?${qs}` : '');
    const response = await fetch(url, {
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

  async shareChartForInvestigation(chartId) {
    const response = await fetch(getEndpoint(`/admin/charts/${chartId}/share-for-investigation`), {
      method: 'POST',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to share chart');
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
  },

  async seedVipSubscriptionPlans() {
    const response = await fetch(getEndpoint('/admin/seed-vip-subscription-plans'), {
      method: 'POST',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to seed VIP plans');
    }

    return response.json();
  },

  async updateSubscriptionPlan(planId, payload) {
    const response = await fetch(getEndpoint(`/admin/subscription-plans/${planId}`), {
      method: 'PUT',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update subscription plan');
    }

    return response.json();
  }
};