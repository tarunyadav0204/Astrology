import React, { useEffect, useState } from 'react';
import { Image, Platform, StyleSheet, View } from 'react-native';
import * as FileSystem from 'expo-file-system/legacy';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { reelHeaders, reelUrl } from '../services/reelMediaCache';

export default function ReelArtwork({ jobId, style, blurRadius = 0, resizeMode = 'contain' }) {
  const [source, setSource] = useState(null);
  useEffect(() => {
    let active = true, objectUrl, localUri;
    const controller = new AbortController();
    setSource(null);
    if (jobId) (async () => {
      const headers = reelHeaders(await AsyncStorage.getItem('authToken'));
      const uri = reelUrl(jobId, 'thumbnail');
      if (Platform.OS === 'web') {
        const response = await fetch(uri, { headers, signal: controller.signal });
        if (!response.ok) throw new Error(`Thumbnail HTTP ${response.status}`);
        const blob = await response.blob();
        if (!active) return;
        objectUrl = URL.createObjectURL(blob);
        setSource({ uri: objectUrl });
      } else {
        // Use the authenticated download path rather than Android's image network loader.
        const path = `${FileSystem.cacheDirectory}reel-cover-${Date.now()}-${Math.random().toString(36).slice(2)}.jpg`;
        localUri = path;
        const response = await FileSystem.downloadAsync(uri, path, { headers });
        if (response.status !== 200) throw new Error(`Thumbnail HTTP ${response.status}`);
        if (active) setSource({ uri: path });
        else await FileSystem.deleteAsync(path, { idempotent: true }).catch(() => {});
      }
    })().catch(error => {
      if (active) console.warn('[ReelArtwork] Thumbnail could not load', jobId, error?.message);
      if (localUri) FileSystem.deleteAsync(localUri, { idempotent: true }).catch(() => {});
    });
    return () => { active = false; controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); if (localUri) FileSystem.deleteAsync(localUri, { idempotent: true }).catch(() => {}); };
  }, [jobId]);
  return <View pointerEvents="none" style={[{ backgroundColor: '#24121e', overflow: 'hidden' }, style]}>
    {source && <Image source={source} style={StyleSheet.absoluteFillObject} resizeMode={resizeMode}
      blurRadius={blurRadius} onError={() => { console.warn('[ReelArtwork] Thumbnail could not decode', jobId); setSource(null); }} accessible={false} />}
  </View>;
}
