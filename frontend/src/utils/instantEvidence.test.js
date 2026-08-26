import { buildReadableEvidence } from './instantEvidence';

describe('buildReadableEvidence career explanations', () => {
    test('shows a promotion graph route without a separate career reading payload', () => {
        const sections = buildReadableEvidence({
            user_derivation: {
                career_graph_route: {
                    shadow_only: true,
                    status: 'matched',
                    question_type: 'Promotion',
                    expected_approach: 'Promotion timing',
                    selected_approach: 'Promotion timing',
                    mode_match: true,
                    answer_contract: 'Promotion answer contract',
                    evidence_policy: 'D1 and D10 promise with dasha and transit delivery',
                    runtime_key: 'promotion',
                    required_nodes: [
                        { id: 'career:H10', label: '10th house (role and authority)', selected: true },
                        { id: 'career:H11', label: '11th house (recognition and gains)', selected: true },
                    ],
                    decision_rules: [{ id: 'career:PromotionRule', label: 'Promotion delivery rule' }],
                },
            },
        });
        const graph = sections.find((section) => section.key === 'knowledge-graph-route-0');
        expect(graph).toBeTruthy();
        expect(graph.groups[0].title).toContain('Promotion');
        expect(graph.groups[0].title).toContain('Matched live calculation');
        expect(graph.groups[1].items[0].title).toContain('10th house');
        expect(graph.groups[1].items[1].title).toContain('11th house');
    });

    test('shows exact ontology labels and the promotion decision-stage hierarchy', () => {
        const sections = buildReadableEvidence({
            user_derivation: {
                career_graph_route: {
                    status: 'matched',
                    question_type: 'Promotion and advancement',
                    expected_approach: 'Promotion timing',
                    selected_approach: 'Promotion timing',
                    mode_match: true,
                    graph_tree: {
                        id: 'ar:QuestionType', label: 'Question type', children: [{
                            id: 'career:PromotionTiming', label: 'Promotion and advancement', children: [{
                                id: 'ar:evaluatesStage', label: 'Decision stages', children: [{
                                    id: 'career:PromotionResponsibilityStage',
                                    label: 'Increased responsibility and visibility',
                                    children: [{
                                        id: 'ar:stageRequiresFactor', label: 'Required astrology factors', children: [
                                            { id: 'career:H6', label: 'Employment, service, workload and competition', children: [] },
                                            { id: 'career:H10', label: 'Role, status, authority and visible responsibility', children: [] },
                                        ],
                                    }],
                                }, {
                                    id: 'career:PromotionRecognitionStage',
                                    label: 'Recognition and advancement',
                                    children: [{
                                        id: 'ar:stageRequiresFactor', label: 'Required astrology factors', children: [
                                            { id: 'career:H10', label: 'Role, status, authority and visible responsibility', children: [] },
                                            { id: 'career:H11', label: 'Recognition, gains, networks and goals', children: [] },
                                        ],
                                    }],
                                }, {
                                    id: 'career:PromotionCompensationStage',
                                    label: 'Compensation and formalization', children: [],
                                }],
                            }],
                        }],
                    },
                },
            },
        });

        const graph = sections.find((section) => section.key === 'knowledge-graph-route-0');
        expect(graph.groups[0].title).toBe('Question type: Promotion and advancement');
        expect(graph.groups[1].title).toBe('Decision stages');
        expect(graph.groups[1].items.map((item) => item.title)).toEqual([
            'Increased responsibility and visibility',
            'Recognition and advancement',
            'Compensation and formalization',
        ]);
        const recognition = graph.groups.find((group) => (
            group.title === 'Decision stages → Recognition and advancement → Required astrology factors'
        ));
        expect(recognition.items.map((item) => item.title)).toEqual([
            'Role, status, authority and visible responsibility',
            'Recognition, gains, networks and goals',
        ]);
    });

    test('shows the knowledge graph route, every selected node, and missing requirements', () => {
        const sections = buildReadableEvidence({
            user_derivation: {
                career_graph_route: {
                    shadow_only: true,
                    status: 'review_needed',
                    question_type: 'Manager or authority relationship',
                    expected_approach: 'Workplace relationship reading',
                    selected_approach: 'Static career profile',
                    mode_match: false,
                    answer_contract: 'Relationship answer contract',
                    evidence_policy: 'Relationship evidence policy',
                    required_nodes: [
                        { id: 'career:H9', label: '9th house (manager and authority)', selected: false },
                        { id: 'career:D1Foundation', label: 'D1 career foundation', selected: true },
                    ],
                    additional_selected_nodes: [
                        { id: 'career:D10Confirmation', label: 'D10 professional confirmation' },
                    ],
                    decision_rules: [{ id: 'career:RuleAuthority', label: 'Authority relationship rule' }],
                    guardrails: [{ id: 'career:NoVocationShortcut', label: 'No vocation shortcut' }],
                },
                career_reading: { professional_foundation: [], professional_expression: [], delivery_windows: [] },
            },
        });
        const graph = sections.find((section) => section.key === 'knowledge-graph-route-0');
        expect(graph.groups[0].title).toContain('Needs review');
        expect(graph.groups[1].items[0].title).toContain('— 9th house');
        expect(graph.groups[1].items[0].text).toContain('missing');
        expect(graph.groups[1].items[1].title).toContain('✓ D1');
        expect(graph.groups[2].items[0].title).toContain('✓ D10');
        expect(graph.groups[3].items[0].title).toBe('Authority relationship rule');
        expect(graph.groups[4].items[0].title).toBe('No vocation shortcut');
    });

    test('shows non-career graph nodes alongside domain-specific evidence', () => {
        const sections = buildReadableEvidence({
            user_derivation: {
                health_graph_route: {
                    domain: 'health',
                    status: 'matched',
                    question_type: 'Health vulnerability',
                    expected_approach: 'Constitutional health reading',
                    selected_approach: 'Constitutional health reading',
                    mode_match: true,
                    required_nodes: [
                        { id: 'health:H6', label: '6th house health axis', selected: true },
                    ],
                },
                medical_reading: {
                    constitutional_lines: ['D1 health foundation calculated.'],
                    vulnerability_groups: [],
                    condition_lines: [],
                    judgment_lines: [],
                    safety: 'Not a diagnosis.',
                },
            },
        });

        expect(sections[0].key).toBe('knowledge-graph-route-0');
        expect(sections[0].title).toContain('Health');
        expect(sections[0].groups[1].items[0].title).toContain('6th house');
        expect(sections.some((section) => section.key === 'medical-constitution')).toBe(true);
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
