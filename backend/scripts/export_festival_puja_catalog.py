"""Regenerate the shared festival selection/coverage data for both clients."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from festivals.verified_puja import coverage_catalog

if __name__ == '__main__':
    text = json.dumps(coverage_catalog(), ensure_ascii=False, indent=2) + '\n'
    for client in ('frontend', 'astroroshni_mobile'):
        path = ROOT / client / 'src/data/festivalPujaCatalog.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
