import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  AppState,
  Image,
  Modal,
  PanResponder,
  Platform,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Vibration,
  useWindowDimensions,
} from "react-native";
import { Audio, ResizeMode, Video } from "expo-av";
import Ionicons from "@expo/vector-icons/Ionicons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import * as MediaLibrary from "expo-media-library";
import { LinearGradient } from "expo-linear-gradient";
import { useTheme } from "../context/ThemeContext";
import { chatAPI } from "../services/api";
import { createReelMediaCache } from "../services/reelMediaCache";
import ReelArtwork from "./ReelArtwork";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTranslation } from "react-i18next";

const clock = (ms) =>
  `${Math.floor((ms || 0) / 60000)}:${String(Math.floor(((ms || 0) / 1000) % 60)).padStart(2, "0")}`;
const destinations = {
  Instagram: "https://www.instagram.com/",
  Facebook: "https://www.facebook.com/",
  YouTube: "https://studio.youtube.com/",
};
const REEL_FEED_HINT_SEEN_KEY = "reel_feed_swipe_hint_seen";
const webVideoStyle = {
  position: "absolute",
  inset: 0,
  width: "100%",
  height: "100%",
  maxWidth: "100vw",
  maxHeight: "100vh",
  objectFit: "contain",
  backgroundColor: "transparent",
};

export default function ReelPlayerModal(props) {
  const [activeId, setActiveId] = useState(props.jobId);
  const [library, setLibrary] = useState([]);
  const cache = useRef(null);
  const dismiss = useRef(props.onClose);
  if (!cache.current) cache.current = createReelMediaCache();
  useEffect(() => { setActiveId(props.jobId); }, [props.jobId]);
  useEffect(() => {
    let active = true;
    if (!props.reels) chatAPI.getReelHistory().then((response) => {
      if (active) setLibrary(response.data?.reels || []);
    }).catch(() => {});
    return () => { active = false; };
  }, [props.reels]);
  useEffect(() => () => cache.current.dispose(), []);
  const reels = props.reels || library;
  const ids = props.reelIds || reels.filter((r) => r.status === 'completed').map((r) => r.job_id);
  return <Modal visible animationType="none" presentationStyle="fullScreen" statusBarTranslucent navigationBarTranslucent
    onRequestClose={() => dismiss.current?.()}>
    <StatusBar hidden />
    <ReelPlayback {...props} key={activeId} jobId={activeId} mediaCache={cache.current} dismissRef={dismiss}
    reelIds={ids} reel={reels.find((r) => r.job_id === activeId)}
    allowRecreate={props.allowRecreate !== false && activeId === props.jobId}
    onSwipeToReel={(id) => { setActiveId(id); props.onSwipeToReel?.(id); }} />
  </Modal>;
}

