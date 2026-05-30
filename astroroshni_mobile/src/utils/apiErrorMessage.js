/**
 * Normalize axios / FastAPI error bodies for React Native Alert.alert.
 * RN's native bridge requires string arguments; FastAPI often returns `detail`
 * as an array of { loc, msg, type } objects on 422.
 */
export function apiErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const data = error?.response?.data;
  if (!data || typeof data !== 'object') {
    const m = error?.message;
    return typeof m === 'string' && m.trim() ? m.trim() : fallback;
  }

  const detail = data.detail;
  if (detail != null) {
    if (typeof detail === 'string' && detail.trim()) return detail.trim();
    if (Array.isArray(detail)) {
      const parts = detail
        .map((item) => {
          if (item == null) return '';
          if (typeof item === 'string') return item;
          if (typeof item === 'object' && typeof item.msg === 'string') return item.msg;
          return '';
        })
        .filter(Boolean);
      if (parts.length) return parts.join('\n');
    }
    if (typeof detail === 'object' && typeof detail.msg === 'string' && detail.msg.trim()) {
      return detail.msg.trim();
    }
  }

  const msg = data.message;
  if (typeof msg === 'string' && msg.trim()) return msg.trim();
  if (Array.isArray(msg)) {
    const joined = msg.map((x) => (typeof x === 'string' ? x : '')).filter(Boolean).join('\n');
    if (joined) return joined;
  }

  return fallback;
}
