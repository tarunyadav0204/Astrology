import { applyInstantProgress, buildImmediateChartPreview, mergeChartContext } from './instantProgress';
import { shouldPaceInstantAnswer } from '../constants/instantChatLoader';
const pending = () => ({ messageId:1, isTyping:true, chatTier:'instant', content:'' });
const preview = { title:'Calculated', rows:[{ key:'md', text:'Major period: Saturn' }], direction:'ltr' };

test('chart context never contaminates LLM content', () => {
    const opening=applyInstantProgress(pending(),{preview});
    expect(opening.content).toBe('');
    expect(opening.instantPreview.rows[0].text).toBe('Major period: Saturn');
    expect(opening.isTyping).toBe(true);
    expect(opening.instantStreaming).toBeUndefined();
    const streaming=applyInstantProgress(opening,{content:'Real model answer'});
    expect(streaming.content).toBe('Real model answer');
    expect(streaming.instantPhase).toBe('answer');
    expect(streaming.isTyping).toBe(false);
    expect(streaming.instantStreaming).toBe(true);
    expect(applyInstantProgress(streaming,{preview}).content).toBe('Real model answer');
    expect(shouldPaceInstantAnswer()).toBe(false);
});

test('immediate positions use existing calculations, including zero longitude', () => {
    const result=buildImmediateChartPreview({ascendant:0,planets:{Moon:{longitude:42},Sun:{longitude:350}}});
    expect(result.rows.map(r=>r.text)).toEqual(['↑ ♈ 0.00°','☽ ♉ 12.00°','☉ ♓ 20.00°']);
    expect(buildImmediateChartPreview({})).toBeNull();
    expect(buildImmediateChartPreview({ascendant:NaN})).toBeNull();
});

test('reconnect merges context independently and does not regress streamed answer', () => {
    const opening=applyInstantProgress(pending(),{preview});
    const streaming=applyInstantProgress(opening,{partial_content:'Already streaming'});
    expect(applyInstantProgress(streaming,{partial_content:'Al'})).toBe(streaming);
    expect(applyInstantProgress(streaming,{content:'Corrected',replace:true}).content).toBe('Corrected');
    const complete={...streaming,instantStreaming:false};
    expect(applyInstantProgress(complete,{content:'Late'})).toBe(complete);
    expect(mergeChartContext(preview,preview).rows).toHaveLength(1);
});

test('unsupported language adds no invented prose; RTL context stays separate', () => {
    const message=pending();
    expect(applyInstantProgress(message,{})).toBe(message);
    const rtl=applyInstantProgress(message,{preview:{...preview,direction:'rtl'}});
    expect(applyInstantProgress(rtl,{content:'شرح'}).responseDirection).toBe('rtl');
});
