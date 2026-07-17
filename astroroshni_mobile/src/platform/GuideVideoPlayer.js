/**
 * Chart / guide video player.
 * Native: expo-av Video.
 * Web/PWA: HTML5 <video> or YouTube iframe — expo-av modal playback is unreliable on web.
 */
import React, { createElement, useEffect } from 'react';
import { Platform, StyleSheet } from 'react-native';
import { Video, ResizeMode } from 'expo-av';

function youtubeEmbedUrl(rawUrl) {
  const url = String(rawUrl || '').trim();
  if (!url) return null;
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.replace(/^www\./, '');
    if (host === 'youtu.be') {
      const id = parsed.pathname.split('/').filter(Boolean)[0];
      return id ? `https://www.youtube.com/embed/${id}?autoplay=1&playsinline=1` : null;
    }
    if (host === 'youtube.com' || host === 'm.youtube.com' || host === 'youtube-nocookie.com') {
      if (parsed.pathname.startsWith('/embed/')) {
        return url.includes('playsinline') ? url : `${url}${url.includes('?') ? '&' : '?'}playsinline=1`;
      }
      const shortId = parsed.pathname.startsWith('/shorts/')
        ? parsed.pathname.split('/').filter(Boolean)[1]
        : null;
      const id = parsed.searchParams.get('v') || shortId;
      return id ? `https://www.youtube.com/embed/${id}?autoplay=1&playsinline=1` : null;
    }
  } catch (_) {
    /* not a URL */
  }
  return null;
}

export default function GuideVideoPlayer({
  uri,
  style,
  shouldPlay = true,
  onLoadStart,
  onReady,
  onError,
}) {
  useEffect(() => {
    if (Platform.OS === 'web' && uri) {
      onLoadStart?.();
    }
  }, [uri, onLoadStart]);

  if (!uri) return null;

  if (Platform.OS === 'web') {
    const flatStyle = {
      width: '100%',
      height: '100%',
      backgroundColor: '#000',
      ...StyleSheet.flatten(style),
    };
    const yt = youtubeEmbedUrl(uri);
    if (yt) {
      return createElement('iframe', {
        src: yt,
        title: 'Guide video',
        style: { ...flatStyle, border: 'none' },
        allow:
          'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen',
        allowFullScreen: true,
        onLoad: () => onReady?.(),
      });
    }
    return createElement('video', {
      src: uri,
      controls: true,
      playsInline: true,
      autoPlay: !!shouldPlay,
      preload: 'auto',
      style: { ...flatStyle, objectFit: 'contain' },
      onLoadStart: () => onLoadStart?.(),
      onLoadedData: () => onReady?.(),
      onCanPlay: () => onReady?.(),
      onError: () => onError?.({ nativeEvent: { error: 'web_video_error' } }),
    });
  }

  return (
    <Video
      source={{ uri }}
      style={style}
      useNativeControls
      resizeMode={ResizeMode.CONTAIN}
      shouldPlay={shouldPlay}
      isLooping={false}
      isMuted={false}
      volume={1.0}
      onLoadStart={onLoadStart}
      onLoad={() => onReady?.()}
      onReadyForDisplay={() => onReady?.()}
      onError={onError}
    />
  );
}
