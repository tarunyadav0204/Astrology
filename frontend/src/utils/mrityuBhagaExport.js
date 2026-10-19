// Keep this pure report formatter aligned with the mobile formatter. Both
// consume only the calculated workspace response; no astrology is recomputed.
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
})[c]);
const label = value => value === 'Ascendant' ? 'Lagna' : value === 'Mandi' ? 'Gulika / Mandi' : value;
export const ordinal = number => {
  const n = Number(number),
    lastTwo = n % 100;
  return `${n}${lastTwo >= 11 && lastTwo <= 13 ? 'th' : {
    1: 'st',
    2: 'nd',
    3: 'rd'
  }[n % 10] || 'th'}`;
};
const list = values => values?.length ? values.join(', ') : 'None';
const paragraph = text => `<p>${escape(text)}</p>`;
const strength = value => value ? `${value.total_rupas} rupas; ${value.required_percent}% of required strength` : 'Not applicable';
export function buildMrityuBhagaReport(data, birth, notes, events) {
  const facts = rows => rows.map(([key, value]) => `<tr><th>${escape(key)}</th><td>${escape(value)}</td></tr>`).join('');
  return `<!doctype html><html><head><meta charset="utf-8"><title>AstroRoshni Mrityu Bhaga Assessment</title><style>@page{size:A4;margin:18mm}body{font:12px Arial,sans-serif;color:#29131e;line-height:1.5}h1,h2,h3{font-family:Georgia,serif;color:#684f22;break-after:avoid}h1{font-size:26px}h2{font-size:19px}table{width:100%;border-collapse:collapse;margin:12px 0}th,td{text-align:left;padding:7px;border-bottom:1px solid #d9ccaf;vertical-align:top}th{background:#f2ead9;color:#29131e}thead{display:table-header-group}tr{break-inside:avoid}p{white-space:pre-wrap;overflow-wrap:anywhere}article{margin:20px 0;border-bottom:1px solid #d9ccaf;padding-bottom:12px}small{color:#756653}.muted{color:#756653}</style></head><body>
  <h1>AstroRoshni · Mrityu Bhaga</h1>${paragraph(birth.name || 'Selected chart')}${paragraph(`Recorded birth: ${birth.date} ${birth.time}; latitude ${birth.latitude}, longitude ${birth.longitude}`)}${paragraph(data.natal.source)}${paragraph(`${data.audit.ayanamsha}; ${data.audit.node_type} nodes; ${data.audit.house_system}`)}${paragraph(`Range: ${data.range.start_at} → ${data.range.end_at}; birth timezone ${data.range.timezone}. All calendar instants below are UTC. End instants are exclusive.`)}
  <h2>Natal assessment · ${data.natal.affected_count} affected points</h2>${(data.natal.unavailable_points || []).map(p => paragraph(`Assessment incomplete: ${p.point} unavailable. ${p.reason}`)).join('')}
  ${data.natal.points.filter(p => p.is_mrityu_bhaga).map(p => `<article><h3>${escape(label(p.point))} is in Mrityu Bhaga</h3><table>${facts([['Mrityu Bhaga range', `${p.degree_span_start}°–${p.degree_span_end}° ${p.sign_name} (up to, but not including, ${p.degree_span_end}°)`], ['Planet’s position', p.position], ['Natal house', p.house], ['Houses ruled', list(p.houses_ruled)], ['Sign condition / motion', `${p.dignity || 'Not applicable'}; ${p.retrograde === true ? 'Retrograde' : p.retrograde === false ? 'Direct' : 'Not applicable'}`], ['Planet strength (Shadbala)', strength(p.strength)], ['Combustion', p.combustion.applicable ? p.combustion.is_combust ? 'Combust' : 'Not combust' : 'Not applicable'], ['Sign ruler', `${p.dispositor}; ${p.dispositor_position}; ${p.dispositor_dignity || 'Unavailable'}`], ['Sign ruler’s strength', strength(p.dispositor_strength)], ['Nakshatra', `${p.nakshatra || 'Unavailable'}; lord ${p.nakshatra_lord || 'Unavailable'}`], ['Planet connections', list(p.relationships.map(r => `${r.planet}: ${r.relation === 'same_sign' ? 'in the same sign' : `${ordinal(r.aspect_number)} aspect`}`))], ['Other charts', Object.entries(p.divisional_placements).map(([d, v]) => `${d}: ${v.sign}, H${v.house}`).join('; ')], ['Distance from nearest range edge', `${p.distance_to_boundary_degrees.toFixed(2)}°`]])}</table>${paragraph(notes[p.point] || '')}</article>`).join('')}
  <h2>All checked points</h2><table><thead><tr><th>Point</th><th>Birth position</th><th>Mrityu Bhaga range</th><th>Result</th></tr></thead><tbody>${data.natal.points.map(p => `<tr><td>${escape(label(p.point))}</td><td>${escape(p.position)}</td><td>${p.degree_span_start}°–${p.degree_span_end}°</td><td>${p.is_mrityu_bhaga ? 'In Mrityu Bhaga' : 'Not in Mrityu Bhaga'}</td></tr>`).join('')}</tbody></table>
  ${data.birth_time_comparison?.length ? `<h2>Birth-time comparison</h2>${data.birth_time_comparison.map(r => paragraph(`${r.offset_minutes} min: ${list(r.affected_points)} (${r.birth_local})`)).join('')}` : ''}
  <h2>Dasha activation</h2>${data.dasha_activations.map(r => paragraph(`${label(r.point)}: ${r.start_at} → ${r.end_at}; ${r.connections.map(c => `${c.level}: ${c.lord} (${c.relation})`).join('; ')}`)).join('') || paragraph('No matching dasha period in the selected dates.')}
  <h2>Potential transit windows · ${events.length}</h2>${!data.calendar_calculated ? paragraph('Transit calendar has not been calculated for these settings.') : ''}
  ${events.map(r => `<article><h3>${escape(r.planet)} → ${escape(label(r.point))}</h3>${paragraph(`${r.kind === 'natal_mb_span' ? 'Passes through the Mrityu Bhaga range' : r.aspect_number === 1 ? 'Passes over the birth position' : `${ordinal(r.aspect_number)} aspect to the birth position`}; ${r.start_at} → ${r.end_at}`)}${paragraph(`Clipped at range start: ${r.clipped_start ? 'Yes' : 'No'}; clipped at range end: ${r.clipped_end ? 'Yes' : 'No'}`)}${r.exact_passes.map(p => paragraph(`${r.midpoint_only ? 'Span midpoint' : 'Exact contact'}: ${p.at}; ${p.motion}`)).join('')}${!r.exact_passes.length ? paragraph('No exact crossing in this clipped or near-pass window.') : ''}${paragraph(`Other contacting bodies during part of this window: ${list(r.concurrent_transits)}`)}${r.dasha_overlaps.map(d => paragraph(`Dasha overlap ${d.start_at} → ${d.end_at}: ${d.connections.map(c => `${c.level} ${c.lord} (${c.relation})`).join('; ')}`)).join('')}${paragraph(notes[r.id] || '')}</article>`).join('')}
  <h2>Calculation audit</h2>${paragraph(data.natal.degree_semantics)}<table>${facts(Object.entries(data.audit).filter(([key]) => !['sources', 'limits'].includes(key)).map(([key, value]) => [key.replace(/_/g, ' '), Array.isArray(value) ? value.join(', ') : String(value)]))}</table>${data.audit.limits.map(paragraph).join('')}${data.audit.sources.map(s => paragraph(`${s.title}: ${s.url}`)).join('')}${paragraph(`Calculation version: ${data.schema_version}`)}</body></html>`;
}
export function printMrityuBhagaReport(html) {
  // An isolated print document preserves Unicode and selectable text.
  return new Promise((resolve, reject) => {
    const frame = document.createElement('iframe');
    frame.title = 'AstroRoshni assessment PDF';
    frame.style.cssText = 'position:fixed;left:-12000px;top:0;width:820px;height:1100px;border:0';
    const cleanup = () => frame.remove();
    frame.onload = async () => {
      try {
        await frame.contentDocument.fonts?.ready;
        frame.contentWindow.addEventListener('afterprint', cleanup, {
          once: true
        });
        frame.contentWindow.focus();
        frame.contentWindow.print();
        resolve();
      } catch (error) {
        cleanup();
        reject(error);
      } finally {
        setTimeout(cleanup, 120000);
      }
    };
    frame.srcdoc = html;
    document.body.appendChild(frame);
  });
}
