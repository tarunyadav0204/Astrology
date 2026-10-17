import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
const source = await readFile(new URL('../src/utils/chartTaraConversation.js', import.meta.url), 'utf8');
const { chartTaraRequest } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const birth = { id: 7, name: 'Test Native', date: '1990-01-01T00:00:00', time: '12:30:45', latitude: '28.6', longitude: '77.2', calculation_profile: { ayanamsha: 'lahiri' } };
test('chart sheet explicitly requests calculator-first Instant and preserves selected chart inputs', () => {
  const body = chartTaraRequest({ sessionId: 'chart-session', pending: { id: 'turn-1', question: 'My career?', chartType: 'navamsa' }, birthData: birth, queryContext: { client_now_iso: '2026-10-17T12:00:00Z' } });
  assert.equal(body.instant_path, 'calculator_first');
  assert.equal(body.query_context.instant_path, 'calculator_first');
  assert.equal(body.chat_tier, 'instant');
  assert.equal(body.query_context.viewed_chart, 'navamsa');
  assert.equal(body.subject_gate_override, 'selected_chart_only');
  assert.equal(body.birth_details.date, '1990-01-01');
  assert.equal(body.birth_details.latitude, 28.6);
  assert.deepEqual(body.birth_details.calculation_profile, birth.calculation_profile);
  assert.equal(body.premium_analysis, false);
  assert.equal(body.partnership_mode, false);
  assert.equal(birth.date, '1990-01-01T00:00:00');
});
test('retry preserves idempotency key and question context; next chart question uses new viewed chart', () => {
  const pending = { id: 'turn-1', question: 'My career?', chartType: 'lagna' };
  const build = () => chartTaraRequest({ sessionId: 'chart-session', pending, birthData: birth, queryContext: {} });
  assert.deepEqual(build(), build());
  const followup = chartTaraRequest({ sessionId: 'chart-session', pending: { id: 'turn-2', question: 'And this chart?', chartType: 'navamsa' }, birthData: birth, queryContext: {} });
  assert.equal(followup.session_id, build().session_id);
  assert.equal(followup.query_context.viewed_chart, 'navamsa');
  assert.notEqual(followup.client_request_id, build().client_request_id);
});
