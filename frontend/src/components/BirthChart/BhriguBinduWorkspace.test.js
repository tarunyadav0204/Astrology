import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { Workspace, makeCalendar } from './BhriguBinduWorkspace';
import { apiService } from '../../services/apiService';
global.IS_REACT_ACT_ENVIRONMENT = true;
jest.mock('../../services/apiService', () => ({
  apiService: {
    getBhriguBinduWorkspace: jest.fn()
  }
}));
jest.mock('../Charts/ChartWidget', () => () => <div>Linked natal chart</div>);
const birth = {
  name: 'Synthetic',
  date: '1990-01-01',
  time: '12:00:42',
  latitude: 28,
  longitude: 77
};
const point = {
 point:'Bhrigu Bindu', position:'Taurus 29° 39′ 30″', house:2, sign_name:'Taurus',
 dispositor:'Venus', dispositor_position:'Cancer 12°', dispositor_strength:null,
 relationships:[], nakshatra:'Mrigashira', nakshatra_lord:'Mars', pada:2,
 moon_position:'Libra 12°13′', rahu_position:'Capricorn 17°06′', forward_arc_degrees:265.1166667,
};
const event = {
  id: 'Rahu:Saturn:contact:2026-10-18',
  point: 'Bhrigu Bindu',
  planet: 'Saturn',
  kind: 'natal_contact',
  aspect_number: 1,
  start_at: '2026-10-18T00:00:00+00:00',
  end_at: '2026-10-19T00:00:00+00:00',
  exact_passes: [{
    at: '2026-10-18T12:00:00+00:00',
    motion: 'retrograde'
  }],
  dasha_overlaps: []
};
const fixture = {
  schema_version: 'test',
  natal: {
    points: [point],
    affected_count: 1,
    degree_semantics: 'Ordinal span',
    source: 'Named table'
  },
  natal_chart: {},
  birth_time_comparison: [],
  dasha_activations: [],
  events: [event],
  calendar_calculated: false,
  range: {
    timezone: 'UTC',
    start_at: event.start_at,
    end_at: event.end_at
  },
  audit: {
    limits: [],
    sources: [],
    ayanamsha: 'lahiri',
    node_type: 'mean'
  }
};
let host, root;
const click = async text => {
  const button = [...host.querySelectorAll('button')].find(b => b.textContent === text);
  expect(button).toBeTruthy();
  await act(async () => {
    button.dispatchEvent(new MouseEvent('click', {
      bubbles: true
    }));
  });
};
beforeEach(() => {
  localStorage.clear();
  host = document.createElement('div');
  document.body.append(host);
  root = createRoot(host);
  apiService.getBhriguBinduWorkspace.mockReset();
  apiService.getBhriguBinduWorkspace.mockImplementation(async (b, options) => ({
    ...fixture,
    calendar_calculated: options.calendar
  }));
});
afterEach(() => {
  act(() => root.unmount());
  host.remove();
});
test('loads directed Bindu assessment and prepares Tara draft only on request', async () => {
 const onAsk=jest.fn(),onClose=jest.fn();
 await act(async () => root.render(<Workspace birthData={birth} onClose={onClose} onAsk={onAsk} />));
 expect(host.textContent).toContain('Taurus 29° 39′ 30″');
 expect(host.textContent).toContain('forward from Rahu to Moon');
 expect(host.textContent).not.toContain('Mrityu Bhaga');
 expect(onAsk).not.toHaveBeenCalled();
 expect(apiService.getBhriguBinduWorkspace.mock.calls[0][1].calendar).toBe(false);
 await click('Ask Tara');
 expect(onAsk.mock.calls[0][0]).toContain('forward Rahu-to-Moon');
 expect(onClose).toHaveBeenCalled();
});
test('calendar calculates on request and separates conjunctions from aspects', async () => {
 await act(async () => root.render(<Workspace birthData={birth} onClose={() => {}} />));
 await click('Activation calendar');
 await act(async () => host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
 expect(apiService.getBhriguBinduWorkspace.mock.calls[1][1].calendar).toBe(true);
 expect(host.textContent).toContain('Saturn → Bhrigu Bindu');
 expect(host.textContent).toContain('Exact contact 1');
 const select=[...host.querySelectorAll('select')].find(x=>x.parentElement.textContent.includes('Evidence'));
 await act(async () => {select.value='aspect';select.dispatchEvent(new Event('change',{bubbles:true}));});
 expect(host.textContent).not.toContain('Saturn → Bhrigu Bindu');
 expect(host.textContent).toContain('No matching contacts');
});
test('shows calculation errors rather than an empty success', async () => {
  apiService.getBhriguBinduWorkspace.mockRejectedValue({
    response: {
      data: {
        detail: 'Ephemeris unavailable'
      }
    }
  });
  await act(async () => root.render(<Workspace birthData={birth} onClose={() => {}} />));
  expect(host.querySelector('[role=alert]').textContent).toContain('Ephemeris unavailable');
  expect(host.textContent).not.toContain('0 natal points');
});
test('calendar export preserves absolute UTC instants and event identity', () => {
  const text = makeCalendar([event]);
  expect(text).toContain('DTSTART:20261018T000000Z');
  expect(text).toContain('DTEND:20261019T000000Z');
  expect(text).toContain('UID:Rahu:Saturn:contact:2026-10-18:');
  expect(text).toContain('SUMMARY:Saturn - Bhrigu Bindu');
});

test('defaults to Patel preset and explicitly calculates selected consultation focus', async () => {
  await act(async () => root.render(<Workspace birthData={birth} onClose={() => {}} />));
  expect(apiService.getBhriguBinduWorkspace.mock.calls[0][1].orb_degrees).toBe(5/3);
  await click('Activation calendar');
  expect(host.textContent).toContain('Patel ±1°40′ (100 arcminutes)');
  const focusSelect=[...host.querySelectorAll('select')].find(x=>x.parentElement.textContent.includes('Consultation focus'));
  await act(async () => {focusSelect.value='career';focusSelect.dispatchEvent(new Event('change',{bubbles:true}));});
  await act(async () => host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  expect(apiService.getBhriguBinduWorkspace.mock.calls.at(-1)[1].focus).toBe('career');
  expect(host.textContent).toContain('Saturn → Bhrigu Bindu');
  const filter=[...host.querySelectorAll('input[type=checkbox]')].find(x=>x.parentElement.textContent.includes('Only contacts with career'));
  await act(async () => filter.click());
  expect(host.textContent).not.toContain('Saturn → Bhrigu Bindu');
  await act(async () => filter.click());
  expect(host.textContent).toContain('Saturn → Bhrigu Bindu');
});

test('opens transit chart at exact UTC contact without replacing calendar', async () => {
  apiService.getBhriguBinduWorkspace.mockImplementation(async (b,options) => ({...fixture,calendar_calculated:options.calendar,
    ...(options.chart_at ? {selected_transit:{at:options.chart_at,frame:'Transit planets over fixed natal whole-sign houses',chart:{},bb_position:point.position,bb_house:point.house}} : {})}));
  await act(async () => root.render(<Workspace birthData={birth} onClose={() => {}} />));
  await click('Activation calendar');
  await act(async () => host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
  await click('Open exact contact 1');
  const options=apiService.getBhriguBinduWorkspace.mock.calls.at(-1)[1];
  expect(options.chart_at).toBe(event.exact_passes[0].at);
  expect(options.calendar).toBe(false);
  expect(host.textContent).toContain('fixed natal whole-sign houses');
  expect(host.textContent).toContain('Saturn → Bhrigu Bindu');
  await click('Close transit chart');
  expect(host.textContent).not.toContain('fixed natal whole-sign houses');
});
