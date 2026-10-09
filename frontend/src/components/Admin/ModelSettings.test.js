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
