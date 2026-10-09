import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import InformationRounds from './InformationRounds';
global.IS_REACT_ACT_ENVIRONMENT = true;
jest.mock('../../services/adminService', () => ({ getAdminAuthHeaders: () => ({ Authorization: 'Bearer test' }) }));

test('loads rounds only when expanded and renders requests and responses as escaped text', async () => {
  const original=global.fetch;
  global.fetch=jest.fn(async()=>({ok:true,json:async()=>({available:true,audit:{max_rounds:8,events:[{round:1,calculator:'parashari.double_transit',requested:{houses:[10]},provided:{finding:'<script>unsafe</script>'},success:true},{round:2,kind:'question',text:'Which city?'},{round:2,kind:'user_reply',text:'Delhi'}]}})}));
  const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host);
  try {
    act(()=>root.render(<InformationRounds messageId={42}/>));
    expect(global.fetch).not.toHaveBeenCalled();
    await act(async()=>{const panel=host.querySelector('details');panel.open=true;panel.dispatchEvent(new Event('toggle'));});
    expect(global.fetch.mock.calls[0][0]).toBe('/api/admin/chat/information-rounds/42');
    expect(host.textContent).toContain('Round 1');
    expect(host.textContent).toContain('Information requested');
    expect(host.textContent).toContain('Information provided');
    expect(host.textContent).toContain('Which city?');
    expect(host.textContent).toContain('Delhi');
    expect(host.querySelector('script')).toBeNull();
  } finally {act(()=>root.unmount());host.remove();global.fetch=original;}
});
