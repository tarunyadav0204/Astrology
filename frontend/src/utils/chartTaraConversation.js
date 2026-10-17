// This override belongs only to chart-sheet conversations. Do not persist it as
// the main chat's selected tier or change the server's Instant default.
export function chartTaraRequest({ sessionId, pending, birthData, queryContext, language = 'english' }) {
  return {
    session_id: sessionId,
    client_request_id: pending.id,
    question: pending.question,
    language,
    birth_details: {
      ...birthData,
      id: birthData.chart_id ?? birthData.birth_chart_id ?? birthData.id ?? null,
      date: typeof birthData.date === 'string' ? birthData.date.split('T')[0] : birthData.date,
      time: typeof birthData.time === 'string' && birthData.time.includes('T') ? birthData.time.split('T')[1].slice(0, 8) : birthData.time,
      latitude: Number(birthData.latitude),
      longitude: Number(birthData.longitude),
    },
    native_name: birthData.name,
    chat_tier: 'instant',
    instant_path: 'calculator_first',
    premium_analysis: false,
    partnership_mode: false,
    response_style: 'simple',
    subject_gate_override: 'selected_chart_only',
    query_context: { ...queryContext, instant_path: 'calculator_first', viewed_chart: pending.chartType, source: 'chart_sheet' },
  };
}
