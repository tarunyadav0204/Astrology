import { useEffect, useState } from 'react';

// Only calculated facts are paced. LLM text is published on arrival.
export function useInstantChartRows(preview, active) {
    const rows = preview?.rows || [];
    const [visibleCount, setVisibleCount] = useState(() => active ? 1 : Math.max(1, rows.length));
    useEffect(() => {
        if (!active || visibleCount >= rows.length) return undefined;
        const timer = setTimeout(() => setVisibleCount(count => count + 1), 650);
        return () => clearTimeout(timer);
    }, [active, visibleCount, rows.length]);
    return rows.slice(0, Math.max(1, visibleCount));
}
