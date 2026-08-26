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

// Saved answers can contain both the current array-shaped contract and older
// scalar/object values. Evidence rendering must remain safe for both shapes.
const asArray = (value) => {
  if (Array.isArray(value)) return value;
  if (value === undefined || value === null || value === '') return [];
  return [value];
};

const textList = (value) => asArray(value)
  .map((item) => String(item ?? '').trim())
  .filter(Boolean);

const houseNumberList = (value) => unique(asArray(value)
  .flatMap((item) => {
    if (item && typeof item === 'object') {
      return [item.house ?? item.house_number ?? item.number ?? item.h];
    }
    return [item];
  })
  .map((item) => Number(item))
  .filter((item) => Number.isInteger(item) && item >= 1 && item <= 12));

const dashaLevelLabel = (level) => ({
  MD: 'Mahadasha', AD: 'Antardasha', PD: 'Pratyantardasha',
  SD: 'Sookshma dasha', PRANA: 'Prana dasha',
}[String(level || '').toUpperCase()] || humanize(level));

const ordinal = (value) => {
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value || '');
  const remainder100 = number % 100;
  if (remainder100 >= 11 && remainder100 <= 13) return `${number}th`;
  return `${number}${({ 1: 'st', 2: 'nd', 3: 'rd' }[number % 10] || 'th')}`;
};

const activationMechanism = (mechanism) => ({
  lordship: 'lordship',
  natal_occupation: 'natal occupation',
  natal_aspect: 'natal aspect',
}[mechanism] || humanize(mechanism));

const decisionActivationItems = (window) => {
  const items = [];
  asArray(window.dasha_carriers).filter((row) => row && typeof row === 'object').forEach((carrier) => {
    const levels = textList(carrier.dasha_levels).map(dashaLevelLabel);
    const links = asArray(carrier.event_links).filter((row) => row && typeof row === 'object');
    const details = links.map((link) => {
      const mechanisms = textList(link.mechanisms).map(activationMechanism);
      return `${houseText(link)}${mechanisms.length ? ` through ${mechanisms.join(' and ')}` : ''}`;
    });
    if (!details.length) {
      houseNumberList(carrier.natal_event_houses)
        .forEach((house) => details.push(`House ${house} through a calculated natal link`));
    }
    items.push({
      title: `${carrier.planet || 'Dasha planet'}${levels.length ? ` · ${levels.join(' and ')}` : ''}`,
      text: unique([
        carrier.natal_placement_house
          ? `Natal ${carrier.planet || 'planet'} is placed in House ${carrier.natal_placement_house}.`
          : null,
        details.length ? `It activates ${details.join('; ')}.` : null,
      ]).join(' '),
    });
  });

  asArray(window.transit_confirmations).filter((row) => row && typeof row === 'object').forEach((transit) => {
    const delivered = asArray(transit.delivered_event_houses)
      .filter((row) => row && typeof row === 'object')
      .map((row) => {
        if (row.mechanism === 'transit_occupation') return `occupies ${houseText(row)}`;
        return `aspects ${houseText(row)}${row.aspect_number ? ` by its ${ordinal(row.aspect_number)} aspect` : ''}`;
      });
    const reaspectsNatal = textList(transit.trigger_kinds).includes('own_natal_aspect');
    const reaspect = reaspectsNatal && transit.natal_placement_house
      ? `${transit.planet} re-aspects its natal position in House ${transit.natal_placement_house}${transit.natal_reaspect_number ? ` by its ${ordinal(transit.natal_reaspect_number)} aspect` : ''}.`
      : null;
    items.push({
      title: `Transit confirmation · ${transit.planet || 'planet'}${formatRange(transit.start, transit.end) ? ` · ${formatRange(transit.start, transit.end)}` : ''}`,
      text: unique([
        transit.transit_native_house ? `Transit ${transit.planet} is in House ${transit.transit_native_house}.` : null,
        delivered.length ? `It ${delivered.join(' and ')}.` : null,
        reaspect,
        ...textList(transit.reasons).filter((reason) => !/re-aspects its natal position/i.test(reason)),
      ]).join(' '),
    });
  });
  return items.filter((item) => item.text);
};

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

