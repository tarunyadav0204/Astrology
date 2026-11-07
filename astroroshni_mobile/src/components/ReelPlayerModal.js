import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  AppState,
  Modal,
  PanResponder,
  Platform,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { Audio, ResizeMode, Video } from "expo-av";
import Ionicons from "@expo/vector-icons/Ionicons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useTranslation } from "react-i18next";
import { API_BASE_URL, getEndpoint } from "../utils/constants";

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
  backgroundColor: "#000",
};

export default function ReelPlayerModal({
  jobId,
  onClose,
  onRecreate,
  allowRecreate = true,
  reelIds = [],
  onSwipeToReel,
}) {
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const video = useRef(null);
  const [source, setSource] = useState(null);
  const [status, setStatus] = useState({});
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [preview, setPreview] = useState(null);
  const [sharing, setSharing] = useState(false);
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
  reelFeedRef.current = { jobId, reelIds, onSwipeToReel };
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
        if (dragRef.current.active) {
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
  const stopPlayback = useCallback(() => {
    if (Platform.OS === "web") {
      if (video.current) video.current.currentTime = 0;
      video.current?.pause?.();
      return Promise.resolve();
    }
    return video.current?.stopAsync?.() || Promise.resolve();
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

  useEffect(() => {
    let active = true;
    let objectUrl;
    const controller = new AbortController();
    const load = async () => {
      try {
        const token = await AsyncStorage.getItem("authToken");
        const headers = token
          ? {
              Authorization: `Bearer ${token}`,
              "X-AstroRoshni-Authorization": `Bearer ${token}`,
            }
          : {};
        const url = `${String(API_BASE_URL || "").replace(/\/$/, "")}${getEndpoint(`/reel-studio/jobs/${encodeURIComponent(jobId)}/download`)}`;
        let uri;
        if (Platform.OS === "web") {
          const response = await fetch(url, {
            headers,
            signal: controller.signal,
          });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          const blob = await response.blob();
          if (!active) return;
          objectUrl = URL.createObjectURL(blob);
          uri = objectUrl;
          mediaRef.current = new File([blob], "astroroshni-reel.mp4", {
            type: "video/mp4",
          });
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
            const downloaded = await FileSystem.downloadAsync(url, temporary, {
              headers,
            });
            if (downloaded.status !== 200) {
              throw new Error(`HTTP ${downloaded.status}`);
            }
            await FileSystem.deleteAsync(uri, { idempotent: true });
            await FileSystem.moveAsync({ from: temporary, to: uri });
            mediaRef.current = uri;
            await Audio.setAudioModeAsync({
              playsInSilentModeIOS: true,
              staysActiveInBackground: false,
            });
          } catch (downloadError) {
            // A reel remains playable if Android cannot write a local cache file
            // (low device storage, a stale OS file lock, or a transient download
            // interruption). Video accepts authenticated remote sources directly.
            // Do not turn a successfully saved reel into an inaccessible one.
            await FileSystem.deleteAsync(temporary, { idempotent: true }).catch(
              () => {},
            );
            console.warn(
              "[ReelPlayer] local reel cache unavailable; streaming instead",
              {
                jobId,
                message: downloadError?.message || String(downloadError),
              },
            );
            if (active) {
              remoteMediaRef.current = { uri: url, headers };
              setNotice(
                t(
                  "premiumUi.reelStudio.streamingFallback",
                  "Playing from your saved reel library.",
                ),
              );
              setSource({ uri: url, headers });
            }
            return;
          }
        }
        // Retain the authenticated source even when playback uses the local
        // cache. Android's media player can keep that cache file open while a
        // reel is playing; sharing that same file then fails on some devices.
        // A share gets its own verified copy below instead.
        remoteMediaRef.current = { uri: url, headers };
        if (active) setSource({ uri });
      } catch (err) {
        if (active && err.name !== "AbortError")
          setError(
            t(
              "premiumUi.reelStudio.loadError",
              "Could not open the saved reel. Please try again.",
            ),
          );
      }
    };
    load();
    const subscription = AppState.addEventListener("change", (state) => {
      if (state !== "active") pausePlayback().catch(() => {});
    });
    return () => {
      active = false;
      controller.abort();
      subscription.remove();
      // Android must release the decoder before this source is opened again.
      unloadPlayback().catch(() => {});
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [jobId, pausePlayback, t, unloadPlayback]);

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
  // Keep the player itself focused on a single MP4.  The surrounding saved-reel
  // library supplies the ordered IDs, so an intentional vertical swipe can
  // replace this one player with the next reel without preloading multiple
  // videos or audio tracks on a phone.
  const feedSwipe = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => false,
      onMoveShouldSetPanResponder: (_event, gesture) =>
        Math.abs(gesture.dy) > 14 &&
        Math.abs(gesture.dy) > Math.abs(gesture.dx) * 1.25,
      onPanResponderRelease: (_event, gesture) => {
        const { jobId: activeJobId, reelIds: feedIds, onSwipeToReel: selectReel } = reelFeedRef.current;
        if (!selectReel || !Array.isArray(feedIds) || feedIds.length < 2 || Math.abs(gesture.dy) < 72) return;
        const currentIndex = feedIds.indexOf(activeJobId);
        if (currentIndex < 0) return;
        // The history is newest first: swipe up for the next saved reel and
        // down to return to the more recent one, matching short-video feeds.
        const nextIndex = gesture.dy < 0 ? currentIndex + 1 : currentIndex - 1;
        if (nextIndex >= 0 && nextIndex < feedIds.length) selectReel(feedIds[nextIndex]);
      },
    }),
  ).current;
  const stop = () => command(stopPlayback);
  const close = () => {
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
    // Never hand the share sheet the file currently used by the player. On
    // Android, MediaPlayer may retain a decoder lock on the cache file even
    // after pause, causing the provider to reject it for every share target.
    // First copy the MP4 that was already successfully downloaded for
    // playback. This avoids a second authenticated network request at the
    // exact moment the user taps Share — the device-only failure we saw.
    // expo-sharing exposes the app's private files area through FileProvider.
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
  const position = preview ?? status.positionMillis ?? 0;
  const duration = status.durationMillis || 0;
  // Expo's ExoPlayer path is dropping the later AAC segments on the Android
  // emulator. MediaPlayer handles this standard local MP4 independently;
  // web continues to use the browser player.
  const playbackStatus = {
    shouldPlay: true,
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

  return (
    <Modal
      visible
      animationType="fade"
      presentationStyle="fullScreen"
      statusBarTranslucent
      navigationBarTranslucent
      onRequestClose={close}
    >
      <View
        style={styles.root}
        onTouchStart={revealControls}
        {...(Platform.OS === "web" ? { onPointerMove: revealControls } : {})}
        {...feedSwipe.panHandlers}
      >
        <StatusBar hidden />
        {source && Platform.OS === "web" && (
          <video
            ref={video}
            src={source.uri}
            autoPlay
            playsInline
            style={webVideoStyle}
            onLoadedMetadata={updateWebStatus}
            onTimeUpdate={updateWebStatus}
            onPlay={updateWebStatus}
            onPause={updateWebStatus}
            onEnded={updateWebStatus}
            onError={() =>
              setError(
                t(
                  "premiumUi.reelStudio.playbackError",
                  "Playback failed. Please reopen the reel.",
                ),
              )
            }
          />
        )}
        {source && Platform.OS !== "web" && (
          <Video
            ref={video}
            source={source}
            style={StyleSheet.absoluteFill}
            resizeMode={ResizeMode.CONTAIN}
            status={playbackStatus}
            useNativeControls={false}
            progressUpdateIntervalMillis={250}
            onPlaybackStatusUpdate={(value) => {
              statusRef.current = value;
              setStatus(value);
            }}
            onError={() =>
              setError(
                t(
                  "premiumUi.reelStudio.playbackError",
                  "Playback failed. Please reopen the reel.",
                ),
              )
            }
          />
        )}
        <Animated.View
          pointerEvents={controlsVisible ? "auto" : "none"}
          accessibilityElementsHidden={!controlsVisible}
          importantForAccessibility={
            controlsVisible ? "auto" : "no-hide-descendants"
          }
          style={[
            styles.top,
            { paddingTop: Math.max(insets.top, 16), opacity: controlsOpacity },
          ]}
        >
          <Text style={styles.brand}>
            {t("premiumUi.chatScreen.brand", "AstroRoshni")}
          </Text>
          {button(t("common.close", "Close"), "close", close)}
        </Animated.View>
        {showFeedHint && (
          <Animated.View
            pointerEvents="none"
            style={[
              styles.feedHint,
              {
                top: Math.max(insets.top, 16) + 52,
                opacity: controlsOpacity,
              },
            ]}
          >
            <Ionicons name="swap-vertical-outline" size={15} color="#eecb86" />
            <Text style={styles.feedHintText}>
              {t(
                "premiumUi.reelStudio.swipeFeedHint",
                "Swipe up or down to browse your reels",
              )}
            </Text>
          </Animated.View>
        )}
        {!source && !error && (
          <View style={styles.loading}>
            <ActivityIndicator color="#eecb86" />
            <Text style={styles.label}>
              {t("premiumUi.reelStudio.openingSaved", "Opening saved reel…")}
            </Text>
          </View>
        )}
        <Animated.View
          pointerEvents={controlsVisible ? "auto" : "none"}
          accessibilityElementsHidden={!controlsVisible}
          importantForAccessibility={
            controlsVisible ? "auto" : "no-hide-descendants"
          }
          style={[
            styles.controls,
            {
              paddingBottom: Math.max(insets.bottom, 18),
              opacity: controlsOpacity,
            },
          ]}
        >
          {!!(error || notice) && (
            <Text style={styles.notice} accessibilityLiveRegion="polite">
              {error || notice}
            </Text>
          )}
          <View
            style={styles.seekTouch}
            onLayout={(event) => {
              widthRef.current = event.nativeEvent.layout.width;
            }}
            {...scrubber.panHandlers}
            accessible
            accessibilityRole="adjustable"
            accessibilityLabel={t(
              "premiumUi.reelStudio.timeline",
              "Reel timeline",
            )}
            accessibilityValue={{
              min: 0,
              max: Math.floor(duration / 1000),
              now: Math.floor(position / 1000),
            }}
            accessibilityActions={[
              { name: "increment" },
              { name: "decrement" },
            ]}
            onAccessibilityAction={(event) =>
              command(() =>
                setPlaybackPosition(
                  Math.min(
                    duration,
                    Math.max(
                      0,
                      position +
                        (event.nativeEvent.actionName === "increment"
                          ? 10000
                          : -10000),
                    ),
                  ),
                ),
              )
            }
          >
            <View style={styles.track}>
              <View
                style={[
                  styles.fill,
                  {
                    width: `${duration ? Math.min(100, (position / duration) * 100) : 0}%`,
                  },
                ]}
              />
            </View>
          </View>
          <Text style={styles.time}>
            {clock(position)} / {clock(duration)}
          </Text>
          <View style={styles.row}>
            {button(
              status.isPlaying
                ? t("premiumUi.reelStudio.pause", "Pause")
                : t("premiumUi.reelStudio.play", "Play"),
              status.isPlaying ? "pause" : "play",
              () =>
                command(() =>
                  status.isPlaying ? pausePlayback() : playPlayback(),
                ),
              !status.isLoaded,
            )}
            {button(
              t("premiumUi.reelStudio.stop", "Stop"),
              "stop",
              stop,
              !status.isLoaded,
            )}
            {button(
              t("premiumUi.reelStudio.share", "Share"),
              "share-outline",
              () => share(),
              !source || sharing,
            )}
            {allowRecreate && button(
              t("premiumUi.reelStudio.recreate", "Recreate"),
              "refresh",
              () => {
                pausePlayback().catch(() => {});
                onRecreate?.();
              },
            )}
          </View>
          <View style={styles.row}>
            {Object.keys(destinations).map((name) => (
              <React.Fragment key={name}>
                {button(name, null, () => share(name), !source || sharing)}
              </React.Fragment>
            ))}
          </View>
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    width: "100%",
    height: "100%",
    overflow: "hidden",
    backgroundColor: "#000",
  },
  top: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#0007",
  },
  brand: { color: "#eecb86", fontSize: 22 },
  feedHint: {
    position: "absolute",
    alignSelf: "center",
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 11,
    paddingVertical: 7,
    borderRadius: 16,
    backgroundColor: "#000a",
  },
  feedHintText: { color: "#f3d99d", fontSize: 11, fontWeight: "700" },
  controls: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "#000b",
    paddingHorizontal: 22,
    paddingTop: 8,
  },
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: 12,
  },
  button: {
    minHeight: 46,
    padding: 8,
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
  },
  label: { color: "#fff", fontSize: 12 },
  notice: {
    color: "#f3d99d",
    fontSize: 12,
    textAlign: "center",
    marginBottom: 10,
  },
  time: { color: "#ddd", fontSize: 12, textAlign: "center", marginBottom: 4 },
  seekTouch: { height: 36, justifyContent: "center", width: "100%" },
  track: {
    height: 5,
    borderRadius: 3,
    backgroundColor: "#ffffff55",
    overflow: "hidden",
  },
  fill: { height: 5, backgroundColor: "#eecb86" },
  loading: { flex: 1, justifyContent: "center", alignItems: "center", gap: 16 },
});
