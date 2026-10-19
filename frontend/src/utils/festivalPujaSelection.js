// Match saved/router spelling to a dropdown value without losing unknown rites.
const normalized = value => String(value || '').toLowerCase().replace(/pooja/g, 'puja').replace(/[_/–—-]+/g, ' ').replace(/\s+/g, ' ').trim();
export const selectedRitualValue = (festival, value) => {
  if (['','puja','main puja','पूजा'].includes(normalized(value))) {
    return festival?.ritual_options?.find(item=>item.supported && item.value===festival.ritual)?.value
      || festival?.ritual_options?.find(item=>item.supported)?.value || '';
  }
  const option = (festival?.ritual_options || []).find(item => [item.value, ...(item.aliases || [])].some(alias => normalized(alias) === normalized(value)));
  return option?.value || value;
};

// Canonicalize incoming setup values before showing the activity control.
// A selected festival is authoritative even if an older draft retained vehicle.
export const initializeMuhuratDraft = (initial = {}, catalog = []) => {
  const event = normalized(initial.event_type);
  const festival = catalog.find(item => item.id === initial.festival_id)
    || catalog.find(item => normalized(item.id) === event || normalized(item.name) === event
      || `${normalized(item.id)} puja` === event || `${normalized(item.name)} puja` === event);
  const isPuja = Boolean(initial.festival_id || festival)
    || ['festival puja','festival','puja','puja muhurat','festival puja muhurat','puja vrat'].includes(event);
  const aliases = {'griha pravesh':'home','business opening':'business'};
  const eventType = isPuja ? 'festival_puja' : aliases[event] || initial.event_type || '';
  const draft = {
    minimum_duration_minutes:15, personalized:false, ...initial,
    event_type:eventType,
    allowed_start:initial.allowed_start || (isPuja ? '00:00' : '08:00'),
    allowed_end:initial.allowed_end || (isPuja ? '23:59' : '18:00'),
  };
  if (festival) draft.festival_id = festival.id;
  if (isPuja) {
    const year = Number(draft.festival_year) || Number(String(draft.start_date || '').slice(0,4)) || new Date().getFullYear();
    draft.festival_year = year;
    if (!draft.start_date && !draft.end_date) {
      draft.start_date = `${year}-01-01`; draft.end_date = `${year}-12-31`;
    }
  }
  return draft;
};