const collectGraphRoutes = (derivation) => {
  const routes = [];
  const add = (route, sourceKey = '') => {
    if (!route || typeof route !== 'object' || Array.isArray(route)) return;
    const identity = route.runtime_key || route.route_id || route.question_type || sourceKey;
    if (routes.some((item) => (item.runtime_key || item.route_id || item.question_type || item.__sourceKey) === identity)) return;
    routes.push({ ...route, __sourceKey: sourceKey });
  };
  asArray(derivation.knowledge_graph_routes || derivation.graph_routes).forEach((route) => add(route, 'graph_routes'));
  Object.entries(derivation).forEach(([key, value]) => {
    if (key.endsWith('_graph_route')) add(value, key);
  });
  return routes;
};

const buildGraphSections = (derivation) => collectGraphRoutes(derivation).map((graphRoute, routeIndex) => {
  const requiredNodes = asArray(graphRoute.required_nodes).filter((node) => node && typeof node === 'object');
  const additionalNodes = asArray(graphRoute.additional_selected_nodes).filter((node) => node && typeof node === 'object');
  const rules = asArray(graphRoute.decision_rules).filter((node) => node && typeof node === 'object');
  const guardrails = asArray(graphRoute.guardrails).filter((node) => node && typeof node === 'object');
  const capabilities = asArray(graphRoute.required_capabilities).filter((node) => node && typeof node === 'object');
  const domain = humanize(graphRoute.domain || graphRoute.category || graphRoute.__sourceKey.replace(/_graph_route$/, '') || 'Astrology');
  return {
    key: `knowledge-graph-route-${routeIndex}`, title: `${domain} knowledge graph audit`,
    groups: [
      {
        key: `knowledge-graph-summary-${routeIndex}`,
        title: `${graphRoute.question_type || `${domain} question`} · ${graphRoute.status === 'matched' ? 'Matched live calculation' : 'Needs review'}`,
        items: [{
          title: 'Question and answer route',
          text: `The graph expected ${graphRoute.expected_approach || 'an unspecified approach'}; the live pipeline selected ${graphRoute.selected_approach || 'an unspecified approach'}. ${graphRoute.mode_match ? 'The answer route matched.' : 'The answer route did not match.'}`,
        }, {
          title: 'Graph policy',
          text: `Answer contract: ${graphRoute.answer_contract || 'not declared'}. Evidence policy: ${graphRoute.evidence_policy || 'not declared'}.${graphRoute.shadow_only ? ' This is a shadow audit and did not influence the answer.' : ''}`,
        }, {
          title: 'Audit identity',
          text: `Ontology ${graphRoute.ontology_version || 'unknown'} · route ${graphRoute.runtime_key || graphRoute.route_id || 'unknown'}.`,
        }],
      },
      requiredNodes.length ? {
        key: `knowledge-graph-required-${routeIndex}`, title: 'Required graph nodes',
        items: requiredNodes.map((node) => ({
          title: `${node.selected ? '✓' : '—'} ${node.label || humanize(node.id)}`,
          text: node.selected ? 'Selected from the live calculation.' : 'Required by the graph but missing from the live calculation.',
        })),
      } : null,
      additionalNodes.length ? {
        key: `knowledge-graph-additional-${routeIndex}`, title: 'Additional nodes selected',
        items: additionalNodes.map((node) => ({ title: `✓ ${node.label || humanize(node.id)}`, text: 'Available in the live calculation; not mandatory for this question route.' })),
      } : null,
      rules.length ? { key: `knowledge-graph-rules-${routeIndex}`, title: 'Decision rules selected', items: rules.map((node) => ({ title: node.label || humanize(node.id), text: 'Required by the selected graph route.' })) } : null,
      capabilities.length ? { key: `knowledge-graph-capabilities-${routeIndex}`, title: 'Calculator capabilities required', items: capabilities.map((node) => ({ title: node.label || humanize(node.id), text: 'The ontology requires this calculator capability for the route.' })) } : null,
      guardrails.length ? { key: `knowledge-graph-guardrails-${routeIndex}`, title: 'Guardrails selected', items: guardrails.map((node) => ({ title: node.label || humanize(node.id), text: 'Applied to prevent an unsupported conclusion.' })) } : null,
    ].filter(Boolean),
  };
});

