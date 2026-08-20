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
    title: `What is tested for ${String(event.label || 'this question').toLowerCase()}`,
    lines,
  };
};

const buildPromiseSection = (derivation) => {
  const promise = derivation.natal_promise || {};
  if (!promise.status && !(promise.basis || []).length) return null;
  return {
    key: 'promise',
    step: 2,
    title: 'Natal promise',
    lines: unique([promiseLine(promise.status), ...(promise.basis || [])]),
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
  return { key: 'dasha', step: 3, title: 'When the dasha activates those houses', lines: unique(lines) };
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
  return { key: 'transits', step: 4, title: 'How transits confirm the timing', lines: unique(lines) };
};

const buildConclusionSection = (derivation) => {
  const conclusion = derivation.conclusion || {};
  const limitations = derivation.limitations || [];
  const lines = [];
  const range = formatRange(conclusion.start, conclusion.end);
  if (range) {
    lines.push(`The strongest supported timing is ${range}${conclusion.chain ? ` during ${conclusion.chain}` : ''}.`);
  } else if (conclusion.direction && conclusion.direction !== 'insufficient_evidence') {
    lines.push(`Overall conclusion: ${humanize(conclusion.direction)}.`);
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
  return { key: 'conclusion', step: 5, title: 'Therefore', lines: unique(lines) };
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
  return [
    buildFrameworkSection(derivation),
    buildPromiseSection(derivation),
    buildDashaSection(derivation),
    buildTransitSection(derivation),
    buildConclusionSection(derivation),
  ].filter((section) => section && section.lines && section.lines.length);
};
