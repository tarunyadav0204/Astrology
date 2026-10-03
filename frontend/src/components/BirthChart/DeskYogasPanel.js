import React, { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { apiService } from '../../services/apiService';
import './DeskYogasPanel.css';

const CATEGORY_LABELS = {
  raj_yogas: 'Raja yogas', dhana_yogas: 'Dhana yogas', mahapurusha_yogas: 'Pancha Mahapurusha yogas',
  neecha_bhanga_yogas: 'Neecha Bhanga yogas', gaja_kesari_yogas: 'Gaja Kesari yoga', amala_yogas: 'Amala yoga',
  viparita_raja_yogas: 'Viparita Raja yogas', dharma_karma_yogas: 'Dharma–Karma yogas', nabhasa_yogas: 'Nabhasa yogas',
  chandra_yogas: 'Chandra yogas', surya_yogas: 'Surya yogas', parivartana_yogas: 'Parivartana yogas',
  career_specific_yogas: 'Career yogas', health_yogas: 'Health yogas', education_yogas: 'Education yogas', marriage_yogas: 'Marriage yogas',
};
const STATUS_LABELS = { formed: 'Formed', protected: 'Condition not formed', not_formed: 'Not formed', unavailable: 'Unavailable', complete: 'Complete enclosure', boundary: 'Node-boundary case' };
const PITRI_RULES = {
  20: 'The debilitated Sun is in House 5, in a Saturn-ruled navamsha, with a malefic in both adjoining houses (H4 and H6).',
  21: 'The Sun is the fifth lord and occupies a trine (H1, H5 or H9); it is joined and aspected by malefics and is hemmed between malefics.',
  22: 'Jupiter is in Leo; the fifth lord joins the Sun; and malefics occupy both House 1 and House 5.',
  23: 'The debilitated ascendant lord is in House 5; the fifth lord joins the Sun; and malefics occupy both House 1 and House 5.',
  24: 'The ninth lord is in House 5, or the fifth lord is in House 10; and malefics occupy both House 1 and House 5.',
  25: 'Mars is the ninth lord and joins the fifth lord; and malefics occupy Houses 1, 5 and 9.',
  26: 'The ninth lord is in House 6, 8 or 12; Jupiter is in a sign ruled by the Sun, Mars or Saturn; and the fifth lord and ascendant lord each join a malefic.',
  27: 'The Sun, Mars and Saturn are distributed across Houses 1 and 5, with both houses occupied; Rahu is in House 8; and Jupiter is in House 12.',
  28: 'The Sun is in House 8; Saturn is in House 5; the fifth lord joins Rahu; and a malefic occupies House 1.',
  29: 'The twelfth lord is in House 1; the eighth lord is in House 5; and the ninth lord is in House 8.',
  30: 'The sixth lord is in House 5; the ninth lord is in House 6; and Jupiter, the progeny significator in this chapter, joins Rahu.',
};
const MATRI_RULES = {
  34: 'Moon is the fifth lord and is debilitated or hemmed between malefics; malefics also occupy Houses 4 and 5.',
  35: 'Saturn is in House 11, a malefic is in House 4, and the debilitated Moon is in House 5.',
  36: 'The fifth lord is in House 6, 8 or 12, the ascendant lord is debilitated, and Moon joins a malefic.',
  37: 'The fifth lord is in House 6, 8 or 12, Moon is in a malefic-ruled navamsha, and malefics occupy Houses 1 and 5.',
  38: 'Moon is the fifth lord, occupies House 5 or 9, and joins Saturn, Rahu and Mars.',
  39: 'Mars is the fourth lord and joins Saturn and Rahu; Sun occupies House 5 and Moon occupies House 1.',
  40: 'The ascendant and fifth lords are in House 6, the fourth lord is in House 8, and the eighth and tenth lords are in House 1.',
  41: 'The sixth and eighth lords are in House 1, the fourth lord is in House 12, and Moon and Jupiter join malefics in House 5.',
  42: 'The ascendant is hemmed between malefics, waning Moon is in House 7, Rahu is in House 4 and Saturn is in House 5.',
  43: 'The fifth and eighth lords exchange Houses 5 and 8; Moon and the fourth lord occupy Houses 6, 8 or 12.',
  44: 'Cancer rises with Mars and Rahu in House 1; Moon and Saturn occupy House 5.',
  45: 'Mars, Rahu, Sun and Saturn occupy Houses 1, 5, 8 and 12 respectively; the ascendant and fourth lords are in Houses 6, 8 or 12.',
  46: 'Mars, Rahu and Jupiter occupy House 8; Saturn and Moon occupy House 5.',
};
const asArray = (value) => (Array.isArray(value) ? value : value == null ? [] : [value]);
const displayValue = (value) => typeof value === 'string' || typeof value === 'number' ? String(value) : value?.name || value?.planet || value?.label || '';
const categoryLabel = (key, parent) => parent
  ? `${CATEGORY_LABELS[parent]} · ${key.replace(/_yogas?$/, '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}`
  : CATEGORY_LABELS[key] || key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

export function buildYogaCategories(payload) {
  if (!payload || typeof payload !== 'object') return [];
  return Object.entries(payload).filter(([key]) => key !== 'major_doshas').flatMap(([key, value]) => {
    if ((key === 'nabhasa_yogas' || key === 'parivartana_yogas') && value && typeof value === 'object' && !Array.isArray(value)) {
      return Object.entries(value).map(([subKey, items]) => ({ key: `${key}_${subKey}`, label: categoryLabel(subKey, key), items }));
    }
    const items = key === 'marriage_yogas' ? asArray(value).filter((item) => item?.name !== 'Mangal Dosha') : value;
    return [{ key, label: categoryLabel(key), items }];
  }).filter(({ items }) => Array.isArray(items) && items.length);
}

export function buildDoshaCategories(payload) {
  const doshas = payload?.major_doshas;
  if (!doshas) return [];
  const result = [];
  const mangal = doshas.mangal_dosha;
  if (mangal) result.push({ key: 'mangal_dosha', label: 'Mangal Dosha', info: 'mangal', items: [{
    name: 'Mangal Dosha', description: mangal.summary, displayStatus: mangal.status, planets: ['Mars'], houses: mangal.mars_house_lagna ? [mangal.mars_house_lagna] : [],
    classical_conditions: asArray(mangal.evidence).filter((row) => row.rule_id !== 'MS-DHANE-VARIANT' || row.material_difference).map((row) => ({ rule_id: row.rule_id, description: row.fact, matched: row.matched })),
    source: mangal.source, textualNote: mangal.source?.textual_note,
    variantSource: mangal.textual_variants?.[0]?.material_difference ? mangal.textual_variants[0]?.source?.reference_label : null,
    variantMatched: !mangal.primary_reading?.matched && mangal.textual_variants?.some((row) => row.matched),
  }] });
  const nodal = doshas.kaal_sarp_dosha;
  if (nodal) {
    const direction = nodal.direction_label || 'Rahu → Ketu';
    const contained = asArray(nodal.contained_planets).join(', ') || '—';
    const outside = asArray(nodal.outside_planets).join(', ') || '—';
    const boundary = asArray(nodal.boundary_planets).map((row) => `${row.planet}–${row.node}`).join(', ') || '—';
    const description = { complete: `All seven visible planets lie within the ${direction} nodal half.`, boundary: `All seven visible planets lie within ${direction}, with ${boundary} exactly on a node boundary.`, not_formed: `No complete nodal enclosure is present; ${outside} lies outside the more populated nodal half.`, unavailable: 'The check is unavailable because one or more exact longitudes are missing.' }[nodal.status] || nodal.summary;
    result.push({ key: 'nodal_enclosure', label: 'Rahu–Ketu nodal enclosure', items: [{ name: 'Rahu–Ketu nodal enclosure', description, displayStatus: nodal.status, planets: ['Rahu', 'Ketu'], source: nodal.source, basisTitle: 'Calculation basis', classical_conditions: [{ rule_id: 'NODE-ENCLOSURE-EXACT', description: `Direction: ${direction} · Inside: ${contained} · Outside: ${outside}`, matched: nodal.present }, ...(asArray(nodal.boundary_planets).length ? [{ rule_id: 'NODE-BOUNDARY-EXACT', description: `Exact node boundary: ${boundary}`, matched: true }] : [])], textualNote: 'This is a later convention, not a verified rule from a named classical verse. No effects, severity, remedies, cancellations or named variants are inferred.' }] });
  }
  [['pitra_dosha', 'pitri_shapa', 'Pitṛ-śāpa · progeny', 'pitri', 11, [5], 'BPHS 83.20–30'], ['matru_dosha', 'matri_shapa', 'Mātṛ-śāpa · progeny', 'matri', 13, [4, 5], 'BPHS 83.34–46']].forEach(([sourceKey, key, name, info, count, houses, range]) => {
    const check = doshas[sourceKey]; if (!check) return;
    const matched = asArray(check.matched_rules);
    const evidence = matched.length ? matched.flatMap((rule) => [{ rule_id: rule.rule_id, description: `${rule.reference}: ${rule.description}`, matched: true }, ...asArray(rule.conditions).map((condition) => ({ rule_id: `${rule.rule_id}-${condition.key}`, description: condition.label, matched: condition.matched }))]) : [{ rule_id: `${key}-none`, description: `None of the ${count === 11 ? 'eleven' : 'thirteen'} complete combinations in ${range} matches this chart.`, matched: false }];
    result.push({ key, label: name, info, items: [{ name, description: check.present ? `${matched.length} complete BPHS ${name.split(' · ')[0]} combination${matched.length === 1 ? '' : 's'} match this chart.` : `None of the ${count === 11 ? 'eleven' : 'thirteen'} complete BPHS ${name.split(' · ')[0]} combinations matches this chart.`, displayStatus: check.status, planets: check.planets || [], houses: check.present ? houses : [], classical_conditions: evidence, source: check.source, textualNote: sourceKey === 'pitra_dosha' ? 'This classical check concerns progeny. A Sun–Rahu or Sun–Saturn conjunction, a node in House 9, or an afflicted ninth lord does not form it by itself.' : 'This classical check concerns progeny. Moon–Rahu, Moon–Saturn, a malefic in House 4, or an afflicted fourth lord does not form it by itself.' }] });
  });
  return result;
}

function SourceReference({ item }) {
  const reference = item.source?.reference_label || asArray(item.references)
    .map((entry) => typeof entry === 'string' ? entry : entry?.reference_label || entry?.reference || entry?.label)
    .filter(Boolean)
    .join(', ');
  if (!reference && !item.textualNote && !item.source?.textual_note && !item.variantSource && !item.variant_readings?.length) return null;
  return <div className="desk-yogas__source">{reference ? <div className="desk-yogas__reference"><span aria-hidden="true">▤</span> <strong>Reference:</strong> {reference}</div> : null}{item.textualNote || item.source?.textual_note ? <p><strong>Textual note:</strong> {item.textualNote || item.source?.textual_note}</p> : null}{asArray(item.variant_readings).map((variant, index) => <p key={`${variant.source?.reference_label || 'variant'}-${index}`}><strong>Separate reading{variant.source?.reference_label ? ` · ${variant.source.reference_label}` : ''}:</strong> {variant.reason}</p>)}{item.variantSource ? <p><strong>Separate reading:</strong> {item.variantSource}</p> : null}{item.variantMatched ? <p className="desk-yogas__variant">The separate second-house reading matches this chart.</p> : null}</div>;
}

function YogaItem({ item, index }) {
  const badge = item.displayStatus || item.strength;
  const planets = asArray(item.planets).map(displayValue).filter(Boolean);
  const houses = asArray(item.houses).filter((house) => house !== '' && house != null);
  return <article className="desk-yogas__item"><header className="desk-yogas__item-head"><span className="desk-yogas__ordinal">{String(index + 1).padStart(2, '0')}</span><h4>{item.name || item.yoga_name || item.type || 'Yoga'}</h4>{badge ? <span className={`desk-yogas__badge desk-yogas__badge--${String(badge).toLowerCase().replace(/[^a-z]+/g, '-')}`}>{item.displayStatus ? STATUS_LABELS[item.displayStatus] || String(item.displayStatus).replace(/_/g, ' ') : badge}</span> : null}</header>
    {item.description || item.effects || item.effect || item.meaning || item.note ? <p className="desk-yogas__description">{item.description || item.effects || item.effect || item.meaning || item.note}</p> : null}
    {asArray(item.classical_conditions).length ? <section className="desk-yogas__basis"><h5>{item.basisTitle || 'Classical basis'}</h5>{asArray(item.classical_conditions).map((condition, conditionIndex) => <div className="desk-yogas__condition" key={condition.rule_id || conditionIndex}><span className={condition.matched ? 'is-matched' : ''} aria-hidden="true">{condition.matched ? '✓' : '○'}</span><p>{condition.description}</p></div>)}{item.classical_result ? <div className="desk-yogas__classical-result"><strong>What the classic says</strong><p>{item.classical_result}</p></div> : null}<SourceReference item={item} /></section> : <SourceReference item={item} />}
    {item.result_delivery?.channels?.length ? <section className="desk-yogas__delivery"><h5>Where {item.planet || 'this planet'} can deliver results</h5><p>Debilitation is cancelled by the classical rule shown above. Other chart pressures still qualify the result.</p><div className="desk-yogas__meta">{item.result_delivery.channels.map((channel) => <span key={`${item.planet}-${channel.house}`}>H{channel.house}</span>)}</div><small>These are delivery areas, not a promise that every result will be positive.</small></section> : null}
    {planets.length || houses.length ? <div className="desk-yogas__meta">{planets.map((planet, planetIndex) => <span key={`${planet}-${planetIndex}`}>◉ {planet}</span>)}{houses.length ? <span>▦ H{houses.join(', H')}</span> : null}</div> : null}</article>;
}

function RulesModal({ type, raw, onClose }) {
  if (!type || typeof document === 'undefined') return null;
  const isPitri = type === 'pitri'; const isMatri = type === 'matri';
  const check = isPitri ? raw?.major_doshas?.pitra_dosha : isMatri ? raw?.major_doshas?.matru_dosha : raw?.major_doshas?.mangal_dosha;
  const matchedIds = new Set(check?.matched_rule_ids || []); const rules = isPitri ? PITRI_RULES : MATRI_RULES;
  const title = isPitri ? 'Complete classical Pitṛ-śāpa rules' : isMatri ? 'Complete classical Mātṛ-śāpa rules' : 'Complete classical Mangal Dosha rules';
  const range = isPitri ? 'BPHS 83.20–30' : isMatri ? 'BPHS 83.34–46' : 'BPHS 80.47';
  return createPortal(<div className="desk-yogas-modal" role="dialog" aria-modal="true" aria-labelledby="yoga-rules-title"><button className="desk-yogas-modal__backdrop" type="button" onClick={onClose} aria-label="Close" /><section className="desk-yogas-modal__sheet"><header><div><span>{range}</span><h2 id="yoga-rules-title">{title}</h2></div><button type="button" onClick={onClose} aria-label="Close">×</button></header><div className="desk-yogas-modal__body">
    {type === 'mangal' ? <><p>The selected verdict follows one complete BPHS rule. The separate second-house reading and counts from the Moon and Venus remain separate.</p><section className="desk-yogas-modal__scope"><h3>Primary BPHS formation</h3><p>Mangal Dosha is formed only when Mars is in House 1, 4, 7, 8 or 12 from the natal Lagna and Mars has no benefic conjunction or Parashari graha aspect. Both conditions are required.</p></section><h3>How this chart was judged</h3><div className="desk-yogas-modal__verdict"><strong>{STATUS_LABELS[check?.status] || check?.status}</strong><p>Mars is in House {check?.mars_house_lagna ?? '—'} from Lagna.</p>{asArray(check?.evidence).map((row) => <p key={row.rule_id}>{row.matched ? '✓' : '○'} {row.fact}</p>)}</div><h3>Three reference counts</h3><p>The Lagna count controls the verdict. Counts from Moon and Venus are supplementary traditional evidence.</p><ul><li>From Lagna: House {check?.mars_house_lagna ?? '—'}</li><li>From Moon: House {check?.mars_house_moon ?? '—'}</li><li>From Venus: House {check?.mars_house_venus ?? '—'}</li></ul><h3>Calculation boundaries</h3><ul><li>Jupiter and Venus are natural benefics for this clause.</li><li>The waxing Moon is benefic; the waning Moon is not used as benefic protection.</li><li>Mercury is benefic unless joined by a natural malefic.</li><li>Qualifying benefics use the seventh aspect; Jupiter also uses its fifth and ninth aspects. Conjunction means the same sign.</li><li>The source gives no Low, Medium, High or percentage intensity, so none is invented.</li><li>D9-house counting, age-28 expiry, sign-based cancellations, rituals and gemstone advice are not added.</li></ul><section className="desk-yogas-modal__source"><h3>Classical references</h3><p>Primary formation: Brihat Parashara Hora Shastra 80.47, beginning “lagne vyaye sukhe vapi…”</p><p>Separate second-house reading: Agastya Samhita, verse beginning “dhane vyaye ca patale…”</p><p>Two-chart balancing: Muhurta Chintamani, Vivaha appendix, verse 50.</p></section></> : <><p>{isPitri ? 'This panel shows the exact eleven combinations evaluated by AstroRoshni.' : 'This check evaluates the thirteen complete combinations stated in BPHS.'} It does not combine incomplete verses into a dosha.</p><section className="desk-yogas-modal__scope"><h3>Classical scope: progeny</h3><p>These verses concern loss or absence of progeny. They are not a general label for ancestral, maternal, relationship, or health difficulties.</p></section><h3>When the combination is formed</h3><p>Any one verse below must match in full. Every clause within that verse is required. Conditions from different verses are never mixed, and partial matches are not scored.</p><div className="desk-yogas-modal__rules">{Object.entries(rules).map(([verse, description]) => { const ruleId = `${isPitri ? 'BPHS-PS' : 'BPHS-MS'}-${verse}`; const matched = matchedIds.has(ruleId); return <div className={matched ? 'is-matched' : ''} key={ruleId}><header><strong>BPHS 83.{verse}</strong>{matched ? <span>Matches this chart</span> : null}</header><p>{description}</p></div>; })}</div><h3>Calculation decisions</h3><ul><li>Every clause of a verse must match.</li><li>Moon is classified by phase; Mercury becomes malefic only through conjunction with a malefic.</li><li>Debated fifth and ninth aspects of Rahu and Ketu are not introduced.</li><li>The text provides no Low, Medium or High grading.</li></ul><section className="desk-yogas-modal__source"><h3>Classical reference</h3><p>Brihat Parashara Hora Shastra, Purvajanma-shapa-dyotana, verses {isPitri ? '20–30' : '34–46'}. Chapter numbering varies by edition.</p></section></>}
  </div></section></div>, document.body);
}

export default function DeskYogasPanel({ birthData, chartData = null, calculationProfile = null }) {
  const [raw, setRaw] = useState(null); const [loading, setLoading] = useState(false); const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState('yogas'); const [expanded, setExpanded] = useState(new Set()); const [modal, setModal] = useState(null);
  useEffect(() => { if (!birthData?.date || !birthData?.time) { setRaw(null); return undefined; } let cancelled = false; setLoading(true); setError(''); apiService.getYogas(birthData, chartData, calculationProfile).then((data) => { if (!cancelled) { setRaw(data?.yogas || data || null); setExpanded(new Set()); } }).catch((err) => { if (!cancelled) { setRaw(null); setError(err?.response?.data?.detail || err.message || 'Failed to load yogas and doshas'); } }).finally(() => { if (!cancelled) setLoading(false); }); return () => { cancelled = true; }; }, [birthData, chartData, calculationProfile]);
  const yogaCategories = useMemo(() => buildYogaCategories(raw), [raw]); const doshaCategories = useMemo(() => buildDoshaCategories(raw), [raw]);
  const categories = activeSection === 'doshas' ? doshaCategories : yogaCategories; const total = categories.reduce((sum, category) => sum + category.items.length, 0);
  useEffect(() => { if (categories.length && !expanded.size) setExpanded(new Set([categories[0].key])); }, [categories, expanded.size]);
  const toggle = (key) => setExpanded((current) => { const next = new Set(current); if (next.has(key)) next.delete(key); else next.add(key); return next; });
  if (loading) return <div className="desk-yogas desk-yogas--status"><span className="desk-yogas__loader" />Calculating classical yogas and doshas…</div>;
  if (error) return <div className="desk-yogas desk-yogas--status desk-yogas--err">{error}</div>;
  if (!raw) return <div className="desk-yogas desk-yogas--status">Chart details are required to calculate yogas and doshas.</div>;
  return <div className="desk-yogas" aria-label="Classical yogas and doshas">
    <div className="desk-yogas__tabs" role="tablist">
      <button type="button" role="tab" aria-selected={activeSection === 'yogas'} className={activeSection === 'yogas' ? 'is-active' : ''} onClick={() => { setActiveSection('yogas'); setExpanded(new Set()); }}>
        Yogas <span>{yogaCategories.reduce((n, c) => n + c.items.length, 0)}</span>
      </button>
      <button type="button" role="tab" aria-selected={activeSection === 'doshas'} className={activeSection === 'doshas' ? 'is-active' : ''} onClick={() => { setActiveSection('doshas'); setExpanded(new Set()); }}>
        Doshas <span>{doshaCategories.length}</span>
      </button>
    </div>
    <div className="desk-yogas__body">
      {activeSection === 'doshas' ? <p className="desk-yogas__intro">Each check states whether it comes from a named classic or a later convention, and shows the exact rule or geometry used.</p> : null}
      <div className="desk-yogas__categories">
        {!total ? <div className="desk-yogas__empty">No {activeSection === 'doshas' ? 'dosha checks are available' : 'classical yogas are formed'} for this chart.</div> : categories.map((category) => {
          const open = expanded.has(category.key);
          return <section className="desk-yogas__category" key={category.key}>
            <header className="desk-yogas__category-head">
              <button type="button" onClick={() => toggle(category.key)} aria-expanded={open}>
                <span><strong>{category.label}</strong><small>{category.items.length} {category.items.length === 1 ? 'finding' : 'findings'}</small></span>
                <span aria-hidden="true">{open ? '−' : '+'}</span>
              </button>
              {category.info ? <button className="desk-yogas__info" type="button" onClick={() => setModal(category.info)} aria-label={`Read complete rules for ${category.label}`}>i</button> : null}
            </header>
            {open ? <div className="desk-yogas__items">{category.items.map((item, index) => <YogaItem item={item} index={index} key={`${item.name || 'item'}-${index}`} />)}</div> : null}
          </section>;
        })}
      </div>
    </div>
    <RulesModal type={modal} raw={raw} onClose={() => setModal(null)} />
  </div>;
}
