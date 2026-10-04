const words = (value) => String(value || '').replaceAll('_', ' ').trim();
const titleWords = (value) => words(value).replace(/\b\w/g, (letter) => letter.toUpperCase());
const house = (value) => value == null ? '' : `House ${value}`;
const houses = (values) => (values || []).map((value) => `House ${value}`).join(', ');
const relation = (value) => value === 'aspects' ? 'aspects' : value === 'occupies' ? 'occupies' : words(value);

const afflictionText = (factor) => {
  if (!factor || typeof factor !== 'object') return '';
  if (factor.type === 'joined_by_malefics') return `joined by ${(factor.planets || []).join(', ')}`;
  if (factor.type === 'aspected_by_malefics') return `aspected by ${(factor.planets || []).join(', ')}`;
  if (factor.type === 'difficult_house') return `placed in difficult ${house(factor.house)}`;
  if (factor.type === 'debilitated') return 'debilitated';
  if (factor.type === 'combust') return 'combust';
  if (factor.type === 'inimical_sign') return `placed in a sign ruled by inimical ${factor.dispositor || 'planet'}`;
  if (factor.type === 'inimical_nakshatra_lord') return `placed in ${factor.nakshatra || 'a nakshatra'} ruled by inimical ${factor.lord || 'planet'}`;
  if (factor.type === 'waning_moon') return 'a waning Moon, which qualifies its natural support';
  return '';
};

const nakshatraQualification = (factor) => {
  const conditions = (factor.lord_affliction_details || []).map(afflictionText).filter(Boolean);
  if (factor.lord_retrograde) conditions.unshift('retrograde');
  if (!conditions.length) return '';
  return `; ${factor.lord}'s condition qualifies this support because it is ${conditions.join(' and ')}`;
};

/**
 * Converts structured engine evidence to reader-facing prose. The structured
 * object remains in the API contract; only this presentation boundary turns it
 * into copy, so future clients can still reason over the individual fields.
 */
export const formatTopicEvidence = (item) => {
  if (typeof item === 'string') return item;
  if (!item || typeof item !== 'object') return '';
  if (item.meaning) return item.meaning;
  if (item.description || item.label) return item.description || item.label;

  const planet = item.planet || 'This planet';
  const placement = [relation(item.relation), house(item.house)].filter(Boolean).join(' ');
  switch (item.type) {
    case 'natural_benefic':
      return `${planet} ${placement} as a natural benefic${item.qualified ? ', with its support qualified by other chart factors' : ''}.`;
    case 'natural_malefic':
      return `${planet} ${placement} as a natural malefic, adding pressure.`;
    case 'supportive_lordship':
      return `${planet} ${placement} with ${item.classification === 'yogakaraka' ? 'Yoga Karaka' : 'supportive'} lordship.`;
    case 'challenging_lordship':
      return `${planet} ${placement} with challenging functional lordship.`;
    case 'mixed_lordship_support':
      return `${planet} ${placement}; its lordship of ${houses(item.houses)} adds support.`;
    case 'mixed_lordship_pressure':
      return `${planet} ${placement}; its lordship of ${houses(item.houses)} adds pressure.`;
    case 'qualified_lordship':
      return `${planet} ${placement}; its ${words(item.classification)} lordship makes the result conditional.`;
    case 'friendly_sign':
      return `${planet} is placed in a sign ruled by its natural friend ${item.dispositor}.`;
    case 'nakshatra_lord_support':
      return `${planet} is in ${item.nakshatra}, ruled by ${item.relationship === 'own' ? 'itself' : `its natural friend ${item.lord}`}${nakshatraQualification(item)}.`;
    case 'joined_by_malefics':
      return `${planet} is joined by ${(item.planets || []).join(', ')}, adding pressure.`;
    case 'aspected_by_malefics':
      return `${planet} receives pressure from ${(item.planets || []).join(', ')}.`;
    case 'difficult_house':
      return `${planet} occupies health-sensitive ${house(item.house)}.`;
    case 'debilitated':
      return `${planet} is debilitated, reducing how cleanly it can deliver its indication.`;
    case 'combust':
      return `${planet} is combust, reducing how independently it can deliver its indication.`;
    case 'inimical_sign':
      return `${planet} is placed in a sign ruled by inimical ${item.dispositor}.`;
    case 'inimical_nakshatra_lord':
      return `${planet} is in ${item.nakshatra}, ruled by inimical ${item.lord}.`;
    case 'waning_moon':
      return `Moon is waning, so its natural support is treated as qualified.`;
    case 'waxing_moon':
      return 'Moon is waxing, strengthening its natural supportive role.';
    case 'yogi_support':
      return `${planet} ${placement} with Yogi support.`;
    case 'reversed_avayogi_support':
      return `${planet} ${placement}; the chart-specific Avayogi reversal adds support.`;
    case 'avayogi_pressure':
      return `${planet} ${placement} with Avayogi pressure.`;
    case 'tithi_dagdha':
      return `${planet} ${placement} from a Tithi Dagdha sign, qualifying its delivery.`;
    case 'dignity':
      return `${planet} has ${titleWords(item.value)} dignity.`;
    case 'dignity_capacity':
      return `${planet}'s ${titleWords(item.value)} dignity strengthens its capacity to deliver results.`;
    case 'vargottama_d1_d9':
    case 'vargottama_capacity':
      return `${planet} is Vargottama in D1 and D9${item.agenda === 'pressure' ? '; this strengthens its challenging agenda as well as the planet itself' : ''}.`;
    case 'divisional_reinforcement':
      return `${planet} is reinforced in ${(item.charts || []).join(', ')}.`;
    case 'divisional_capacity': {
      const strong = (item.strong_vargas || []).join(', ');
      const weak = (item.weak_vargas || []).join(', ');
      if (strong && weak) return `${planet} is strong in ${strong} and weakened in ${weak}, so divisional support is mixed.`;
      if (strong) return `${planet} gains divisional strength in ${strong}.`;
      return `${planet} is weakened in ${weak || 'the assessed divisional charts'}.`;
    }
    case 'supportive_house_placement':
      return `${planet} occupies ${house(item.house)}, a ${titleWords(item.group)}, strengthening this factor.`;
    case 'neecha_bhanga':
      return `${planet}'s debilitation is mitigated by a matched classical Neecha Bhanga condition.`;
    case 'retrograde_intensification':
      return `${planet} is retrograde, intensifying its agenda without making it automatically positive or negative.`;
    case 'mutual_sign_exchange':
    case 'mutual_exchange_capacity':
      return `${planet} exchanges signs with ${item.partner || 'the connected planet'}, linking ${houses(item.houses)}.`;
    default: {
      const details = Object.entries(item)
        .filter(([key, value]) => key !== 'type' && value != null && !Array.isArray(value) && typeof value !== 'object')
        .map(([key, value]) => `${titleWords(key)}: ${titleWords(value)}`);
      return details.length ? details.join(' · ') : 'An additional chart factor qualifies this indication.';
    }
  }
};
