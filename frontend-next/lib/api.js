/** Same-origin API base (nginx proxies /api to backend). */

export function getApiBase() {
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_API_BASE || 'https://astroroshni.com';
  }
  return '';
}

export function authHeaders() {
  if (typeof window === 'undefined') return {};
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function loadStoredUser() {
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function loadBirthChart() {
  try {
    const birthData = JSON.parse(localStorage.getItem('astrology_birth_data') || 'null');
    const chartData = JSON.parse(localStorage.getItem('astrology_chart_data') || 'null');
    return { birthData, chartData };
  } catch {
    return { birthData: null, chartData: null };
  }
}
