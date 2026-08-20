// Render the backend's explicit user_derivation contract. The app does not
// reinterpret raw evidence records; it shows the same calculated chain used to
// reach the answer.

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const humanize = (value) =>
  String(value || '')
    .replace(/[_.]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^\w/, (c) => c.toUpperCase());

const routerSourceLabel = (source) => {
  const value = String(source || '').toLowerCase();
  if (value === 'primary_intent_llm') return 'Primary interpretation';
  if (value === 'secondary_answer_mode_llm') return 'Secondary interpretation';
  if (value.includes('regex_recovery')) return 'Recovered interpretation';
  if (value.includes('fallback') || value.includes('error')) return 'Fallback routing';
  return humanize(source || 'Unknown');
};

// Internal QA labels. These intentionally stay technical so routing traces are
// comparable across app languages during the pre-launch validation period.
export const ROUTING_DEBUG_LABELS = {
  finalMode: 'FINAL MODE',
  selected: 'SELECTED',
  source: 'SOURCE',
  confidence: 'CONFIDENCE',
  adjusted: 'Mode adjusted after routing',
  fallback: 'Fallback used',
};

export const buildRoutingSummary = (packet) => {
  const route = packet?.routing_decision || packet?.query_plan?.routing_decision || {};
  const selectedMode = route.selected_mode || route.intent_answer_mode || packet?.query_plan?.answer_mode || 'unknown';
  const finalMode = route.final_mode || packet?.query_plan?.answer_mode || selectedMode;
  return {
    finalMode: humanize(finalMode),
    selectedMode: humanize(selectedMode),
    source: routerSourceLabel(route.source),
    confidence: humanize(route.confidence || 'unknown'),
    changed: Boolean(route.post_selection_changed) || String(selectedMode) !== String(finalMode),
    degraded: Boolean(route.degraded),
    category: humanize(route.intent_category || packet?.query_plan?.category || 'general'),
  };
};

const formatDate = (iso) => {
  const raw = String(iso || '').slice(0, 10);
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(raw);
  if (!match) return raw || null;
  const [, year, month, day] = match;
  return `${Number(day)} ${MONTHS[Number(month) - 1] || month} ${year}`;
};

const formatRange = (start, end) => {
  const from = formatDate(start);
  const to = formatDate(end);
  return from && to ? `${from} – ${to}` : from || to || null;
};

const houseText = (row) => {
  if (!row) return null;
  const house = row.house ?? row;
  const meaning = row.meaning;
  return `House ${house}${meaning ? ` — ${meaning}` : ''}`;
};

const unique = (items) => [...new Set(items.filter(Boolean))];

const promiseLine = (status) => {
  if (String(status).startsWith('supported')) return 'The natal chart permits this outcome.';
  if (String(status).startsWith('qualified')) return 'The natal chart permits this outcome conditionally.';
  return 'The natal chart does not establish a strong promise for this outcome.';
};

const compactHouseNote = (line) => {
  const compact = String(line || '')
    // The card title carries the number. Preserve a grammatical reference
    // instead of deleting the object of "supports / affects / pressures".
    .replace(/D1 House \d+/g, 'this house')
    .replace(/\s+/g, ' ')
    .trim();
  return compact.replace(/^this house\b/, 'This house');
};

const buildFrameworkSection = (derivation) => {
  const event = derivation.event || {};
  const houses = event.houses || [];
  if (!houses.length) return null;
  const primary = houses.filter((row) => row.role !== 'supporting').map(houseText);
  const supporting = houses.filter((row) => row.role === 'supporting').map(houseText);
  const lines = [];
  if (primary.length) lines.push(`Primary houses: ${primary.join('; ')}`);
  if (supporting.length) lines.push(`Supporting houses: ${supporting.join('; ')}`);
  return {
    key: 'framework',
    step: 1,
    title: `Astrology used for ${String(event.label || 'this question').toLowerCase()}`,
    lines,
  };
};