function ReelPlayback({
  jobId,
  onClose,
  onRecreate,
  allowRecreate = true,
  reelIds = [],
  onSwipeToReel,
  reel,
  mediaCache,
  dismissRef,
}) {
  const { t } = useTranslation();
  const { colors } = useTheme();
  const { height, width } = useWindowDimensions();
  const frameHeight = Math.min(height, width * 16 / 9);
  const videoFrame = { position: 'absolute', height: frameHeight, width: frameHeight * 9 / 16,
    top: (height - frameHeight) / 2, left: (width - frameHeight * 9 / 16) / 2 };
  const insets = useSafeAreaInsets();
  const video = useRef(null);
  const [source, setSource] = useState(null);
  const [status, setStatus] = useState({});
  const [error, setError] = useState("");
  const errorRef = useRef(''); errorRef.current = error;
  const [notice, setNotice] = useState("");
  const [preview, setPreview] = useState(null);
  const [sharing, setSharing] = useState(false);
  const [menu, setMenu] = useState(null);
  const [ready, setReady] = useState(false);
  const [resume, setResume] = useState(0);
  const [peekId, setPeekId] = useState(null);
  const slide = useRef(new Animated.Value(0)).current;
  const changing = useRef(false);
  const menuRef = useRef(null); menuRef.current = menu;
  const busyRef = useRef(false); busyRef.current = sharing;
  const lastSaved = useRef(0);
  const [showFeedHint, setShowFeedHint] = useState(false);
  const mediaRef = useRef(null);
  const remoteMediaRef = useRef(null);
  const statusRef = useRef({});
  const widthRef = useRef(1);
  const dragRef = useRef({ start: 0, value: 0, active: false });
  const [controlsVisible, setControlsVisible] = useState(true);
  const controlsOpacity = useRef(new Animated.Value(1)).current;
  const hideTimer = useRef(null);
  const feedHintTimer = useRef(null);
  const reelFeedRef = useRef({ jobId, reelIds, onSwipeToReel });
  reelFeedRef.current = { jobId, reelIds, onSwipeToReel, height };
  const hasReelFeed = Array.isArray(reelIds) && reelIds.length > 1;
  const revealControls = useCallback(
    function reveal() {
      setControlsVisible(true);
      Animated.timing(controlsOpacity, {
        toValue: 1,
        duration: 140,
        useNativeDriver: true,
      }).start();
      clearTimeout(hideTimer.current);
      hideTimer.current = setTimeout(() => {
        if (dragRef.current.active || menuRef.current || busyRef.current || errorRef.current) {
          reveal();
          return;
        }
        setControlsVisible(false);
        Animated.timing(controlsOpacity, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }).start();
      }, 3000);
    },
    [controlsOpacity],
  );
  // expo-av Web uses the movie's intrinsic box, which can extend beyond the
  // modal and crop the right side of portrait reels. A native browser video
  // element lets us explicitly contain the complete 9:16 frame.
  const updateWebStatus = useCallback((event) => {
    const node = event.currentTarget;
    const value = {
      isLoaded: Number.isFinite(node.duration),
      isPlaying: !node.paused && !node.ended,
      durationMillis: Number.isFinite(node.duration) ? node.duration * 1000 : 0,
      positionMillis: Number.isFinite(node.currentTime)
        ? node.currentTime * 1000
        : 0,
    };
    statusRef.current = value;
    setStatus(value);
  }, []);
  const pausePlayback = useCallback(() => {
    if (Platform.OS === "web") {
      video.current?.pause?.();
      return Promise.resolve();
    }
    return video.current?.pauseAsync?.() || Promise.resolve();
  }, []);
  const playPlayback = useCallback(() => {
    if (Platform.OS === "web")
      return video.current?.play?.() || Promise.resolve();
    return video.current?.playAsync?.() || Promise.resolve();
  }, []);
  const setPlaybackPosition = useCallback((millis) => {
    if (Platform.OS === "web") {
      if (video.current) video.current.currentTime = millis / 1000;
      return Promise.resolve();
    }
    return video.current?.setPositionAsync?.(millis) || Promise.resolve();
  }, []);
  const unloadPlayback = useCallback(
    () =>
      Platform.OS === "web"
        ? Promise.resolve()
        : video.current?.unloadAsync?.() || Promise.resolve(),
    [],
  );
  useEffect(() => {
    revealControls();
    return () => {
      clearTimeout(hideTimer.current);
      clearTimeout(feedHintTimer.current);
      controlsOpacity.stopAnimation();
    };
  }, [controlsOpacity, revealControls]);
  useEffect(() => {
    if (!hasReelFeed) return undefined;
    let active = true;
    AsyncStorage.getItem(REEL_FEED_HINT_SEEN_KEY).then((seen) => {
      if (!active || seen) return;
      setShowFeedHint(true);
      // Store on first display rather than after a completed swipe: the hint is
      // onboarding, not a permanent player control.
      AsyncStorage.setItem(REEL_FEED_HINT_SEEN_KEY, "1").catch(() => {});
      feedHintTimer.current = setTimeout(() => setShowFeedHint(false), 3200);
    });
    return () => {
      active = false;
      clearTimeout(feedHintTimer.current);
    };
  }, [hasReelFeed]);
  useEffect(() => {
    if (source) revealControls();
  }, [source, revealControls]);

  const savePosition = useCallback(() => {
    const value = statusRef.current;
    if (!value.isLoaded) return;
    const finished = value.didJustFinish || (value.durationMillis && value.positionMillis >= value.durationMillis - 1500);
    AsyncStorage.setItem(`reel-position:${jobId}`, String(finished ? 0 : value.positionMillis || 0)).catch(() => {});
  }, [jobId]);
  useEffect(() => {
    let active = true;
    Promise.all([mediaCache.prepare(jobId), AsyncStorage.getItem(`reel-position:${jobId}`)]).then(async ([media, saved]) => {
      if (!active) return;
      if (Platform.OS !== "web") await Audio.setAudioModeAsync({ playsInSilentModeIOS: true, staysActiveInBackground: false });
      if (!active) return;
      setResume(Math.max(0, Number(saved) || 0));
      remoteMediaRef.current = media.remote;
      mediaRef.current = Platform.OS === "web" ? media.file : media.uri;
      setSource({ uri: media.uri });
    }).catch(() => {
      if (active) setError(t("premiumUi.reelStudio.loadError", "Could not open the saved reel. Please try again."));
    });
    const subscription = AppState.addEventListener("change", (state) => {
      if (state !== "active") { savePosition(); pausePlayback().catch(() => {}); }
    });
    return () => {
      active = false;
      savePosition();
      subscription.remove();
      unloadPlayback().catch(() => {});
    };
  }, [jobId, mediaCache, pausePlayback, savePosition, t, unloadPlayback]);
  const feedIndex = reelIds.indexOf(jobId);
  const nextId = reelIds[feedIndex + 1];
  const previousId = reelIds[feedIndex - 1];
  useEffect(() => {
    if (!source) return;
    mediaCache.keep([jobId, nextId, previousId].filter(Boolean));
    if (nextId) mediaCache.prepare(nextId).catch(() => {});
  }, [jobId, mediaCache, nextId, previousId, source]);
  const command = async (action) => {
    try {
      await action();
    } catch (_) {
      setError(
        t(
          "premiumUi.reelStudio.playbackError",
          "Playback failed. Please reopen the reel.",
        ),
      );
    }
  };
  const positionAt = (x) =>
    Math.min(1, Math.max(0, x / widthRef.current)) *
    (statusRef.current.durationMillis || 0);
  const scrubber = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (event) => {
        revealControls();
        dragRef.current = {
          start: event.nativeEvent.locationX,
          value: positionAt(event.nativeEvent.locationX),
          active: true,
        };
        setPreview(dragRef.current.value);
      },
      onPanResponderMove: (_event, gesture) => {
        revealControls();
        dragRef.current.value = positionAt(dragRef.current.start + gesture.dx);
        setPreview(dragRef.current.value);
      },
      onPanResponderRelease: () => {
        const value = dragRef.current.value;
        revealControls();
        setPlaybackPosition(value)
          .catch(() => {})
          .finally(() => {
            dragRef.current.active = false;
            setPreview(null);
          });
      },
      onPanResponderTerminate: () => {
        dragRef.current.active = false;
        setPreview(null);
      },
    }),
  ).current;
  // Own touches on a separate surface above the native video from touch-down.
  // Waiting for a move to bubble from Android's video view loses the gesture.
  // Controls are siblings above this surface, so scrubbing and button presses
  // keep their own responders instead of becoming feed swipes.
  const feedSwipe = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => !busyRef.current && !menuRef.current,
      onPanResponderGrant: revealControls,
      onMoveShouldSetPanResponder: (_event, gesture) =>
        Math.abs(gesture.dy) > 14 &&
        Math.abs(gesture.dy) > Math.abs(gesture.dx) * 1.25,
      onPanResponderMove: (_event, gesture) => {
        if (changing.current || Math.abs(gesture.dy) <= Math.abs(gesture.dx) * 1.25) return;
        const feed = reelFeedRef.current;
        const adjacent = feed.reelIds[feed.reelIds.indexOf(feed.jobId) + (gesture.dy < 0 ? 1 : -1)];
        setPeekId(adjacent || null);
        slide.setValue(adjacent ? gesture.dy : gesture.dy * 0.15);
      },
      onPanResponderRelease: (_event, gesture) => {
        const { jobId: activeJobId, reelIds: feedIds, onSwipeToReel: selectReel } = reelFeedRef.current;
        if (!selectReel || !Array.isArray(feedIds) || feedIds.length < 2 ||
            Math.abs(gesture.dy) < 72 || Math.abs(gesture.dy) <= Math.abs(gesture.dx) * 1.25) {
          Animated.spring(slide, { toValue: 0, useNativeDriver: true }).start(); return;
        }
        const currentIndex = feedIds.indexOf(activeJobId);
        if (currentIndex < 0) return;
        // The history is newest first: swipe up for the next saved reel and
        // down to return to the more recent one, matching short-video feeds.
        const nextIndex = gesture.dy < 0 ? currentIndex + 1 : currentIndex - 1;
        if (nextIndex >= 0 && nextIndex < feedIds.length && !changing.current) {
          changing.current = true;
          Animated.timing(slide, { toValue: gesture.dy < 0 ? -reelFeedRef.current.height : reelFeedRef.current.height,
            duration: 180, useNativeDriver: true }).start(({ finished }) => {
            if (finished) { savePosition(); pausePlayback().catch(() => {});
              if (Platform.OS !== 'web') Vibration.vibrate(10);
              selectReel(feedIds[nextIndex]); }
          });
        } else Animated.spring(slide, { toValue: 0, useNativeDriver: true }).start();
      },
      onPanResponderTerminate: () => Animated.spring(slide, { toValue: 0, useNativeDriver: true }).start(),
    }),
  ).current;
  const close = () => {
    savePosition();
    pausePlayback().catch(() => {});
    unloadPlayback().catch(() => {});
    onClose();
  };
  const downloadWeb = () => {
    const link = document.createElement("a");
    link.href = source.uri;
    link.download = "astroroshni-reel.mp4";
    link.click();
  };

  const shareableNativeUri = async () => {
    const remote = remoteMediaRef.current;
    // Reuse the downloaded MP4 to avoid another authenticated request. Keep
    // the exported copy in the private files area exposed by FileProvider.
    const directory = `${FileSystem.documentDirectory}shared-reels/`;
    await FileSystem.makeDirectoryAsync(directory, { intermediates: true });
    const uri = `${directory}astroroshni-reel-${jobId}-${Date.now()}.mp4`;
    const playerUri = typeof mediaRef.current === "string" ? mediaRef.current : null;
    let copied = false;
    if (playerUri?.startsWith("file:")) {
      const playerFile = await FileSystem.getInfoAsync(playerUri, { size: true });
      if (playerFile.exists && Number(playerFile.size) >= 1024) {
        try {
          await FileSystem.copyAsync({ from: playerUri, to: uri });
          copied = true;
        } catch (_) {
          await FileSystem.deleteAsync(uri, { idempotent: true });
        }
      }
    }
    if (!copied) {
      if (!remote?.uri) throw new Error("Saved reel source is unavailable");
      const downloaded = await FileSystem.downloadAsync(remote.uri, uri, {
        headers: remote.headers,
      });
      if (downloaded.status !== 200) {
        await FileSystem.deleteAsync(uri, { idempotent: true });
        throw new Error(`HTTP ${downloaded.status}`);
      }
    }
    const info = await FileSystem.getInfoAsync(uri, { size: true });
    if (!info.exists || !Number.isFinite(info.size) || info.size < 1024) {
      await FileSystem.deleteAsync(uri, { idempotent: true });
      throw new Error("Downloaded reel is incomplete");
    }
    return uri;
  };

  const share = async (destination) => {
    if (!source || sharing) return;
    setMenu(null);
    pausePlayback().catch(() => {});
    setSharing(true);
    try {
      if (Platform.OS === "web") {
        const file = mediaRef.current;
        if (navigator.share && navigator.canShare?.({ files: [file] })) {
          if (destination)
            setNotice(
              t(
                "premiumUi.reelStudio.chooseShareApp",
                "Choose {{app}} in the share sheet to continue publishing.",
                { app: destination },
              ),
            );
          await navigator.share({ files: [file], title: "AstroRoshni" });
        } else {
          downloadWeb();
          if (destination)
            window.open(
              destinations[destination],
              "_blank",
              "noopener,noreferrer",
            );
          setNotice(
            t(
              "premiumUi.reelStudio.downloadUpload",
              "MP4 downloaded. Select it in your social app to finish uploading.",
            ),
          );
        }
      } else {
        if (!(await Sharing.isAvailableAsync()))
          throw new Error("Sharing unavailable");
        const shareUri = await shareableNativeUri();
        if (destination)
          setNotice(
            t(
              "premiumUi.reelStudio.chooseShareApp",
              "Choose {{app}} in the share sheet to continue publishing.",
              { app: destination },
            ),
          );
        await Sharing.shareAsync(shareUri, {
          mimeType: "video/mp4",
          UTI: "public.mpeg-4",
          dialogTitle: destination || t("premiumUi.reelStudio.share", "Share"),
        });
      }
    } catch (err) {
      console.warn("[ReelPlayer] reel share failed", {
        jobId,
        destination: destination || "system",
        message: err?.message || String(err),
      });
      if (err.name !== "AbortError")
        Alert.alert(
          t("premiumUi.reelStudio.title", "Your premium reel"),
          t(
            "premiumUi.reelStudio.shareError",
            "Could not share this reel. Please try again.",
          ),
        );
    } finally {
      setSharing(false);
    }
  };
  const saveToDevice = async () => {
    if (!source || sharing) return;
    setSharing(true); setMenu(null);
    try {
      if (Platform.OS === 'web') downloadWeb();
      else {
        const permission = await MediaLibrary.requestPermissionsAsync(true, ['video']);
        if (!permission.granted) { setNotice(t('reelPlayer.savePermission')); return; }
        await MediaLibrary.saveToLibraryAsync(mediaRef.current);
      }
      setNotice(t('reelPlayer.saved'));
    } catch (_) { setNotice(t('reelPlayer.saveError')); }
    finally { setSharing(false); revealControls(); }
  };
  const position = preview ?? status.positionMillis ?? 0;
  const duration = status.durationMillis || 0;
  // Expo's ExoPlayer path is dropping the later AAC segments on the Android
  // emulator. MediaPlayer handles this standard local MP4 independently;
  // web continues to use the browser player.
  const playbackStatus = {
    shouldPlay: true,
    positionMillis: resume,
    ...(Platform.OS === "android"
      ? { androidImplementation: "MediaPlayer" }
      : {}),
  };
  const button = (label, icon, action, disabled = false) => (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={label}
      style={styles.button}
      onPress={action}
      disabled={disabled}
    >
      {icon && (
        <Ionicons name={icon} color={disabled ? "#888" : "#fff"} size={22} />
      )}
      <Text style={[styles.label, disabled && { color: "#888" }]}>{label}</Text>
    </TouchableOpacity>
  );

  useEffect(() => {
    if (error) revealControls();
  }, [error, revealControls]);
  useEffect(() => {
    if (Date.now() - lastSaved.current > 5000 || status.didJustFinish) {
      lastSaved.current = Date.now(); savePosition();
    }
    if (status.didJustFinish) revealControls();
  }, [status, savePosition, revealControls]);
  const overlayProps = { pointerEvents: controlsVisible ? 'auto' : 'none',
    accessibilityElementsHidden: !controlsVisible, importantForAccessibility: controlsVisible ? 'auto' : 'no-hide-descendants' };
  dismissRef.current = menu ? () => setMenu(null) : close;
  return <View style={styles.root} onTouchStart={revealControls} {...(Platform.OS === 'web' ? { onPointerMove: revealControls } : {})}>
      <Animated.View pointerEvents="none" style={[StyleSheet.absoluteFill, { transform: [{ translateY: slide }] }]}>
        <ReelArtwork jobId={jobId} resizeMode="cover" blurRadius={35} style={StyleSheet.absoluteFill} />
        <LinearGradient colors={['#321220aa', '#120c1aaa', '#321220aa']} style={StyleSheet.absoluteFill} />
        {source && Platform.OS === 'web' && <video ref={video} src={source.uri} autoPlay playsInline style={webVideoStyle}
          onLoadedMetadata={(e) => { if (resume < e.currentTarget.duration * 1000 - 1500) e.currentTarget.currentTime = resume / 1000; updateWebStatus(e); }}
          onCanPlay={() => setReady(true)} onTimeUpdate={updateWebStatus} onPlay={updateWebStatus} onPause={updateWebStatus} onEnded={(e) => { updateWebStatus(e); revealControls(); }}
          onError={() => setError(t('premiumUi.reelStudio.playbackError', 'Playback failed. Please reopen the reel.'))} />}
        {source && Platform.OS !== 'web' && <Video ref={video} source={source} style={videoFrame}
          resizeMode={ResizeMode.CONTAIN} status={playbackStatus} useNativeControls={false} progressUpdateIntervalMillis={250}
          onReadyForDisplay={() => setReady(true)} onPlaybackStatusUpdate={(value) => { statusRef.current = value; setStatus(value); }}
          onError={() => setError(t('premiumUi.reelStudio.playbackError', 'Playback failed. Please reopen the reel.'))} />}
        {!ready && <ReelArtwork jobId={jobId} style={StyleSheet.absoluteFill} />}
        {peekId && <ReelArtwork jobId={peekId} style={{ position: 'absolute', left: 0, right: 0, height,
          top: reelIds.indexOf(peekId) > feedIndex ? height : -height }} />}
      </Animated.View>
      <View testID="reel-swipe-surface" accessible={false} pointerEvents="box-only"
        style={[StyleSheet.absoluteFill, Platform.OS === 'web' && { touchAction: 'none' }]} {...feedSwipe.panHandlers} />
      <Animated.View {...overlayProps} style={[styles.top, { paddingTop: Math.max(insets.top, 16), opacity: controlsOpacity }]}>
        <View style={styles.brandRow}><Image source={require('../../assets/logo.png')} style={styles.logo} />
          <Text style={styles.brand}>{t('premiumUi.chatScreen.brand', 'AstroRoshni')}</Text></View>
        {hasReelFeed && feedIndex >= 0 && <Text style={styles.count}>{t('reelPlayer.count', { current: feedIndex + 1, total: reelIds.length })}</Text>}
        <TouchableOpacity accessibilityRole="button" accessibilityLabel={t('common.close', 'Close')} onPress={close} style={styles.close}>
          <Ionicons name="close" size={25} color="#fff" /></TouchableOpacity>
      </Animated.View>
      {showFeedHint && <View pointerEvents="none" style={[styles.feedHint, { top: Math.max(insets.top, 16) + 56 }]}>
        <Text style={styles.feedHintText}>{t('premiumUi.reelStudio.swipeFeedHint', 'Swipe up or down to browse your reels')}</Text></View>}
      {!ready && !error && <View pointerEvents="none" style={styles.loading}><ActivityIndicator color="#eecb86" />
        <Text style={styles.label}>{t('premiumUi.reelStudio.openingSaved', 'Opening saved reel…')}</Text></View>}
      {ready && <Animated.View {...overlayProps} style={[styles.center, { opacity: controlsOpacity }]}>
        <TouchableOpacity style={styles.centerButton} accessibilityRole="button"
          accessibilityLabel={status.isPlaying ? t('premiumUi.reelStudio.pause', 'Pause') : t('premiumUi.reelStudio.play', 'Play')}
          onPress={() => command(() => status.isPlaying ? pausePlayback() : playPlayback())}>
          <Ionicons name={status.isPlaying ? 'pause' : 'play'} size={34} color="#fff" />
        </TouchableOpacity></Animated.View>}
      <Animated.View {...overlayProps} style={[styles.rail, { bottom: Math.max(insets.bottom, 18) + 118, opacity: controlsOpacity }]}>
        {button(t('premiumUi.reelStudio.share', 'Share'), 'share-social-outline', () => setMenu('share'), !source || sharing)}
        {button(t('reelPlayer.save'), 'download-outline', saveToDevice, !source || sharing)}
        {button(t('reelPlayer.more'), 'ellipsis-horizontal', () => setMenu('more'), sharing)}
      </Animated.View>
      <Animated.View {...overlayProps} style={[styles.controls, { paddingBottom: Math.max(insets.bottom, 18), opacity: controlsOpacity }]}>
        {!!reel?.question && <Text style={styles.question} numberOfLines={2}>{reel.question}</Text>}
        {!!(error || notice) && <Text style={styles.notice} accessibilityLiveRegion="polite">{error || notice}</Text>}
        <View style={styles.seekTouch} onLayout={(e) => { widthRef.current = e.nativeEvent.layout.width; }} {...scrubber.panHandlers}
          accessible accessibilityRole="adjustable" accessibilityLabel={t('premiumUi.reelStudio.timeline', 'Reel timeline')}
          accessibilityValue={{ min: 0, max: Math.floor(duration / 1000), now: Math.floor(position / 1000) }}
          accessibilityActions={[{ name: 'increment' }, { name: 'decrement' }]}
          onAccessibilityAction={(e) => command(() => setPlaybackPosition(Math.max(0, Math.min(duration,
            position + (e.nativeEvent.actionName === 'increment' ? 10000 : -10000)))))}>
          <View style={[styles.track, preview !== null && { height: 7 }]}><View style={[styles.fill, {
            width: `${duration ? Math.min(100, position / duration * 100) : 0}%` }]} /></View>
        </View><Text style={styles.time}>{clock(position)} / {clock(duration)}</Text>
      </Animated.View>
      {!controlsVisible && <View pointerEvents="none" style={[styles.passiveTrack, { bottom: Math.max(insets.bottom, 3) }]}>
        <View style={[styles.fill, { width: `${duration ? Math.min(100, position / duration * 100) : 0}%` }]} /></View>}
      {menu && <View style={styles.menuBackdrop}>
        <TouchableOpacity style={StyleSheet.absoluteFill} accessibilityLabel={t('common.close', 'Close')} onPress={() => setMenu(null)} />
        <View style={[styles.menu, { backgroundColor: colors.surfaceRaised, paddingBottom: Math.max(insets.bottom, 20) }]}>
          <Text style={[styles.menuTitle, { color: colors.text }]}>{menu === 'share' ? t('premiumUi.reelStudio.share', 'Share') : t('reelPlayer.more')}</Text>
          {(menu === 'share' ? [t('reelPlayer.shareApps'), ...Object.keys(destinations)] :
            [t('reelPlayer.restart'), ...(allowRecreate && onRecreate ? [t('premiumUi.reelStudio.recreate', 'Recreate')] : [])]).map((label, index) =>
            <TouchableOpacity key={label} accessibilityRole="button" style={[styles.menuItem, { borderBottomColor: colors.cardBorder }]} onPress={() => {
              if (menu === 'share') share(index ? Object.keys(destinations)[index - 1] : undefined);
              else if (!index) { setMenu(null); command(() => setPlaybackPosition(0)); }
              else { setMenu(null); pausePlayback().catch(() => {}); onRecreate?.(); }
            }}><Text style={{ color: colors.text, fontSize: 16 }}>{label}</Text><Ionicons name="chevron-forward" size={18} color={colors.textSecondary} /></TouchableOpacity>)}
          <TouchableOpacity style={styles.menuItem} onPress={() => setMenu(null)}><Text style={{ color: colors.primary }}>{t('common.close', 'Close')}</Text></TouchableOpacity>
        </View>
      </View>}
    </View>;
}

