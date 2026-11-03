import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
fig, ax = plt.subplots(figsize=(11, 6.2)); ax.set_xlim(0, 110); ax.set_ylim(0, 62); ax.axis('off')
def box(x, y, w, h, title, lines, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.4,rounding_size=1.2', fc=color, ec='#444', lw=1))
    ax.text(x + w/2, y + h - 2.2, title, ha='center', va='top', fontsize=9.5, weight='bold', color='#1d1d1b')
    ax.text(x + w/2, y + h - 5.6, '\n'.join(lines), ha='center', va='top', fontsize=7.6, color='#333', linespacing=1.35)
def arrow(x1, y1, x2, y2):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', color='#555', lw=1.3))
B, O, G, P, Y = '#dbe8f8', '#fbe1d3', '#e6e4dc', '#e7dcf3', '#f4ecd0'
box(1, 44, 22, 16, 'H6 · HPD complaints', ['ygpa-z7cr (Socrata API)', '3,160,386 problems', '2022-01 → 2025-12', '26 of 33 columns'], B)
box(1, 24, 22, 16, 'T3 · DOT permits', ['tqtj-sjs8 (Socrata API)', '2,577,722 permits', '2022-01 → 2025-12', '20 of 39 columns + WKT'], O)
box(1, 4, 22, 16, 'NTA 2020 boundaries', ['9nt8-h7nd (DCP)', '262 areas, 197 residential', 'used for spatial join', '+ area in km²'], G)
box(29, 44, 24, 16, 'Pre-clean H6', ['text/placeholder fix, labels', 'dates, ZIP/BBL/coord rules', 'impute from same building', 'IQR cap days-to-close'], B)
box(29, 24, 24, 16, 'Pre-clean T3', ['drop voided, typo fixes', 'domain rules + IQR caps', 'WKT → point → sjoin NTA', 'fill from same segment'], O)
box(59, 30, 22, 24, 'Integration', ['aggregate both to', 'NTA × month (main)', '197 × 48 = 9,456 rows', '', '+ street × month', '+ borough × month', 'outer grid, conservation', 'checks'], P)
box(59, 4, 22, 20, 'Post-integration', ['NaN from joins → 0', '(medians stay NaN)', 'drop constant columns', 'fix float→int dtypes', 'features: /km², lags,', 'z-scores, shares'], P)
box(87, 38, 22, 18, 'Notebook 02', ['src/analysis.py', '12 research questions', 'Spearman, lags, tests,', 'out-of-sample R²', '→ PNG + JSON charts'], Y)
box(87, 10, 22, 22, 'Dash website', ['app.py (Render)', '5 dropdowns + search', 'Generate Report →', '7 live charts + KPIs', 'Story / 12 RQs / Team', 'tabs'], Y)
arrow(23, 52, 29, 52); arrow(23, 32, 29, 32); arrow(23, 12, 40, 24)
arrow(53, 52, 59, 46); arrow(53, 32, 59, 38); arrow(70, 30, 70, 24)
arrow(81, 18, 87, 44); arrow(81, 14, 87, 18); arrow(98, 38, 98, 32)
ax.text(55, 61.5, 'Pipeline: notebooks/01_cleaning_integration.ipynb  →  data/processed/  →  notebook 02 + website',
        ha='center', fontsize=10, weight='bold', color='#16233a')
plt.savefig(__import__('pathlib').Path(__file__).resolve().parents[1] / 'docs' / 'images' / 'architecture.png', dpi=200, bbox_inches='tight')
