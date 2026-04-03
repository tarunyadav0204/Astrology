/**
 * Shape birth_details for /api/chat-v2/ask exactly like mobile ChatScreen.js
 * (sendChatRequestWithRetry). Prevents ascendant/house errors when date/time
 * arrive as ISO strings — ChartCalculator splits on ":" and expects HH:MM.
 */
export function normalizeBirthDetailsForChat(raw) {
    if (!raw) return null;

    const date =
        typeof raw.date === 'string'
            ? raw.date.split('T')[0]
            : raw.date != null
              ? String(raw.date).split('T')[0]
              : '';

    let time = raw.time;
    if (typeof time === 'string' && time.includes('T')) {
        const afterT = time.split('T')[1];
        time = afterT ? afterT.slice(0, 5) : time;
    } else if (time != null && typeof time !== 'string') {
        time = String(time);
    }

    const lat = parseFloat(raw.latitude);
    const lon = parseFloat(raw.longitude);

    return {
        name: raw.name,
        date,
        time: time || '',
        latitude: Number.isFinite(lat) ? lat : NaN,
        longitude: Number.isFinite(lon) ? lon : NaN,
        place: raw.place || '',
        gender: raw.gender || '',
    };
}
