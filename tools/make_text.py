"""Combine rq_meta.py + rq_answers.py into tools/rq_text.json (read by notebook 02 and, via story.json, by the website)."""
import json
from pathlib import Path
import rq_meta as M
import rq_answers as A

rqs = []
for r in M.RQS:
    ans, lim = A.ANSWERS[r['id']]
    rqs.append({**r, 'answer': ans, 'limits': lim})
out = {'research_questions': rqs, 'team': M.TEAM, 'prompts': M.PROMPTS, 'summary_table': A.SUMMARY_TABLE,
       **{k: v for k, v in A.STORY.items() if v is not None},
       'links': {'H6 · Housing Maintenance Code Complaints and Problems (HPD)': 'https://data.cityofnewyork.us/d/ygpa-z7cr',
                 'T3 · Street Construction Permits 2022-Present (DOT)': 'https://data.cityofnewyork.us/d/tqtj-sjs8',
                 '2020 Neighborhood Tabulation Areas (DCP, boundaries only)': 'https://data.cityofnewyork.us/d/9nt8-h7nd'}}
Path(__file__).with_name('rq_text.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
print('rq_text.json written')
