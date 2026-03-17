import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  Dimensions,
  Pressable,
  Animated,
  PanResponder,
  ActivityIndicator,
} from 'react-native';
import { Audio } from 'expo-av';
import { LinearGradient } from 'expo-linear-gradient';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from 'react-i18next';
import { COSMIC_AMBIENT_URL } from '../utils/constants';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const MODAL_WIDTH = Math.min(SCREEN_WIDTH * 0.9, 360);

function formatTime(ms) {
  if (ms == null || !Number.isFinite(ms)) return '0:00';
  const totalSec = Math.floor(ms / 1000);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

/** Animated sound bars for "speaking" indicator */
function SoundWaveIcon({ isActive, colors }) {
  const bars = 5;
  const anims = useRef(Array.from({ length: bars }, () => new Animated.Value(0.4))).current;

  useEffect(() => {
    if (!isActive) {
      anims.forEach((a) => a.setValue(0.4));
      return;
    }
    const animations = anims.map((anim, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(anim, {
            toValue: 1,
            duration: 300 + i * 80,
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0.35,
            duration: 300 + i * 80,
            useNativeDriver: true,
          }),
        ])
      )
    );
    animations.forEach((a) => a.start());
    return () => animations.forEach((a) => a.stop());
  }, [isActive]);

  const barWidth = 6;
  const gap = 4;
  const totalWidth = bars * barWidth + (bars - 1) * gap;
  const height = 32;

  return (
    <View style={styles.soundWaveWrap}>
      {anims.map((anim, i) => (
        <Animated.View
          key={i}
          style={[
            styles.soundBar,
            {
              width: barWidth,
              height,
              marginHorizontal: gap / 2,
              backgroundColor: colors.accent || '#ff6b35',
              opacity: anim,
            },
          ]}
        />
      ))}
    </View>
  );
}

const SPEED_OPTIONS = [0.75, 1, 1.25, 1.5];

