import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import MuhuratSetup from './MuhuratSetup';
jest.mock('../../services/locationService', () => ({ locationService:{ searchPlaces:jest.fn() } }));
global.IS_REACT_ACT_ENVIRONMENT=true;
const request={event_type:'vehicle',start_date:'2026-09-07',end_date:'2026-09-07',location:{name:'Gurugram',latitude:28.45,longitude:77.02,timezone:'Asia/Kolkata'}};
for (const invalid of [false,true]) test(invalid ? 'invalid range shows friendly guidance' : 'same-day city and hours are submitted', () => {
  const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host),onSubmit=jest.fn();
  try {
    act(() => root.render(<MuhuratSetup initial={invalid ? {...request,end_date:'2027-01-01'} : request} onSubmit={onSubmit} />));
    act(() => host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
    if(invalid) {expect(onSubmit).not.toHaveBeenCalled();expect(host.querySelector('[role="alert"]').textContent).toContain('1–60 days');}
    else expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({...request,allowed_start:'08:00',allowed_end:'18:00',personalized:false}));
  } finally {act(() => root.unmount());host.remove();}
});