const buildCareerSections = (derivation) => {
  const hasCareerReading = derivation.career_reading && typeof derivation.career_reading === 'object';
  const career = hasCareerReading ? derivation.career_reading : {};
  if (!hasCareerReading) return null;
  const sections = [];
  const relationship = career.relationship && typeof career.relationship === 'object'
    ? career.relationship : {};
  const relationshipRows = asArray(relationship.house_roles)
    .filter((row) => row && typeof row === 'object');
  const isRelationship = relationshipRows.length > 0;
  if (isRelationship) sections.push({
    key: 'career-relationship', title: 'Workplace relationship examined',
    groups: [{
      key: 'career-relationship-roles',
      title: `${humanize(relationship.target || 'workplace relationship')} · Role-specific astrology`,
      items: relationshipRows.map((row) => {
        const natal = row.natal_foundation && typeof row.natal_foundation === 'object'
          ? row.natal_foundation : {};
        const professional = row.professional_confirmation && typeof row.professional_confirmation === 'object'
          ? row.professional_confirmation : {};
        return {
          title: `House ${row.house} · ${humanize(row.role || 'relationship factor')}`,
          text: unique([
            natal.lord ? `${natal.lord} rules this factor${natal.lord_placement_house ? ` from House ${natal.lord_placement_house}` : ''}.` : null,
            textList(natal.occupants).length ? `Occupants: ${textList(natal.occupants).join(', ')}.` : 'No occupants; its lord and aspects carry the result.',
            textList(natal.aspecting_planets || natal.aspects).length ? `Influenced by ${textList(natal.aspecting_planets || natal.aspects).join(', ')}.` : null,
            row.assessment ? `D1 assessment: ${humanize(row.assessment)}.` : null,
            professional.lord ? `D10 confirmation: ${professional.lord} rules this factor${professional.lord_placement_house ? ` from House ${professional.lord_placement_house}` : ''}.` : null,
          ]).join(' '),
        };
      }),
    }],
  });
  const foundation = career.professional_foundation || [];
  if (foundation.length && !isRelationship) sections.push({
    key: 'career-foundation', title: 'Career foundation · D1',
    groups: [{
      key: 'career-d1', title: 'Natal professional promise',
      items: foundation.map((row) => ({
        title: `House ${row.house}`,
        text: unique([
          row.lord ? `${row.lord} rules this area${row.lord_placement_house ? ` from House ${row.lord_placement_house}` : ''}.` : null,
          (row.occupants || []).length ? `Occupants: ${row.occupants.join(', ')}.` : 'No occupants; its lord and aspects carry the result.',
          (row.aspecting_planets || row.aspects || []).length ? `Influenced by ${(row.aspecting_planets || row.aspects).join(', ')}.` : null,
          row.tone ? `Assessment: ${humanize(row.tone)}.` : null,
        ]).join(' '),
      })),
    }],
  });
  const expression = career.professional_expression || [];
  if (expression.length && !isRelationship) {
    const byChart = expression.reduce((result, row) => {
      const chart = row.chart || 'D10';
      if (!result[chart]) result[chart] = [];
      result[chart].push(row);
      return result;
    }, {});
    sections.push({
      key: 'career-expression', title: 'Professional signature',
      groups: Object.entries(byChart).map(([chart, rows]) => ({
        key: `career-${chart}`, title: `${chart} · How the career is expressed`,
        items: rows.map((row) => ({
          title: `House ${row.house}`,
          text: unique([
            row.lord ? `${row.lord} rules it${row.lord_placement_house ? ` from House ${row.lord_placement_house}` : ''}.` : null,
            (row.occupants || []).length ? `Occupants: ${row.occupants.join(', ')}.` : 'No occupants.',
            row.rating || row.tone ? `Assessment: ${humanize(row.rating || row.tone)}.` : null,
          ]).join(' '),
        })),
      })),
    });
  }
  const windows = career.delivery_windows || [];
  const decisionLabel = (verdict) => ({
    planned_transition_supported: 'Planned transition supported',
    prepare_do_not_resign: 'Prepare and apply; do not resign yet',
    stay_for_now: 'Current role has continuity support',
    instability_not_exit_permission: 'Pressure is present; leaving is not yet supported',
    insufficient_decision_evidence: 'Not enough support for a stay-or-leave verdict',
  }[verdict] || humanize(verdict || 'Decision not calculated'));
  const gateText = (label, value) => `${value ? '✓' : '—'} ${label}: ${value ? 'supported' : 'not established'}`;
  if (windows.length && !isRelationship) sections.push({
    key: 'career-delivery', title: windows.some((window) => window.decision_matrix)
      ? 'How the stay-or-change calculation was made'
      : 'How and when results can arrive',
    groups: windows.slice(0, 5).map((window, index) => ({
      key: `career-window-${index}`,
      title: [formatRange(window.start, window.end), window.chain].filter(Boolean).join(' · '),
      items: window.decision_matrix ? [
        {
          title: decisionLabel(window.decision_matrix.verdict),
          text: unique([
            gateText('Current-job continuity (H6 + H10)', window.decision_matrix.continuity_support),
            gateText('Change momentum (H3 + H10)', window.decision_matrix.change_momentum),
            gateText('Separation from current role (H10 + H12)', window.decision_matrix.separation_support),
            gateText('Next-role landing (H2 + H6 + H10 + H11)', window.decision_matrix.landing_support),
            window.decision_matrix.guidance,
          ]).join(' '),
        },
        {
          title: 'Combined activation used for this verdict',
          text: `The decision test receives Houses ${houseNumberList(window.activated_focus_houses || window.decision_matrix.active_houses).join(', ') || 'not supplied'} after combining the dasha links and transit confirmation below.`,
        },
        ...decisionActivationItems(window),
      ] : asArray(window.stages).filter((stage) => stage && typeof stage === 'object').map((stage) => ({
        title: humanize(stage.stage || 'career activity'),
        text: `${stage.label || humanize(stage.stage || 'Career activity')}${textList(stage.supporting_houses).length ? ` Supported by Houses ${textList(stage.supporting_houses).join(', ')}.` : ''}${stage.confidence ? ` Confidence: ${humanize(stage.confidence)}.` : ''}`,
      })),
    })),
  });
  if (!isRelationship) sections.push({
    key: 'career-meaning', title: 'How to read this career answer',
    lines: unique([
      career.interpretation_rule,
      'Activity, formalization, joining, compensation and stability are separate stages; an active period is not automatically a guaranteed offer or promotion.',
    ]),
  });
  return sections.filter((section) => section.lines?.length || section.groups?.length)
    .map((section, index) => ({ ...section, step: index + 1 }));
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
  const graphs = buildGraphSections(derivation);
  const numbered = (sections) => sections
    .filter((section) => section && (section.lines?.length || section.groups?.length))
    .map((section, index) => ({ ...section, step: index + 1 }));
  const medical = derivation.medical_reading;
  if (medical && typeof medical === 'object') {
    const sections = [];
    if ((medical.constitutional_lines || []).length) sections.push({
      key: 'medical-constitution', title: 'Constitutional health foundation',
      lines: unique(medical.constitutional_lines),
    });
    (medical.vulnerability_groups || []).forEach((group, index) => sections.push({
      key: `medical-vulnerability-${index}`, title: `${group.title} · calculated susceptibility`,
      lines: unique(group.lines || []),
    }));
    if ((medical.condition_lines || []).length) sections.push({
      key: 'medical-condition', title: 'Planet strength and condition',
      lines: unique(medical.condition_lines),
    });
    if ((medical.judgment_lines || []).length) sections.push({
      key: 'medical-judgment', title: `What this means for ${humanize(medical.category || 'health').toLowerCase()}`,
      lines: unique(medical.judgment_lines),
    });
    sections.push({
      key: 'medical-safety', title: 'How to use this reading',
      lines: unique([
        (medical.divisions_checked || []).length ? `Divisional checks used: ${medical.divisions_checked.join(', ')}.` : null,
        medical.safety,
      ]),
    });
    return numbered([...graphs, ...sections]);
  }
  const career = buildCareerSections(derivation);
  if (career) return numbered([...graphs, ...career]);
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
    return numbered([...graphs, ...sections]);
  }
  return numbered([
    ...graphs,
    buildFrameworkSection(derivation),
    buildPromiseSection(derivation),
    buildDashaSection(derivation),
    buildTransitSection(derivation),
    buildConclusionSection(derivation),
  ]);
};