export default function PodcastPlayerModal({
  visible,
  onClose,
  mode,
  positionMillis = 0,
  durationMillis = 0,
  onSeek,
  onPause,
  onResume,
  onStop,
  onShare,
  playbackRate = 1,
  onSpeedChange,
}) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const trackWidthRef = useRef(MODAL_WIDTH - 48);
  const isGenerating = mode === 'generating';
  const isPlaying = mode === 'playing';
  const isPaused = mode === 'paused';

  const [ambienceOn, setAmbienceOn] = useState(false);
  const ambientSoundRef = useRef(null);
  const ambienceUrl = (COSMIC_AMBIENT_URL || '').trim();
  const showAmbienceToggle = !!ambienceUrl;

  // Load and play ambient loop when toggled on; stop and unload when toggled off or modal closes
  useEffect(() => {
    if (!showAmbienceToggle) return;
    if (ambienceOn) {
      let mounted = true;
      (async () => {
        try {
          const { sound } = await Audio.Sound.createAsync(
            { uri: ambienceUrl },
            { shouldPlay: true, isLooping: true }
          );
          if (!mounted) {
            sound.unloadAsync();
            return;
          }
          await sound.setVolumeAsync(0.2);
          ambientSoundRef.current = sound;
        } catch (e) {
          if (mounted) setAmbienceOn(false);
        }
      })();
      return () => {
        mounted = false;
        const s = ambientSoundRef.current;
        ambientSoundRef.current = null;
        if (s) s.unloadAsync().catch(() => {});
      };
    } else {
      const s = ambientSoundRef.current;
      ambientSoundRef.current = null;
      if (s) s.unloadAsync().catch(() => {});
    }
  }, [ambienceOn, showAmbienceToggle, ambienceUrl]);

  // When modal closes or unmounts, stop ambient
  useEffect(() => {
    if (!visible) {
      setAmbienceOn(false);
      const s = ambientSoundRef.current;
      ambientSoundRef.current = null;
      if (s) s.unloadAsync().catch(() => {});
    }
  }, [visible]);

  /** While dragging the progress bar, show this position; otherwise use positionMillis. Seek only on release to avoid "Seeking interrupted". */
  const [dragPositionMillis, setDragPositionMillis] = useState(null);
  const dragPositionRef = useRef(null);
  const displayPosition = dragPositionMillis ?? positionMillis;
  const progress = durationMillis > 0 ? Math.min(1, displayPosition / durationMillis) : 0;

  /** Ref so panResponder (created once) always uses current durationMillis when computing seek position. */
  const durationMillisRef = useRef(durationMillis);
  durationMillisRef.current = durationMillis;

  const computePositionFromTouch = (locationX) => {
    const w = trackWidthRef.current;
    if (w <= 0) return 0;
    const duration = durationMillisRef.current;
    if (duration <= 0) return 0;
    const ratio = Math.max(0, Math.min(1, locationX / w));
    return Math.floor(ratio * duration);
  };

  const panResponder = useRef(
    PanResponder.create({
      onStartShouldSetPanResponder: () => true,
      onMoveShouldSetPanResponder: () => true,
      onPanResponderGrant: (evt) => {
        const pos = computePositionFromTouch(evt.nativeEvent.locationX);
        dragPositionRef.current = pos;
        setDragPositionMillis(pos);
      },
      onPanResponderMove: (evt) => {
        const pos = computePositionFromTouch(evt.nativeEvent.locationX);
        dragPositionRef.current = pos;
        setDragPositionMillis(pos);
      },
      onPanResponderRelease: () => {
        const pos = dragPositionRef.current;
        dragPositionRef.current = null;
        setDragPositionMillis(null);
        if (onSeek != null && pos != null) onSeek(pos);
      },
    })
  ).current;

  const gradientColors = isDark
    ? ['#1a0033', '#2d1b4e', '#4a2c6d']
    : [colors.cardBackground || '#fff', colors.backgroundSecondary || '#f5f5f5'];
  const overlayBg = 'rgba(0, 0, 0, 0.75)';
  const accentColor = colors.primary || '#f97316';

  if (!visible) return null;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Pressable
        style={[styles.overlay, { backgroundColor: overlayBg }]}
        onPress={() => {}}
      >
        <View style={styles.outer} pointerEvents="box-none">
          <View style={styles.modalCard} pointerEvents="box-none">
            <LinearGradient colors={gradientColors} style={styles.gradient}>
              <TouchableOpacity
                style={styles.closeButton}
                onPress={onClose}
                hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
              >
                <Ionicons name="close" size={26} color={colors.textSecondary || '#999'} />
              </TouchableOpacity>

              {isGenerating && (
                <View style={styles.generatingContent}>
                  <ActivityIndicator size="large" color={accentColor} />
                  <Text style={[styles.generatingTitle, { color: colors.text }]}>
                    {t('podcast.generatingTitle', 'Generating your podcast')}
                  </Text>
                  <Text style={[styles.generatingSubtitle, { color: colors.textSecondary }]}>
                    {t('podcast.generatingSubtitle', 'This may take up to 2 minutes. We’re creating a smooth listen for you.')}
                  </Text>
                </View>
              )}

              {(isPlaying || isPaused) && (
                <View style={styles.playerContent}>
                  <View style={styles.waveRow}>
                    <SoundWaveIcon isActive={isPlaying} colors={colors} />
                    <Text style={[styles.playingLabel, { color: colors.textSecondary }]}>
                      {isPlaying ? t('podcast.playing', 'Playing') : t('podcast.paused', 'Paused')}
                    </Text>
                  </View>

                  <View
                    style={styles.seekTrackWrap}
                    onLayout={(e) => {
                      const { width } = e.nativeEvent.layout;
                      if (width > 0) trackWidthRef.current = width;
                    }}
                    {...panResponder.panHandlers}
                  >
                    <View style={[styles.seekTrack, { backgroundColor: colors.surface || 'rgba(255,255,255,0.2)' }]}>
                      <View
                        style={[
                          styles.seekFill,
                          {
                            width: `${progress * 100}%`,
                            backgroundColor: accentColor,
                          },
                        ]}
                      />
                    </View>
                  </View>

                  <View style={styles.timeRow}>
                    <Text style={[styles.timeText, { color: colors.textSecondary }]}>
                      {formatTime(displayPosition)}
                    </Text>
                    <Text style={[styles.timeText, { color: colors.textSecondary }]}>
                      {formatTime(durationMillis)}
                    </Text>
                  </View>

                  <View style={styles.controlsRow}>
                    <TouchableOpacity
                      style={[styles.controlBtn, { backgroundColor: colors.surface || 'rgba(255,255,255,0.15)' }]}
                      onPress={onStop}
                    >
                      <Ionicons name="stop" size={28} color={colors.text} />
                      <Text style={[styles.controlLabel, { color: colors.text }]}>{t('podcast.stop', 'Stop')}</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.controlBtnMain, { backgroundColor: accentColor }]}
                      onPress={isPlaying ? onPause : onResume}
                    >
                      <Ionicons name={isPlaying ? 'pause' : 'play'} size={36} color="#fff" />
                      <Text style={[styles.controlLabelMain, { color: '#fff' }]}>
                        {isPlaying ? t('podcast.pause', 'Pause') : t('podcast.play', 'Play')}
                      </Text>
                    </TouchableOpacity>
                    {onShare && (
                      <TouchableOpacity
                        style={[styles.controlBtn, { backgroundColor: colors.surface || 'rgba(255,255,255,0.15)' }]}
                        onPress={onShare}
                      >
                        <Ionicons name="share-outline" size={28} color={colors.text} />
                        <Text style={[styles.controlLabel, { color: colors.text }]}>{t('podcast.share', 'Share')}</Text>
                      </TouchableOpacity>
                    )}
                  </View>

                  {onSpeedChange && (
                    <View style={styles.speedRow}>
                      <Text style={[styles.speedLabel, { color: colors.textSecondary }]}>
                        {t('podcast.speed', 'Speed')}
                      </Text>
                      <View style={styles.speedOptions}>
                        {SPEED_OPTIONS.map((speed) => (
                          <TouchableOpacity
                            key={speed}
                            style={[
                              styles.speedChip,
                              { backgroundColor: colors.surface || 'rgba(255,255,255,0.15)' },
                              playbackRate === speed && { backgroundColor: accentColor },
                            ]}
                            onPress={() => onSpeedChange(speed)}
                          >
                            <Text
                              style={[
                                styles.speedChipText,
                                { color: playbackRate === speed ? '#fff' : (colors.textSecondary || '#999') },
                                playbackRate === speed && styles.speedChipTextActive,
                              ]}
                            >
                              {speed === 1 ? '1×' : `${speed}×`}
                            </Text>
                          </TouchableOpacity>
                        ))}
                      </View>
                    </View>
                  )}

                  {showAmbienceToggle && (
                    <TouchableOpacity
                      style={[styles.ambienceRow, { backgroundColor: colors.surface || 'rgba(255,255,255,0.1)' }]}
                      onPress={() => setAmbienceOn((v) => !v)}
                      activeOpacity={0.8}
                    >
                      <Ionicons
                        name={ambienceOn ? 'planet' : 'planet-outline'}
                        size={22}
                        color={ambienceOn ? accentColor : (colors.textSecondary || '#999')}
                      />
                      <Text style={[styles.ambienceLabel, { color: ambienceOn ? accentColor : colors.textSecondary }]}>
                        {t('podcast.cosmicAmbience', 'Cosmic ambience')}
                      </Text>
                    </TouchableOpacity>
                  )}
                </View>
              )}
            </LinearGradient>
          </View>
        </View>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  outer: {
    width: MODAL_WIDTH,
  },
  modalCard: {
    borderRadius: 24,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 12,
  },
  gradient: {
    padding: 28,
    paddingTop: 44,
    minHeight: 280,
  },
  closeButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    zIndex: 2,
  },
  generatingContent: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  generatingTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginTop: 20,
    marginBottom: 8,
  },
  generatingSubtitle: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 16,
  },
  playerContent: {
    alignItems: 'center',
  },
  waveRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
    gap: 12,
  },
  soundWaveWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 32,
  },
  soundBar: {
    borderRadius: 3,
  },
  playingLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  seekTrackWrap: {
    width: '100%',
    paddingVertical: 12,
    paddingHorizontal: 4,
  },
  seekTrack: {
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
    width: '100%',
  },
  seekFill: {
    height: '100%',
    borderRadius: 3,
  },
  timeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    paddingHorizontal: 4,
    marginTop: -4,
    marginBottom: 20,
  },
  timeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  controlsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 24,
  },
  controlBtn: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  controlLabel: {
    fontSize: 11,
    fontWeight: '600',
    marginTop: 4,
  },
  controlBtnMain: {
    width: 88,
    height: 88,
    borderRadius: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  controlLabelMain: {
    fontSize: 12,
    fontWeight: '700',
    marginTop: 4,
  },
  ambienceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginTop: 20,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 24,
  },
  ambienceLabel: {
    fontSize: 14,
    fontWeight: '600',
  },
  speedRow: {
    marginTop: 16,
    alignItems: 'center',
  },
  speedLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  speedOptions: {
    flexDirection: 'row',
    gap: 10,
  },
  speedChip: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 20,
  },
  speedChipText: {
    fontSize: 14,
    fontWeight: '600',
  },
  speedChipTextActive: {
    color: '#fff',
    fontWeight: '700',
  },
});
