import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
import InstantChartContext from './InstantChartContext';

test('first fact is immediate, subsequent facts arrive incrementally, LLM stops the queue', () => {
    jest.useFakeTimers();
    global.IS_REACT_ACT_ENVIRONMENT=true;
    const container=document.createElement('div');
    const root=createRoot(container);
    const preview={title:'Calculated',rows:[{key:'a',text:'First fact'},{key:'b',text:'Second fact'},{key:'c',text:'Third fact'}]};
    act(()=>root.render(<InstantChartContext preview={preview} active />));
    expect(container.querySelectorAll('[data-context-row]')).toHaveLength(1);
    act(()=>jest.advanceTimersByTime(650));
    expect(container.querySelectorAll('[data-context-row]')).toHaveLength(2);
    act(()=>root.render(<InstantChartContext preview={preview} active={false} />));
    act(()=>jest.advanceTimersByTime(2000));
    expect(container.querySelectorAll('[data-context-row]')).toHaveLength(2);
    act(()=>root.unmount());
    jest.useRealTimers();
});

test('a cold chart arriving later still reveals its first row immediately', () => {
    jest.useFakeTimers();
    global.IS_REACT_ACT_ENVIRONMENT=true;
    const container=document.createElement('div');
    const root=createRoot(container);
    act(()=>root.render(<InstantChartContext preview={null} active />));
    const preview={title:'Calculated',rows:[{key:'a',text:'First fact'},{key:'b',text:'Second fact'}]};
    act(()=>root.render(<InstantChartContext preview={preview} active />));
    expect(container.querySelectorAll('[data-context-row]')).toHaveLength(1);
    act(()=>jest.advanceTimersByTime(650));
    expect(container.querySelectorAll('[data-context-row]')).toHaveLength(2);
    act(()=>root.unmount());
    jest.useRealTimers();
});
