import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import { Workspace, makeCalendar } from './MrityuBhagaWorkspace';
import { apiService } from '../../services/apiService';
global.IS_REACT_ACT_ENVIRONMENT = true;
jest.mock('../../services/apiService', () => ({
  apiService: {
    getMrityuBhagaWorkspace: jest.fn()
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
  point: 'Rahu',
  is_mrityu_bhaga: true,
  position: 'Aries 13° 30′',
  house: 1,
  sign_name: 'Aries',
  degree_span_start: 13,
  degree_span_end: 14,
  houses_ruled: [],
  dispositor: 'Mars',
  dispositor_position: 'Aries 1°',
  relationships: [],
  divisional_placements: {
    D9: {
      sign: 'Leo',
      house: 5
    }
  },
  combustion: {
    applicable: false
  },
  distance_to_boundary_degrees: .5
};
const event = {
  id: 'Rahu:Saturn:contact:2026-10-18',
  point: 'Rahu',
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
  apiService.getMrityuBhagaWorkspace.mockReset();
  apiService.getMrityuBhagaWorkspace.mockImplementation(async (b, options) => ({
    ...fixture,
    calendar_calculated: options.calendar
  }));
});
afterEach(() => {
  act(() => root.unmount());
  host.remove();
});
test('loads natal assessment and prepares contextual Tara question', async () => {
  const onAsk = jest.fn(),
    onClose = jest.fn();
  await act(async () => root.render(<Workspace birthData={birth} onClose={onClose} onAsk={onAsk} />));
  expect(host.textContent).toContain('Rahu is in Mrityu Bhaga');
  expect(host.textContent).toContain('Linked natal chart');
  expect(host.textContent).toContain('Mrityu Bhaga range: 13°–14° Aries');
  expect(host.textContent).toContain('Rahu’s position: Aries 13° 30′');
  expect(host.textContent).not.toContain('ordinal');
  expect(host.textContent).not.toContain('Endpoint samples');
  expect(apiService.getMrityuBhagaWorkspace.mock.calls[0][1].calendar).toBe(false);
  await click('Ask Tara about this finding');
  expect(onAsk.mock.calls[0][0]).toContain('Rahu');
  expect(onClose).toHaveBeenCalled();
});
test('calendar calculates on request and filters direct dasha overlaps', async () => {
  await act(async () => root.render(<Workspace birthData={birth} onClose={() => {}} />));
  await click('Activation calendar');
  await act(async () => host.querySelector('form').dispatchEvent(new Event('submit', {
    bubbles: true,
    cancelable: true
  })));
  expect(apiService.getMrityuBhagaWorkspace.mock.calls[1][1].calendar).toBe(true);
  expect(host.textContent).toContain('Saturn → Rahu');
  expect(host.textContent).toContain('Exact contact 1');
  const checkbox = [...host.querySelectorAll('input[type=checkbox]')].find(x => x.parentElement.textContent.includes('Only during'));
  await act(async () => checkbox.click());
  expect(host.textContent).not.toContain('Saturn → Rahu');
  expect(host.textContent).toContain('No matching contacts');
});
test('shows calculation errors rather than an empty success', async () => {
  apiService.getMrityuBhagaWorkspace.mockRejectedValue({
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
  expect(text).toContain('SUMMARY:Saturn - Rahu');
});
