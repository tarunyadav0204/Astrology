const authHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

const parseJson = async (response) => {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data?.detail || data?.error || data?.message || `Request failed (${response.status})`;
    const err = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    err.status = response.status;
    err.data = data;
    throw err;
  }
  return data;
};

export const reportService = {
  listTypes: async () => {
    const response = await fetch('/api/reports/types', { headers: authHeaders() });
    return parseJson(response);
  },

  getHistory: async ({ reportType = null, status = null, limit = 30, offset = 0 } = {}) => {
    const params = new URLSearchParams();
    if (reportType) params.append('report_type', reportType);
    if (status) params.append('status', status);
    params.append('limit', String(limit));
    params.append('offset', String(offset));
    const suffix = params.toString() ? `?${params.toString()}` : '';
    const response = await fetch(`/api/reports/history${suffix}`, { headers: authHeaders() });
    return parseJson(response);
  },

  lookupExistingPartnershipReport: async (personA, personB, language = 'english', options = {}) => {
    const response = await fetch('/api/reports/partnership/existing', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        report_type: 'partnership',
        boy_birth_data: personA,
        girl_birth_data: personB,
        language,
        chart_style: options.chartStyle || 'both',
        force_regenerate: false,
        include_images: options.includeImages !== false,
      }),
    });
    return parseJson(response);
  },

  startPartnershipReport: async (personA, personB, language = 'english', options = {}) => {
    const response = await fetch('/api/reports/partnership/start', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        report_type: 'partnership',
        boy_birth_data: personA,
        girl_birth_data: personB,
        language,
        chart_style: options.chartStyle || 'both',
        force_regenerate: Boolean(options.forceRegenerate),
        include_images: options.includeImages !== false,
      }),
    });
    return parseJson(response);
  },

  getPartnershipReportStatus: async (reportId) => {
    const response = await fetch(`/api/reports/partnership/status/${encodeURIComponent(reportId)}`, {
      headers: authHeaders(),
    });
    return parseJson(response);
  },

  lookupExistingWealthReport: async (person, language = 'english', options = {}) => {
    const response = await fetch('/api/reports/wealth/existing', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        report_type: 'wealth',
        birth_data: person,
        language,
        chart_style: options.chartStyle || 'both',
        force_regenerate: false,
        include_images: options.includeImages !== false,
      }),
    });
    return parseJson(response);
  },

  startWealthReport: async (person, language = 'english', options = {}) => {
    const response = await fetch('/api/reports/wealth/start', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        report_type: 'wealth',
        birth_data: person,
        language,
        chart_style: options.chartStyle || 'both',
        force_regenerate: Boolean(options.forceRegenerate),
        include_images: options.includeImages !== false,
      }),
    });
    return parseJson(response);
  },

  getWealthReportStatus: async (reportId) => {
    const response = await fetch(`/api/reports/wealth/status/${encodeURIComponent(reportId)}`, {
      headers: authHeaders(),
    });
    return parseJson(response);
  },

  lookupExistingHealthReport: async (person, language = 'english', options = {}) => {
    const response = await fetch('/api/reports/health/existing', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        report_type: 'health',
        birth_data: person,
        language,
        chart_style: options.chartStyle || 'both',
        force_regenerate: false,
        include_images: options.includeImages !== false,
      }),
    });
    return parseJson(response);
  },

  startHealthReport: async (person, language = 'english', options = {}) => {
    const response = await fetch('/api/reports/health/start', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        report_type: 'health',
        birth_data: person,
        language,
        chart_style: options.chartStyle || 'both',
        force_regenerate: Boolean(options.forceRegenerate),
        include_images: options.includeImages !== false,
      }),
    });
    return parseJson(response);
  },

  getHealthReportStatus: async (reportId) => {
    const response = await fetch(`/api/reports/health/status/${encodeURIComponent(reportId)}`, {
      headers: authHeaders(),
    });
    return parseJson(response);
  },

  lookupExistingJanamKundliReport: async (person, language = 'english', options = {}) => {
    const response = await fetch('/api/reports/janam_kundli/existing', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        report_type: 'janam_kundli',
        birth_data: person,
        language,
        chart_style: options.chartStyle || 'both',
        force_regenerate: false,
        include_images: options.includeImages !== false,
      }),
    });
    return parseJson(response);
  },

  getReportBranding: async () => {
    const response = await fetch('/api/reports/branding', { headers: authHeaders() });
    return parseJson(response);
  },

  saveReportBranding: async (branding) => {
    const response = await fetch('/api/reports/branding', {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(branding || {}),
    });
    return parseJson(response);
  },

  startJanamKundliReport: async (person, language = 'english', options = {}) => {
    const response = await fetch('/api/reports/janam_kundli/start', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        report_type: 'janam_kundli',
        birth_data: person,
        language,
        chart_style: options.chartStyle || 'both',
        force_regenerate: Boolean(options.forceRegenerate),
        include_images: options.includeImages !== false,
        ...(options.branding ? { branding: options.branding } : {}),
      }),
    });
    return parseJson(response);
  },

  getJanamKundliReportStatus: async (reportId) => {
    const response = await fetch(`/api/reports/janam_kundli/status/${encodeURIComponent(reportId)}`, {
      headers: authHeaders(),
    });
    return parseJson(response);
  },

  getReportPdfUrl: async (reportId) => {
    const response = await fetch(`/api/reports/pdf/${encodeURIComponent(reportId)}`, {
      headers: authHeaders(),
    });
    return parseJson(response);
  },
};

export default reportService;
