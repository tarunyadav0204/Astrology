import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import ConflictResolution from './ConflictResolution';
global.IS_REACT_ACT_ENVIRONMENT = true;
const messages = Array.from({length:3}, (_, index) => [{role:'user', content:`Question ${index+1}`},{role:'assistant', content:`Answer ${index+1}`, messageId:index+1}]).flat();

test('selects exactly two answers and submits their IDs', async () => {
  const originalFetch=global.fetch, originalWS=global.WebSocket;
  let ws;
  global.WebSocket=class { constructor(){ ws=this; this.close=jest.fn(); this.send=jest.fn(); } };
  global.fetch=jest.fn().mockImplementation(async (url, options) => ({ok:true,json:async()=>options?.method==='POST'?{id:'run',phase:'ready',rounds:0,revision:0,sources:[{answer_id:1,question:'Question 1'},{answer_id:2,question:'Question 2'}],events:[]}:{comparisons:[]}}));
  const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host);
  try{
    await act(async()=>root.render(<ConflictResolution messages={messages}/>));
    const boxes=host.querySelectorAll('input[type=checkbox]');
    act(()=>boxes[0].click());act(()=>boxes[1].click());
    expect(boxes[2].disabled).toBe(true);
    const submit=[...host.querySelectorAll('button')].find(b=>b.textContent.startsWith('Resolve selected'));
    await act(async()=>submit.click());
    const post=global.fetch.mock.calls.find(([,options])=>options?.method==='POST');
    expect(JSON.parse(post[1].body).message_ids).toEqual([1,2]);
    expect(JSON.parse(post[1].body).request_id).toMatch(/^[a-f0-9-]{36}$/);
    await act(async()=>ws.onmessage({data:JSON.stringify({type:'state',id:'run',phase:'waiting',rounds:1,revision:2,question:'Which year?',sources:[{answer_id:1,question:'Question 1'},{answer_id:2,question:'Question 2'}],events:[]})}));
    expect(host.querySelector('textarea[aria-label="Your clarification"]')).not.toBeNull();
    expect(host.textContent).toContain('Information rounds 1/8');
  }finally{act(()=>root.unmount());host.remove();global.fetch=originalFetch;global.WebSocket=originalWS;}
});

test('appends a saved resolution once when reconnecting to the same result', () => {
  const { appendConflictResolution } = require('../../hooks/useConflictResolution');
  const result={message_id:50,question_message_id:49,content:'Corrected answer',question_text:'Resolve conflicting answers',completed_at:'2026-10-09T12:00:00Z'};
  const updated=appendConflictResolution(messages,result);
  expect(updated).toHaveLength(messages.length+2);
  expect(updated[updated.length-1].chatTier).toBe('verified');
  expect(updated[updated.length-1].messageId).toBe(50);
  expect(appendConflictResolution(updated,result)).toBe(updated);
});
