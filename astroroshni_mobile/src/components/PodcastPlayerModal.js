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
import PodcastVisualStage from './PodcastVisualStage';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const MODAL_WIDTH = Math.min(SCREEN_WIDTH * 0.9, 360);
const COMPACT_WATCH = SCREEN_HEIGHT < 760;

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
              transform: [{ scaleY: anim }],
            },
          ]}
        />
      ))}
    </View>
  );
}

const GENERATION_STAGES = [
  { after: 0, icon: 'book-outline', key: 'reading', fallback: 'Reading your consultation' },
  { after: 25, icon: 'create-outline', key: 'writing', fallback: 'Shaping it into a natural conversation' },
  { after: 65, icon: 'people-outline', key: 'hosts', fallback: 'Preparing Ananya and Arjun' },
  { after: 110, icon: 'mic-outline', key: 'voices', fallback: 'Creating the voices' },
  { after: 165, icon: 'options-outline', key: 'mixing', fallback: 'Mixing your podcast' },
  { after: 220, icon: 'sparkles-outline', key: 'finishing', fallback: 'Adding the finishing touches' },
  { after: 300, icon: 'hourglass-outline', key: 'longer', fallback: 'Still working — your podcast is safe' },
];

function PodcastGeneratingExperience({ accentColor, colors, t, startedAt }) {
  const initialElapsed = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
  const [elapsedSeconds, setElapsedSeconds] = useState(initialElapsed);
  const pulse = useRef(new Animated.Value(0.92)).current;

  useEffect(() => {
    setElapsedSeconds(Math.max(0, Math.floor((Date.now() - startedAt) / 1000)));
    const timer = setInterval(() => {
      setElapsedSeconds(Math.max(0, Math.floor((Date.now() - startedAt) / 1000)));
    }, 1000);
    const pulseAnimation = Animated.loop(Animated.sequence([
      Animated.timing(pulse, { toValue: 1.05, duration: 900, useNativeDriver: true }),
      Animated.timing(pulse, { toValue: 0.92, duration: 900, useNativeDriver: true }),
    ]));
    pulseAnimation.start();
    return () => {
      clearInterval(timer);
      pulseAnimation.stop();
    };
  }, [pulse, startedAt]);

  const stageIndex = GENERATION_STAGES.reduce(
    (selected, stage, index) => (elapsedSeconds >= stage.after ? index : selected),
    0,
  );
  const stage = GENERATION_STAGES[stageIndex];
  const elapsed = `${Math.floor(elapsedSeconds / 60)}:${String(elapsedSeconds % 60).padStart(2, '0')}`;

  return (
    <View style={styles.generatingContent} accessibilityRole="progressbar" accessibilityLabel={stage.fallback}>
      <Text style={[styles.generatingEyebrow, { color: colors.textSecondary }]}>{t('podcast.creationStudio', 'ASTROROSHNI PODCAST STUDIO')}</Text>
      <View style={styles.generatingHosts}>
        <Animated.View style={[styles.generatingHostGlow, { transform: [{ scale: pulse }] }]}>
          <LinearGradient colors={['#FFD58A', '#EF4F9D', '#40104D']} style={styles.generatingHostAvatar}>
            <Text style={styles.generatingHostInitial}>A</Text>
          </LinearGradient>
        </Animated.View>
        <View style={styles.generatingWaveCard}>
          <SoundWaveIcon isActive colors={{ accent: accentColor }} />
        </View>
        <Animated.View style={[styles.generatingHostGlow, { transform: [{ scale: pulse }] }]}>
          <LinearGradient colors={['#C8ACFF', '#6543A1', '#281248']} style={styles.generatingHostAvatar}>
            <Text style={styles.generatingHostInitial}>A</Text>
          </LinearGradient>
        </Animated.View>
      </View>
      <View style={styles.generatingHostNames}>
        <Text style={[styles.generatingHostName, { color: colors.textSecondary }]}>{t('podcast.hostAnanya', 'ANANYA')}</Text>
        <Text style={[styles.generatingHostName, { color: colors.textSecondary }]}>{t('podcast.hostArjun', 'ARJUN')}</Text>
      </View>
      <Text style={[styles.generatingTitle, { color: colors.text }]}>
        {t('podcast.generatingTitle', 'Creating your podcast')}
      </Text>
      <View style={[styles.generatingStatusCard, { borderColor: `${accentColor}55` }]}>
        <View style={[styles.generatingStatusIcon, { backgroundColor: `${accentColor}22` }]}>
          <Ionicons name={stage.icon} size={18} color={accentColor} />
        </View>
        <View style={styles.generatingStatusCopy}>
          <Text style={[styles.generatingStatusText, { color: colors.text }]}>
            {t(`podcast.generationStages.${stage.key}`, stage.fallback)}
          </Text>
          <Text style={[styles.generatingStageHint, { color: colors.textSecondary }]}>
            {t('podcast.stagesMayOverlap', 'Creation steps may overlap')}
          </Text>
        </View>
        <Text style={[styles.generatingElapsed, { color: accentColor }]}>{elapsed}</Text>
      </View>
      <View style={styles.generatingStageDots}>
        {GENERATION_STAGES.slice(0, 6).map((item, index) => (
          <View
            key={item.key}
            style={[
              styles.generatingStageDot,
              { backgroundColor: index <= Math.min(stageIndex, 5) ? accentColor : `${accentColor}2A` },
              index === Math.min(stageIndex, 5) && styles.generatingStageDotCurrent,
            ]}
          />
        ))}
      </View>
      <Text style={[styles.generatingSubtitle, { color: colors.textSecondary }]}>
        {elapsedSeconds < 300
          ? t('podcast.generatingSubtitle', 'Usually ready in 3–4 minutes. We’ll begin playing it as soon as it is ready.')
          : t('podcast.generatingLonger', 'Longer readings can take a little more time. No action is needed.')}
      </Text>
      <View style={[styles.generatingLeaveNote, { backgroundColor: colors.surface || 'rgba(255,255,255,0.1)' }]}>
        <Ionicons name="information-circle-outline" size={16} color={colors.textSecondary} />
        <Text style={[styles.generatingLeaveText, { color: colors.textSecondary }]}>
          {t('podcast.canReturnLater', 'You can close this window and return to the podcast icon shortly.')}
        </Text>
      </View>
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
  viewMode = 'listen',
  onViewModeChange,
  visualManifest = null,
  isVisualLoading = false,
  visualError = '',
}) {
  const { t } = useTranslation();
  const { theme, colors } = useTheme();
  const isDark = theme === 'dark';
  const trackWidthRef = useRef(MODAL_WIDTH - 48);
  const isGenerating = mode === 'generating';
  const isPlaying = mode === 'playing';
  const isPaused = mode === 'paused';
  const isWatchMode = viewMode === 'watch';
  const generationStartedAtRef = useRef(null);
  if (isGenerating && generationStartedAtRef.current == null) {
    generationStartedAtRef.current = Date.now();
  } else if (!isGenerating) {
    generationStartedAtRef.current = null;
  }

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
        <View style={[styles.outer, isWatchMode && styles.outerWatch]} pointerEvents="box-none">
          <View style={styles.modalCard} pointerEvents="box-none">
            <LinearGradient colors={gradientColors} style={[styles.gradient, isWatchMode && styles.gradientWatch]}>
              <TouchableOpacity
                style={styles.closeButton}
                onPress={onClose}
                hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
              >
                <Ionicons name="close" size={26} color={colors.textSecondary || '#999'} />
              </TouchableOpacity>

              {isGenerating && (
                <PodcastGeneratingExperience
                  accentColor={accentColor}
                  colors={colors}
                  t={t}
                  startedAt={generationStartedAtRef.current || Date.now()}
                />
              )}

              {(isPlaying || isPaused) && (
                <View style={styles.playerContent}>
                  <View style={[styles.modeTabs, { backgroundColor: colors.surface || 'rgba(255,255,255,0.12)' }]}>
                    <TouchableOpacity
                      style={[styles.modeTab, !isWatchMode && { backgroundColor: accentColor }]}
                      onPress={() => onViewModeChange?.('listen')}
                    >
                      <Ionicons name="headset-outline" size={17} color={!isWatchMode ? '#fff' : colors.textSecondary} />
                      <Text style={[styles.modeTabText, { color: !isWatchMode ? '#fff' : colors.textSecondary }]}>
                        {t('podcast.listen', 'Listen')}
                      </Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.modeTab, isWatchMode && { backgroundColor: accentColor }]}
                      onPress={() => onViewModeChange?.('watch')}
                    >
                      <Ionicons name="play-circle-outline" size={18} color={isWatchMode ? '#fff' : colors.textSecondary} />
                      <Text style={[styles.modeTabText, { color: isWatchMode ? '#fff' : colors.textSecondary }]}>
                        {t('podcast.watch', 'Watch')}
                      </Text>
                    </TouchableOpacity>
                  </View>

                  {isWatchMode ? (
                    isVisualLoading ? (
                      <LinearGradient colors={['#270640', '#63215E', '#F07838']} style={[styles.visualLoading, COMPACT_WATCH && styles.visualLoadingCompact]}>
                        <ActivityIndicator size="large" color="#FFD58A" />
                        <Text style={styles.visualLoadingTitle}>{t('podcast.preparingVisuals', 'Preparing your visual podcast')}</Text>
                        <Text style={styles.visualLoadingText}>{t('podcast.preparingVisualsBody', 'Your audio continues while AstroRoshni builds the visual story.')}</Text>
                      </LinearGradient>
                    ) : visualManifest ? (
                      <PodcastVisualStage
                        manifest={visualManifest}
                        positionMillis={positionMillis}
                        durationMillis={durationMillis}
                        paused={isPaused}
                        compact={COMPACT_WATCH}
                      />
                    ) : (
                      <LinearGradient colors={['#270640', '#63215E', '#F07838']} style={[styles.visualLoading, COMPACT_WATCH && styles.visualLoadingCompact]}>
                        <Ionicons name="sparkles-outline" size={38} color="#FFD58A" />
                        <Text style={styles.visualLoadingTitle}>{t('podcast.visualUnavailable', 'Visual story unavailable')}</Text>
                        <Text style={styles.visualLoadingText}>{visualError || t('podcast.visualUnavailableBody', 'You can continue listening to the podcast.')}</Text>
                      </LinearGradient>
                    )
                  ) : (
                    <View style={styles.waveRow}>
                      <SoundWaveIcon isActive={isPlaying} colors={colors} />
                      <Text style={[styles.playingLabel, { color: colors.textSecondary }]}>
                        {isPlaying ? t('podcast.playing', 'Playing') : t('podcast.paused', 'Paused')}
                      </Text>
                    </View>
                  )}

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

                  <View style={[styles.controlsRow, isWatchMode && styles.controlsRowWatch]}>
                    <TouchableOpacity
                      style={[styles.controlBtn, isWatchMode && styles.controlBtnWatch, { backgroundColor: colors.surface || 'rgba(255,255,255,0.15)' }]}
                      onPress={onStop}
                    >
                      <Ionicons name="stop" size={28} color={colors.text} />
                      <Text style={[styles.controlLabel, { color: colors.text }]}>{t('podcast.stop', 'Stop')}</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.controlBtnMain, isWatchMode && styles.controlBtnMainWatch, { backgroundColor: accentColor }]}
                      onPress={isPlaying ? onPause : onResume}
                    >
                      <Ionicons name={isPlaying ? 'pause' : 'play'} size={36} color="#fff" />
                      <Text style={[styles.controlLabelMain, { color: '#fff' }]}>
                        {isPlaying ? t('podcast.pause', 'Pause') : t('podcast.play', 'Play')}
                      </Text>
                    </TouchableOpacity>
                    {onShare && (
                      <TouchableOpacity
                        style={[styles.controlBtn, isWatchMode && styles.controlBtnWatch, { backgroundColor: colors.surface || 'rgba(255,255,255,0.15)' }]}
                        onPress={onShare}
                      >
                        <Ionicons name="share-outline" size={28} color={colors.text} />
                        <Text style={[styles.controlLabel, { color: colors.text }]}>{t('podcast.share', 'Share')}</Text>
                      </TouchableOpacity>
                    )}
                  </View>

                  {onSpeedChange && !isWatchMode && (
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

                  {showAmbienceToggle && !isWatchMode && (
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
  outerWatch: {
    width: Math.min(SCREEN_WIDTH * 0.95, 420),
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
  gradientWatch: {
    paddingHorizontal: 14,
    paddingBottom: 18,
  },
  closeButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    zIndex: 2,
  },
  generatingContent: {
    alignItems: 'center',
    paddingTop: 4,
    paddingBottom: 8,
  },
  generatingEyebrow: {
    color: '#D9B7C8',
    fontSize: 8,
    fontWeight: '900',
    letterSpacing: 1.8,
    marginBottom: 18,
  },
  generatingHosts: {
    width: 224,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  generatingHostGlow: {
    width: 58,
    height: 58,
    borderRadius: 29,
    padding: 3,
    backgroundColor: 'rgba(255, 229, 164, 0.2)',
    shadowColor: '#FFD58A',
    shadowOpacity: 0.65,
    shadowRadius: 13,
    shadowOffset: { width: 0, height: 0 },
    elevation: 7,
  },
  generatingHostAvatar: {
    flex: 1,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.55)',
  },
  generatingHostInitial: {
    color: '#FFF8E8',
    fontFamily: 'serif',
    fontSize: 24,
    fontWeight: '800',
  },
  generatingWaveCard: {
    width: 78,
    height: 45,
    borderRadius: 23,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(31, 3, 47, 0.28)',
    borderWidth: 1,
    borderColor: 'rgba(255, 213, 138, 0.18)',
  },
  generatingHostNames: {
    width: 224,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 4,
    marginTop: 8,
  },
  generatingHostName: {
    width: 56,
    color: '#EBCFD8',
    fontSize: 7,
    fontWeight: '900',
    letterSpacing: 1,
    textAlign: 'center',
  },
  generatingTitle: {
    fontFamily: 'serif',
    fontSize: 24,
    fontWeight: '700',
    marginTop: 15,
    marginBottom: 12,
    textAlign: 'center',
  },
  generatingStatusCard: {
    width: '100%',
    minHeight: 62,
    borderRadius: 15,
    borderWidth: 1,
    backgroundColor: 'rgba(33, 3, 50, 0.16)',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 11,
  },
  generatingStatusIcon: {
    width: 34,
    height: 34,
    borderRadius: 17,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 9,
  },
  generatingStatusCopy: {
    flex: 1,
  },
  generatingStatusText: {
    fontSize: 12,
    lineHeight: 16,
    fontWeight: '800',
  },
  generatingStageHint: {
    fontSize: 8,
    marginTop: 2,
  },
  generatingElapsed: {
    fontSize: 11,
    fontWeight: '900',
    fontVariant: ['tabular-nums'],
    marginLeft: 7,
  },
  generatingStageDots: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 12,
  },
  generatingStageDot: {
    width: 18,
    height: 3,
    borderRadius: 2,
  },
  generatingStageDotCurrent: {
    width: 28,
  },
  generatingLeaveNote: {
    width: '100%',
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 10,
    paddingVertical: 8,
    marginTop: 12,
  },
  generatingLeaveText: {
    flex: 1,
    fontSize: 9,
    lineHeight: 13,
    marginLeft: 5,
  },
  generatingSubtitle: {
    fontSize: 11,
    textAlign: 'center',
    lineHeight: 16,
    paddingHorizontal: 8,
    marginTop: 10,
  },
  playerContent: {
    alignItems: 'center',
  },
  modeTabs: {
    flexDirection: 'row',
    width: '100%',
    borderRadius: 16,
    padding: 4,
    marginBottom: 14,
  },
  modeTab: {
    flex: 1,
    minHeight: 38,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 7,
  },
  modeTabText: {
    fontSize: 13,
    fontWeight: '700',
  },
  visualLoading: {
    width: '100%',
    height: 470,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 34,
  },
  visualLoadingCompact: {
    height: 380,
  },
  visualLoadingTitle: {
    color: '#FFF8ED',
    fontSize: 19,
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 18,
  },
  visualLoadingText: {
    color: '#F7DDD1',
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
    marginTop: 8,
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
  controlsRowWatch: {
    gap: 20,
  },
  controlBtn: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  controlBtnWatch: {
    width: 60,
    height: 60,
    borderRadius: 30,
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
  controlBtnMainWatch: {
    width: 72,
    height: 72,
    borderRadius: 36,
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
