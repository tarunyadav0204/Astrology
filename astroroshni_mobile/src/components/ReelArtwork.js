import React, { useEffect, useState } from 'react';
import { Image, Platform, View } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { reelHeaders, reelUrl } from '../services/reelMediaCache';

export default function ReelArtwork({ jobId, style, blurRadius = 0, resizeMode = 'contain' }) {
  const [source, setSource] = useState(null);
  useEffect(() => {
    let active = true, objectUrl;
    const controller = new AbortController();
    setSource(null);
    if (jobId) (async () => {
      const headers = reelHeaders(await AsyncStorage.getItem('authToken'));
      const uri = reelUrl(jobId, 'thumbnail');
      if (Platform.OS === 'web') {
        const response = await fetch(uri, { headers, signal: controller.signal });
        if (!response.ok) return;
        const blob = await response.blob();
        if (!active) return;
        objectUrl = URL.createObjectURL(blob);
        setSource({ uri: objectUrl });
      } else if (active) setSource({ uri, headers });
    })().catch(() => {});
    return () => { active = false; controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [jobId]);
  return <View pointerEvents="none" style={[{ backgroundColor: '#24121e', overflow: 'hidden' }, style]}>
    {source && <Image source={source} style={{ width: '100%', height: '100%' }} resizeMode={resizeMode}
      blurRadius={blurRadius} onError={() => setSource(null)} accessible={false} />}
  </View>;
}
