import React from 'react';
import Svg, { Path, Rect } from 'react-native-svg';

export default function ReelIcon({ size = 20, color = 'currentColor' }) {
  return <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" accessible={false}>
    <Rect x={3} y={3} width={18} height={18} rx={4} />
    <Path d="M3 8h18M8 3l4 5M15 3l4 5" />
    <Path d="m10 11 6 3.5-6 3.5z" fill={color} stroke="none" />
  </Svg>;
}