const buildPromiseSection = (derivation) => {
  const promise = derivation.natal_promise || {};
  if (!promise.status && !(promise.basis || []).length && !(promise.d1_factors || []).length
    && !(promise.divisional_factors || []).length && !(promise.d1_house_factors || []).length
    && !(promise.divisional_house_factors || []).length) return null;
  const d1Rows = promise.d1_house_factors || [];
  const divisionalRows = promise.divisional_house_factors || [];
  const groups = [{
    key: 'verdict', title: 'Overall promise',
    lines: unique([promiseLine(promise.status), ...(promise.basis || [])]),
  }];
  if (d1Rows.length) groups.push({
    key: 'd1', title: 'D1 · Birth-chart foundation',
    items: d1Rows.map((row) => ({
      title: `House ${row.house}`,
      text: unique([
        row.lord ? `${row.lord} rules it${row.lord_placement_house ? ` from House ${row.lord_placement_house}` : ''}.` : null,
        (row.occupants || []).length ? `Occupants: ${row.occupants.join(', ')}.` : 'No classical occupants; the lord and aspects carry the judgment.',
        (row.aspecting_planets || []).length ? `Aspected by ${row.aspecting_planets.join(', ')}.` : null,
        row.tone ? `Assessment: ${humanize(row.tone)}.` : null,
        [...(row.support_notes || []), ...(row.caution_notes || [])].length
          ? `Key factors: ${unique([...(row.support_notes || []), ...(row.caution_notes || [])]).map(compactHouseNote).join(' ')}` : null,
      ]).join(' '),
    })),
  });
  const byChart = divisionalRows.reduce((result, row) => {
    const chart = row.chart || 'Divisional chart';
    if (!result[chart]) result[chart] = [];
    result[chart].push(row);
    return result;
  }, {});
  Object.entries(byChart).forEach(([chart, rows]) => groups.push({
    key: `division-${chart}`, title: `${chart} · Divisional confirmation`,
    items: rows.map((row) => ({
      title: `House ${row.house}`,
      text: unique([
        row.lord ? `${row.lord} rules it${row.lord_placement_house ? ` from House ${row.lord_placement_house}` : ''}.` : null,
        (row.occupants || []).length ? `Occupants: ${row.occupants.join(', ')}.` : 'No occupants.',
        row.rating ? `Assessment: ${humanize(row.rating)}.` : null,
      ]).join(' '),
    })),
  }));
  if (!d1Rows.length && (promise.d1_factors || []).length) groups.push({
    key: 'd1-legacy', title: 'D1 · Birth-chart foundation', lines: unique(promise.d1_factors),
  });
  if (!divisionalRows.length && (promise.divisional_factors || []).length) groups.push({
    key: 'division-legacy', title: 'Divisional confirmation',
    lines: unique(promise.divisional_factors).map((line) => String(line).replace(/^Divisional confirmation:\s*/i, '')),
  });
  const lines = [];
  if (promise.evidence_complete === false) {
    const hasD1 = (promise.d1_factors || []).length > 0;
    const hasDivisional = (promise.divisional_factors || []).length > 0;
    if (!hasD1 && !hasDivisional) lines.push('Detailed D1 and relevant divisional confirmation were unavailable, so no complete promise judgment is shown.');
    else if (!hasD1) lines.push('Relevant divisional confirmation is available, but the detailed D1 foundation was unavailable; treat the promise judgment as directional.');
    else if (!hasDivisional) lines.push('The detailed D1 foundation is available, but the relevant divisional confirmation was unavailable; treat the promise judgment as directional.');
  }
  return {
    key: 'promise',
    step: 2,
    title: 'What the birth chart promises',
    lines: unique(lines),
    groups,
  };
};

const buildDashaSection = (derivation) => {
  const windows = (derivation.dasha_activation || []).slice(0, 4);
  if (!windows.length) return null;
  const lines = [];
  windows.forEach((window) => {
    const heading = [
      formatRange(window.start, window.end),
      window.chain,
      window.strength ? humanize(window.strength) : null,
    ].filter(Boolean).join(' · ');
    if (heading) lines.push(heading);
    const activated = (window.activated_houses || []).map(houseText).filter(Boolean);
    if (activated.length) lines.push(`Taken together, this dasha chain activates ${activated.join('; ')}.`);
    const carriers = window.carriers || [];
    carriers.forEach((carrier) => {
      const levels = (carrier.dasha_levels || []).join('/');
      const prefix = [levels, carrier.planet].filter(Boolean).join(' ');
      if (carrier.natal_placement_house) {
        lines.push(`${prefix}: natal placement is House ${carrier.natal_placement_house}.`);
      }
      const links = carrier.event_links || [];
      if (links.length) {
        links.forEach((link) => {
          const mechanisms = (link.mechanisms || []).map((mechanism) => ({
            lordship: 'lordship',
            natal_occupation: 'natal occupation',
            natal_aspect: 'natal aspect',
          }[mechanism] || humanize(mechanism))).join(' and ');
          lines.push(`${prefix} activates ${houseText(link)}${mechanisms ? ` through ${mechanisms}` : ''}.`);
        });
      } else {
        const houses = (carrier.natal_event_houses || []).map((house) => `House ${house}`).join(', ');
        if (prefix && houses) lines.push(`${prefix} has natal links to ${houses}.`);
      }
    });
    if (!carriers.length) {
      (window.reasons || []).slice(0, 6).forEach((reason) => lines.push(reason));
    }
  });
  return { key: 'dasha', step: 3, title: 'Why the current period can deliver the result', lines: unique(lines) };
};

