const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../src/utils/instantProgress.js'), 'utf8');
const progress = import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);

test('calculator-only polls populate the loader without dismissing it', async () => {
  const { applyVerifiedCalculationProgress, applyInstantProgress } = await progress;
  const row = { isTyping: true, content: '', calculationTrace: [] };
  const updates = [{ id: 'panchang', type: 'calculation', text: 'Checking Panchang', detail: 'Tomorrow' }];
  const updated = applyInstantProgress(applyVerifiedCalculationProgress(row, updates), { partial_content: '', replace: true });
  assert.equal(updated.isTyping, true);
  assert.equal(updated.content, '');
  assert.deepEqual(updated.calculationTrace, [{ id: 'panchang', title: 'Checking Panchang', detail: 'Tomorrow' }]);
  assert.equal(applyVerifiedCalculationProgress(updated, updates), updated);
  assert.equal(applyVerifiedCalculationProgress(updated, undefined), updated);
  const answer = applyInstantProgress(updated, { partial_content: 'Your answer', replace: true });
  assert.equal(answer.isTyping, false);
  assert.equal(answer.instantStreaming, true);
  assert.deepEqual(answer.calculationTrace, updated.calculationTrace);
});

test('progress ignores non-calculation updates and completed answers', async () => {
  const { applyVerifiedCalculationProgress } = await progress;
  const row = { isTyping: true, calculationTrace: [] };
  assert.equal(applyVerifiedCalculationProgress(row, [{ type: 'insight', text: 'Insight' }, { type: 'calculation', text: '' }]), row);
  const completed = { isTyping: false, content: 'Done' };
  assert.equal(applyVerifiedCalculationProgress(completed, [{ type: 'calculation', text: 'Late update' }]), completed);
});
