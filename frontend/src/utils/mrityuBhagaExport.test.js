import { buildMrityuBhagaReport, ordinal } from './mrityuBhagaExport';
const data = {
  schema_version: 'v1',
  natal: {
    points: [],
    affected_count: 0,
    source: 'Classical table',
    degree_semantics: 'Ordinal'
  },
  range: {
    start_at: '2026-01-01',
    end_at: '2027-01-01',
    timezone: 'UTC'
  },
  audit: {
    ayanamsha: 'lahiri',
    node_type: 'mean',
    house_system: 'whole_sign',
    sources: [],
    limits: ['Endpoint samples only']
  },
  dasha_activations: [],
  calendar_calculated: false
};
test('print report preserves Unicode and escapes all user-authored text', () => {
  const html = buildMrityuBhagaReport(data, {
    name: 'राम <script>alert(1)</script>',
    date: '1990-01-01',
    time: '12:00:42'
  }, {}, []);
  expect(html).toContain('राम &lt;script&gt;');
  expect(html).not.toContain('<script>');
  expect(html).toContain('12:00:42');
  expect(html).toContain('Transit calendar has not been calculated');
  expect(html).toContain('Endpoint samples only');
  expect(html).toContain('All checked points');
});

test('aspect labels use readable ordinal numbers',()=>{expect([1,2,3,7,11,12,13,21].map(ordinal)).toEqual(['1st','2nd','3rd','7th','11th','12th','13th','21st']);});
