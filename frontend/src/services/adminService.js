import { APP_CONFIG } from '../config/app.config';

const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? APP_CONFIG.api.prod
  : APP_CONFIG.api.dev;

const DEVICE_ID_KEY = 'admin_device_id';

const getEndpoint = (path) => {
  if (API_BASE_URL.includes('localhost')) {
    return `${API_BASE_URL}/api${path}`;
  }
  return `/api${path}`;
};

/** Get or create a persistent device ID for this browser (used for admin device allowlist). */
export function getDeviceId() {
  let id = localStorage.getItem(DEVICE_ID_KEY);
  if (!id || id.length < 10) {
    id = 'web-' + crypto.randomUUID();
    localStorage.setItem(DEVICE_ID_KEY, id);
  }
  return id;
}

/** Auth headers for admin API calls. Includes X-Device-Id for device allowlist. */
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    'X-Device-Id': getDeviceId(),
  };
};

/** Export for use in components that call admin APIs directly (e.g. fetch). */
export function getAdminAuthHeaders() {
  const token = localStorage.getItem('token');
  return {
    'Authorization': `Bearer ${token}`,
    'X-Device-Id': getDeviceId(),
  };
}

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

  async getUsersSummary(params = {}) {
    const sp = new URLSearchParams();
    if (params.phone != null && params.phone !== '') sp.set('phone', params.phone);
    if (params.name != null && params.name !== '') sp.set('name', params.name);
    if (params.role != null && params.role !== '' && params.role !== 'all') sp.set('role', params.role);
    if (params.subscription != null && params.subscription !== '' && params.subscription !== 'all') sp.set('subscription', params.subscription);
    const qs = sp.toString();
    const url = getEndpoint('/admin/users/summary') + (qs ? `?${qs}` : '');
    const response = await fetch(url, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      throw new Error('Failed to fetch users summary');
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
  },

  async getAllowedDevices() {
    const response = await fetch(getEndpoint('/admin/allowed-devices'), {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch allowed devices');
    }
    return response.json();
  },

  /** One-click register current device for this admin (exempt from device check). */
  async registerThisDevice() {
    const response = await fetch(getEndpoint('/admin/register-this-device'), {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to register device');
    }
    return response.json();
  },

  async addAllowedDevice(deviceId, label, forUserId = null) {
    const body = { device_id: deviceId, label: label || '' };
    if (forUserId != null && forUserId !== '') body.for_user_id = Number(forUserId);
    const response = await fetch(getEndpoint('/admin/allowed-devices'), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to add device');
    }
    return response.json();
  },

  async removeAllowedDevice(deviceId) {
    const response = await fetch(getEndpoint(`/admin/allowed-devices/${encodeURIComponent(deviceId)}`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to remove device');
    }
    return response.json();
  },

  async removeAllowedDeviceById(rowId) {
    const response = await fetch(getEndpoint(`/admin/allowed-devices-by-id/${rowId}`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to remove device');
    }
    return response.json();
  },

  async generateNudgeFromChat(userId) {
    const response = await fetch(getEndpoint('/nudge/admin/generate-nudge-from-chat'), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ user_id: Number(userId) }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      const d = err.detail;
      const msg =
        typeof d === 'string'
          ? d
          : Array.isArray(d)
            ? d.map((x) => x?.msg || JSON.stringify(x)).join('; ')
            : d
              ? JSON.stringify(d)
              : 'Failed to generate nudge from chat';
      throw new Error(msg);
    }
    return response.json();
  },

  async getAcquisitionInstallations(params = {}) {
    const sp = new URLSearchParams();
    if (params.date_from != null && params.date_from !== '') sp.set('date_from', params.date_from);
    if (params.date_to != null && params.date_to !== '') sp.set('date_to', params.date_to);
    if (params.registered != null && params.registered !== '' && params.registered !== 'all') {
      sp.set('registered', params.registered);
    }
    if (params.utm_campaign != null && params.utm_campaign !== '') sp.set('utm_campaign', params.utm_campaign);
    if (params.utm_source != null && params.utm_source !== '') sp.set('utm_source', params.utm_source);
    if (params.utm_medium != null && params.utm_medium !== '') sp.set('utm_medium', params.utm_medium);
    if (params.app_build != null && params.app_build !== '') sp.set('app_build', params.app_build);
    if (params.page != null) sp.set('page', String(params.page));
    if (params.limit != null) sp.set('limit', String(params.limit));
    const qs = sp.toString();
    const url = getEndpoint('/admin/acquisition-installations') + (qs ? `?${qs}` : '');
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (!response.ok) {
      throw new Error('Failed to fetch mobile install funnel');
    }
    return response.json();
  },

  async getAcquisitionInstallationsSummary(params = {}) {
    const sp = new URLSearchParams();
    if (params.date_from != null && params.date_from !== '') sp.set('date_from', params.date_from);
    if (params.date_to != null && params.date_to !== '') sp.set('date_to', params.date_to);
    if (params.utm_campaign != null && params.utm_campaign !== '') sp.set('utm_campaign', params.utm_campaign);
    if (params.utm_source != null && params.utm_source !== '') sp.set('utm_source', params.utm_source);
    if (params.utm_medium != null && params.utm_medium !== '') sp.set('utm_medium', params.utm_medium);
    if (params.app_build != null && params.app_build !== '') sp.set('app_build', params.app_build);
    const qs = sp.toString();
    const url = getEndpoint('/admin/acquisition-installations/summary') + (qs ? `?${qs}` : '');
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (!response.ok) {
      throw new Error('Failed to fetch install funnel summary');
    }
    return response.json();
  },

  async getAcquisitionInstallationsAnalytics(params = {}) {
    const sp = new URLSearchParams();
    if (params.date_from != null && params.date_from !== '') sp.set('date_from', params.date_from);
    if (params.date_to != null && params.date_to !== '') sp.set('date_to', params.date_to);
    if (params.utm_campaign != null && params.utm_campaign !== '') sp.set('utm_campaign', params.utm_campaign);
    if (params.utm_source != null && params.utm_source !== '') sp.set('utm_source', params.utm_source);
    if (params.utm_medium != null && params.utm_medium !== '') sp.set('utm_medium', params.utm_medium);
    if (params.app_build != null && params.app_build !== '') sp.set('app_build', params.app_build);
    const qs = sp.toString();
    const url = getEndpoint('/admin/acquisition-installations/analytics') + (qs ? `?${qs}` : '');
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (!response.ok) {
      throw new Error('Failed to fetch install funnel analytics');
    }
    return response.json();
  },

  async getAcquisitionInstallationEvents(installationId) {
    const url = getEndpoint(`/admin/acquisition-installations/${encodeURIComponent(installationId)}/events`);
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (!response.ok) {
      throw new Error('Failed to fetch install timeline');
    }
    return response.json();
  },

  async exportAcquisitionInstallations(params = {}) {
    const sp = new URLSearchParams();
    if (params.date_from != null && params.date_from !== '') sp.set('date_from', params.date_from);
    if (params.date_to != null && params.date_to !== '') sp.set('date_to', params.date_to);
    if (params.registered != null && params.registered !== '' && params.registered !== 'all') {
      sp.set('registered', params.registered);
    }
    if (params.utm_campaign != null && params.utm_campaign !== '') sp.set('utm_campaign', params.utm_campaign);
    if (params.utm_source != null && params.utm_source !== '') sp.set('utm_source', params.utm_source);
    if (params.utm_medium != null && params.utm_medium !== '') sp.set('utm_medium', params.utm_medium);
    if (params.app_build != null && params.app_build !== '') sp.set('app_build', params.app_build);
    const qs = sp.toString();
    const url = getEndpoint('/admin/acquisition-installations/export') + (qs ? `?${qs}` : '');
    const response = await fetch(url, { headers: getAdminAuthHeaders() });
    if (!response.ok) {
      let detail = 'Failed to export install funnel';
      try {
        const body = await response.json();
        detail = body.detail || detail;
      } catch (_) {
        // ignore non-JSON error bodies
      }
      throw new Error(detail);
    }
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="([^"]+)"/i);
    const filename = match?.[1] || 'install-funnel-export.zip';
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = objectUrl;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(objectUrl);
    return { ok: true, filename };
  },

  async getAdminExpenses(params = {}) {
    const sp = new URLSearchParams();
    if (params.date_from != null && params.date_from !== '') sp.set('date_from', params.date_from);
    if (params.date_to != null && params.date_to !== '') sp.set('date_to', params.date_to);
    if (params.category != null && params.category !== '') sp.set('category', params.category);
    if (params.page != null) sp.set('page', String(params.page));
    if (params.limit != null) sp.set('limit', String(params.limit));
    const qs = sp.toString();
    const url = getEndpoint('/admin/expenses') + (qs ? `?${qs}` : '');
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (!response.ok) {
      throw new Error('Failed to fetch expenses');
    }
    return response.json();
  },

  async createAdminExpense(formData) {
    const token = localStorage.getItem('token');
    const response = await fetch(getEndpoint('/admin/expenses'), {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Device-Id': getDeviceId(),
      },
      body: formData,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      const d = err.detail;
      const msg = typeof d === 'string' ? d : d ? JSON.stringify(d) : 'Failed to create expense';
      throw new Error(msg);
    }
    return response.json();
  },

  async deleteAdminExpense(expenseId) {
    const response = await fetch(getEndpoint(`/admin/expenses/${expenseId}`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete expense');
    }
    return response.json();
  },

  getAdminExpenseInvoiceUrl(expenseId) {
    return getEndpoint(`/admin/expenses/${expenseId}/invoice`);
  },

  async getExpenseMasterVendors(params = {}) {
    const sp = new URLSearchParams();
    if (params.include_inactive) sp.set('include_inactive', 'true');
    const qs = sp.toString();
    const url = getEndpoint('/admin/expense-masters/vendors') + (qs ? `?${qs}` : '');
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (!response.ok) throw new Error('Failed to load vendors');
    return response.json();
  },

  async createExpenseMasterVendor(body) {
    const response = await fetch(getEndpoint('/admin/expense-masters/vendors'), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create vendor');
    }
    return response.json();
  },

  async patchExpenseMasterVendor(id, body) {
    const response = await fetch(getEndpoint(`/admin/expense-masters/vendors/${id}`), {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update vendor');
    }
    return response.json();
  },

  async deleteExpenseMasterVendor(id) {
    const response = await fetch(getEndpoint(`/admin/expense-masters/vendors/${id}`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete vendor');
    }
    return response.json();
  },

  async getExpenseMasterPaidBy(params = {}) {
    const sp = new URLSearchParams();
    if (params.include_inactive) sp.set('include_inactive', 'true');
    const qs = sp.toString();
    const url = getEndpoint('/admin/expense-masters/paid-by') + (qs ? `?${qs}` : '');
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (!response.ok) throw new Error('Failed to load paid-by list');
    return response.json();
  },

  async createExpenseMasterPaidBy(body) {
    const response = await fetch(getEndpoint('/admin/expense-masters/paid-by'), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create paid-by entry');
    }
    return response.json();
  },

  async patchExpenseMasterPaidBy(id, body) {
    const response = await fetch(getEndpoint(`/admin/expense-masters/paid-by/${id}`), {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update paid-by entry');
    }
    return response.json();
  },

  async deleteExpenseMasterPaidBy(id) {
    const response = await fetch(getEndpoint(`/admin/expense-masters/paid-by/${id}`), {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete paid-by entry');
    }
    return response.json();
  },

  async getAdminIssues(params = {}) {
    const sp = new URLSearchParams();
    if (params.status) sp.set('status', params.status);
    if (params.page != null) sp.set('page', String(params.page));
    if (params.limit != null) sp.set('limit', String(params.limit));
    const qs = sp.toString();
    const url = getEndpoint('/admin/issues') + (qs ? `?${qs}` : '');
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch issues');
    }
    return response.json();
  },

  async getAdminIssue(issueId) {
    const response = await fetch(getEndpoint(`/admin/issues/${issueId}`), {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch issue');
    }
    return response.json();
  },

  async createAdminIssue(formData) {
    const token = localStorage.getItem('token');
    const response = await fetch(getEndpoint('/admin/issues'), {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Device-Id': getDeviceId(),
      },
      body: formData,
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      const d = err.detail;
      const msg = typeof d === 'string' ? d : d ? JSON.stringify(d) : 'Failed to create issue';
      throw new Error(msg);
    }
    return response.json();
  },

  async updateAdminIssue(issueId, body) {
    const response = await fetch(getEndpoint(`/admin/issues/${issueId}`), {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to update issue');
    }
    return response.json();
  },

  async addAdminIssueComment(issueId, body) {
    const response = await fetch(getEndpoint(`/admin/issues/${issueId}/comments`), {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ body }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to add comment');
    }
    return response.json();
  },

  getAdminIssueScreenshotUrl(issueId) {
    return getEndpoint(`/admin/issues/${issueId}/screenshot`);
  },
};
