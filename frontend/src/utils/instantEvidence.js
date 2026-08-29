// User-facing rendering of the backend's explicit derivation contract. This
// deliberately avoids exposing calculator payloads or raw evidence records.

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const humanize = (value) => String(value || '')
    .replace(/[_.]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/^\w/, (char) => char.toUpperCase());

const unique = (items) => [...new Set(items.filter(Boolean))];

// Evidence is persisted with chat history and can therefore contain older
// scalar/object shapes as well as the current arrays. Rendering an explanation
// must never be allowed to crash (and remount) the whole chat screen.
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
            houseNumberList(carrier.natal_event_houses).forEach((house) => details.push(`House ${house} through a calculated natal link`));
        }
        items.push({
            title: `${carrier.planet || 'Dasha planet'}${levels.length ? ` · ${levels.join(' and ')}` : ''}`,
            text: unique([
                carrier.natal_placement_house ? `Natal ${carrier.planet || 'planet'} is placed in House ${carrier.natal_placement_house}.` : null,
                details.length ? `It activates ${details.join('; ')}.` : null,
            ]).join(' '),
        });
    });
    asArray(window.transit_confirmations).filter((row) => row && typeof row === 'object').forEach((transit) => {
        const delivered = asArray(transit.delivered_event_houses)
            .filter((row) => row && typeof row === 'object')
            .map((row) => {
                if (row.mechanism === 'transit_occupation') return `occupies ${houseText(row)}`;
                const aspect = row.aspect_number ? ` by its ${ordinal(row.aspect_number)} aspect` : '';
                return `aspects ${houseText(row)}${aspect}`;
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

const careerEvidence = (data) => {
    const hasCareerReading = data.career_reading && typeof data.career_reading === 'object';
    const career = hasCareerReading ? data.career_reading : {};
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
    const diagnosis = career.diagnosis && typeof career.diagnosis === 'object'
        ? career.diagnosis : {};
    const diagnosisChain = asArray(diagnosis.conversion_chain)
        .filter((row) => row && typeof row === 'object');
    if (diagnosisChain.length || diagnosis.conclusion) sections.push({
        key: 'career-diagnosis', title: diagnosis.title || 'What is creating the career blockage',
        groups: diagnosisChain.length ? [{
            key: 'career-diagnosis-chain', title: 'How work converts into professional results',
            items: [
                ...diagnosisChain.map((row) => ({
                    title: `House ${row.house} · ${humanize(row.role || 'career factor')}`,
                    text: unique([
                        `Natal foundation: ${humanize(row.natal_assessment || 'not established')}.`,
                        row.currently_activated
                            ? 'This link is active in the supplied present-period evidence.'
                            : 'This link is not established as active in the supplied present-period evidence.',
                    ]).join(' '),
                })),
                diagnosis.conclusion ? { title: 'Calculated conclusion', text: diagnosis.conclusion } : null,
                diagnosis.practical_action ? { title: 'Practical implication', text: diagnosis.practical_action } : null,
            ].filter(Boolean),
        }] : undefined,
        lines: diagnosisChain.length ? undefined : unique([diagnosis.conclusion, diagnosis.practical_action]),
    });
    const foundation = asArray(career.professional_foundation).filter((row) => row && typeof row === 'object');
    if (foundation.length && !isRelationship) sections.push({
        key: 'career-foundation', title: 'Career foundation · D1',
        groups: [{
            key: 'career-d1', title: 'Natal professional promise',
            items: foundation.map((row) => ({
                title: `House ${row.house}`,
                text: unique([
                    row.lord ? `${row.lord} rules this area${row.lord_placement_house ? ` from House ${row.lord_placement_house}` : ''}.` : null,
                    textList(row.occupants).length ? `Occupants: ${textList(row.occupants).join(', ')}.` : 'No occupants; its lord and aspects carry the result.',
                    textList(row.aspecting_planets || row.aspects).length ? `Influenced by ${textList(row.aspecting_planets || row.aspects).join(', ')}.` : null,
                    row.tone ? `Assessment: ${humanize(row.tone)}.` : null,
                ]).join(' '),
            })),
        }],
    });
    const expression = asArray(career.professional_expression).filter((row) => row && typeof row === 'object');
    if (expression.length && !isRelationship) {
        const byChart = expression.reduce((result, row) => {
            const chart = row.chart || 'D10';
            (result[chart] ||= []).push(row);
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
                        textList(row.occupants).length ? `Occupants: ${textList(row.occupants).join(', ')}.` : 'No occupants.',
                        row.rating || row.tone ? `Assessment: ${humanize(row.rating || row.tone)}.` : null,
                    ]).join(' '),
                })),
            })),
        });
    }
    const synthesis = career.vocation_synthesis && typeof career.vocation_synthesis === 'object'
        ? career.vocation_synthesis : {};
    const tenthLord = synthesis.tenth_lord_signature && typeof synthesis.tenth_lord_signature === 'object'
        ? synthesis.tenth_lord_signature : {};
    const combinations = asArray(synthesis.combination_signatures).filter((row) => row && typeof row === 'object');
    const signatureItems = [];
    if (tenthLord.planet) signatureItems.push({
        title: `10th lord · ${tenthLord.planet}`,
        text: unique([
            tenthLord.house ? `Placed in House ${tenthLord.house}.` : null,
            textList(tenthLord.conjunct_planets).length
                ? `Conjoined with ${textList(tenthLord.conjunct_planets).join(', ')}; these planets modify the vocation signature together.`
                : 'No calculated conjunction cluster.',
        ]).join(' '),
    });
    combinations.forEach((row) => signatureItems.push({
        title: textList(row.planets).join(' + '),
        text: unique([
            textList(row.work_functions).length ? `Work functions: ${textList(row.work_functions).join('; ')}.` : null,
            textList(row.fields).length ? `Supported directions: ${textList(row.fields).join('; ')}.` : null,
        ]).join(' '),
    }));
    if (signatureItems.length && !isRelationship) sections.push({
        key: 'career-tenth-lord-signature', title: '10th-lord vocation signature',
        groups: [{ key: 'career-tenth-lord-combinations', title: 'How the profession is shaped', items: signatureItems }],
    });
    const vocation = career.vocation_indicators && typeof career.vocation_indicators === 'object'
        ? career.vocation_indicators : {};
    const amatya = vocation.amatyakaraka && typeof vocation.amatyakaraka === 'object'
        ? vocation.amatyakaraka : {};
    const karkamsa = vocation.karkamsa && typeof vocation.karkamsa === 'object'
        ? vocation.karkamsa : {};
    const karkamsaPlanets = karkamsa.planets && typeof karkamsa.planets === 'object'
        ? Object.entries(karkamsa.planets).filter(([, row]) => row && typeof row === 'object') : [];
    const vocationItems = [];
    if (amatya.planet) vocationItems.push({
        title: `Amatyakaraka · ${amatya.planet}`,
        text: unique([
            amatya.house ? `Placed in House ${amatya.house}.` : null,
            amatya.sign ? `Sign: ${humanize(amatya.sign)}.` : null,
            'This is the Jaimini indicator of vocation, responsibility and the way professional ability is applied.',
        ]).join(' '),
    });
    if (vocation.karkamsa_ascendant || karkamsaPlanets.length) vocationItems.push({
        title: 'Karakamsha · vocation confirmation',
        text: unique([
            vocation.karkamsa_ascendant ? `Karakamsha ascendant: ${humanize(vocation.karkamsa_ascendant)}.` : null,
            ...karkamsaPlanets
                .filter(([, row]) => [1, 6, 10].includes(Number(row.house)))
                .slice(0, 4)
                .map(([planet, row]) => `${planet} is in House ${row.house}${row.sign_name || row.sign ? ` (${humanize(row.sign_name || row.sign)})` : ''}.`),
            'Used as a Jaimini confirmation after the D1 and D10 career foundation.',
        ]).join(' '),
    });
    if (vocationItems.length && !isRelationship) sections.push({
        key: 'career-jaimini', title: 'Jaimini vocation indicators',
        groups: [{ key: 'career-jaimini-signature', title: 'Amatyakaraka and Karakamsha', items: vocationItems }],
    });
    const windows = asArray(career.delivery_windows).filter((window) => window && typeof window === 'object');
    const decisionLabel = (verdict) => ({
        planned_transition_supported: 'Planned transition supported',
        prepare_do_not_resign: 'Prepare and apply; do not resign yet',
        stay_for_now: 'Current role has continuity support',
        instability_not_exit_permission: 'Pressure is present; leaving is not yet supported',
        insufficient_decision_evidence: 'Not enough support for a stay-or-leave verdict',
    }[verdict] || humanize(verdict || 'Decision not calculated'));
    const decisionExplanation = (matrix = {}) => {
        if (matrix.verdict === 'planned_transition_supported') {
            return 'This window supports preparing the move, separating from the current role, and landing the next role or income. Secure the next position before resigning.';
        }
        if (matrix.verdict === 'prepare_do_not_resign') {
            return 'Movement toward change is active, but the next role or income is not fully secured by this window. Prepare and apply; do not treat it as a safe resignation window.';
        }
        if (matrix.verdict === 'stay_for_now') {
            return 'The current job has continuity support in this window. Use it to strengthen the role or prepare options rather than resigning immediately.';
        }
        if (matrix.verdict === 'instability_not_exit_permission') {
            return 'The chart shows disruption or pressure, but pressure alone does not mean leaving will improve the outcome.';
        }
        return 'This window does not contain enough of the required factors to call it either a safe change window or a definite stay window.';
    };
    const gateItem = (title, value, supported, missing) => ({
        title: `${value ? '✓' : '—'} ${title}`,
        text: value ? supported : missing,
    });
    if (windows.length) sections.push({
        key: 'career-delivery', title: windows.some((window) => window.decision_matrix)
            ? 'How the stay-or-change calculation was made'
            : 'How and when results can arrive',
        groups: windows.slice(0, 5).map((window, index) => ({
            key: `career-window-${index}`,
            title: [formatRange(window.start, window.end), window.chain].filter(Boolean).join(' · '),
            items: window.decision_matrix ? [
                {
                    title: `Verdict · ${decisionLabel(window.decision_matrix.verdict)}`,
                    text: decisionExplanation(window.decision_matrix),
                },
                gateItem(
                    'Can the current job continue?', window.decision_matrix.continuity_support,
                    'Yes. Employment and professional-role support are active together (Houses 6 and 10).',
                    'Not established. Employment and professional-role support are not both active (Houses 6 and 10).',
                ),
                gateItem(
                    'Is movement toward a change active?', window.decision_matrix.change_momentum,
                    'Yes. Initiative for change and professional movement are active together (Houses 3 and 10).',
                    'Not established. Initiative for change and professional movement are not both active (Houses 3 and 10).',
                ),
                gateItem(
                    'Is separation from the current role supported?', window.decision_matrix.separation_support,
                    'Yes. Career and release/separation factors are active together (Houses 10 and 12).',
                    'Not established. Career and release/separation factors are not both active (Houses 10 and 12).',
                ),
                gateItem(
                    'Is the next role and income supported?', window.decision_matrix.landing_support,
                    'Yes. Income, employment, role and gains are active together (Houses 2, 6, 10 and 11).',
                    'Not established. The complete income, employment, role and gains combination is missing (Houses 2, 6, 10 and 11).',
                ),
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
    sections.push({
        key: 'career-meaning', title: 'How to read this career answer',
        lines: unique([
            career.interpretation_rule,
            windows.length ? 'Activity, formalization, joining, compensation and stability are separate stages; an active period is not automatically a guaranteed offer or promotion.' : null,
        ]),
    });
    return sections.filter((section) => section.lines?.length || section.groups?.length)
        .map((section, index) => ({ ...section, step: index + 1 }));
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
    const numbered = (sections) => sections
        .filter((section) => section && (section.lines?.length || section.groups?.length))
        .map((section, index) => ({ ...section, step: index + 1 }));
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
        return numbered(sections);
    }
    const career = careerEvidence(data);
    if (career) return numbered(career);
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
        return numbered(sections);
    }
    return numbered([
        framework(data), promise(data), dasha(data), transits(data), conclusion(data),
    ]);
};
