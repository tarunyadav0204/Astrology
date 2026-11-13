"""Render a manually evidence-audited benchmark matrix; never calls a model.

Usage: python report_cross_chart_validation.py /path/to/matrix
The findings.json ledger is a human-reviewed input, not an automatic accuracy score.
"""
import html
import json
from pathlib import Path
import sys


def render(root):
    ledger = json.loads((root / 'findings.json').read_text())
    findings = ledger['findings']
    runs = json.loads((root / 'runs.json').read_text())
    esc = lambda value: html.escape(str(value))
    sections = []
    total_calls = total_tokens = 0
    for run in runs:
        name = run['case']
        folder = root / name
        calls = json.loads((folder / 'calls.json').read_text())
        answer = json.loads((folder / 'answer.json').read_text())
        manifest = json.loads((folder / 'manifest.json').read_text())
        rows = [f for f in findings if f['case'] == name]
        tokens = sum(c['metrics']['token_usage']['input_tokens'] for c in calls)
        total_calls += len(calls)
        total_tokens += tokens
        retained = sum(f['final'].startswith(('Present', 'Repeated')) for f in rows)
        branch = sum(f['stage'] != 'merge' for f in rows)
        sections.append(
            f"<tr><td><a href='#{esc(name)}'>{esc(name)}</a></td>"
            f"<td>{len(calls)}</td><td>{esc(answer.get('success'))}</td>"
            f"<td>{branch}</td><td>{retained}</td><td>{tokens:,}</td>"
            f"<td>{run['elapsed_s']}s</td></tr>"
        )
        run.update(input_tokens=tokens, model_calls=len(calls),
                   all_model_calls_successful=all(c['metrics']['success'] for c in calls),
                   answer_success=answer.get('success'),
                   documented_branch_errors=branch, documented_final_errors=retained,
                   question=manifest['question'])
    summary = {
        'method': ledger['scope'], 'runs': runs, 'total_model_calls': total_calls,
        'total_input_tokens': total_tokens, 'documented_discrepancies': len(findings),
        'findings_file': str(root / 'findings.json'),
        'coverage': ledger.get('coverage', []),
        'baseline_regressions': ledger.get('baseline_regressions', []),
    }
    (root / 'summary.json').write_text(json.dumps(summary, indent=2))
    content = ["<!doctype html><meta charset='utf-8'><title>Cross-chart factual validation</title>",
               "<style>body{font:16px system-ui;max-width:1150px;margin:40px auto;padding:0 24px;color:#17212b}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{border:1px solid #ccd4db;padding:10px;text-align:left;vertical-align:top}th{background:#eef2f5}li{margin:8px 0}.finding{border-left:4px solid #b24938;padding:10px 18px;margin:20px 0}small{color:#52616e}a{color:#175eac}</style>",
               f"<h1>Cross-chart factual validation</h1><p><b>{esc(ledger.get('result', 'See the documented findings below.'))}</b></p>",
               f"<p>{esc(ledger['scope'])}</p><ul>"]
    content += [f'<li>{esc(x)}</li>' for x in summary['coverage']]
    content += ["</ul><table><tr><th>Case</th><th>Calls</th><th>Completed</th><th>Branch errors found</th><th>Final errors found</th><th>Input tokens</th><th>Wall time</th></tr>", *sections, "</table>",
                "<p>Zero errors found in a final answer means no confirmed error within this audit, not a certificate of correctness. Interpretive quality and prediction validity were not scored. Branch errors omitted by merge are distinguished from corrected facts.</p>"]
    if ledger.get('baseline_regressions'):
        content.append('<h2>Original discrepancies: rerun comparison</h2><table><tr><th>ID / case</th><th>Original error</th><th>Rerun evidence</th></tr>')
        for row in ledger['baseline_regressions']:
            content.append(f"<tr><td>{esc(row['id'])} / {esc(row['case'])}</td><td>{esc(row['claim'])}</td><td>{esc(row['outcome'])}</td></tr>")
        content.append('</table>')
    for run in runs:
        name = run['case']
        content += [f"<h2 id='{esc(name)}'>{esc(name)}</h2><p>{esc(run['question'])}</p>",
                    f"<p><a href='{esc(name)}/answer.json'>Final answer</a> · <a href='{esc(name)}/builder.json'>Calculated context</a> · <a href='{esc(name)}/calls.json'>Call metrics</a></p>"]
        for f in findings:
            if f['case'] != name:
                continue
            content.append(f"<div class='finding'><b>{esc(f['id'])} — {esc(f['stage'])}</b><p>Claim: {esc(f['claim'])}</p><p>Calculated fact: {esc(f['expected'])}</p><p>Final outcome: {esc(f['final'])}</p><small>Evidence: {esc(f['source'])}</small></div>")
    (root / 'report.html').write_text('\n'.join(content))
    print(json.dumps({'runs': len(runs), 'model_calls': total_calls, 'input_tokens': total_tokens,
                      'findings': len(findings), 'report': str(root / 'report.html')}))


if __name__ == '__main__':
    render(Path(sys.argv[1]))
