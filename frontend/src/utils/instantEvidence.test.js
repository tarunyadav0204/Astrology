import { buildReadableEvidence } from './instantEvidence';

describe('buildReadableEvidence career explanations', () => {
    test('never exposes knowledge-graph audit internals in readable evidence', () => {
        const sections = buildReadableEvidence({
            user_derivation: {
                education_graph_route: {
                    domain: 'education',
                    status: 'matched',
                    runtime_key: 'higher_education',
                    ontology_version: '0.2.4',
                    answer_contract: 'Internal education decision contract',
                    graph_tree: { id: 'secret:QuestionType', label: 'Question type' },
                },
                chart_reading: {
                    requested_charts: ['D1', 'D24'],
                    fact_groups: [{
                        chart: 'D24',
                        life_area: 'higher education',
                        lines: ['Jupiter supports sustained advanced study.'],
                    }],
                    missing_charts: [],
                },
            },
        });

        const rendered = JSON.stringify(sections);
        expect(rendered).toContain('Jupiter supports sustained advanced study');
        expect(rendered).not.toMatch(/knowledge graph audit/i);
        expect(rendered).not.toContain('higher_education');
        expect(rendered).not.toContain('0.2.4');
        expect(rendered).not.toContain('secret:QuestionType');
        expect(rendered).not.toContain('Internal education decision contract');
    });
    test('returns group-only career sections without requiring top-level lines', () => {
        const sections = buildReadableEvidence({
            user_derivation: {
                career_reading: {
                    professional_foundation: [{
                        house: 10,
                        lord: 'Mars',
                        lord_placement_house: 2,
                        occupants: [],
                        aspecting_planets: ['Jupiter', 'Moon'],
                        tone: 'supportive',
                    }],
                    professional_expression: [],
                    delivery_windows: [],
                },
            },
        });

        expect(sections[0].groups[0].items[0].text).toContain('Influenced by Jupiter, Moon');
        expect(sections[0].lines).toBeUndefined();
    });

    test('normalizes legacy scalar career fields instead of throwing', () => {
        expect(() => buildReadableEvidence({
            user_derivation: {
                career_reading: {
                    professional_foundation: {
                        house: 10,
                        occupants: 'Mercury',
                        aspects: 'Jupiter',
                    },
                    delivery_windows: {
                        start: '2026-08-23',
                        end: '2026-09-18',
                        stages: {
                            stage: 'professional_activity',
                            supporting_houses: 10,
                        },
                    },
                },
            },
        })).not.toThrow();
    });

    test('shows the four auditable gates for a stay-or-change window', () => {
        const sections = buildReadableEvidence({
            user_derivation: {
                career_reading: {
                    professional_foundation: [],
                    professional_expression: [],
                    delivery_windows: [{
                        start: '2027-04-15', end: '2027-10-04', chain: 'Saturn-Rahu-Venus',
                        activated_focus_houses: [2, 3, 6, 10, 11, 12],
                        why: 'Saturn activates House 10; Venus activates Houses 2, 6, 11 and 12',
                        dasha_carriers: [{
                            planet: 'Saturn', dasha_levels: ['MD', 'PD'], natal_placement_house: 2,
                            event_links: [
                                { house: 2, meaning: 'income', mechanisms: ['natal_occupation'] },
                                { house: 4, meaning: 'home', mechanisms: ['natal_aspect'] },
                                { house: 7, meaning: 'agreements', mechanisms: ['lordship'] },
                                { house: 8, meaning: 'change', mechanisms: ['lordship'] },
                                { house: 11, meaning: 'gains', mechanisms: ['natal_aspect'] },
                            ],
                        }, {
                            planet: 'Rahu', dasha_levels: ['AD'], natal_placement_house: 2,
                            event_links: [
                                { house: 2, meaning: 'income', mechanisms: ['natal_occupation'] },
                                { house: 8, meaning: 'change', mechanisms: ['natal_aspect'] },
                            ],
                        }],
                        transit_confirmations: [{
                            start: '2027-04-15', end: '2027-05-15', planet: 'Rahu',
                            transit_native_house: 8, natal_placement_house: 2,
                            trigger_kinds: ['own_natal_aspect'], natal_reaspect_number: 7,
                            delivered_event_houses: [{
                                house: 2, meaning: 'income', mechanism: 'transit_aspect', aspect_number: 7,
                            }],
                        }],
                        decision_matrix: {
                            verdict: 'planned_transition_supported',
                            continuity_support: true,
                            change_momentum: true,
                            separation_support: true,
                            landing_support: true,
                        },
                    }],
                },
            },
        });
        const delivery = sections.find((section) => section.key === 'career-delivery');
        expect(delivery.title).toBe('How the stay-or-change calculation was made');
        expect(delivery.groups[0].items[0].title).toContain('Planned transition supported');
        expect(delivery.groups[0].items[4].title).toContain('Is the next role and income supported?');
        expect(delivery.groups[0].items[4].text).toContain('Houses 2, 6, 10 and 11');
        expect(delivery.groups[0].items[5].title).toBe('Combined activation used for this verdict');
        expect(delivery.groups[0].items[6].title).toContain('Saturn · Mahadasha and Pratyantardasha');
        expect(delivery.groups[0].items[6].text).toContain('House 4 — home through natal aspect');
        expect(delivery.groups[0].items[6].text).toContain('House 7 — agreements through lordship');
        expect(delivery.groups[0].items[6].text).toContain('House 8 — change through lordship');
        expect(delivery.groups[0].items[6].text).toContain('House 11 — gains through natal aspect');
        expect(delivery.groups[0].items[7].title).toContain('Rahu · Antardasha');
        expect(delivery.groups[0].items[7].text).toContain('House 8 — change through natal aspect');
        expect(delivery.groups[0].items[8].text).toContain('Transit Rahu is in House 8');
        expect(delivery.groups[0].items[8].text).toContain('7th aspect');
        expect(delivery.groups[0].items[8].text).toContain('natal position in House 2');
    });

    test('renders object-shaped activated houses without object text', () => {
        const sections = buildReadableEvidence({
            user_derivation: { career_reading: { delivery_windows: [{
                start: '2027-04-15', end: '2027-10-04',
                activated_focus_houses: [{ house: 3 }, { house: 10 }, { house: 12 }],
                decision_matrix: {
                    verdict: 'prepare_do_not_resign', active_houses: [3, 10, 12],
                    change_momentum: true, separation_support: true, landing_support: false,
                },
            }] } },
        });
        const text = sections.find((section) => section.key === 'career-delivery').groups[0].items[5].text;
        expect(text).toContain('Houses 3, 10, 12');
        expect(text).not.toContain('[object Object]');
    });
});
