import textToSpeech, { normalizeAstrologyPronunciation } from './textToSpeech';

describe('textToSpeech voice selection', () => {
    test('prefers a voice matching the requested language', () => {
        const english = { name: 'English Voice', lang: 'en-IN' };
        const hindi = { name: 'Hindi Female', lang: 'hi-IN' };

        expect(textToSpeech.getPreferredVoice([english, hindi], 'hi-IN')).toBe(hindi);
        expect(textToSpeech.getPreferredVoice([english, hindi], 'en-IN')).toBe(english);
    });

    test('stores the selected speech provider', () => {
        textToSpeech.setProvider('google');
        expect(textToSpeech.getProvider()).toBe('google');
        textToSpeech.setProvider('local');
        expect(textToSpeech.getProvider()).toBe('local');
    });

    test('routes speech through Google when the admin provider is Google', () => {
        const stopSpy = jest.spyOn(textToSpeech, 'stop').mockImplementation(() => {});
        const googleSpy = jest.spyOn(textToSpeech, '_speakWithGoogle').mockResolvedValue();
        textToSpeech.setProvider('google');

        expect(textToSpeech.speak('A spoken answer.', { lang: 'en-IN' })).toBe(true);
        expect(googleSpy).toHaveBeenCalledWith(
            'A spoken answer.',
            expect.objectContaining({ lang: 'en-IN' }),
            expect.any(Number)
        );

        textToSpeech.setProvider('local');
        googleSpy.mockRestore();
        stopSpy.mockRestore();
    });
});

describe('astrology speech pronunciation', () => {
    test('disambiguates standalone Mangal and Budh without changing weekday words', () => {
        expect(normalizeAstrologyPronunciation('मंगल दूसरे भाव में है और बुध मजबूत है।'))
            .toBe('मंगल ग्रह दूसरे भाव में है और बुध ग्रह मजबूत है।');
        expect(normalizeAstrologyPronunciation('मंगलवार और बुधवार'))
            .toBe('मंगलवार और बुधवार');
    });

    test('does not duplicate graha or alter Mangal dosh', () => {
        expect(normalizeAstrologyPronunciation('मंगल ग्रह, बुध ग्रह और मंगल दोष'))
            .toBe('मंगल ग्रह, बुध ग्रह और मंगल दोष');
        expect(normalizeAstrologyPronunciation('Mangal and Budh graha'))
            .toBe('Mangal graha and Budh graha');
    });
});
