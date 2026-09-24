import React, { useRef, useState } from 'react';
import { PanResponder, Platform, StyleSheet, View } from 'react-native';
import { NativeViewGestureHandler } from 'react-native-gesture-handler';
import Svg, { Circle, Path } from 'react-native-svg';

const clamp01 = (value) => Math.min(1, Math.max(0, value));

const pointFromEvent = (event, size) => {
  const native = event.nativeEvent || {};
  const node = event.currentTarget;
  const rect = node?.getBoundingClientRect?.();
  const width = size.width || rect?.width || 1;
  const height = size.height || rect?.height || 1;
  let x = native.locationX;
  let y = native.locationY;
  const clientX = native.clientX ?? native.pageX;
  const clientY = native.clientY ?? native.pageY;
  if (rect && Number.isFinite(clientX) && Number.isFinite(clientY)) {
    const localX = clientX - rect.left;
    const localY = clientY - rect.top;
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      x = localX;
      y = localY;
    }
  }
  return [clamp01((x || 0) / width), clamp01((y || 0) / height)];
};

const arrowHead = (points, width, height) => {
  if (points.length < 2) return '';
  const start = points[0];
  const end = points[points.length - 1];
  const x1 = start[0] * width;
  const y1 = start[1] * height;
  const x2 = end[0] * width;
  const y2 = end[1] * height;
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const length = 12;
  const spread = Math.PI / 7;
  const leftX = x2 - length * Math.cos(angle - spread);
  const leftY = y2 - length * Math.sin(angle - spread);
  const rightX = x2 - length * Math.cos(angle + spread);
  const rightY = y2 - length * Math.sin(angle + spread);
  return `M ${x2} ${y2} L ${leftX} ${leftY} L ${rightX} ${rightY} Z`;
};

const strokePath = (points, width, height) => points
  .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point[0] * width} ${point[1] * height}`)
  .join(' ');

const ChartDrawingLayer = ({ strokes, color, tool = 'pen', enabled, onChange }) => {
  const [size, setSize] = useState({ width: 0, height: 0 });
  const sizeRef = useRef(size);
  const colorRef = useRef(color);
  const onChangeRef = useRef(onChange);
  const enabledRef = useRef(enabled);
  const activeRef = useRef(null);
  const toolRef = useRef(tool);
  sizeRef.current = size;
  colorRef.current = color;
  toolRef.current = tool;
  onChangeRef.current = onChange;
  enabledRef.current = enabled;

  const begin = (event) => {
    if (!enabledRef.current) return;
    event.preventDefault?.();
    const stroke = {
      color: colorRef.current,
      tool: toolRef.current,
      points: [pointFromEvent(event, sizeRef.current)],
    };
    activeRef.current = stroke;
    onChangeRef.current((prev) => [...prev, stroke]);
  };

  const extend = (event) => {
    const active = activeRef.current;
    if (!active || !enabledRef.current) return;
    event.preventDefault?.();
    const point = pointFromEvent(event, sizeRef.current);
    if (active.tool === 'arrow') {
      active.points = [active.points[0], point];
    } else {
      active.points.push(point);
    }
    const points = active.points.slice();
    onChangeRef.current((prev) => {
      if (!prev.length) return prev;
      const next = prev.slice();
      next[next.length - 1] = { color: active.color, tool: active.tool, points };
      return next;
    });
  };

  const finish = () => {
    activeRef.current = null;
  };

  const panResponder = useRef(PanResponder.create({
    onStartShouldSetPanResponderCapture: () => enabledRef.current,
    onMoveShouldSetPanResponderCapture: () => enabledRef.current,
    onStartShouldSetPanResponder: () => enabledRef.current,
    onMoveShouldSetPanResponder: () => enabledRef.current,
    onPanResponderTerminationRequest: () => false,
    onPanResponderGrant: begin,
    onPanResponderMove: extend,
    onPanResponderRelease: finish,
    onPanResponderTerminate: finish,
  })).current;

  const width = size.width || 1;
  const height = size.height || 1;

  const layer = (
    <View
      style={[styles.layer, enabled && styles.captureTouch]}
      pointerEvents={enabled ? 'box-only' : 'none'}
      collapsable={false}
      onLayout={(event) => {
        const nextWidth = event.nativeEvent.layout.width;
        const nextHeight = event.nativeEvent.layout.height;
        if (nextWidth > 0 && nextHeight > 0) {
          const next = { width: nextWidth, height: nextHeight };
          sizeRef.current = next;
          setSize((prev) => (prev.width === nextWidth && prev.height === nextHeight ? prev : next));
        }
      }}
      {...(enabled ? panResponder.panHandlers : {})}
    >
      <Svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        pointerEvents="none"
      >
        {strokes.map((stroke, index) => {
          const d = strokePath(stroke.points, width, height);
          if (!d) return null;
          const last = stroke.points[stroke.points.length - 1];
          return (
            <React.Fragment key={`stroke-${index}`}>
              <Path
                d={d}
                stroke={stroke.color}
                strokeWidth={2.5}
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
              />
              {stroke.tool === 'arrow' ? (
                <Path d={arrowHead(stroke.points, width, height)} fill={stroke.color} />
              ) : last ? (
                <Circle
                  cx={last[0] * width}
                  cy={last[1] * height}
                  r={1.4}
                  fill={stroke.color}
                />
              ) : null}
            </React.Fragment>
          );
        })}
      </Svg>
    </View>
  );

  if (Platform.OS === 'web' || !enabled) return layer;
  return (
    <NativeViewGestureHandler shouldActivateOnStart disallowInterruption>
      {layer}
    </NativeViewGestureHandler>
  );
};

const styles = StyleSheet.create({
  layer: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 20,
    backgroundColor: 'transparent',
  },
  captureTouch: Platform.OS === 'web' ? { touchAction: 'none', cursor: 'crosshair' } : null,
});

export default ChartDrawingLayer;
