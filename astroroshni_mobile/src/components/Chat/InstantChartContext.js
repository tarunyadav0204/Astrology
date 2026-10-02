import React from 'react';
import { View, Text } from 'react-native';
import { useInstantChartRows } from '../../utils/useInstantChartRows';

export default function InstantChartContext({ preview, active, color, startedAt }) {
    const rows = useInstantChartRows(preview, active);
    if (!rows.length) return null;
    return (
        <View style={{ marginBottom: 14, padding: 10, borderLeftWidth: 2, borderLeftColor: color, borderRadius: 6, backgroundColor: 'rgba(128,128,128,0.06)' }}>
            <Text style={{ color, fontSize: 11, opacity: 0.7, marginBottom: 7, writingDirection: preview.direction || 'auto' }}>◇ {preview.title}</Text>
            {rows.map(row => <Text key={row.key} onLayout={__DEV__ && startedAt ? () => console.info('[InstantChatTiming]', JSON.stringify({ phase: 'context-layout', row: row.key, elapsedMs: Date.now() - startedAt })) : undefined} style={{ color, fontSize: 13, lineHeight: 23, writingDirection: preview.direction || 'auto' }}>{row.text}</Text>)}
            {preview.as_of ? <Text style={{ color, fontSize: 10, opacity: 0.6 }}>{preview.as_of}</Text> : null}
        </View>
    );
}
