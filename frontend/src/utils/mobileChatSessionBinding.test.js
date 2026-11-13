import fs from 'fs';
import path from 'path';

// Exercise the actual mobile session creators without mounting React Native.
describe.each(['astroroshni_mobile', 'astroroshni_ios'])('%s session binding', app => {
    const source = fs.readFileSync(path.resolve(process.cwd(), '..', app, 'src/components/Chat/ChatScreen.js'), 'utf8');
    const creator = source.match(/const createSession = (async \(\) => \{[\s\S]*?\n  \});/)[1];
    test.each([true, false])('partnership=%s binds the selected native', async partnershipMode => {
        const storage = { getItem: jest.fn(async key => key === 'authToken' ? 'test-token' : null), setItem: jest.fn() };
        const fetchMock = jest.fn(async () => ({ok: true, json: async () => ({session_id: 'new-session'})}));
        const deps = {
            AsyncStorage: storage, partnershipMode, nativeChart: {id: 10325, name: 'Apurva'},
            birthData: {id: 10322, name: 'Diksha'}, isMundane: false, buildQueryContext: () => ({}),
            API_BASE_URL: '', getEndpoint: x => x, fetch: fetchMock, setSessionId: jest.fn(),
            subjectGateOverrideRef: {current: null}, subjectGateMemoryRef: {current: []},
            chatPersonStorageKey: chart => String(chart.id),
        };
        const create = new Function(...Object.keys(deps), `return (${creator});`)(...Object.values(deps));
        expect(await create()).toBe('new-session');
        expect(JSON.parse(fetchMock.mock.calls[0][1].body).birth_chart_id).toBe(partnershipMode ? 10325 : 10322);
        if (partnershipMode) expect(storage.setItem).not.toHaveBeenCalled();
    });
});
