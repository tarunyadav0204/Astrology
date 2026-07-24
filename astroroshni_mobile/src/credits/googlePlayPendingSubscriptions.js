import AsyncStorage from '@react-native-async-storage/async-storage';

export const PENDING_GOOGLE_PLAY_SUBSCRIPTIONS_KEY = 'pendingGooglePlaySubscriptionsV1';

export function normalizePendingGooglePlaySubscription(entry) {
  if (!entry) return null;
  const purchaseToken = String(entry.purchaseToken || '').trim();
  const productId = String(entry.productId || '').trim();
  const orderId = String(entry.orderId || '').trim();
  const userId = String(entry.userId ?? '').trim();
  if (!purchaseToken || !productId || !orderId || !userId) return null;
  return {
    purchaseToken,
    productId,
    orderId,
    userId,
    savedAt: entry.savedAt || new Date().toISOString(),
  };
}

export async function getStoredGooglePlayUserId() {
  try {
    const raw = await AsyncStorage.getItem('userData');
    const parsed = raw ? JSON.parse(raw) : null;
    const userId = parsed?.userid ?? parsed?.user_id ?? parsed?.id;
    return userId == null ? null : String(userId).trim() || null;
  } catch (_) {
    return null;
  }
}

export async function loadPendingGooglePlaySubscriptions() {
  try {
    const raw = await AsyncStorage.getItem(PENDING_GOOGLE_PLAY_SUBSCRIPTIONS_KEY);
    const parsed = JSON.parse(raw || '[]');
    return Array.isArray(parsed)
      ? parsed.map(normalizePendingGooglePlaySubscription).filter(Boolean)
      : [];
  } catch (_) {
    return [];
  }
}

export async function savePendingGooglePlaySubscription(entry) {
  const normalized = normalizePendingGooglePlaySubscription(entry);
  if (!normalized) {
    throw new Error('Cannot persist Google Play subscription without purchase, product, order, and user identifiers');
  }
  const existing = await loadPendingGooglePlaySubscriptions();
  const filtered = existing.filter(
    (item) =>
      !(
        item.purchaseToken === normalized.purchaseToken &&
        item.productId === normalized.productId &&
        item.userId === normalized.userId
      )
  );
  filtered.unshift(normalized);
  await AsyncStorage.setItem(
    PENDING_GOOGLE_PLAY_SUBSCRIPTIONS_KEY,
    JSON.stringify(filtered.slice(0, 20))
  );
  return normalized;
}

export async function removePendingGooglePlaySubscription({
  purchaseToken,
  productId,
  userId,
}) {
  const existing = await loadPendingGooglePlaySubscriptions();
  const filtered = existing.filter(
    (item) =>
      !(
        item.purchaseToken === String(purchaseToken || '').trim() &&
        item.productId === String(productId || '').trim() &&
        item.userId === String(userId || '').trim()
      )
  );
  await AsyncStorage.setItem(PENDING_GOOGLE_PLAY_SUBSCRIPTIONS_KEY, JSON.stringify(filtered));
}

export async function retryPendingGooglePlaySubscriptions(syncSubscription, userId = null) {
  if (typeof syncSubscription !== 'function') {
    throw new Error('A subscription sync function is required');
  }
  const activeUserId = String(userId || (await getStoredGooglePlayUserId()) || '').trim();
  if (!activeUserId) return { attempted: 0, recovered: 0, failed: 0 };

  const pending = await loadPendingGooglePlaySubscriptions();
  let attempted = 0;
  let recovered = 0;
  let failed = 0;
  for (const item of pending) {
    if (item.userId !== activeUserId) continue;
    attempted += 1;
    try {
      await syncSubscription(item.purchaseToken, item.productId, item.orderId);
      await removePendingGooglePlaySubscription(item);
      recovered += 1;
    } catch (_) {
      failed += 1;
    }
  }
  return { attempted, recovered, failed };
}
