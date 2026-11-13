import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import AdminEvidenceErrors from './AdminEvidenceErrors';
jest.mock('../../services/adminService', () => ({ getAdminAuthHeaders: () => ({ Authorization: 'Bearer test' }) }));
global.IS_REACT_ACT_ENVIRONMENT = true;
let host,root,originalFetch;
beforeEach(()=>{host=document.createElement('div');document.body.appendChild(host);root=createRoot(host);originalFetch=global.fetch;});
afterEach(()=>{act(()=>root.unmount());host.remove();global.fetch=originalFetch;});
const click=async text=>{const b=[...host.querySelectorAll('button')].find(x=>x.textContent===text);await act(async()=>b.click());};
const row={message_id:17,username:'Alice',user_id:1,chat_type:'standard',question:'What is my D9 ascendant?',mismatch_count:1,unverified_count:1};

test('defaults to mismatches and separates detail findings and other views',async()=>{
 global.fetch=jest.fn(async url=>({ok:true,json:async()=>url.includes('evidence-audit/17')?{found:true,status:'completed',evidence_brief:{answer:'Original answer'},evaluator_result:{fact_checks:[{status:'mismatch',quote:'Ascendant is Scorpio',asserted_value:'Scorpio',calculated_value:'Sagittarius',evidence_path:'native.D9.ascendant'},{status:'unsupported',quote:'Unverified technique'}]}}:{items:[row],total:1,total_pages:1}}));
 await act(async()=>root.render(<AdminEvidenceErrors/>));
 expect(global.fetch.mock.calls[0][0]).toContain('view=mismatches');
 expect(host.textContent).toContain('What is my D9 ascendant?');
 await click('View findings');
 expect(host.querySelector('article').textContent).toContain('Sagittarius');
 expect(host.querySelectorAll('article')).toHaveLength(1);
 await click('Unverified claims');
 expect(global.fetch.mock.calls.at(-1)[0]).toContain('view=unverified');
 expect(host.querySelector('article')).toBeNull();
 await click('Audit failures');
 expect(global.fetch.mock.calls.at(-1)[0]).toContain('view=failures');
});

test('applies filters and shows request errors without stale results',async()=>{
 global.fetch=jest.fn(async()=>({ok:true,json:async()=>({items:[],total:0,total_pages:1})}));
 await act(async()=>root.render(<AdminEvidenceErrors/>));
 const inputs=host.querySelectorAll('input');
 await act(async()=>{
  [['Alice',inputs[0]],['2026-11-01',inputs[1]],['2026-11-13',inputs[2]]].forEach(([v,i])=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(i,v);i.dispatchEvent(new Event('input',{bubbles:true}));});
  const select=host.querySelector('select');select.value='speech';select.dispatchEvent(new Event('change',{bubbles:true}));
 });
 await click('Apply filters');
 const url=global.fetch.mock.calls.at(-1)[0];
 ['username=Alice','start_date=2026-11-01','end_date=2026-11-13','chat_type=speech','page=1'].forEach(part=>expect(url).toContain(part));
 global.fetch.mockResolvedValueOnce({ok:false,json:async()=>({detail:'Report unavailable'})});
 await click('Refresh');
 expect(host.querySelector('[role="alert"]').textContent).toBe('Report unavailable');
 expect(host.querySelector('table')).toBeNull();
});
