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

test('festival intake accepts a full year and keeps evening/night available', () => {
  const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host),onSubmit=jest.fn();
  try {
    act(() => root.render(<MuhuratSetup initial={{event_type:'festival_puja',festival_id:'diwali',festival_year:2026,start_date:'2026-01-01',end_date:'2026-12-31',location:request.location}} onSubmit={onSubmit} />));
    expect(host.textContent).toContain('Lakshmi Puja');
    expect(host.textContent).not.toContain('Daylight windows only');
    expect(host.querySelectorAll('input[type="date"]')).toHaveLength(0);
    act(() => host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({festival_id:'diwali',allowed_start:'00:00',allowed_end:'23:59'}));
  } finally {act(() => root.unmount());host.remove();}
});

test('festival intake requires an explicit puja city', () => {
  const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host),onSubmit=jest.fn();
  try {
    act(() => root.render(<MuhuratSetup initial={{event_type:'festival_puja',festival_id:'dussehra',festival_year:2026,start_date:'2026-01-01',end_date:'2026-12-31'}} onSubmit={onSubmit} />));
    act(() => host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
    expect(onSubmit).not.toHaveBeenCalled();expect(host.querySelector('[role="alert"]').textContent).toContain('event city');
  } finally {act(() => root.unmount());host.remove();}
});

test('Dussehra ritual dropdown recognizes Aparajita spelling and separates unsupported rites', () => {
  const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host),onSubmit=jest.fn();
  try {
    act(() => root.render(<MuhuratSetup initial={{event_type:'festival_puja',festival_id:'dussehra',ritual:'Aparajita Pooja',festival_year:2026,start_date:'2026-01-01',end_date:'2026-12-31',location:request.location}} onSubmit={onSubmit} />));
    const select=Array.from(host.querySelectorAll('select')).find(el=>Array.from(el.options).some(option=>option.value==='Aparajita puja'));
    expect(select.value).toBe('Aparajita puja');
    expect(Array.from(select.options).find(option=>option.value==='Durga Visarjan').disabled).toBe(true);
    expect(Array.from(select.options).find(option=>option.value==='Shami puja').disabled).toBe(false);
    act(()=>{ const setter=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set;setter.call(select,'Shami puja');select.dispatchEvent(new Event('change',{bubbles:true})); });
    act(()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ritual:'Shami puja'}));
  } finally {act(()=>root.unmount());host.remove();}
});

test('a supplied festival selects puja even when a stale activity says vehicle', () => {
  const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host),onSubmit=jest.fn();
  try {
    act(()=>root.render(<MuhuratSetup initial={{...request,festival_id:'dussehra'}} onSubmit={onSubmit}/>));
    expect(host.querySelector('select').value).toBe('festival_puja');
    expect(host.textContent).toContain('Shami');
    act(()=>root.render(<MuhuratSetup initial={{...request,event_type:'Pooja Muhurat',festival_id:null}} onSubmit={onSubmit}/>));
    expect(host.querySelector('select').value).toBe('festival_puja');
  } finally {act(()=>root.unmount());host.remove();}
});

test('festival year is selected from valid years and updates the search dates', () => {
  const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host),onSubmit=jest.fn();
  try {
    act(()=>root.render(<MuhuratSetup initial={{...request,event_type:'festival_puja',festival_id:'dussehra',festival_year:2026,start_date:'2026-01-01',end_date:'2026-12-31'}} onSubmit={onSubmit}/>));
    const year=host.querySelector('select[aria-label="Year"]');
    expect(year.value).toBe('2026');expect(year.options.length).toBe(201);
    expect(host.querySelector('input[type="number"]')).toBeNull();
    act(()=>{year.value='2027';year.dispatchEvent(new Event('change',{bubbles:true}));});
    act(()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({festival_year:2027,start_date:'2027-01-01',end_date:'2027-12-31'}));
  } finally {act(()=>root.unmount());host.remove();}
});

test('a new puja setup selects the current year and submits its dates without interaction', () => {
  const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host),onSubmit=jest.fn();
  const year=new Date().getFullYear();
  try {
    act(()=>root.render(<MuhuratSetup initial={{event_type:'festival_puja',festival_id:'dussehra',location:request.location}} onSubmit={onSubmit}/>));
    expect(host.querySelector('select[aria-label="Year"]').value).toBe(String(year));
    act(()=>host.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({festival_year:year,start_date:`${year}-01-01`,end_date:`${year}-12-31`}));
  } finally {act(()=>root.unmount());host.remove();}
});

test('Lakshmi puja appears once and a generic saved puja maps to it', () => {
  const host=document.createElement('div');document.body.appendChild(host);const root=createRoot(host);
  try {
    act(()=>root.render(<MuhuratSetup initial={{event_type:'festival_puja',festival_id:'diwali',ritual:'puja'}} onSubmit={jest.fn()}/>));
    const select=Array.from(host.querySelectorAll('select')).find(el=>Array.from(el.options).some(o=>o.textContent==='Lakshmi Puja'));
    expect(select.options.length).toBe(1);
    expect(select.selectedOptions[0].textContent).toBe('Lakshmi Puja');
    expect(host.textContent).not.toMatch(/limited engine|midpoint|engine coverage/i);
  } finally {act(()=>root.unmount());host.remove();}
});
