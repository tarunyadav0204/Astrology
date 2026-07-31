import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

export const WHEEL_ITEM_HEIGHT = 44;
export const WHEEL_VISIBLE_ROWS = 5;
const WHEEL_PAD = WHEEL_ITEM_HEIGHT * Math.floor(WHEEL_VISIBLE_ROWS / 2);

/**
 * iOS-style scroll wheel for PWA (native DateTimePicker/Picker are not spinners on web).
 */
export default function WebWheelSpinner({ options, value, onChange, textColor, mutedColor }) {
  const scrollRef = useRef(null);
  const isUserScrollingRef = useRef(false);
  const isProgrammaticRef = useRef(false);
  const settleTimerRef = useRef(null);
  const latestOffsetRef = useRef(0);
  const selectedIndex = Math.max(
    0,
    options.findIndex((opt) => String(opt.value) === String(value)),
  );
  const [visualIndex, setVisualIndex] = useState(selectedIndex);

  const indexFromOffset = useCallback((y) => Math.max(
    0,
    Math.min(options.length - 1, Math.round(y / WHEEL_ITEM_HEIGHT)),
  ), [options.length]);

  const scrollToIndex = useCallback((index, animated) => {
    const clamped = Math.max(0, Math.min(options.length - 1, index));
    isProgrammaticRef.current = true;
    latestOffsetRef.current = clamped * WHEEL_ITEM_HEIGHT;
    scrollRef.current?.scrollTo({
      y: latestOffsetRef.current,
      animated: !!animated,
    });
    if (settleTimerRef.current) clearTimeout(settleTimerRef.current);
    settleTimerRef.current = setTimeout(() => {
      isProgrammaticRef.current = false;
    }, animated ? 220 : 50);
  }, [options.length]);

  useEffect(() => {
    if (isUserScrollingRef.current) return undefined;
    setVisualIndex(selectedIndex);
    const id = requestAnimationFrame(() => scrollToIndex(selectedIndex, false));
    return () => cancelAnimationFrame(id);
  }, [selectedIndex, options.length, scrollToIndex]);

  useEffect(() => () => {
    if (settleTimerRef.current) clearTimeout(settleTimerRef.current);
  }, []);

  const commitIndex = useCallback((index) => {
    const clamped = Math.max(0, Math.min(options.length - 1, index));
    setVisualIndex(clamped);
    const next = options[clamped];
    if (next && String(next.value) !== String(value)) {
      onChange(next.value);
    }
    scrollToIndex(clamped, true);
  }, [onChange, options, scrollToIndex, value]);

  const scheduleCommitFromOffset = useCallback((y) => {
    latestOffsetRef.current = y;
    const index = indexFromOffset(y);
    setVisualIndex(index);
    if (settleTimerRef.current) clearTimeout(settleTimerRef.current);
    settleTimerRef.current = setTimeout(() => {
      isUserScrollingRef.current = false;
      isProgrammaticRef.current = false;
      commitIndex(indexFromOffset(latestOffsetRef.current));
    }, 140);
  }, [commitIndex, indexFromOffset]);

  return (
    <View style={styles.webWheelColumn}>
      <View
        pointerEvents="none"
        style={[styles.webWheelHighlight, { borderColor: mutedColor }]}
      />
      <ScrollView
        ref={scrollRef}
        showsVerticalScrollIndicator={false}
        snapToInterval={WHEEL_ITEM_HEIGHT}
        snapToAlignment="start"
        decelerationRate="fast"
        disableIntervalMomentum
        nestedScrollEnabled
        scrollEventThrottle={16}
        onScrollBeginDrag={() => {
          isUserScrollingRef.current = true;
          isProgrammaticRef.current = false;
        }}
        onScroll={(event) => {
          const y = event.nativeEvent.contentOffset.y;
          latestOffsetRef.current = y;
          const index = indexFromOffset(y);
          if (index !== visualIndex) setVisualIndex(index);
          if (isProgrammaticRef.current) return;
          isUserScrollingRef.current = true;
          scheduleCommitFromOffset(y);
        }}
        onMomentumScrollEnd={(event) => {
          if (isProgrammaticRef.current) return;
          scheduleCommitFromOffset(event.nativeEvent.contentOffset.y);
        }}
        onScrollEndDrag={(event) => {
          if (isProgrammaticRef.current) return;
          scheduleCommitFromOffset(event.nativeEvent.contentOffset.y);
        }}
        contentContainerStyle={{ paddingVertical: WHEEL_PAD }}
        style={styles.webWheelScroll}
      >
        {options.map((opt, index) => {
          const active = index === visualIndex;
          return (
            <TouchableOpacity
              key={`${opt.value}-${opt.label}`}
              activeOpacity={0.7}
              onPress={() => {
                isUserScrollingRef.current = false;
                isProgrammaticRef.current = false;
                commitIndex(index);
              }}
              style={styles.webWheelItem}
            >
              <Text
                style={[
                  styles.webWheelItemText,
                  {
                    color: textColor,
                    opacity: active ? 1 : 0.35,
                    fontWeight: active ? '700' : '500',
                    fontSize: active ? 20 : 16,
                  },
                ]}
              >
                {opt.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  webWheelColumn: {
    flex: 1,
    height: WHEEL_ITEM_HEIGHT * WHEEL_VISIBLE_ROWS,
    overflow: 'hidden',
    position: 'relative',
  },
  webWheelScroll: {
    flex: 1,
  },
  webWheelItem: {
    height: WHEEL_ITEM_HEIGHT,
    alignItems: 'center',
    justifyContent: 'center',
  },
  webWheelItemText: {
    textAlign: 'center',
  },
  webWheelHighlight: {
    position: 'absolute',
    left: 4,
    right: 4,
    top: WHEEL_ITEM_HEIGHT * 2,
    height: WHEEL_ITEM_HEIGHT,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderRadius: 8,
    zIndex: 2,
  },
});
