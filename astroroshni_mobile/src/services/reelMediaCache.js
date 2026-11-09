import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL, getEndpoint } from '../utils/constants';

export const reelUrl = (jobId, asset = 'download') =>
  `${String(API_BASE_URL || '').replace(/\/$/, '')}${getEndpoint(`/reel-studio/jobs/${encodeURIComponent(jobId)}/${asset}`)}`;
export const reelHeaders = (token) => token ? {
  Authorization: `Bearer ${token}`, 'X-AstroRoshni-Authorization': `Bearer ${token}`,
} : {};

// Scoped to one open player. Only current/adjacent reels are retained; closing
// releases files and object URLs, including a prefetch that finishes afterwards.
export function createReelMediaCache() {
  const entries = new Map();
  const prefix = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  let sequence = 0;
  let closed = false;
  const remove = async (media) => {
    if (Platform.OS === 'web') URL.revokeObjectURL(media.uri);
    else await FileSystem.deleteAsync(media.uri, { idempotent: true }).catch(() => {});
  };
  const prepare = (jobId) => {
    if (closed) return Promise.reject(new Error("Video Reading player is closed"));
    if (entries.has(jobId)) return entries.get(jobId);
    const requestNumber = ++sequence;
    const promise = (async () => {
      const headers = reelHeaders(await AsyncStorage.getItem('authToken'));
      const remote = { uri: reelUrl(jobId), headers };
      if (Platform.OS === 'web') {
        const response = await fetch(remote.uri, { headers });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const blob = await response.blob();
        return { ...remote, uri: URL.createObjectURL(blob), remote,
          file: new File([blob], 'astroroshni-video-reading.mp4', { type: 'video/mp4' }) };
      }
      const uri = `${FileSystem.cacheDirectory}reel-player-${prefix}-${requestNumber}-${jobId}.mp4`;
      const temporary = `${uri}.part`;
      try {
        const result = await FileSystem.downloadAsync(remote.uri, temporary, { headers });
        if (result.status !== 200) throw new Error(`HTTP ${result.status}`);
        await FileSystem.moveAsync({ from: temporary, to: uri });
        return { uri, remote };
      } finally {
        await FileSystem.deleteAsync(temporary, { idempotent: true }).catch(() => {});
      }
    })();
    entries.set(jobId, promise);
    promise.catch(() => { if (entries.get(jobId) === promise) entries.delete(jobId); });
    return promise;
  };
  const keep = (ids) => {
    for (const [id, promise] of entries) {
      if (!ids.includes(id)) {
        entries.delete(id);
        promise.then(remove).catch(() => {});
      }
    }
  };
  return { prepare, keep, dispose() { closed = true; keep([]); } };
}
