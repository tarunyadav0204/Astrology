import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import AdminChatToolActivity from './AdminChatToolActivity';

jest.mock('../../services/adminService', () => ({ getAdminAuthHeaders: () => ({ Authorization: 'Bearer test' }) }));
global.IS_REACT_ACT_ENVIRONMENT = true;

test('admin can inspect the user, sources, model and measured cost', async () => {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root = createRoot(host);
  const originalFetch = global.fetch;
  global.fetch = jest.fn().mockResolvedValue({ ok: true, json: async () => ({ total: 1, total_pages: 1, usd_to_inr: 93, items: [{
    id: 'run1', user_id: 42, user_name: 'Example user', tool: 'summary', status: 'completed', model: 'gpt-5.6-luna',
    usage: { input_tokens: 1000, cached_tokens: 400, output_tokens: 200 }, cost_inr: 0.034224, cost_usd: 0.000368, cost_basis: 'measured_tokens_estimate',
    sources: [{ answer_id: 8, session_id: 'session1', question: 'Original question', answer: 'Original answer' }],
    result: 'Summary result', events: [], cached: false, legacy: false,
  }] }) });
  try {
    await act(async () => root.render(<AdminChatToolActivity />));
    expect(global.fetch.mock.calls[0][0]).toContain('/api/admin/chat/tool-activity?');
    for (const value of ['Example user', 'User ID: 42', 'gpt-5.6-luna', '₹0.0342', 'Original question', 'Original answer', 'Answer #8', 'Summary result', 'Cached input: 400']) {
      expect(host.textContent).toContain(value);
    }
  } finally {
    act(() => root.unmount());
    host.remove();
    global.fetch = originalFetch;
  }
});
