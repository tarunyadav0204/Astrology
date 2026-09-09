import {
    buildConversationalClosing,
    inferSpeechLanguage,
    speechLocaleForLanguage,
    takeSpeakableChunks,
} from './speechStreaming';

describe('speech streaming helpers', () => {
    test('holds incomplete text and releases complete sentences', () => {
        const first = takeSpeakableChunks('First sentence. Second sen');
        expect(first).toEqual({ chunks: ['First sentence.'], remainder: 'Second sen' });

        const second = takeSpeakableChunks(`${first.remainder}tence!`);
        expect(second).toEqual({ chunks: ['Second sentence!'], remainder: '' });
    });

    test('recognizes Hindi sentence boundaries and language', () => {
        expect(takeSpeakableChunks('यह पहला वाक्य है। अगला')).toEqual({
            chunks: ['यह पहला वाक्य है।'],
            remainder: 'अगला',
        });
        expect(inferSpeechLanguage('मेरा करियर कैसा रहेगा?', 'english')).toBe('hindi');
        expect(speechLocaleForLanguage('hindi')).toBe('hi-IN');
    });

    test('flushes a final sentence without punctuation', () => {
        expect(takeSpeakableChunks('Final answer', { flush: true })).toEqual({
            chunks: ['Final answer'],
            remainder: '',
        });
    });

    test('uses the model follow-up as the conversational ending without duplicating it', () => {
        const question = 'Is work pressure or growth your bigger concern right now?';
        expect(buildConversationalClosing('Your career is entering a steadier phase.', [question], 'english'))
            .toBe(question);
        expect(buildConversationalClosing(`Your career is steadier. ${question}`, [question], 'english'))
            .toBe('');
    });

    test('provides a localized conversational question when no follow-up was generated', () => {
        expect(buildConversationalClosing('उत्तर पूरा हुआ।', [], 'hindi'))
            .toBe('अब आप किस बात को थोड़ा और समझना चाहेंगे?');
    });
});
