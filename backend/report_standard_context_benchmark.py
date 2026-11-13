"""Summarize captured benchmark artifacts; no model or database calls."""
import csv
import json
from pathlib import Path
import re

from benchmark_standard_context import OUT, ROWS, measure

calls = json.loads((OUT / 'calls.json').read_text())
manifest = json.loads((OUT / 'manifest.json').read_text())
rows = list(csv.DictReader((OUT / 'object_sizes.csv').open()))
for file in OUT.glob('call_*_input.json'):
    prompt = json.loads(file.read_text())['prompt']
    for match in re.finditer(r'([A-Z][A-Z_]*JSON):\s*\n', prompt):
        try:
            obj, _ = json.JSONDecoder().raw_decode(prompt[match.end():])
        except ValueError:
            continue
        measure(file.stem + ':' + match[1], obj)
rows.extend(ROWS)
with (OUT / 'all_object_sizes.csv').open('w') as f:
    writer = csv.DictWriter(f, fieldnames=['stage', 'path', 'type', 'chars', 'utf8_bytes', 'items'])
    writer.writeheader()
    writer.writerows(rows)

lines = ['# Standard context benchmark', '', 'Question: ' + manifest['question'], '',
         f"Saved chart: {manifest['chart_id']}. Actual model calls; Standard, Technical, empty history. "
         'Controlled replay runs reuse saved router intent and chart evidence. '
         'This invokes the analyzer directly, not the billing/persistence HTTP endpoint. '
         'Sizes below are exact compact-JSON characters; model tokens come from provider usage. '
         'Shared cache is additional input to every model call. Object sizes are inclusive: parents and children must not be added together.', '',
         '| Stage | JSON chars | Instruction chars | Full uncached prompt chars | Input tokens | Cached tokens | Uncached tokens |',
         '|---|---:|---:|---:|---:|---:|---:|']
for call in calls:
    label = call['tag'].removeprefix('parallel_')
    file = OUT / ('branch_' + label + '.json')
    if file.exists():
        data = json.loads(file.read_text())
        size = len(json.dumps(data['payload'], ensure_ascii=False, separators=(',', ':')))
        instruction = len(data['instructions'])
    else:
        size = instruction = '—'
    usage = call.get('metrics', {}).get('token_usage', {})
    lines.append(f"| {label} | {size} | {instruction} | {call['prompt_chars']} | {usage.get('input_tokens')} | {usage.get('cached_tokens')} | {usage.get('non_cached_input_tokens')} |")
for stage in [r['stage'] for r in rows if r['path'] == '$']:
    parts = [r for r in rows if r['stage'] == stage and r['path'].startswith('$.') and r['path'].count('.') == 1 and '[' not in r['path']]
    lines.extend(['', '## ' + stage, '', '| Object | Characters |', '|---|---:|'])
    for r in sorted(parts, key=lambda r: int(r['chars']), reverse=True):
        lines.append(f"| {r['path']} | {r['chars']} |")
(OUT / 'report.md').write_text('\n'.join(lines) + '\n')
print('\n'.join(lines[:17]))
print('Object rows:', len(rows))
print('Total input tokens:', sum(c.get('metrics',{}).get('token_usage',{}).get('input_tokens',0) for c in calls))