const buildTransitSection = (derivation) => {
  const windows = (derivation.transit_confirmation || []).slice(0, 4);
  if (!windows.length) return null;
  const lines = [];
  windows.forEach((window) => {
    const heading = [formatRange(window.start, window.end), window.planet, window.strength ? humanize(window.strength) : null]
      .filter(Boolean)
      .join(' · ');
    if (heading) lines.push(heading);
    if (window.natal_placement_house) {
      lines.push(`Natal ${window.planet} is in House ${window.natal_placement_house}.`);
    }
    (window.delivered_event_houses || []).forEach((delivered) => {
      if (delivered.mechanism === 'transit_occupation') {
        lines.push(`Transit ${window.planet} occupies ${houseText(delivered)}, activating that event area.`);
      } else if (delivered.mechanism === 'transit_aspect') {
        const from = window.transit_native_house ? ` from House ${window.transit_native_house}` : '';
        lines.push(`Transit ${window.planet}${from} aspects ${houseText(delivered)}, activating that event area.`);
      }
    });
    (window.reasons || []).forEach((reason) => lines.push(reason));
    const confirmed = window.confirmed_houses || [];
    if (!(window.delivered_event_houses || []).length && confirmed.length) {
      lines.push(`This transit confirms timing for ${confirmed.map(houseText).join('; ')}; these are event houses, not ${window.planet}'s natal placement.`);
    }
  });
  return { key: 'transits', step: 4, title: 'How current planetary movement confirms timing', lines: unique(lines) };
};

const buildConclusionSection = (derivation) => {
  const conclusion = derivation.conclusion || {};
  const limitations = derivation.limitations || [];
  const lines = [];
  const range = formatRange(conclusion.start, conclusion.end);
  if (range) {
    lines.push(`The strongest supported timing is ${range}${conclusion.chain ? ` during ${conclusion.chain}` : ''}.`);
  } else if (conclusion.direction && conclusion.direction !== 'insufficient_evidence') {
    const promise = derivation.natal_promise || {};
    if (conclusion.direction === 'supported_natal_promise') {
      lines.push(promise.evidence_complete
        ? 'The D1 foundation and relevant divisional chart both support the possibility; timing still requires a separate dasha-and-transit check.'
        : 'The available natal checks lean supportive, but the evidence shown here is not detailed enough to treat that as a complete promise judgment.');
    } else {
      lines.push(`Overall conclusion: ${humanize(conclusion.direction)}.`);
    }
  }
  if (Array.isArray(conclusion.why)) {
    conclusion.why.slice(0, 3).forEach((reason) => lines.push(String(reason)));
  } else if (conclusion.why) {
    String(conclusion.why).split(';').slice(0, 3).forEach((reason) => lines.push(reason.trim()));
  }
  if (limitations.length) {
    lines.push('Timing confidence is limited because one or more required calculation layers were unavailable.');
  }
  if (!lines.length) return null;
  return { key: 'conclusion', step: 5, title: 'What this means for you', lines: unique(lines) };
};

export const buildReadableEvidence = (packet) => {
  const derivation = packet?.user_derivation;
  if (!derivation || typeof derivation !== 'object') {
    return [{
      key: 'legacy',
      step: null,
      title: 'Derivation unavailable',
      lines: ['This saved answer contains the old evidence format. Ask the question again to generate the complete derivation chain.'],
    }];
  }
  const chartReading = derivation.chart_reading;
  if (chartReading && typeof chartReading === 'object') {
    const requested = chartReading.requested_charts || [];
    const sections = [];
    if (requested.length) {
      sections.push({
        key: 'chart-examined',
        title: 'Chart examined',
        lines: [`The ${requested.join(', ')} calculation was used for this reading.`],
      });
    }
    (chartReading.fact_groups || []).forEach((group) => {
      sections.push({
        key: `chart-facts-${group.chart}`,
        title: `${group.chart} factors used`,
        lines: unique([
          group.life_area ? `This chart is read for ${group.life_area}.` : null,
          ...(group.lines || []),
        ]),
      });
    });
    if ((chartReading.missing_charts || []).length) {
      sections.push({
        key: 'chart-missing',
        title: 'Calculation limitation',
        lines: [`Could not calculate: ${chartReading.missing_charts.join(', ')}. No facts were invented for these charts.`],
      });
    }
    const why = Array.isArray(derivation.conclusion?.why) ? derivation.conclusion.why : [];
    if (why.length) sections.push({ key: 'chart-result', title: 'Calculation record', lines: unique(why) });
    return sections
      .filter((section) => section.lines?.length)
      .map((section, index) => ({ ...section, step: index + 1 }));
  }
  return [
    buildFrameworkSection(derivation),
    buildPromiseSection(derivation),
    buildDashaSection(derivation),
    buildTransitSection(derivation),
    buildConclusionSection(derivation),
  ]
    .filter((section) => section && (section.lines?.length || section.groups?.length))
    .map((section, index) => ({ ...section, step: index + 1 }));
};
