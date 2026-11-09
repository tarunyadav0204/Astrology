"""Local review artifact. No backend, customer charge or reel render required."""
import argparse
import asyncio
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from .service import build_next_chapter, narrate_next_chapter, narration_context


def render_preview(dossier, narration=None):
    hindi = (narration or {}).get('language') == 'hi'
    labels = {
        'Your Next Chapter': 'आपका अगला अध्याय', 'Mahadasha': 'महादशा', 'Antardasha': 'अंतरदशा',
        'Pratyantardasha': 'प्रत्यंतरदशा', 'When to pay attention': 'किन समयों पर ध्यान दें',
        'Support and pressure': 'सहयोग और चुनौतियाँ', 'Calculated transit contacts': 'गणना किए गए गोचर संबंध',
        'Natal foundation · calculation worksheets': 'जन्म-कुंडली का आधार · गणना विवरण',
        'Possible events across this Antardasha': 'इस अंतरदशा में संभावित घटनाएँ',
        'Mahadasha and Antardasha transits across this chapter': 'इस अवधि में महादशा और अंतरदशा स्वामियों का गोचर',
        'Mahadasha, Antardasha and Pratyantardasha transits': 'महादशा, अंतरदशा और प्रत्यंतरदशा स्वामियों का गोचर',
        'Activation evidence': 'सक्रिय भावों के प्रमाण', 'Period roles': 'दशा स्तर',
        'Natal occupation': 'जन्म स्थिति', 'Natal lordship': 'जन्म भाव स्वामित्व', 'Natal aspects': 'जन्म दृष्टियाँ',
        'Local interval': 'स्थानीय अवधि', 'Transit occupation': 'गोचर स्थिति', 'Transit aspects': 'गोचर दृष्टियाँ',
        'House': 'भाव', 'Contact': 'संबंध', 'Window (UTC)': 'अवधि (UTC)', 'Exact passes (UTC)': 'सटीक अंश संबंध (UTC)',
    }
    names = dict(zip(('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'),
                     ('सूर्य', 'चंद्रमा', 'मंगल', 'बुध', 'गुरु', 'शुक्र', 'शनि', 'राहु', 'केतु')))
    def label(value):
        return (labels.get(value) or names.get(value) or value) if hindi else value

    def esc(value):
        return html.escape(str(value))

    def dates(row):
        def date_text(value):
            at = datetime.fromisoformat(value)
            if hindi:
                months = ('जनवरी', 'फ़रवरी', 'मार्च', 'अप्रैल', 'मई', 'जून', 'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर')
                return f'{at.day} {months[at.month - 1]} {at.year}'
            return at.strftime('%d %b %Y')
        return ' → '.join(date_text(row[key]) for key in ('start_at', 'end_at'))

    context = narration_context(dossier)
    sign_names = ('मेष', 'वृषभ', 'मिथुन', 'कर्क', 'सिंह', 'कन्या', 'तुला', 'वृश्चिक', 'धनु', 'मकर', 'कुंभ', 'मीन') if hindi else ('Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces')
    role_names = {'MD': 'Mahadasha', 'AD': 'Antardasha', 'PD': 'Pratyantardasha'}
    spine = dossier['spine']
    report = (narration or {}).get('report')
    title = report['title'] if report else label('Your Next Chapter')
    sections = [f"<p class='brand'>ASTROROSHNI · {label('Your Next Chapter')}</p><h1>{esc(title)}</h1><p>{esc(dossier['native']['name'])}</p>",
        f"<h2>{esc(label(spine['mahadasha']['planet']))} {label('Mahadasha')} · {esc(label(spine['antardasha']['planet']))} {label('Antardasha')}</h2>",
        f"<p>{esc(dates(spine['antardasha']))} · {esc(spine['timezone'])}</p>"]
    if report:
        for key in ('overview', 'mahadasha_context', 'antardasha_themes'):
            sections.append(f"<p>{esc(report[key])}</p>")
        if report.get('antardasha_events'):
            sections.append(f"<section><h2>{label('Possible events across this Antardasha')}</h2>")
            for event in report['antardasha_events']:
                sections.append(f"<h3>{esc(event['theme'])}</h3><p>{esc(event['circumstances'])}</p><ul>" +
                    ''.join(f"<li>{esc(text)}</li>" for text in event['possibilities']) + '</ul>' +
                    f"<p>{esc(event['why'])}</p><p>{esc(event['timing'])}</p>")
            sections.append('</section>')
        if report.get('antardasha_transits'):
            sections.append(f"<section><h2>{label('Mahadasha and Antardasha transits across this chapter')}</h2>")
            for transit in report['antardasha_transits']:
                sections.append(f"<p>{esc(transit['explanation'])}</p>")
            sections.append('</section>')
        sections.append('<nav aria-label="Chapter periods">' + ''.join(
            f'<a href="#period-{i + 1}">{i + 1}. {esc(label(pd["planet"]))}<small>{esc(dates(pd))}</small></a>'
            for i, pd in enumerate(dossier['periods'])) + '</nav>')
    else:
        sections.append('<p>Calculation preview. Interpretation has not been generated. House themes below are possibilities to interpret, not predicted events.</p>')
    for index, pd in enumerate(dossier['periods']):
        sections.append(f"<section id='period-{index + 1}'><h2>{index + 1}. {esc(label(pd['planet']))} {label('Pratyantardasha')}</h2><p class='period-date'>{esc(dates(pd))}</p>")
        if report:
            narrative = report['periods'][index]
            sections.append(f"<h3>{esc(narrative['summary'])}</h3><p>{esc(narrative['what_changes'])}</p>")
            if narrative.get('transit_story'):
                sections.append(f"<h4>{label('Mahadasha, Antardasha and Pratyantardasha transits')}</h4>")
                for transit in narrative['transit_story']:
                    sections.append(f"<p>{esc(transit['explanation'])}</p>")
            sections.append(f"<h4>{label('When to pay attention')}</h4><p>{esc(narrative['timing_explanation'])}</p>")
            selected_contacts = {window['id']: window for item in narrative['manifestations']
                                 for window in item.get('timing_windows', [])}
            if selected_contacts:
                sections.append('<ul class="timing-windows">')
                for window in selected_contacts.values():
                    n = window['aspect_from_planet']
                    relation = ('युति' if n == 1 else f'{n}वीं दृष्टि') if hindi else ('conjunction' if n == 1 else f'aspect {n}')
                    local_dates = dates({'start_at': window['local_start_at'], 'end_at': window['local_end_at']})
                    sections.append(f"<li><strong>{esc(local_dates)}</strong> · {esc(label(window['transiting_planet']))} → {esc(label(window['natal_planet']))} · {relation}</li>")
                sections.append('</ul>')
            sections.append(f"<h4>{label('Support and pressure')}</h4><p>{esc(narrative['conditions_and_cautions'])}</p>")
            for item in narrative['manifestations']:
                sections.append(f"<h3>{esc(item['theme'])}</h3><ul>" + ''.join(f"<li>{esc(text)}</li>" for text in item['possibilities']) + '</ul>')
                sections.append(f"<p>{esc(item['why'])}</p><p>{esc(item['practical_guidance'])}</p>")
        levels = pd['activation']['levels']
        sections.append(f"<details class='activation-evidence'><summary>{label('Activation evidence')}</summary><table><tr>" +
            ''.join(f"<th>{label(k)}</th>" for k in ('Period roles', 'Natal occupation', 'Natal lordship', 'Natal aspects')) + '</tr>')
        for planet in dict.fromkeys(levels.values()):
            roles = ', '.join(label(role_names[level]) for level, name in levels.items() if name == planet)
            natal = context['natal_summary']['planets'][planet]
            cells = [f"{label(planet)} · {roles}", dossier['foundation']['planets'][planet]['house'],
                     ', '.join(map(str, natal['ruled_houses'])) or '—', ', '.join(map(str, natal['aspected_houses'])) or '—']
            sections.append('<tr>' + ''.join(f'<td>{esc(value)}</td>' for value in cells) + '</tr>')
        sections.append('</table><table><tr>' + ''.join(f"<th>{label(k)}</th>" for k in
            ('Period roles', 'Local interval', 'Transit occupation', 'Transit aspects')) + '</tr>')
        for row in context['periods'][index]['background_house_transits']:
            planet = row['transiting_planet']
            if planet not in levels.values():
                continue
            roles = ', '.join(label(role_names[level]) for level, name in levels.items() if name == planet)
            cells = [f"{label(planet)} · {roles}", dates(row),
                     f"{label('House')} {row['natal_house']} · {sign_names[row['sign_number'] - 1]}",
                     ', '.join(map(str, row['aspected_natal_houses'])) or '—']
            sections.append('<tr>' + ''.join(f'<td>{esc(value)}</td>' for value in cells) + '</tr>')
        sections.append('</table></details>')
        sections.append(f"<details><summary>{label('Calculated transit contacts')}</summary><table><tr><th>{label('Contact')}</th><th>{label('Window (UTC)')}</th><th>{label('Exact passes (UTC)')}</th></tr>")
        for contact in pd['transits']['contacts']:
            contact_label = f"{contact['transiting_planet']} → natal {contact['natal_planet']} ({contact['relationship']}, {contact['aspect_from_planet']})"
            exact = ', '.join(f"{row['at']} {row['motion']}" for row in contact['exact_passes']) or 'In orb; no exact crossing in this PD'
            sections.append(f"<tr><td>{esc(contact_label)}</td><td>{esc(contact['start_at'])}<br>{esc(contact['end_at'])}</td><td>{esc(exact)}</td></tr>")
        sections.append('</table></details></section>')
    if report:
        sections.append(f"<p class='closing'>{esc(report['closing'])}</p>")
    sections.append(f"<details><summary>{label('Natal foundation · calculation worksheets')}</summary>")
    for number, house in dossier['foundation']['houses'].items():
        sections.append(f"<details><summary>{label('House')} {esc(number)} · {esc(house['sign_name'])} · {esc(house['house_lord'])}</summary><pre>{esc(json.dumps(house, ensure_ascii=False, indent=2))}</pre></details>")
    sections.append('</details>')
    return '''<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Your Next Chapter · Local preview</title><style>
*{box-sizing:border-box}body{font:17px/1.65 system-ui;background:#faf5ed;color:#291420;width:100%;max-width:1050px;margin:36px auto;padding:0 24px;overflow-wrap:anywhere}
h1,h2,h3{color:#74183c}h1{font:48px Georgia}section{background:white;padding:24px;border:1px solid #e0cba8;border-radius:18px;margin:22px 0}
table{border-collapse:collapse;font-size:13px;width:100%}td,th{border:1px solid #e0cba8;padding:9px;text-align:left;overflow-wrap:anywhere}
summary{cursor:pointer;padding:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}details{margin:10px 0}
.timing-windows{padding:14px 14px 14px 34px;background:#faf5ed;border-radius:12px;font-size:14px}.brand{font-size:12px;letter-spacing:.16em;color:#74183c;font-weight:700}.period-date{color:#796450}
nav{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px;margin:24px 0}
nav a{padding:14px;border:1px solid #e0cba8;border-radius:10px;color:#74183c;text-decoration:none;background:#fff}
nav small{display:block;color:#796450}h4{margin-bottom:0;color:#74183c}.closing{padding:24px;background:#f0e4d3;border-radius:14px}
section{scroll-margin-top:20px}h1{line-height:1.15}a{color:#74183c}@media(max-width:600px){body{padding:0 14px}h1{font-size:34px}section{padding:18px}}
@media print{body{max-width:none;margin:0}nav,details{display:none}section{break-inside:avoid}}
</style><body>''' + '\n'.join(sections) + '</body></html>'


