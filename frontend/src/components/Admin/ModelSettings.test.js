import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import ModelSettings from './ModelSettings';
jest.mock('../../services/adminService', () => ({ getAdminAuthHeaders: () => ({ Authorization: 'Bearer admin', 'X-Device-Id': 'device' }) }));
global.IS_REACT_ACT_ENVIRONMENT = true;
test('saves only selected feature and reports errors inline', async () => {
  const host = document.createElement('div'); document.body.appendChild(host); const root = createRoot(host);
  const originalFetch = global.fetch;
  global.fetch = jest.fn().mockResolvedValueOnce({ ok: true }).mockResolvedValueOnce({ ok: false, json: async () => ({ detail: 'Model unavailable' }) });
  const groups = ['standard', 'summary'].map(id => ({ id, title: id, description: id, fields: [{ key: `${id}_model`, label: 'Model', value: 'chosen-model', set: jest.fn() }] }));
  try {
    act(() => root.render(<ModelSettings groups={groups} advanced={[]} />));
    const buttons = host.querySelectorAll('button');
    await act(async () => buttons[1].click());
    expect(global.fetch).toHaveBeenCalledTimes(1);
    expect(global.fetch.mock.calls[0][0]).toBe('/api/admin/settings/summary_model');
    expect(global.fetch.mock.calls[0][1].headers.Authorization).toBe('Bearer admin');
    expect(global.fetch.mock.calls[0][1].headers['X-Device-Id']).toBe('device');
    expect(JSON.parse(global.fetch.mock.calls[0][1].body).value).toBe('chosen-model');
    expect(host.querySelector('[role="status"]').textContent).toContain('settings saved');
    await act(async () => buttons[0].click());
    expect(host.querySelector('[role="alert"]').textContent).toBe('Model unavailable');
    expect(buttons[0].disabled).toBe(false);
  } finally { act(() => root.unmount()); host.remove(); global.fetch = originalFetch; }
});

test('saves independent Standard and Premium branch eligibility including false', async () => {
  const host = document.createElement('div'); document.body.appendChild(host); const root = createRoot(host);
  const originalFetch = global.fetch;
  global.fetch = jest.fn().mockResolvedValue({ ok: true });
  function Harness() {
    const [standard, setStandard] = React.useState(true);
    const [premium, setPremium] = React.useState(true);
    return <ModelSettings groups={[]} advanced={[{ id: 'jaimini', title: 'Jaimini', fields: [
      { key: 'parallel_branch_enabled_standard_jaimini', label: 'Standard enabled', type: 'checkbox', value: standard, set: setStandard },
      { key: 'parallel_branch_enabled_premium_jaimini', label: 'Premium enabled', type: 'checkbox', value: premium, set: setPremium },
    ] }]} />;
  }
  try {
    act(() => root.render(<Harness />));
    const toggles = host.querySelectorAll('input[type="checkbox"]');
    act(() => toggles[0].click());
    expect(toggles[0].checked).toBe(false);
    expect(toggles[1].checked).toBe(true);
    await act(async () => host.querySelector('button').click());
    expect(global.fetch.mock.calls.map(([url, options]) => [url, JSON.parse(options.body).value])).toEqual([
      ['/api/admin/settings/parallel_branch_enabled_standard_jaimini', 'false'],
      ['/api/admin/settings/parallel_branch_enabled_premium_jaimini', 'true'],
    ]);
  } finally { act(() => root.unmount()); host.remove(); global.fetch = originalFetch; }
});
