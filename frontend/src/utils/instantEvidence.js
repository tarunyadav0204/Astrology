// User-facing rendering of the backend's explicit derivation contract. This
// deliberately avoids exposing calculator payloads or raw evidence records.

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const humanize = (value) => String(value || '')
    .replace(/[_.]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^\w/, (char) => char.toUpperCase());

const unique = (items) => [...new Set(items.filter(Boolean))];

const formatDate = (iso) => {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || '').slice(0, 10));
    if (!match) return String(iso || '') || null;
    return `${Number(match[3])} ${MONTHS[Number(match[2]) - 1] || match[2]} ${match[1]}`;
};

const formatRange = (start, end) => {
    const from = formatDate(start);
    const to = formatDate(end);
    return from && to ? `${from} – ${to}` : from || to || null;
};

const houseText = (row) => {
    if (!row) return null;
    const house = row.house ?? row;
    return `House ${house}${row.meaning ? ` — ${row.meaning}` : ''}`;
};

const promiseLine = (status) => {
    if (String(status).startsWith('supported')) return 'The natal chart permits this outcome.';
    if (String(status).startsWith('qualified')) return 'The natal chart permits this outcome conditionally.';
    return 'The natal chart does not establish a strong promise for this outcome.';
};

const compactHouseNote = (line) => {
    const compact = String(line || '')
        // The card heading already identifies the house, but deleting this
        // phrase entirely breaks sentences such as "supports D1 House 2".
        .replace(/D1 House \d+/g, 'this house')
        .replace(/\s+/g, ' ')
        .trim();
    return compact.replace(/^this house\b/, 'This house');
};

const framework = (data) => {
    const event = data.event || {};
    const houses = event.houses || [];
    if (!houses.length) return null;
    const primary = houses.filter((row) => row.role !== 'supporting').map(houseText);
    const supporting = houses.filter((row) => row.role === 'supporting').map(houseText);
    return {
        key: 'framework', step: 1,
        title: `Astrology used for ${String(event.label || 'this question').toLowerCase()}`,
        lines: unique([
            primary.length ? `Primary houses: ${primary.join('; ')}` : null,
            supporting.length ? `Supporting houses: ${supporting.join('; ')}` : null,
        ]),
    };
};

