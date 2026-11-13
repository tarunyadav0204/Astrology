import { normalizeBirthDetailsForChat } from './normalizeBirthDetailsForChat';

test.each(['id', 'chart_id', 'birth_chart_id', 'birthChartId'])('preserves %s so mismatched sessions cannot bypass validation', key => {
    const result = normalizeBirthDetailsForChat({[key]: 10325, name: 'Apurva', date: '1992-02-02T00:00:00', time: '1992-02-02T11:00:00', latitude: '28.6', longitude: '77.2'});
    expect(result.id).toBe(10325);
    expect(result.date).toBe('1992-02-02');
    expect(result.time).toBe('11:00');
});
