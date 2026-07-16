/**
 * Scroll helpers for Expo Web vs native.
 *
 * - Horizontal lists: RN ScrollView on web (RNGH wrapper breaks device-mode touch).
 * - Vertical Home feed on web: RN ScrollView inside a fixed viewport shell
 *   so bottom tabs can stay pinned (see webShell.css).
 * - Native (Play/iOS): gesture-handler ScrollView unchanged.
 */
import React from 'react';
import { Platform, ScrollView as RNScrollView } from 'react-native';
import { ScrollView as GHScrollView } from 'react-native-gesture-handler';

const AppScrollView = Platform.OS === 'web' ? RNScrollView : GHScrollView;

/**
 * Main vertical page body. Web uses a real ScrollView in a height-locked shell;
 * native keeps gesture-handler ScrollView.
 */
export function VerticalPageScroll({
  style,
  contentContainerStyle,
  children,
  onScroll,
  scrollEventThrottle,
  showsVerticalScrollIndicator,
  nestedScrollEnabled,
  ...rest
}) {
  if (Platform.OS === 'web') {
    return (
      <RNScrollView
        style={[
          {
            flex: 1,
            minHeight: 0,
            // RN Web: make the node the scrollport (device-mode touch).
            overflow: 'auto',
            touchAction: 'pan-y',
          },
          style,
        ]}
        contentContainerStyle={contentContainerStyle}
        onScroll={onScroll}
        scrollEventThrottle={scrollEventThrottle}
        showsVerticalScrollIndicator={showsVerticalScrollIndicator}
        nestedScrollEnabled={nestedScrollEnabled}
        {...rest}
      >
        {children}
      </RNScrollView>
    );
  }
  return (
    <GHScrollView
      style={style}
      contentContainerStyle={contentContainerStyle}
      onScroll={onScroll}
      scrollEventThrottle={scrollEventThrottle}
      showsVerticalScrollIndicator={showsVerticalScrollIndicator}
      nestedScrollEnabled={nestedScrollEnabled}
      {...rest}
    >
      {children}
    </GHScrollView>
  );
}

export default AppScrollView;