const styles = StyleSheet.create({
  root: { flex: 1, width: "100%", height: "100%", overflow: "hidden", backgroundColor: "#21111e" },
  top: { position: "absolute", top: 0, left: 0, right: 0, paddingHorizontal: 18, paddingBottom: 12,
    flexDirection: "row", alignItems: "center", gap: 12, backgroundColor: "#130c1866" },
  brandRow: { flex: 1, flexDirection: "row", alignItems: "center", gap: 9 },
  logo: { width: 30, height: 30, borderRadius: 8 },
  brand: { color: "#eecb86", fontSize: 18, fontFamily: Platform.OS === "android" ? "serif" : "Georgia" },
  count: { color: "#eee", fontSize: 12 }, close: { padding: 10, borderRadius: 24, backgroundColor: "#0005" },
  rail: { position: "absolute", right: 12, gap: 16 },
  button: { width: 62, minHeight: 62, borderRadius: 22, backgroundColor: "#170e23aa", padding: 8,
    alignItems: "center", justifyContent: "center", gap: 5, borderWidth: 1, borderColor: "#ffffff25" },
  label: { color: "#fff", fontSize: 10, textAlign: "center" },
  center: { position: "absolute", top: "50%", left: "50%", marginTop: -34, marginLeft: -34 },
  centerButton: { width: 68, height: 68, borderRadius: 34, alignItems: "center", justifyContent: "center",
    backgroundColor: "#150b2088", borderWidth: 1, borderColor: "#ffffff44" },
  feedHint: { position: "absolute", alignSelf: "center", paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, backgroundColor: "#150c23aa" },
  feedHintText: { color: "#f3d99d", fontSize: 11 },
  controls: { position: "absolute", bottom: 0, left: 0, right: 0, backgroundColor: "#100a16bb", paddingHorizontal: 20, paddingTop: 12 },
  question: { color: "#fff", fontSize: 15, lineHeight: 22, fontWeight: "600", marginBottom: 4 },
  notice: { color: "#f3d99d", fontSize: 12, textAlign: "center", marginBottom: 8 },
  time: { color: "#ddd", fontSize: 11, textAlign: "right", fontVariant: ["tabular-nums"] },
  seekTouch: { height: 34, justifyContent: "center", width: "100%" },
  track: { height: 3, borderRadius: 4, backgroundColor: "#ffffff40", overflow: "hidden" },
  fill: { height: "100%", backgroundColor: "#eecb86" },
  passiveTrack: { position: "absolute", left: 18, right: 18, height: 2, backgroundColor: "#ffffff20" },
  loading: { position: "absolute", left: 0, right: 0, top: "48%", alignItems: "center", gap: 12 },
  menuBackdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: "#0007", justifyContent: "flex-end" },
  menu: { padding: 24, borderTopLeftRadius: 28, borderTopRightRadius: 28 },
  menuTitle: { fontSize: 22, fontWeight: "700", marginBottom: 12 },
  menuItem: { minHeight: 54, paddingVertical: 15, borderBottomWidth: StyleSheet.hairlineWidth,
    flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
});
