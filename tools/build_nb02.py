"""Builds notebooks/02_research_questions.ipynb from the text below (keeps the notebook easy to regenerate)."""
import json
import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
TEXT = json.loads((ROOT / 'tools' / 'rq_text.json').read_text(encoding='utf-8'))

nb = nbf.v4.new_notebook()
cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s.strip('\n')))
code = lambda s: cells.append(nbf.v4.new_code_cell(s.strip('\n')))

md(r"""
# NYC Homes × NYC Streets — 12 Research Questions (Milestone 1, part 2)

**Course:** Data Engineering and Visualization, Winter 2026 (GIU) · **Team size:** 6 → 12 research questions + 12 visualizations

This notebook answers the team's research questions using **only** the cleaned and integrated tables produced by
[`01_cleaning_integration.ipynb`](01_cleaning_integration.ipynb). Run that notebook first.

| Input file (data/processed/) | One row is | Used by |
|---|---|---|
| `integrated_nta_month.parquet` | one residential neighborhood (NTA 2020) in one month | RQ1, 2, 4, 5, 7–12 |
| `street_month.parquet` | one street (same normalized name in both datasets) in one month | RQ3 |
| `borough_month.csv` | one borough in one month (all rows, incl. permits without a neighborhood) | RQ6 |
| `nta_boundaries.geojson` | one neighborhood shape | RQ5 map |

**How we avoid trivial or misleading answers** (graded: *"avoid simplistic counts"*, *"claims of causation unsupported by the data"*):
1. **Densities, not raw counts.** Big, busy neighborhoods have more of everything. We divide by area (km²) and by years.
2. **Rank correlation (Spearman ρ).** Counts are very skewed (a few neighborhoods are huge), so ranks are more robust than Pearson.
3. **Within-borough comparisons.** Manhattan has both dense permits and dense housing; comparing inside the borough removes that confounder.
4. **Two-way demeaning for timing questions.** Before testing "does street work come *before* complaints?", we remove each
   neighborhood's own average and each month's city-wide average. What is left is "unusual street work here, this month" vs
   "unusual complaints here, this month", so winter and busy places cannot create a fake link.
5. **Out-of-sample testing for prediction** (train 2022–2024, test 2025).
6. Every answer states its **limits**. Correlation is never presented as causation.

All analysis code is in [`src/analysis.py`](../src/analysis.py) (one function per question), so the **same code** feeds this
notebook and the website.
""")

code(r"""
import sys, json
from pathlib import Path
import pandas as pd
import plotly.io as pio

ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT / 'src'))
import analysis as A            # our analysis functions (one per research question)

PROCESSED = ROOT / 'data' / 'processed'
FIG_DIR = ROOT / 'visualizations'            # PNG copies of every chart (for the report / README)
APP_FIG_DIR = ROOT / 'data' / 'app' / 'rq_figures'   # interactive copies used by the website
FIG_DIR.mkdir(exist_ok=True); APP_FIG_DIR.mkdir(parents=True, exist_ok=True)
pd.set_option('display.float_format', '{:,.3f}'.format)
pd.set_option('display.width', 180)

integrated, street, borough_month, nta_geo = A.load_outputs(PROCESSED)
print('integrated :', integrated.shape, '| months:', integrated['year_month'].nunique(),
      '| neighborhoods:', integrated['nta_code'].nunique())
print('street     :', street.shape)
print('borough    :', borough_month.shape)
print('H6 problems in the integrated table:', f"{integrated['h6_problems'].sum():,}",
      '| T3 permits:', f"{integrated['t3_permits'].sum():,}")


def save(fig, name, width=1100):
    # Save an interactive JSON copy for the website and (if kaleido is installed) a PNG for reports.
    (APP_FIG_DIR / f'{name}.json').write_text(pio.to_json(fig), encoding='utf-8')
    try:
        fig.write_image(FIG_DIR / f'{name}.png', width=width, height=fig.layout.height or 500, scale=2)
    except Exception as err:          # PNG export is optional (needs `pip install kaleido`)
        print(f'(PNG not saved: {err.__class__.__name__})')
    fig.show()


RESULTS = {}   # key numbers collected for the website's story section
""")

