import React, { useEffect, useMemo, useState } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import './AdminSutraAuthoring.css';

const blankCondition = () => ({ id: crypto.randomUUID(), subject_type: 'planet', stream: 'parashari', chart: 'D1', subject: { planet: 'Sun' }, predicate: 'in_sign', operator: 'equals', value: '' });
const blankRule = () => ({
  rule_key: '', title: '', status: 'draft', primary_stream: 'jaimini', primary_chart: 'D1', category: 'self', subcategory: 'identity', tags: [],
  authority: { work: '', reference: '', commentary_school: '', literal_text: '' }, logic_operator: 'all',
  conditions: [blankCondition()], modifiers: { supports: [], weakens: [], exceptions: [] },
  outputs: { user_summary: '', user_reason: '', astrologer_interpretation: '' }, visibility: 'astrologer_only',
  safety: { forbid_deterministic_claim: true, require_counterevidence: true }, reviewer_notes: '',
});

const api = async (path, options = {}) => {
  const response = await fetch(`/api/admin/sutra-rules${path}`, { headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' }, ...options });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || 'Could not complete request');
  return body;
};

function ConditionRow({ condition, catalog, onChange, onRemove, label }) {
  const subjectTypes = catalog?.subject_types || {};
  const type = subjectTypes[condition.subject_type] || subjectTypes.planet;
  // A rule saved under a newer grammar must never crash an older frontend or
  // a frontend whose catalog request was interrupted. The parent only renders
  // rows once the typed catalog is available; this is the final defensive guard.
  if (!type) return null;
  const fields = type?.fields || [];
  const updateSubject = (field, value) => onChange({ ...condition, subject: { ...condition.subject, [field]: value } });
  const subjectOptions = (field) => ({ planet: catalog.planets || [], house: catalog.houses || [], cusp: catalog.houses || [], relative_house: catalog.houses || [], house_reference: catalog.house_references || [], karaka: catalog.karakas || [], arudha: catalog.arudhas || [], dasha_level: ['maha', 'antar', 'pratyantar'] }[field] || []);
  return <div className="sutra-condition">
    <select aria-label={`${label} subject type`} value={condition.subject_type} onChange={(e) => { const next = subjectTypes[e.target.value]; onChange({ ...blankCondition(), id: condition.id, subject_type: e.target.value, stream: next.streams[0], chart: condition.chart || 'D1', subject: Object.fromEntries(next.fields.map((field) => [field, subjectOptions(field)[0] || ''])), predicate: Object.keys(next.predicates)[0] }); }}>
      {Object.entries(subjectTypes).map(([key, item]) => <option key={key} value={key}>{item.label}</option>)}
    </select>
    <select aria-label={`${label} stream`} value={condition.stream} onChange={(e) => onChange({ ...condition, stream: e.target.value })}>
      {type.streams.map((stream) => <option key={stream} value={stream}>{stream}</option>)}
    </select>
    {fields.map((field) => <select key={field} aria-label={`${label} ${field}`} value={condition.subject?.[field] || ''} onChange={(e) => updateSubject(field, e.target.value)}><option value="">{field.replaceAll('_',' ')}</option>{subjectOptions(field).map((value) => <option key={value} value={value}>{value}</option>)}</select>)}
    <select aria-label={`${label} chart`} value={condition.chart || ''} onChange={(e) => onChange({ ...condition, chart: e.target.value })}>
      {(catalog.charts || []).map((chart) => <option key={chart} value={chart}>{chart}</option>)}
    </select>
    <select aria-label={`${label} predicate`} value={condition.predicate} onChange={(e) => onChange({ ...condition, predicate: e.target.value, value: '' })}>{Object.entries(type.predicates).map(([key, value]) => <option key={key} value={key}>{value}</option>)}</select>
    <select aria-label={`${label} operator`} value={condition.operator} onChange={(e) => onChange({ ...condition, operator: e.target.value })}>
      {(catalog.operators || []).map((operator) => <option key={operator} value={operator}>{operator.replaceAll('_', ' ')}</option>)}
    </select>
    <input aria-label={`${label} value`} value={condition.value ?? ''} placeholder="Required comparison value" onChange={(e) => onChange({ ...condition, value: e.target.value })} />
    <button type="button" className="sutra-icon-button" onClick={onRemove} aria-label={`Remove ${label}`}>×</button>
  </div>;
}

export default function AdminSutraAuthoring() {
  const [catalog, setCatalog] = useState({ streams: [], charts: [], categories: {}, subject_types: {}, visibility: [], operators: [] });
  const [rules, setRules] = useState([]); const [rule, setRule] = useState(blankRule); const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false); const [message, setMessage] = useState('');
  const load = async () => { setLoading(true); try { const [c, r] = await Promise.all([api('/catalog'), api('')]); setCatalog(c); setRules(r.rules || []); } catch (e) { setMessage(e.message); } finally { setLoading(false); } };
  useEffect(() => { load(); }, []);
  const update = (key, value) => setRule((old) => ({ ...old, [key]: value }));
  const updateNested = (group, index, value) => setRule((old) => ({ ...old, [group]: old[group].map((item, i) => i === index ? value : item) }));
  const addCondition = (group = 'conditions') => setRule((old) => group === 'conditions' ? ({ ...old, conditions: [...old.conditions, blankCondition()] }) : ({ ...old, modifiers: { ...old.modifiers, [group]: [...old.modifiers[group], blankCondition()] } }));
  const removeCondition = (group, index) => setRule((old) => group === 'conditions' ? ({ ...old, conditions: old.conditions.filter((_, i) => i !== index) }) : ({ ...old, modifiers: { ...old.modifiers, [group]: old.modifiers[group].filter((_, i) => i !== index) } }));
  const save = async () => { setSaving(true); setMessage(''); try { const result = await api(editingId ? `/${editingId}` : '', { method: editingId ? 'PUT' : 'POST', body: JSON.stringify(rule) }); setEditingId(result.id); setMessage('Saved as a governed draft. It is not available to chat or users.'); await load(); } catch (e) { setMessage(e.message); } finally { setSaving(false); } };
  const edit = (item) => { setEditingId(item.id); setRule({ ...blankRule(), ...item, authority: item.authority || {}, conditions: item.conditions || [], modifiers: { supports: [], weakens: [], exceptions: [], ...(item.modifiers || {}) }, outputs: item.outputs || {} }); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const subcategories = catalog.categories?.[rule.category] || [];
  const hasTypedCatalog = Object.keys(catalog.subject_types || {}).length > 0;
  if (loading) return <div className="sutra-authoring"><p>Loading classical-rule studio…</p></div>;
  if (!hasTypedCatalog) return <section className="sutra-authoring"><div className="sutra-message" role="alert">The rule editor could not load its typed calculation catalog. Reload this page; if it persists, restart the backend so the Sutra routes are updated.</div></section>;
  return <section className="sutra-authoring">
    <header className="sutra-hero"><div><span>CLASSICAL RULE STUDIO</span><h2>Author a Sutra</h2><p>Store the original authority first, then its explicit AstroRoshni operationalization. Nothing authored here is live.</p></div><div className="sutra-status">{rules.length} rules<br/><small>all governed</small></div></header>
    {message && <div className="sutra-message" role="status">{message}</div>}
    <div className="sutra-layout"><main className="sutra-editor">
      <section><b>01 · Classical basis</b><div className="sutra-grid two"><label>Rule key<input value={rule.rule_key} placeholder="JAI.UP.2.RELATIONSHIP_PRESSURE" onChange={(e) => update('rule_key', e.target.value)} /></label><label>Working title<input value={rule.title} placeholder="Pressure on partnership sustenance" onChange={(e) => update('title', e.target.value)} /></label></div><div className="sutra-grid three"><label>Primary stream<select value={rule.primary_stream} onChange={(e) => update('primary_stream', e.target.value)}>{catalog.streams.map((x) => <option key={x}>{x}</option>)}</select></label><label>Primary chart<select value={rule.primary_chart} onChange={(e) => update('primary_chart', e.target.value)}>{catalog.charts.map((x) => <option key={x}>{x}</option>)}</select></label><label>Status<select value={rule.status} onChange={(e) => update('status', e.target.value)}>{['draft','review','active','deprecated'].map((x) => <option key={x}>{x}</option>)}</select></label></div><div className="sutra-grid two"><label>Classical work<input value={rule.authority.work || ''} placeholder="Jaimini Upadesa Sutras" onChange={(e) => update('authority', { ...rule.authority, work: e.target.value })} /></label><label>Chapter / sutra reference<input value={rule.authority.reference || ''} placeholder="Upapada section · source edition reference" onChange={(e) => update('authority', { ...rule.authority, reference: e.target.value })} /></label></div><label>Literal source / translation<textarea value={rule.authority.literal_text || ''} placeholder="Store the source wording before interpretation…" onChange={(e) => update('authority', { ...rule.authority, literal_text: e.target.value })} /></label></section>
      <section><b>02 · Portrait placement</b><p className="sutra-hint">This controls where a matched insight belongs. It does not alter the calculation.</p><div className="sutra-grid three"><label>Category<select value={rule.category} onChange={(e) => { const category=e.target.value; update('category',category); update('subcategory',(catalog.categories?.[category]||[])[0]||''); }}>{Object.keys(catalog.categories||{}).map((x)=><option key={x} value={x}>{x.replaceAll('_',' ')}</option>)}</select></label><label>Subcategory<select value={rule.subcategory} onChange={(e)=>update('subcategory',e.target.value)}>{subcategories.map((x)=><option key={x} value={x}>{x.replaceAll('_',' ')}</option>)}</select></label><label>Tags<input value={(rule.tags||[]).join(', ')} placeholder="e.g. Venus, first impression" onChange={(e)=>update('tags',e.target.value.split(',').map((x)=>x.trim()).filter(Boolean))}/></label></div></section>
      <section><b>03 · Match logic</b><p className="sutra-hint">Every row is an explicit calculation. Use the group operator to combine them.</p><div className="sutra-toolbar"><select value={rule.logic_operator} onChange={(e) => update('logic_operator', e.target.value)}><option value="all">ALL conditions must match</option><option value="any">ANY condition may match</option><option value="at_least">At least N conditions match</option></select><button type="button" onClick={() => addCondition()}>+ Required condition</button></div>{rule.conditions.map((condition, i) => <ConditionRow key={condition.id} label="Required condition" condition={condition} catalog={catalog} onChange={(value) => updateNested('conditions', i, value)} onRemove={() => removeCondition('conditions', i)} />)}</section>
      <section><b>04 · Context and counterevidence</b>{['supports','weakens','exceptions'].map((group) => <div className="sutra-modifier" key={group}><div><strong>{group}</strong><button type="button" onClick={() => addCondition(group)}>+ Add</button></div>{rule.modifiers[group].map((condition, i) => <ConditionRow key={condition.id} label={group} condition={condition} catalog={catalog} onChange={(value) => setRule((old) => ({ ...old, modifiers: { ...old.modifiers, [group]: old.modifiers[group].map((item, n) => n === i ? value : item) } }))} onRemove={() => removeCondition(group, i)} />)}</div>)}</section>
      <section><b>05 · Outputs and visibility</b><div className="sutra-grid two"><label>User summary<textarea value={rule.outputs.user_summary || ''} placeholder="Warm, plain-language tendency…" onChange={(e) => update('outputs', { ...rule.outputs, user_summary: e.target.value })} /></label><label>User reason<textarea value={rule.outputs.user_reason || ''} placeholder="Translated astrological reason…" onChange={(e) => update('outputs', { ...rule.outputs, user_reason: e.target.value })} /></label></div><label>Astrologer interpretation<textarea value={rule.outputs.astrologer_interpretation || ''} placeholder="Technical interpretation and boundary…" onChange={(e) => update('outputs', { ...rule.outputs, astrologer_interpretation: e.target.value })} /></label><div className="sutra-grid two"><label>Visibility<select value={rule.visibility} onChange={(e) => update('visibility', e.target.value)}>{catalog.visibility.map((x) => <option key={x}>{x.replaceAll('_',' ')}</option>)}</select></label><label>Reviewer notes<textarea value={rule.reviewer_notes} placeholder="Open questions, edition differences, test notes…" onChange={(e) => update('reviewer_notes', e.target.value)} /></label></div></section>
      <footer><button type="button" className="sutra-save" disabled={saving || !rule.rule_key || !rule.title} onClick={save}>{saving ? 'Saving…' : editingId ? 'Save revision' : 'Save governed draft'}</button><button type="button" onClick={() => { setRule(blankRule()); setEditingId(null); }}>New rule</button></footer>
    </main><aside className="sutra-library"><h3>Rule library</h3>{rules.length === 0 ? <p>No authored rules yet.</p> : rules.map((item) => <button type="button" key={item.id} onClick={() => edit(item)}><span>{item.status}</span><strong>{item.title}</strong><small>{item.rule_key} · {item.primary_stream} / {item.primary_chart}</small></button>)}</aside></div>
  </section>;
}
