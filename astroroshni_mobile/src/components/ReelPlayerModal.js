import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, Animated, AppState, Modal, PanResponder, Platform, StatusBar, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { Audio, ResizeMode, Video } from 'expo-av';
import Ionicons from '@expo/vector-icons/Ionicons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { API_BASE_URL, getEndpoint } from '../utils/constants';

const clock = (ms) => `${Math.floor((ms || 0) / 60000)}:${String(Math.floor(((ms || 0) / 1000) % 60)).padStart(2, '0')}`;
const destinations = { Instagram: 'https://www.instagram.com/', Facebook: 'https://www.facebook.com/', YouTube: 'https://studio.youtube.com/' };

export default function ReelPlayerModal({ jobId, onClose, onRecreate }) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const video = useRef(null);
  const [source, setSource] = useState(null);
  const [status, setStatus] = useState({});
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [preview, setPreview] = useState(null);
  const [sharing, setSharing] = useState(false);
  const mediaRef = useRef(null);
  const remoteMediaRef = useRef(null);
  const statusRef = useRef({});
  const widthRef = useRef(1);
  const dragRef = useRef({ start: 0, value: 0, active: false });
  const [controlsVisible, setControlsVisible] = useState(true);
  const controlsOpacity = useRef(new Animated.Value(1)).current;
  const hideTimer = useRef(null);
  const revealControls = useCallback(function reveal() {
    setControlsVisible(true);
    Animated.timing(controlsOpacity, { toValue: 1, duration: 140, useNativeDriver: true }).start();
    clearTimeout(hideTimer.current);
    hideTimer.current = setTimeout(() => {
      if (dragRef.current.active) { reveal(); return; }
      setControlsVisible(false);
      Animated.timing(controlsOpacity, { toValue: 0, duration: 200, useNativeDriver: true }).start();
    }, 3000);
  }, [controlsOpacity]);
  useEffect(() => {
    revealControls();
    return () => { clearTimeout(hideTimer.current); controlsOpacity.stopAnimation(); };
  }, [controlsOpacity, revealControls]);
  useEffect(() => { if (source) revealControls(); }, [source, revealControls]);

  useEffect(() => {
    let active = true;
    let objectUrl;
    const controller = new AbortController();
    const load = async () => {
      try {
        const token = await AsyncStorage.getItem('authToken');
        const headers = token ? { Authorization: `Bearer ${token}`, 'X-AstroRoshni-Authorization': `Bearer ${token}` } : {};
        const url = `${String(API_BASE_URL || '').replace(/\/$/, '')}${getEndpoint(`/reel-studio/jobs/${encodeURIComponent(jobId)}/download`)}`;
        let uri;
        if (Platform.OS === 'web') {
          const response = await fetch(url, { headers, signal: controller.signal });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          const blob = await response.blob();
          if (!active) return;
          objectUrl = URL.createObjectURL(blob);
          uri = objectUrl;
          mediaRef.current = new File([blob], 'astroroshni-reel.mp4', { type: 'video/mp4' });
        } else {
          uri = `${FileSystem.cacheDirectory}astroroshni-reel-${jobId}.mp4`;
          // A completed reel is persistently cached in our storage bucket.
          // Do not reuse an emulator's old local file: Android MediaPlayer can
          // retain a partially decoded AAC track after the modal closes.
          // Downloading into a temporary file and swapping it atomically keeps
          // the player on one complete, current MP4 every time it opens.
          const temporary = `${uri}.part`;
          try {
            await FileSystem.deleteAsync(temporary, { idempotent: true });
            const downloaded = await FileSystem.downloadAsync(url, temporary, { headers });
            if (downloaded.status !== 200) {
              throw new Error(`HTTP ${downloaded.status}`);
            }
            await FileSystem.deleteAsync(uri, { idempotent: true });
            await FileSystem.moveAsync({ from: temporary, to: uri });
            mediaRef.current = uri;
            await Audio.setAudioModeAsync({ playsInSilentModeIOS: true, staysActiveInBackground: false });
          } catch (downloadError) {
            // A reel remains playable if Android cannot write a local cache file
            // (low device storage, a stale OS file lock, or a transient download
            // interruption). Video accepts authenticated remote sources directly.
            // Do not turn a successfully saved reel into an inaccessible one.
            await FileSystem.deleteAsync(temporary, { idempotent: true }).catch(() => {});
            console.warn('[ReelPlayer] local reel cache unavailable; streaming instead', {
              jobId,
              message: downloadError?.message || String(downloadError),
            });
            if (active) {
              remoteMediaRef.current = { uri: url, headers };
              setNotice(t('premiumUi.reelStudio.streamingFallback', 'Playing from your saved reel library.'));
              setSource({ uri: url, headers });
            }
            return;
          }
        }
        remoteMediaRef.current = null;
        if (active) setSource({ uri });
      } catch (err) { if (active && err.name !== 'AbortError') setError(t('premiumUi.reelStudio.loadError', 'Could not open the saved reel. Please try again.')); }
    };
    load();
    const subscription = AppState.addEventListener('change', (state) => {
      if (state !== 'active') video.current?.pauseAsync().catch(() => {});
    });
    return () => {
      active = false;
      controller.abort();
      subscription.remove();
      // Android must release the decoder before this source is opened again.
      video.current?.unloadAsync().catch(() => {});
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [jobId, t]);

  const command = async (action) => {
    try { await action(); } catch (_) { setError(t('premiumUi.reelStudio.playbackError', 'Playback failed. Please reopen the reel.')); }
  };
  const positionAt = (x) => Math.min(1, Math.max(0, x / widthRef.current)) * (statusRef.current.durationMillis || 0);
  const scrubber = useRef(PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onMoveShouldSetPanResponder: () => true,
    onPanResponderGrant: (event) => {
      revealControls();
      dragRef.current = { start: event.nativeEvent.locationX, value: positionAt(event.nativeEvent.locationX), active: true };
      setPreview(dragRef.current.value);
    },
    onPanResponderMove: (_event, gesture) => { revealControls(); dragRef.current.value = positionAt(dragRef.current.start + gesture.dx); setPreview(dragRef.current.value); },
    onPanResponderRelease: () => {
      const value = dragRef.current.value;
      revealControls();
      video.current?.setPositionAsync(value).catch(() => {}).finally(() => { dragRef.current.active = false; setPreview(null); });
    },
    onPanResponderTerminate: () => { dragRef.current.active = false; setPreview(null); },
  })).current;
  const stop = () => command(() => video.current?.stopAsync());
  const close = () => {
    video.current?.pauseAsync().catch(() => {});
    video.current?.unloadAsync().catch(() => {});
    onClose();
  };
  const downloadWeb = () => {
    const link = document.createElement('a'); link.href = source.uri; link.download = 'astroroshni-reel.mp4'; link.click();
  };

  const shareableNativeUri = async () => {
    if (typeof mediaRef.current === 'string') return mediaRef.current;
    const remote = remoteMediaRef.current;
    if (!remote?.uri) throw new Error('Saved reel source is unavailable');
    // Streaming is ideal for playback, but Android's share sheet needs a local
    // content URI. Retry independently with a unique filename so a stale player
    // cache lock never prevents the user from sharing an otherwise playable reel.
    const uri = `${FileSystem.cacheDirectory}astroroshni-reel-share-${jobId}-${Date.now()}.mp4`;
    const downloaded = await FileSystem.downloadAsync(remote.uri, uri, { headers: remote.headers });
    if (downloaded.status !== 200) {
      await FileSystem.deleteAsync(uri, { idempotent: true });
      throw new Error(`HTTP ${downloaded.status}`);
    }
    mediaRef.current = uri;
    return uri;
  };

  const share = async (destination) => {
    if (!source || sharing) return;
    video.current?.pauseAsync().catch(() => {});
    setSharing(true);
    try {
      if (Platform.OS === 'web') {
        const file = mediaRef.current;
        if (navigator.share && navigator.canShare?.({ files: [file] })) {
          if (destination) setNotice(t('premiumUi.reelStudio.chooseShareApp', 'Choose {{app}} in the share sheet to continue publishing.', { app: destination }));
          await navigator.share({ files: [file], title: 'AstroRoshni' });
        } else {
          downloadWeb();
          if (destination) window.open(destinations[destination], '_blank', 'noopener,noreferrer');
          setNotice(t('premiumUi.reelStudio.downloadUpload', 'MP4 downloaded. Select it in your social app to finish uploading.'));
        }
      } else {
        if (!await Sharing.isAvailableAsync()) throw new Error('Sharing unavailable');
        const shareUri = await shareableNativeUri();
        if (destination) setNotice(t('premiumUi.reelStudio.chooseShareApp', 'Choose {{app}} in the share sheet to continue publishing.', { app: destination }));
        await Sharing.shareAsync(shareUri, { mimeType: 'video/mp4', UTI: 'public.mpeg-4', dialogTitle: destination || t('premiumUi.reelStudio.share', 'Share') });
      }
    } catch (err) {
      if (err.name !== 'AbortError') Alert.alert(t('premiumUi.reelStudio.title', 'Your premium reel'), t('premiumUi.reelStudio.shareError', 'Could not share this reel. Please try again.'));
    } finally { setSharing(false); }
  };
  const position = preview ?? status.positionMillis ?? 0;
  const duration = status.durationMillis || 0;
  // Expo's ExoPlayer path is dropping the later AAC segments on the Android
  // emulator. MediaPlayer handles this standard local MP4 independently;
  // web continues to use the browser player.
  const playbackStatus = { shouldPlay: true, ...(Platform.OS === 'android' ? { androidImplementation: 'MediaPlayer' } : {}) };
  const button = (label, icon, action, disabled = false) => <TouchableOpacity accessibilityRole="button" accessibilityLabel={label} style={styles.button} onPress={action} disabled={disabled}>
    {icon && <Ionicons name={icon} color={disabled ? '#888' : '#fff'} size={22} />}<Text style={[styles.label, disabled && { color: '#888' }]}>{label}</Text>
  </TouchableOpacity>;

  return <Modal visible animationType="fade" presentationStyle="fullScreen" statusBarTranslucent navigationBarTranslucent onRequestClose={close}>
    <View style={styles.root} onTouchStart={revealControls} {...(Platform.OS === 'web' ? { onPointerMove: revealControls } : {})}>
      <StatusBar hidden />
      {source && <Video ref={video} source={source} style={StyleSheet.absoluteFill} resizeMode={ResizeMode.CONTAIN}
        status={playbackStatus} useNativeControls={false}
        progressUpdateIntervalMillis={250} onPlaybackStatusUpdate={(value) => { statusRef.current = value; setStatus(value); }}
        onError={() => setError(t('premiumUi.reelStudio.playbackError', 'Playback failed. Please reopen the reel.'))} />}
      <Animated.View pointerEvents={controlsVisible ? 'auto' : 'none'} accessibilityElementsHidden={!controlsVisible} importantForAccessibility={controlsVisible ? 'auto' : 'no-hide-descendants'} style={[styles.top, { paddingTop: Math.max(insets.top, 16), opacity: controlsOpacity }]}><Text style={styles.brand}>{t('premiumUi.chatScreen.brand', 'AstroRoshni')}</Text>
        {button(t('common.close', 'Close'), 'close', close)}</Animated.View>
      {!source && !error && <View style={styles.loading}><ActivityIndicator color="#eecb86" /><Text style={styles.label}>{t('premiumUi.reelStudio.openingSaved', 'Opening saved reel…')}</Text></View>}
      <Animated.View pointerEvents={controlsVisible ? 'auto' : 'none'} accessibilityElementsHidden={!controlsVisible} importantForAccessibility={controlsVisible ? 'auto' : 'no-hide-descendants'} style={[styles.controls, { paddingBottom: Math.max(insets.bottom, 18), opacity: controlsOpacity }]}>
        {!!(error || notice) && <Text style={styles.notice} accessibilityLiveRegion="polite">{error || notice}</Text>}
        <View style={styles.seekTouch} onLayout={(event) => { widthRef.current = event.nativeEvent.layout.width; }} {...scrubber.panHandlers}
          accessible accessibilityRole="adjustable" accessibilityLabel={t('premiumUi.reelStudio.timeline', 'Reel timeline')}
          accessibilityValue={{ min: 0, max: Math.floor(duration / 1000), now: Math.floor(position / 1000) }}
          accessibilityActions={[{ name: 'increment' }, { name: 'decrement' }]}
          onAccessibilityAction={(event) => command(() => video.current?.setPositionAsync(Math.min(duration, Math.max(0, position + (event.nativeEvent.actionName === 'increment' ? 10000 : -10000)))))}>
          <View style={styles.track}><View style={[styles.fill, { width: `${duration ? Math.min(100, position / duration * 100) : 0}%` }]} /></View>
        </View>
        <Text style={styles.time}>{clock(position)} / {clock(duration)}</Text>
        <View style={styles.row}>
          {button(status.isPlaying ? t('premiumUi.reelStudio.pause', 'Pause') : t('premiumUi.reelStudio.play', 'Play'), status.isPlaying ? 'pause' : 'play', () => command(() => status.isPlaying ? video.current?.pauseAsync() : video.current?.playAsync()), !status.isLoaded)}
          {button(t('premiumUi.reelStudio.stop', 'Stop'), 'stop', stop, !status.isLoaded)}
          {button(t('premiumUi.reelStudio.share', 'Share'), 'share-outline', () => share(), !source || sharing)}
          {button(t('premiumUi.reelStudio.recreate', 'Recreate'), 'refresh', () => { video.current?.pauseAsync().catch(() => {}); onRecreate(); })}
        </View>
        <View style={styles.row}>{Object.keys(destinations).map((name) => <React.Fragment key={name}>{button(name, null, () => share(name), !source || sharing)}</React.Fragment>)}</View>
      </Animated.View>
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#000' }, top: { position: 'absolute', top: 0, left: 0, right: 0, paddingHorizontal: 20, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#0007' },
  brand: { color: '#eecb86', fontSize: 22 }, controls: { position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: '#000b', paddingHorizontal: 22, paddingTop: 8 },
  row: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: 12 }, button: { minHeight: 46, padding: 8, alignItems: 'center', justifyContent: 'center', gap: 4 },
  label: { color: '#fff', fontSize: 12 }, notice: { color: '#f3d99d', fontSize: 12, textAlign: 'center', marginBottom: 10 },
  time: { color: '#ddd', fontSize: 12, textAlign: 'center', marginBottom: 4 }, seekTouch: { height: 36, justifyContent: 'center', width: '100%' },
  track: { height: 5, borderRadius: 3, backgroundColor: '#ffffff55', overflow: 'hidden' }, fill: { height: 5, backgroundColor: '#eecb86' },
  loading: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16 },
});