const promise = (data) => {
    const value = data.natal_promise || {};
    if (!value.status && !(value.basis || []).length && !(value.d1_factors || []).length
        && !(value.divisional_factors || []).length && !(value.d1_house_factors || []).length
        && !(value.divisional_house_factors || []).length) return null;
    const d1Rows = value.d1_house_factors || [];
    const divisionalRows = value.divisional_house_factors || [];
    const groups = [{
        key: 'verdict', title: 'Overall promise',
        lines: unique([promiseLine(value.status), ...(value.basis || [])]),
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
        (result[chart] ||= []).push(row);
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
    if (!d1Rows.length && (value.d1_factors || []).length) groups.push({
        key: 'd1-legacy', title: 'D1 · Birth-chart foundation', lines: unique(value.d1_factors),
    });
    if (!divisionalRows.length && (value.divisional_factors || []).length) groups.push({
        key: 'division-legacy', title: 'Divisional confirmation',
        lines: unique(value.divisional_factors).map((line) => String(line).replace(/^Divisional confirmation:\s*/i, '')),
    });
    const lines = [];
    if (value.evidence_complete === false) {
        const hasD1 = (value.d1_factors || []).length > 0;
        const hasDivisional = (value.divisional_factors || []).length > 0;
        if (!hasD1 && !hasDivisional) lines.push('Detailed D1 and relevant divisional confirmation were unavailable, so no complete promise judgment is shown.');
        else if (!hasD1) lines.push('Relevant divisional confirmation is available, but the detailed D1 foundation was unavailable; treat the promise judgment as directional.');
        else if (!hasDivisional) lines.push('The detailed D1 foundation is available, but the relevant divisional confirmation was unavailable; treat the promise judgment as directional.');
    }
    return {
        key: 'promise', step: 2, title: 'What the birth chart promises',
        lines: unique(lines), groups,
    };
};

const dasha = (data) => {
    const lines = [];
    (data.dasha_activation || []).slice(0, 4).forEach((window) => {
        lines.push([formatRange(window.start, window.end), window.chain, humanize(window.strength)].filter(Boolean).join(' · '));
        const activated = (window.activated_houses || []).map(houseText).filter(Boolean);
        if (activated.length) lines.push(`Taken together, this dasha chain activates ${activated.join('; ')}.`);
        (window.carriers || []).forEach((carrier) => {
            const prefix = [(carrier.dasha_levels || []).join('/'), carrier.planet].filter(Boolean).join(' ');
            if (carrier.natal_placement_house) {
                lines.push(`${prefix}: natal placement is House ${carrier.natal_placement_house}.`);
            }
            (carrier.event_links || []).forEach((link) => {
                const methods = (link.mechanisms || []).map((mechanism) => ({
                    lordship: 'lordship',
                    natal_occupation: 'natal occupation',
                    natal_aspect: 'natal aspect',
                }[mechanism] || humanize(mechanism))).join(' and ');
                lines.push(`${prefix} activates ${houseText(link)}${methods ? ` through ${methods}` : ''}.`);
            });
            if (!(carrier.event_links || []).length) {
                const houses = (carrier.natal_event_houses || []).map((house) => `House ${house}`).join(', ');
                if (prefix && houses) lines.push(`${prefix} has natal links to ${houses}.`);
            }
        });
        if (!(window.carriers || []).length) (window.reasons || []).slice(0, 5).forEach((reason) => lines.push(reason));
    });
    return lines.length ? { key: 'dasha', step: 3, title: 'Why the current period can deliver the result', lines: unique(lines) } : null;
};

const transits = (data) => {
    const lines = [];
    (data.transit_confirmation || []).slice(0, 4).forEach((window) => {
        lines.push([formatRange(window.start, window.end), window.planet, humanize(window.strength)].filter(Boolean).join(' · '));
        if (window.natal_placement_house) {
            lines.push(`Natal ${window.planet} is in House ${window.natal_placement_house}.`);
        }
        (window.delivered_event_houses || []).forEach((delivered) => {
            if (delivered.mechanism === 'transit_aspect') {
                const from = window.transit_native_house ? ` from House ${window.transit_native_house}` : '';
                lines.push(`Transit ${window.planet}${from} aspects ${houseText(delivered)}, activating that event area.`);
            } else {
                lines.push(`Transit ${window.planet} occupies ${houseText(delivered)}, activating that event area.`);
            }
        });
        (window.reasons || []).forEach((reason) => lines.push(reason));
        if (!(window.delivered_event_houses || []).length && (window.confirmed_houses || []).length) {
            lines.push(`This movement confirms timing for ${(window.confirmed_houses || []).map(houseText).join('; ')}.`);
        }
    });
    return lines.length ? { key: 'transits', step: 4, title: 'How current planetary movement confirms timing', lines: unique(lines) } : null;
};

const conclusion = (data) => {
    const value = data.conclusion || {};
    const lines = [];
    const range = formatRange(value.start, value.end);
    if (range) lines.push(`The strongest supported timing is ${range}${value.chain ? ` during ${value.chain}` : ''}.`);
    else if (value.direction && value.direction !== 'insufficient_evidence') {
        const promise = data.natal_promise || {};
        if (value.direction === 'supported_natal_promise') {
            lines.push(promise.evidence_complete
                ? 'The D1 foundation and relevant divisional chart both support the possibility; timing still requires a separate dasha-and-transit check.'
                : 'The available natal checks lean supportive, but the evidence shown here is not detailed enough to treat that as a complete promise judgment.');
        } else {
            lines.push(`Overall conclusion: ${humanize(value.direction)}.`);
        }
    }
    const why = Array.isArray(value.why) ? value.why : String(value.why || '').split(';');
    why.slice(0, 3).filter(Boolean).forEach((reason) => lines.push(String(reason).trim()));
    if ((data.limitations || []).length) lines.push('Confidence is limited because one or more required astrology layers were unavailable.');
    return lines.length ? { key: 'conclusion', step: 5, title: 'What this means for you', lines: unique(lines) } : null;
};

const routerSourceLabel = (source) => {
    const value = String(source || '').toLowerCase();
    if (value === 'primary_intent_llm') return 'Primary interpretation';
    if (value === 'secondary_answer_mode_llm') return 'Secondary interpretation';
    if (value.includes('regex_recovery')) return 'Recovered interpretation';
    if (value.includes('fallback') || value.includes('error')) return 'Fallback routing';
    return humanize(source || 'Unknown');
};

export const buildRoutingSummary = (packet) => {
    const route = packet?.routing_decision || packet?.query_plan?.routing_decision || {};
    const selectedMode = route.selected_mode || route.intent_answer_mode || packet?.query_plan?.answer_mode || 'unknown';
    const finalMode = route.final_mode || packet?.query_plan?.answer_mode || selectedMode;
    return {
        finalMode: humanize(finalMode), selectedMode: humanize(selectedMode),
        source: routerSourceLabel(route.source), confidence: humanize(route.confidence || 'unknown'),
        changed: Boolean(route.post_selection_changed) || String(selectedMode) !== String(finalMode),
        degraded: Boolean(route.degraded), category: humanize(route.intent_category || packet?.query_plan?.category || 'general'),
    };
};

export const buildReadableEvidence = (packet) => {
    const data = packet?.user_derivation;
    if (!data || typeof data !== 'object') return [{
        key: 'legacy', step: null, title: 'Explanation unavailable',
        lines: ['This saved answer uses an older evidence format. Ask it again to see the readable astrology behind the answer.'],
    }];
    const medical = data.medical_reading;
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
        return sections.filter((section) => section.lines?.length)
            .map((section, index) => ({ ...section, step: index + 1 }));
    }
    const chartReading = data.chart_reading;
    if (chartReading && typeof chartReading === 'object') {
        const requested = chartReading.requested_charts || [];
        const sections = [];
        if (requested.length) sections.push({
            key: 'chart-examined', title: 'Chart examined',
            lines: [`The ${requested.join(', ')} calculation was used for this reading.`],
        });
        (chartReading.fact_groups || []).forEach((group) => sections.push({
            key: `chart-facts-${group.chart}`, title: `${group.chart} factors used`,
            lines: unique([
                group.life_area ? `This chart is read for ${group.life_area}.` : null,
                ...(group.lines || []),
            ]),
        }));
        if ((chartReading.missing_charts || []).length) sections.push({
            key: 'chart-missing', title: 'Calculation limitation',
            lines: [`Could not calculate: ${chartReading.missing_charts.join(', ')}. No facts were invented for these charts.`],
        });
        const why = Array.isArray(data.conclusion?.why) ? data.conclusion.why : [];
        if (why.length) sections.push({ key: 'chart-result', title: 'Calculation record', lines: unique(why) });
        return sections.filter((section) => section.lines?.length)
            .map((section, index) => ({ ...section, step: index + 1 }));
    }
    return [framework(data), promise(data), dasha(data), transits(data), conclusion(data)]
        .filter((section) => section && (section.lines?.length || section.groups?.length))
        .map((section, index) => ({ ...section, step: index + 1 }));
};