def main():
    parser = argparse.ArgumentParser(description='Build a local Your Next Chapter preview')
    parser.add_argument('--birth-json', type=Path, required=True)
    parser.add_argument('--as-of', help='ISO timestamp with timezone; defaults to now')
    parser.add_argument('--language', choices=('en', 'hi'), default='en')
    parser.add_argument('--narrate', action='store_true', help='Call the configured timeline model; provider charges apply')
    parser.add_argument('--resume-audit', type=Path, help='Reuse exact matching, revalidated stage responses from a local audit')
    parser.add_argument('--out', type=Path, default=Path('storage/next_chapter/preview'))
    args = parser.parse_args()
    as_of = datetime.fromisoformat(args.as_of.replace('Z', '+00:00')) if args.as_of else datetime.now(timezone.utc)
    dossier = build_next_chapter(json.loads(args.birth_json.read_text()), as_of)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'evidence.json').write_text(json.dumps(dossier, ensure_ascii=False, indent=2, default=str))
    if args.narrate:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    def save_audit(audit):
        (args.out / 'generation-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    resume = json.loads(args.resume_audit.read_text()) if args.resume_audit else None
    narration = asyncio.run(narrate_next_chapter(dossier, args.language, audit_sink=save_audit, resume_audit=resume)) if args.narrate else None
    if narration:
        (args.out / 'report.json').write_text(json.dumps(narration, ensure_ascii=False, indent=2))
    path = args.out / 'preview.html'
    path.write_text(render_preview(dossier, narration))
    print(f"Preview: {path.resolve()}\nCalculation: {dossier['calculation_seconds']} seconds")


if __name__ == '__main__':
    main()
