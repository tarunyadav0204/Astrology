import { formatTopicEvidence } from './topicEvidenceFormatters';

describe('formatTopicEvidence', () => {
  test('renders structured protection factors as readable astrology', () => {
    expect(formatTopicEvidence({
      type: 'supportive_lordship', planet: 'Mars', relation: 'occupies', house: 8, classification: 'yogakaraka',
    })).toBe('Mars occupies House 8 with Yoga Karaka lordship.');
    expect(formatTopicEvidence({
      type: 'mixed_lordship_support', planet: 'Jupiter', relation: 'occupies', house: 2, houses: [5],
    })).toBe('Jupiter occupies House 2; its lordship of House 5 adds support.');
  });

  test('explains when nakshatra support is qualified', () => {
    expect(formatTopicEvidence({
      type: 'nakshatra_lord_support',
      planet: 'Jupiter',
      nakshatra: 'Hasta',
      lord: 'Moon',
      relationship: 'friendly',
      lord_retrograde: false,
      lord_affliction_details: [
        { type: 'joined_by_malefics', planets: ['Saturn'] },
        { type: 'aspected_by_malefics', planets: ['Sun', 'Mars'] },
      ],
    })).toBe("Jupiter is in Hasta, ruled by its natural friend Moon; Moon's condition qualifies this support because it is joined by Saturn and aspected by Sun, Mars.");
  });

  test('never exposes an object serialization for an unknown factor', () => {
    const output = formatTopicEvidence({ type: 'future_factor', planet: 'Venus', score: 2 });
    expect(output).toBe('Planet: Venus · Score: 2');
    expect(output).not.toContain('[object Object]');
    expect(output).not.toContain('{');
  });

  test('uses the authored D30 explanation when supplied', () => {
    expect(formatTopicEvidence({
      type: 'd30_source_nodal_pressure',
      meaning: 'Saturn shares D30 House 2 with the nodal axis.',
    })).toBe('Saturn shares D30 House 2 with the nodal axis.');
  });
});