calls = {
    'rq1': ("table, fig, st = A.rq1_density_scatter(integrated)\n"
            "print(f\"Spearman rho = {st['rho']:.3f} (p = {st['p']:.2g}, n = {st['n']})\")\n"
            "display(table.round(3))"),
    'rq2': ("table, fig, st = A.rq2_seasonal_cycles(integrated)\n"
            "print({k: v for k, v in st.items()})\n"
            "display(table.T)"),
    'rq3': ("table, fig, st = A.rq3_same_street_gas(street)\n"
            "display(table)"),
    'rq4': ("table, fig, st = A.rq4_lagged_utility_links(integrated)\n"
            "display(table.pivot(index='pair', columns='lag_months', values='rho').round(3))\n"
            "display(table[['pair', 'lag_months', 'rho', 'ci_low', 'ci_high', 'p', 'n']])"),
    'rq5': ("table, fig, st = A.rq5_double_burden_map(integrated, nta_geo)\n"
            "print('Neighborhood counts per class:', st['counts'])\n"
            "print('If the two were unrelated we would expect about', st['expected_if_independent'],\n"
            "      'double-burden neighborhoods (25% x 25% of', st['n'], ')')\n"
            "print('Double-burden neighborhoods by borough:', st['by_borough'])\n"
            "display(table.head(25))"),
    'rq6': ("table, fig, st = A.rq6_complaints_per_permit_heatmap(borough_month)\n"
            "display(table.round(2))"),
    'rq7': ("table, fig, st = A.rq7_close_time_by_intensity(integrated)\n"
            "print(f\"Kruskal-Wallis p = {st['kruskal_p']:.3g} | Spearman rho = {st['rho']:.3f} (n = {st['n']:,})\")\n"
            "display(table)"),
    'rq8': ("table, fig, st = A.rq8_top_stress_neighborhoods(integrated)\n"
            "display(table.round(2))"),
    'rq9': ("table, fig, st = A.rq9_work_mix_by_heat_quintile(integrated)\n"
            "display(table)"),
    'rq10': ("table, fig, st = A.rq10_change_on_change(integrated)\n"
             "print(f\"Spearman rho = {st['rho']:.3f} (p = {st['p']:.2g}, n = {st['n']})\")\n"
             "print('Rows: permits grew?  Columns: complaints grew?'); display(st['quadrants'])"),
    'rq11': ("table, fig, st = A.rq11_correlation_matrix(integrated)\n"
             "print('Strongest cross-domain pairs:', st['strongest_cross_pairs'])\n"
             "display(table)"),
    'rq12': ("table, fig, st = A.rq12_predictive_value(integrated)\n"
             "print(st)\n"
             "display(table)"),
}

member_of = {r['id']: r['member'] for r in TEXT['research_questions']}
last_member = None
for r in TEXT['research_questions']:
    if r['member'] != last_member:
        md(f"---\n## {r['member']}")
        last_member = r['member']
    md(f"### {r['id'].upper()}. {r['question']}\n\n**Why it matters:** {r['why']}\n\n**Method:** {r['method']}\n\n"
       f"**Chart choice:** {r['chart']}")
    code(calls[r['id']] + f"\nRESULTS['{r['id']}'] = st\nsave(fig, '{r['id']}')")
    md(f"**Answer.** {r['answer']}\n\n**Limits.** {r['limits']}")

md(r"""
---
## Summary of findings

""" + TEXT['summary_table'])

md(r"""
## Export the story for the website
The website (`app.py`) shows the same 12 charts (saved above as JSON) and the story text below. Writing it from the notebook
keeps the notebook, the website and the report consistent.
""")
code(r"""
story = json.loads((ROOT / 'tools' / 'rq_text.json').read_text(encoding='utf-8'))
(ROOT / 'data' / 'app' / 'story.json').write_text(json.dumps(story, indent=2, ensure_ascii=False), encoding='utf-8')
print('story.json written with', len(story['research_questions']), 'research questions')
""")

md(r"""
## Prompts used (required deliverable)
AI assistance (Claude) was used while building this notebook. The prompts were:
""" + '\n'.join(f'{i + 1}. *{p}*' for i, p in enumerate(TEXT['prompts'])))

nb['cells'] = cells
nb['metadata'] = {'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'},
                  'language_info': {'name': 'python'}}
out = ROOT / 'notebooks' / '02_research_questions.ipynb'
out.parent.mkdir(exist_ok=True)
nbf.write(nb, out)
print('written', out)
