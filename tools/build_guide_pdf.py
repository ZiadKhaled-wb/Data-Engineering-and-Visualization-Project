"""Builds docs/Team_Evaluation_Guide.pdf (the team's explainer for the evaluation)."""
import json
import re
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / 'docs' / 'images'
TEXT = json.loads((ROOT / 'tools' / 'rq_text.json').read_text(encoding='utf-8'))
OUT = ROOT / 'docs' / 'Team_Evaluation_Guide.pdf'
OUT.parent.mkdir(exist_ok=True)

F = '/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('DV', F + 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVB', F + 'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DVI', F + 'DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DVM', F + 'DejaVuSansMono.ttf'))
from reportlab.pdfbase.pdfmetrics import registerFontFamily  # noqa: E402
registerFontFamily('DV', normal='DV', bold='DVB', italic='DVI', boldItalic='DVB')

NAVY, ACCENT, BLUE, ORANGE, MUTED = (colors.HexColor(c) for c in ('#16233a', '#8b1e3f', '#2a78d6', '#eb6834', '#6b6a64'))
LIGHT = colors.HexColor('#f3f2ee')
base = dict(fontName='DV', fontSize=9.6, leading=13.6, textColor=colors.HexColor('#1d1d1b'))
S = {
    'body': ParagraphStyle('body', **base, spaceAfter=5),
    'small': ParagraphStyle('small', **{**base, 'fontSize': 8.4, 'leading': 11.4, 'textColor': MUTED}),
    'h1': ParagraphStyle('h1', fontName='DVB', fontSize=17, leading=21, textColor=NAVY, spaceBefore=4, spaceAfter=8),
    'h2': ParagraphStyle('h2', fontName='DVB', fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=10, spaceAfter=5),
    'h3': ParagraphStyle('h3', fontName='DVB', fontSize=10.5, leading=14, textColor=ACCENT, spaceBefore=8, spaceAfter=3),
    'bullet': ParagraphStyle('bullet', **base, leftIndent=12, bulletIndent=2, spaceAfter=2.5),
    'cell': ParagraphStyle('cell', **{**base, 'fontSize': 8.4, 'leading': 11}),
    'cellb': ParagraphStyle('cellb', **{**base, 'fontName': 'DVB', 'fontSize': 8.4, 'leading': 11, 'textColor': colors.white}),
    'q': ParagraphStyle('q', fontName='DVB', fontSize=9.6, leading=13.4, textColor=NAVY, spaceBefore=6, spaceAfter=1),
    'a': ParagraphStyle('a', **base, leftIndent=10, spaceAfter=4),
    'tag': ParagraphStyle('tag', fontName='DVB', fontSize=8, leading=10, textColor=ACCENT),
    'cover_t': ParagraphStyle('ct', fontName='DVB', fontSize=30, leading=36, textColor=colors.white),
    'cover_s': ParagraphStyle('cs', fontName='DV', fontSize=12.5, leading=18, textColor=colors.HexColor('#d7dce6')),
}


def md(text):
    """tiny markdown → reportlab markup (**bold**, *italic*, `code`)."""
    t = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?!\w)', r'<i>\1</i>', t)
    t = re.sub(r'`(.+?)`', r'<font name="DVM" size="8.4">\1</font>', t)
    return t


def P(text, style='body'):
    return Paragraph(md(text), S[style])


def bullets(items, style='bullet'):
    return [Paragraph(md(i), S[style], bulletText='•') for i in items]


def table(rows, widths, header=True, zebra=True):
    data = [[Paragraph(md(str(c)), S['cellb' if (header and r == 0) else 'cell']) for c in row]
            for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#d6d4cc')),
          ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
          ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
    if header:
        st.append(('BACKGROUND', (0, 0), (-1, 0), NAVY))
    if zebra:
        for r in range(1, len(rows)):
            if r % 2 == 0:
                st.append(('BACKGROUND', (0, r), (-1, r), LIGHT))
    t.setStyle(TableStyle(st))
    return t


def img(path, width):
    w, h = PILImage.open(path).size
    return Image(str(path), width=width, height=width * h / w)


def callout(text, color=BLUE):
    t = Table([[Paragraph(md(text), S['body'])]], colWidths=[170 * mm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), LIGHT), ('LINEBEFORE', (0, 0), (0, -1), 3, color),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 6),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    return t


W = 170 * mm
story = []

# ---------------------------------------------------------------- cover
cover = Table([[[Spacer(1, 30 * mm), Paragraph('NYC Homes × NYC Streets', S['cover_t']), Spacer(1, 4 * mm),
                 Paragraph('Team Evaluation Guide', ParagraphStyle('x', parent=S['cover_s'], fontName='DVB',
                                                                    fontSize=16, leading=20, textColor=colors.white)),
                 Spacer(1, 6 * mm),
                 Paragraph('Housing Maintenance Code Complaints (H6, HPD) × Street Construction Permits (T3, DOT), '
                           'New York City 2022–2025', S['cover_s']),
                 Spacer(1, 4 * mm),
                 Paragraph('Data Engineering and Visualization · Winter 2026 · Milestone 1<br/>'
                           'German International University · Faculty of Informatics and Computer Science',
                           S['cover_s']),
                 Spacer(1, 60 * mm),
                 Paragraph('What this guide is for: every team member should be able to explain the whole project, '
                           'defend every cleaning and integration decision, present their own two research '
                           'questions, demo the website and answer the evaluators\' questions. Read sections 1–3 '
                           'together, then each member studies their own RQs (section 6) and the Q&amp;A '
                           '(section 9).', S['cover_s']),
                 Spacer(1, 30 * mm)]]], colWidths=[W])
cover.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), NAVY), ('LEFTPADDING', (0, 0), (-1, -1), 10 * mm),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 10 * mm)]))
story += [cover, PageBreak()]

# ---------------------------------------------------------------- contents
story.append(P('Contents', 'h1'))
for line in ['1. The project in one page', '2. Requirements checklist (what the graders look for)',
             '3. Datasets and why we chose them', '4. Architecture and the data pipeline, step by step',
             '5. Integration: key, granularity and post-integration cleaning',
             '6. The 12 research questions (one page per member)', '7. The website: features and a 3-minute demo script',
             '8. How to run, reproduce and deploy', '9. Likely evaluation questions with model answers',
             '10. Statistics cheat-sheet', '11. Limitations to state honestly',
             '12. Before submission: open tasks and per-member checklist']:
    story.append(P(line))
story.append(PageBreak())

# ---------------------------------------------------------------- 1
story.append(P('1. The project in one page', 'h1'))
story.append(callout('**Question.** Are street disruption (DOT street construction permits) and housing distress (HPD '
                     'housing maintenance problems) concentrated in the same NYC neighborhoods? If so, does street work '
                     'come *before* indoor problems (a mechanism), or do both simply reflect the same kind of place '
                     '(a shared cause)?'))
story.append(Spacer(1, 4))
story.append(callout('**Answer.** Same places, but no mechanism. Densities are strongly linked across 197 residential '
                     'neighborhoods (Spearman ρ = 0.65). Every test of *timing* or *change* finds nothing: same-street '
                     'gas work, 0–3 month lags, growth-on-growth, and out-of-sample prediction (R² 0.924 → 0.925). The '
                     'overlap is explained by shared neighborhood characteristics (dense, older residential housing '
                     'stock), not by street work damaging homes.', ACCENT))
story.append(P('Headline numbers to remember', 'h2'))
story.append(table([
    ['Item', 'Value'],
    ['H6 housing problems 2022–2025', '3,160,386 downloaded → 3,153,693 after cleaning'],
    ['T3 street permits 2022–2025', '2,577,722 downloaded → 2,575,684 after cleaning (2,038 voided removed)'],
    ['Permits placed in a neighborhood', '2,508,047 in residential NTAs (97.4%); 42,132 in parks/airports etc.; 25,505 unplaceable'],
    ['Integrated table', '197 residential neighborhoods × 48 months = 9,456 rows, 119 columns'],
    ['Spatial link', 'ρ = 0.65 city-wide; Bronx 0.82, Queens 0.77, Staten Island 0.65, Brooklyn 0.19, Manhattan −0.78'],
    ['Double-burden neighborhoods', '18 (12 expected by chance), West Bronx + Upper Manhattan'],
    ['Seasons', 'complaints peak Dec–Jan (heat ×15 vs Aug); permits peak Mar and Jun'],
    ['Prediction', 'own history + season R² = 0.924; + street-work lags 0.925; street-work only 0.13'],
], [55 * mm, 115 * mm]))
story.append(P('The five parts of our story (the project description asks for exactly these)', 'h2'))
story += bullets([
    '**The question:** see above. It matters because more than 600,000 permits a year open or occupy streets right outside '
    'buildings where tenants report 750k–850k problems a year.',
    '**The data:** H6 + T3 from NYC Open Data, connected by a *spatial join* (permit geometry → official 2020 '
    'neighborhood) and aggregation to neighborhood × month.',
    '**The discovery:** strong co-location, a reversed pattern inside Manhattan (commercial Midtown vs residential '
    'Harlem), opposite seasons, and no evidence of a street-to-home mechanism.',
    '**The limits:** correlation is not causation, permits are permissions and not observed work, monthly × neighborhood '
    'aggregation can hide very local or very short effects, complaints measure reporting, and there is no '
    'population denominator.',
    '**The impact:** a double-burden map and within-borough ranking for joint HPD/DOT outreach, and a finding that saves '
    'HPD effort: complaint forecasting needs only the neighborhood\'s own history and the heat season.',
])
story.append(PageBreak())

# ---------------------------------------------------------------- 2
story.append(P('2. Requirements checklist (what the graders look for)', 'h1'))
story.append(P('Every requirement from the Milestone 1 description, and where we meet it. Know where each one is so you '
               'can open it during the evaluation.'))
story.append(table([
    ['Requirement', 'Where it is', 'Status'],
    ['One housing + one transport dataset, each ≥ 9 columns, with an integration attribute', 'H6 (33 cols) + T3 (39 cols); NB01 §4, automatic check §14', 'Done'],
    ['Dataset overview: rows, columns, geo/time attributes, known issues, why chosen, how sizes are aligned', 'NB01 §4 + §4.1 table', 'Done'],
    ['EDA with statistics and plots', 'NB01 §5 (H6) and §6 (T3): missing values, categories, time, geography, duplicates, outliers', 'Done'],
    ['Missing values: justify drop vs impute', 'NB01 §7.8 (impute from same building), §8.10 (fill from same street segment), log', 'Done'],
    ['Outliers (IQR, domain rules)', 'NB01 §7.10 (days to close, log-IQR) and §8.6–8.7 (durations, sizes)', 'Done'],
    ['Inconsistent data, standardized formats', 'NB01 §7.2–7.6, §8.2–8.3 (text, labels, dates, ZIP/BBL/coords, typo fixes)', 'Done'],
    ['Remove duplicates', 'NB01 §7.7, §8.5 (exact, repeated IDs; renewals are not duplicates)', 'Done'],
    ['Integration with justified key and granularity', 'NB01 §9.1 comparison table; key = NTA × month', 'Done'],
    ['Post-integration cleaning: new NaNs, redundant columns, type mismatches', 'NB01 §10.1–10.4', 'Done'],
    ['Visualizations validating cleaning', 'NB01 §12', 'Done'],
    ['Prompts used + dataset links', 'NB01 §16, NB02 last section, README §10', 'Done'],
    ['2 RQs + 2 charts per member (6 → 12 + 12)', 'NB02, src/analysis.py, website tab "12 research questions"', 'Done'],
    ['Website: multiple dropdowns', 'Borough, Year, H6 type, T3 kind, Neighborhood', 'Done'],
    ['Website: search mode', 'Free text → sets the dropdowns (e.g. "Brooklyn 2022 new buildings")', 'Done'],
    ['Website: central "Generate Report" button', 'Rebuilds KPIs + 7 charts', 'Done'],
    ['Variety of interactive charts incl. a cross-domain one', 'Map, scatter, timeline, lag bars, ranking, heatmap, box', 'Done'],
    ['Story section', 'Website tab "Our story"', 'Done'],
    ['Deployed on a free platform', 'Render config ready (render.yaml, Procfile)', '**TO DO**: deploy + test'],
    ['GitHub repo with full source + README (setup, deploy, contributions)', 'README.md written', '**TO DO**: push to the team repo'],
    ['Contribution documentation', 'README §7, NB01 header, website "Team & data" tab', '**Check** the roles are accurate'],
    ['Submission email to ICS503Data@gmail.com by 9 Nov 2026', 'IDs, repo link, deployment link, dataset links', '**TO DO**'],
], [62 * mm, 82 * mm, 26 * mm]))
story.append(PageBreak())

# ---------------------------------------------------------------- 3
story.append(P('3. Datasets and why we chose them', 'h1'))
story.append(table([
    ['', 'H6: Housing Maintenance Code Complaints and Problems', 'T3: Street Construction Permits (2022–Present)'],
    ['Agency / ID', 'HPD · ygpa-z7cr', 'DOT · tqtj-sjs8'],
    ['One row is', 'one problem inside a tenant complaint (a complaint can list several problems; mean 1.64)', 'one permit to open, occupy or build on a street or sidewalk'],
    ['Size', '~16.4M rows in total; 3,160,386 in 2022–2025; 33 columns', '~3.99M rows in total; 2,577,722 issued 2022–2025; 39 columns'],
    ['Time', 'received_date, problem_status_date', 'permitissuedate, issuedworkstartdate, issuedworkenddate'],
    ['Geography', 'borough, ZIP, street, house no., lat/lon, BBL, **NTA name**', 'borough, on/from/to street, **WKT geometry** (State Plane feet)'],
    ['Known issues', 'placeholders (N/A, UNKNWN), label variants (HEATING vs HEAT/HOT WATER), 6,363 negative close times, 15.9% HPD duplicate-report flags', '~13% no geometry, typo COMMERICAL, 650 equipment spelling variants, impossible sizes (e.g. 102M sq ft), voided permits'],
], [24 * mm, 73 * mm, 73 * mm]))
story.append(P('Why this pair?', 'h2'))
story += bullets([
    'Both are in the official catalog (H6 and T3). Both have time *and* geography, and both are large enough for '
    'neighborhood × month statistics.',
    'The connection is physical and plausible: gas, water and steam mains and building operations happen *outside* '
    'the very buildings tenants complain about. That gives testable hypotheses (heat ↔ gas work, plumbing ↔ water/sewer '
    'work), not just "count A vs count B".',
    'T3 only exists from 2022, so the window is 2022-01-01 to 2025-12-31: **4 complete years**, so every month and '
    'season appears equally often.',
    '**Why the full data and not a sample?** The description allows a filtered sample *if justified*. Our earlier starter '
    'sample took the first ~860 rows of each month, all from days 1–3, which makes every month identical in size and '
    'is useless for counts. The full download (paged, resumable, about 1 hour) removes any sampling bias. If asked: '
    '"we chose the full window because our questions are about counts and densities, and a sample would distort exactly '
    'those."',
])
story.append(PageBreak())

# ---------------------------------------------------------------- 4
story.append(P('4. Architecture and the data pipeline, step by step', 'h1'))
story.append(img(SHOTS / 'architecture.png', W))
story.append(P('Step-by-step (notebook 01, section numbers in brackets)', 'h2'))
steps = [
    ('Download [2–3]', 'Socrata SoQL API with `$select`, `$where` (date window), `$order=:id` (stable paging), `$limit` 250,000, `$offset`. Each page is saved as parquet, so a crash resumes from the last page. Text columns are stored as *category* to save memory (H6 fits in 0.55 GB).'),
    ('EDA [5–6]', 'Shape, dtypes, missing-value report, value counts, spelling-variant detection, monthly time pattern, coordinate/ZIP checks, duplicates, distribution of close times and permit sizes, geometry types.'),
    ('H6 cleaning [7]', 'snake_case names; trim/UPPER/placeholders → NaN; semantic label merges (HEATING → HEAT/HOT WATER, VERMIN/PESTS → PESTS/VERMIN) and automatic spelling-variant merges; ISO dates; domain rules (5 boroughs, NYC ZIPs 100–104/110–116, coords inside NYC box, valid BBL/community board); duplicates; imputation **from the same building** (2,505 ZIPs, 264 coordinates/NTA names); NTA name → official code (100% matched; 99.93% agree with coordinates); 6,294 borough conflicts and 399 rows without neighborhood dropped; days-to-close: 6,359 impossible → NaN, log-IQR fence 180.9 days, 32,677 capped (1.04%).'),
    ('T3 cleaning [8]', 'short readable names; typo COMMERICAL fixed; 650 equipment variants merged; 2,038 VOIDED permits removed (no work allowed); renewals kept (a renewal is a new legal permit); duplicates checked (0); domain rules (cuts > 1,000, sq ft > 5M, linear feet = 9,999 placeholder → NaN) then IQR capping (27,368 cut counts, 72 sq-ft values); work duration checked (0 inconsistent).'),
    ('Geometry → neighborhood [8.8–8.10]', 'WKT text → shapely geometry → `point_on_surface` (always on the line) → EPSG:2263 feet; `geopandas.sjoin(predicate="within")` with the NTA polygons, plus nearest NTA within 300 ft for points on boundary streets. Permits with no geometry are filled from other permits on the **same segment** (on/from/to street, 260,709), same segment end (45,790) or same street (2,312), using only clear majorities (≥ 90%). 2,616 borough conflicts → UNMAPPED.'),
    ('Integration [9]', 'complete grid of 197 residential NTAs × 48 months; H6 and T3 aggregated with 0/1 indicators + `groupby().agg()`; left-joined onto the grid. Conservation check: every problem and permit is counted exactly once.'),
    ('Post-integration [10]', 'NaN created by the join → 0 for counts (no complaint = zero complaints), medians stay NaN (a median of nothing is undefined, not 0); constant columns dropped (nta_type, is_residential); float → int for counts; key dtypes unified (datetime64[ns]); automatic asserts.'),
    ('Features [11]', 'per-km² densities, shares and rates, log transforms, lags 1–3 and rolling 3-month sums, year-over-year change, within-borough-month z-scores, calendar features.'),
    ('Outputs [13]', '`integrated_nta_month.parquet/csv`, `street_month.parquet`, `borough_month.csv`, `nta_boundaries.geojson`, `data_dictionary.csv`, `cleaning_log.csv`.'),
]
story.append(table([['Step', 'What we did and why']] + [[a, b] for a, b in steps], [33 * mm, 137 * mm]))
story.append(PageBreak())

# ---------------------------------------------------------------- 5
story.append(P('5. Integration: key, granularity and post-integration cleaning', 'h1'))
story.append(P('The two datasets share **no ID**. The catalog warns against forcing a row-level join "merely because a '
               'common attribute exists". We compared every option:'))
story.append(table([
    ['Option', 'Verdict'],
    ['Row level (complaint ↔ permit)', 'No shared ID or address → meaningless; explicitly discouraged'],
    ['Building / address', 'T3 house number is ~63% empty and T3 rows are street segments → too few matches'],
    ['Street name × month', 'Useful for "same street" (RQ3), kept as an extra table; long streets cross many neighborhoods'],
    ['ZIP code', 'T3 has no ZIP; ZIPs are postal routes, not neighborhoods'],
    ['Borough', 'Only 5 units → too coarse (kept for totals and the website filter)'],
    ['**NTA 2020 neighborhood × month (chosen)**', 'Official statistical units (DCP), stable boundaries, known area for per-km² rates; H6 has the NTA, T3 gets it by spatial join. Month smooths daily noise, shows seasons and allows lags'],
], [55 * mm, 115 * mm]))
story.append(P('Why only residential neighborhoods?', 'h3'))
story.append(P('65 of 262 NTAs are parks, cemeteries, airports and similar (ntatype ≠ 0). Almost nobody lives there '
               '(235 H6 problems) but they get 42,132 permits (e.g. airport roads). Keeping them would add rows with '
               'street work and no possible complaints, which biases every correlation toward zero. They stay in the '
               'borough totals.'))
story.append(P('Typical question: "Why left join on a grid and not an inner join?"', 'h3'))
story.append(P('An inner join keeps only neighborhood-months that have both a complaint and a permit. Months with '
               'zero activity disappear, which is survivorship bias. The grid keeps all 9,456 combinations, and a '
               'missing count becomes a true 0.'))
story.append(PageBreak())

# ---------------------------------------------------------------- 6 RQs
story.append(P('6. The 12 research questions', 'h1'))
story.append(P('Each member presents their two. For each: say the question, *why it matters*, the method in one '
               'sentence, what the chart shows, the answer with one number, and the limit. Everyone should know RQ1, '
               'RQ4, RQ5 and RQ12 because together they carry the main story.'))
TIPS = {
    'rq1': 'If asked "why log axes?": densities span 10 to 17,000 problems/km²/yr; linear axes would squash 190 dots into a corner. If asked "why Spearman?": counts are skewed and the relationship is monotonic but not linear.',
    'rq2': 'If asked "why not a dual axis?": two axes can be scaled to make any two lines look related. The index (average month = 100) puts both on one honest scale.',
    'rq3': 'Key word: **paired**. Each street is compared with itself, which removes street length, building count and income. The Wilcoxon test is the paired, non-parametric test.',
    'rq4': 'Key word: **two-way demeaning**. Without it, "busy neighborhood" and "winter" would create fake correlations. Live demo caveat: on a small website filter (e.g. Bronx 2024) the timing bar can show ρ ≈ 0.2. With only ~37 neighborhoods × 12 months that is within noise and multiple-testing range, while the full 4-year city test is ≈ 0.',
    'rq5': 'Why compare with 12.3? If the two rankings were independent, 25% × 25% = 6.25% of 197 neighborhoods would be in both top quartiles. We see 18, about 1.5× chance.',
    'rq6': 'The ratio is an index, not a rate (complaints and permits are different things). Its value is the comparison across cells.',
    'rq7': 'Key idea: **statistical vs practical significance**. With n = 9,399, a 5-hour difference is "significant" (p = 0.001) but meaningless. Always report effect size.',
    'rq8': 'Within-borough z-scores answer "unusual for its borough", which is what borough-level offices act on. Read both bars, because Long Island City is high almost only on streets.',
    'rq9': '"Building operations" = permits for work next to buildings (sheds, scaffolds, construction). High-complaint areas are dense residential blocks, so more building-side work and proportionally less utility work.',
    'rq10': 'Change-on-change cancels everything constant about a neighborhood (size, age, income). That is a stronger test of a causal link than levels. It shows no relation.',
    'rq11': 'The black box is the cross-domain block. Within-domain blocks (e.g. heat share ↔ emergency share 0.88) show the metrics behave sensibly, which is a sanity check.',
    'rq12': 'Out-of-sample (train 2022–24, test 2025) avoids overfitting claims. If T3 carried signal beyond "dense place", model 3 would beat model 2. It does not (+0.0001 R²).',
}
for r in TEXT['research_questions']:
    rid = r['id']
    block = [Paragraph(md(f"{rid.upper()} · {r['member']}"), S['tag']),
             Paragraph(md(r['question']), S['h2']),
             P(f"**Why it matters.** {r['why']}"),
             P(f"**Method.** {r['method']}"),
             img(ROOT / 'visualizations' / f'{rid}.png', W * (0.82 if rid in ('rq5', 'rq11') else 1)),
             Spacer(1, 3),
             P(f"**Chart choice.** {r['chart']}"),
             callout(f"**Answer.** {r['answer']}", ACCENT),
             Spacer(1, 3),
             P(f"**Limits.** {r['limits']}"),
             callout(f"**If the evaluator asks…** {TIPS[rid]}")]
    story += block
    story.append(PageBreak())

story.append(P('All 12 answers on one page', 'h2'))
rows = [l.strip('|').split('|') for l in TEXT['summary_table'].splitlines() if not l.startswith('|---')]
story.append(table([[c.strip() for c in r] for r in rows], [10 * mm, 28 * mm, 132 * mm]))
story.append(PageBreak())

# ---------------------------------------------------------------- 7 website
story.append(P('7. The website: features and a 3-minute demo script', 'h1'))
story.append(img(SHOTS / 'web_top.png', W * 0.92))
story.append(P('Opening view: header, tabs, five dropdowns, search box, the Generate Report button, KPI cards and the '
               '"double burden" map.', 'small'))
story.append(P('How it works (be ready to explain the code)', 'h2'))
story += bullets([
    '`app.py` loads the processed tables once at start-up (`integrated_nta_month.parquet`, `borough_month.csv`, the NTA '
    'GeoJSON) and the 12 RQ charts saved by notebook 02 (`data/app/rq_figures/*.json`). **No data is simulated.**',
    'One central callback, `generate_report()`, is triggered by the **Generate Report** button, Enter in the search box, '
    'Reset, or the map-layer radio. It (1) parses the search text if present, (2) filters the table, (3) rebuilds the '
    'KPIs and all 7 figures.',
    'Search mode: `parse_search()` matches boroughs and aliases (BK, BX, "Staten"), a year, housing keywords (heat, '
    'leak, mice, mold…), street keywords (sewer, paving, scaffold → building, dig → street openings…), shared words '
    '(gas, water set both sides) and neighborhood names (Astoria → 4 NTAs). It then **writes the result back into the '
    'dropdowns** so the user sees what was applied, and shows a banner such as "Search … understood as: borough=BRONX, '
    'year=2024 …". A new search starts from the defaults.',
    'The H6/T3 category dropdowns choose *which metric* every chart uses (e.g. heat complaints vs gas permits). This is '
    'more meaningful than filtering rows, because the data is aggregated.',
    'Charts: choropleth map (double burden / housing density / street density layers), cross-domain log-log scatter with '
    'live ρ, timeline, timing test (lag correlations with 95% CI), top-12 ranking, borough × month ratio heatmap, box plot '
    'of days to close by street-work tier. All have hover, zoom and legend toggling.',
    'Tabs: Interactive report · Our story · 12 research questions · Team & data.',
])
story.append(img(SHOTS / 'web_search.png', W * 0.92))
story.append(P('After typing "Bronx 2024 heat gas" and pressing Generate Report: the dropdowns were set automatically '
               'and the banner explains the parse.', 'small'))
story.append(img(SHOTS / 'web_charts.png', W * 0.92))
story.append(P('Demo script (about 3 minutes)', 'h2'))
story += bullets([
    '1. Open the site. "This is NYC Homes × NYC Streets: 3.15M housing problems and 2.5M street permits, 197 '
    'neighborhoods, 48 months." Point at the KPIs: ρ = 0.65.',
    '2. Map, "double burden" layer: "dark red = top quartile for both: the West Bronx and Upper Manhattan." Switch to '
    'housing density, then to street density: "Midtown is orange, not blue."',
    '3. Type `Manhattan` → Generate Report → scatter: "inside Manhattan the link reverses (ρ ≈ −0.78)."',
    '4. Type `Bronx heat gas` → Generate Report: "this is our mechanism test. The city-wide 4-year result in RQ4 is ≈ 0." '
    '(See the RQ4 caveat about small subsets.)',
    '5. Reset → Timeline and heatmap: "opposite seasons: complaints peak in winter, permits in spring and summer."',
    '6. Tab "12 research questions" → scroll to RQ12: "street permits do not help predict complaints."',
    '7. Tab "Our story": question, data, discovery, limits, impact. Finish with the impact sentence.',
])
story.append(PageBreak())

# ---------------------------------------------------------------- 8 run/deploy
story.append(P('8. How to run, reproduce and deploy', 'h1'))
story.append(P('Local run (Windows)', 'h2'))
for line in ['python -m venv .venv', '.venv\\Scripts\\activate', 'pip install -r requirements-notebooks.txt',
             'python app.py                → http://127.0.0.1:8050']:
    story.append(Paragraph(f'<font name="DVM" size="8.6">{line}</font>', S['bullet'], bulletText='›'))
story.append(P('The processed outputs are in the repository, so the website runs right after cloning. To reproduce '
               'everything from the API:'))
for line in ['jupyter nbconvert --to notebook --execute notebooks/01_cleaning_integration.ipynb --inplace --ExecutePreprocessor.timeout=-1',
             'jupyter nbconvert --to notebook --execute notebooks/02_research_questions.ipynb --inplace']:
    story.append(Paragraph(f'<font name="DVM" size="7.6">{line}</font>', S['bullet'], bulletText='›'))
story += bullets([
    'Notebook 01 downloads about 5.7M rows (45–90 min, resumable). An optional free app token '
    '(`NYC_OPEN_DATA_APP_TOKEN`) speeds it up. `NYC_DATA_MODE=starter` runs an offline code check on the small starter '
    'CSVs (its counts are not real).',
    'Notebook 02 runs in about 1 minute and writes `visualizations/*.png` (needs `kaleido` for PNGs) and `data/app/`.',
])
story.append(P('Deploy on Render (free)', 'h2'))
story += bullets([
    'Push the repository to GitHub, including `data/processed` (except the two big *_clean.parquet files, which are '
    'git-ignored) and `data/app`.',
    'render.com → New → Blueprint → select the repo (`render.yaml` sets everything), or New → Web Service with build '
    '`pip install -r requirements.txt` and start `gunicorn app:server --bind 0.0.0.0:$PORT --workers 1 --threads 4 '
    '--timeout 120`.',
    'Test every control on the live URL. The free plan sleeps after inactivity, so **open the link 2 minutes before '
    'the evaluation** to wake it up.',
    'The map uses the free Carto basemap. If a network blocks it, set the environment variable `MAP_STYLE=white-bg`.',
])
story.append(P('Repository layout', 'h2'))
story.append(table([
    ['Path', 'Content'],
    ['app.py, assets/style.css', 'Dash website'],
    ['src/analysis.py', 'one function per research question (shared by notebook 02 and the website)'],
    ['notebooks/01_cleaning_integration.ipynb', 'download, EDA, cleaning, spatial join, integration, post-cleaning, features (executed on the full data)'],
    ['notebooks/02_research_questions.ipynb', '12 RQs with charts, answers, limits, prompts (executed)'],
    ['data/processed/', 'integrated tables, dictionary, cleaning log, NTA boundaries'],
    ['data/app/', '12 chart JSONs + story.json for the website'],
    ['visualizations/', 'rq1.png … rq12.png'],
    ['tools/', 'text of the RQs/answers and the generators for notebook 02 and this PDF'],
    ['docs/Team_Evaluation_Guide.pdf', 'this guide'],
], [62 * mm, 108 * mm]))
story.append(PageBreak())

# ---------------------------------------------------------------- 9 Q&A
story.append(P('9. Likely evaluation questions with model answers', 'h1'))
QA = [
    ('Data & cleaning', [
        ('Why did you impute some values and drop others?', 'We impute only when another record gives the true value with near certainty: a building never moves, so its ZIP, coordinates and neighborhood can be copied from its other complaints (2,505 ZIPs, 264 coordinates). We drop only rows that cannot be placed in a neighborhood-month at all (399 H6 rows) or that contradict themselves (6,294 borough ≠ NTA borough). Other missing values (e.g. permit sizes) stay NaN because guessing them would invent measurements.'),
        ('How did you detect outliers?', 'Two layers. First, domain rules for impossible values: closed before received, a linear-feet value of 9,999 (a placeholder), more than 1,000 cuts, more than 5M sq ft. These become NaN. Second, the IQR rule (Q1 − 1.5·IQR, Q3 + 1.5·IQR) for extreme but possible values, applied on log(1+x) because durations and sizes are right-skewed. Those values are capped, not deleted, and flagged with an *_outlier column so nothing is hidden.'),
        ('Why cap instead of removing outliers?', 'The row is still a real complaint or permit and must be counted. Only its extreme measurement is limited, so one 1,400-day case cannot dominate a median or mean.'),
        ('What duplicates did you find?', 'No exact duplicates and no repeated IDs in either dataset (checked). H6 has an HPD "duplicate report" flag (15.9%): several tenants reporting the same problem. We keep those rows and flag them, because repeated reporting is itself a signal of severity. A unique-problems count is also provided. T3 renewals are not duplicates: they are new legal permits for continued work.'),
        ('What inconsistent data did you fix?', 'Old vs new HPD labels (HEATING = HEAT/HOT WATER), spelling variants (DOOR/DOORS, 650 equipment variants such as PORT-O-SAN), the typo COMMERICAL, placeholders like N/A and UNKNWN, leading spaces in street names, ZIP/borough mismatches (flagged), and invalid ZIPs, BBLs and community boards.'),
        ('Why remove voided permits?', 'VOIDED AFTER ISSUE means the permit was cancelled, so no work was allowed. Counting it would invent street work that never happened (2,038 permits).'),
        ('How did you handle the T3 geometry?', 'WKT text in NY State Plane feet → shapely geometry → a point that lies on the line (point_on_surface) → spatial join "within" the NTA polygons using an R-tree index, plus nearest NTA within 300 ft for points exactly on boundary streets. Missing geometry is filled from permits on the same street segment, only when ≥ 90% of those agree.'),
    ]),
    ('Integration', [
        ('Why NTA × month and not ZIP × year?', 'T3 has no ZIP, and ZIPs are postal routes. NTAs are statistical neighborhoods with known areas, so densities are possible. Months show seasons and allow 1–3 month lags, while years would leave only 4 points per neighborhood.'),
        ('What new problems did the join create, and how did you fix them?', 'Missing values: a neighborhood-month without permits gets NaN, which is a true 0 for counts, but medians stay NaN. Redundant columns: nta_type and is_residential became constant and were dropped. Type mismatches: counts became float after NaN and were converted back to int, and the key year_month was unified to datetime64[ns] before joining (a classic silent-join bug).'),
        ('How do you know the join did not lose or double-count rows?', 'Conservation asserts: the sum of h6_problems in the integrated table plus the excluded non-residential and unmapped rows equals the cleaned H6 row count. The same holds for T3. One row per key is asserted, and the grid size is asserted to be 197 × 48.'),
        ('What does the integration add that one dataset cannot?', 'Every RQ needs both sides: co-location (RQ1, RQ5), timing (RQ4), same-street pairing (RQ3), composition (RQ9), growth (RQ10) and prediction value (RQ12). It also produces a useful negative result: DOT data does not help forecast HPD complaints.'),
    ]),
    ('Analysis & honesty', [
        ('Your ρ = 0.65. Does street work cause complaints?', 'No, and we tested it. If it did, we would expect same-street effects, lags, growth-on-growth and predictive value. All four are ≈ 0. The correlation reflects shared characteristics: dense, older residential neighborhoods have more of both.'),
        ('Why per km² and not per person?', 'We did not integrate a population table (an honest limitation). Per km² still removes the biggest size effect. Per-resident or per-unit rates would be the next step, e.g. with census data.'),
        ('Why is Manhattan negative?', 'Its permit hot-spots are commercial and office districts (Midtown ~7,500 permits/km²/yr, ~500 problems) and its complaint hot-spots are residential uptown (Harlem ~10,000 problems/km²/yr, ~1,500 permits). Land use separates the two, which supports the shared-cause explanation.'),
        ('RQ7 is significant (p = 0.001). Why do you say "no"?', 'With 9,399 observations, tiny differences become significant. The effect is 4.63 vs 4.84 median days (about 5 hours) and ρ = 0.03. That has no practical importance.'),
        ('Did you check for multiple comparisons?', 'We report effect sizes and confidence intervals, not only p-values. In RQ4, 1 of 16 tests has p < 0.05, which is what chance alone would give (16 × 0.05 ≈ 0.8).'),
        ('Why Spearman rather than Pearson?', 'Counts and densities are highly skewed with a few giant values. Spearman uses ranks, measures monotonic association and is robust to outliers.'),
        ('Why is your prediction R² so high (0.92)?', 'A neighborhood\'s complaints are very stable from month to month and very seasonal. The point of RQ12 is the *difference* when street data is added (+0.0001), measured on a held-out year.'),
        ('Are your research questions "simple counts"?', 'No. They use densities, within-borough comparisons, paired same-street tests, lagged two-way-demeaned correlations, change-on-change, a correlation matrix and an out-of-sample model. The spec asks for "unexpected connections, spatial trends, or predictive patterns", and we have all three.'),
    ]),
    ('Website', [
        ('Show me the Generate Report button working.', 'Change Borough to Bronx and the H6 type to Heat/hot water, then press Generate Report. The KPIs, map, scatter, timeline, timing test, ranking, heatmap and box plot all update. Explain that it is one Dash callback with the button as the Input and the filters as State.'),
        ('How does the search work? Try "Brooklyn 2022 new buildings".', 'It sets Borough = Brooklyn, Year = 2022 and T3 kind = Building operations, and shows a banner saying what it understood. The parser uses keyword dictionaries with longest-match first ("hot water" beats "water") and neighborhood-name matching.'),
        ('Which chart shows the relationship between the two domains?', 'The scatter (H6 density vs T3 density with live ρ), the double-burden map, the timing test and the heatmap ratio.'),
        ('Is the website data real?', 'Yes. It loads the integrated table produced by notebook 01 from the full API download, and the 12 charts saved by notebook 02. (An earlier draft in the repo used generated demo data; it was replaced.)'),
    ]),
    ('Process', [
        ('Did you use AI?', 'Yes, Claude. The prompts are listed in notebook 01 §16 and notebook 02. Every output was run and checked by the team, and every number in the story comes from executed notebook cells.'),
        ('What would you do next?', 'Add population (ACS) to get per-resident rates; use daily data around individual gas-main permits within a radius of buildings (a sharper mechanism test); add a third dataset such as building age (PLUTO) to test the shared-cause explanation directly.'),
        ('What was the hardest part?', 'Placing 2.5M permits in neighborhoods: 13% had no geometry, and points on boundary streets fall between polygons. The segment-based filling and the 300 ft nearest rule solved it, with 97.4% placed.'),
    ]),
]
for group, items in QA:
    story.append(P(group, 'h2'))
    for q, a in items:
        story.append(KeepTogether([Paragraph(md('Q: ' + q), S['q']), Paragraph(md(a), S['a'])]))
story.append(PageBreak())

# ---------------------------------------------------------------- 10 stats
story.append(P('10. Statistics cheat-sheet', 'h1'))
story.append(table([
    ['Concept', 'Plain explanation', 'Used in'],
    ['Spearman ρ', 'Correlation of ranks, from −1 to +1. Measures "when one goes up, does the other go up?" without assuming a straight line. Robust to outliers.', 'RQ1, 2, 4, 7, 10, 11'],
    ['Density per km² per year', 'count ÷ area ÷ years. Removes the "bigger place, more of everything" effect.', 'RQ1, 5, 8, 9, 11'],
    ['Within-borough z-score', '(value − borough mean) ÷ borough std of log density: "how unusual for its borough".', 'RQ7, RQ8'],
    ['Two-way demeaning', 'x − neighborhood mean − month mean + overall mean. Leaves only "unusual for this place in this month", so place size and season cannot fake a link.', 'RQ4, website timing test'],
    ['Lag k', 'compare street work in month t with complaints in month t + k.', 'RQ4, RQ12'],
    ['95% CI (Fisher z)', 'range that would contain the true correlation 95% of the time; if it includes 0, there is no clear effect.', 'RQ4'],
    ['IQR rule', 'outlier if below Q1 − 1.5·IQR or above Q3 + 1.5·IQR (IQR = Q3 − Q1), here on log(1+x) for skewed data.', 'NB01 cleaning'],
    ['Wilcoxon signed-rank', 'paired, non-parametric test: is the "with" value systematically different from the "without" value for the same street?', 'RQ3'],
    ['Kruskal–Wallis', 'non-parametric test whether several groups (quartiles) have the same distribution.', 'RQ7'],
    ['Statistical vs practical significance', 'p-value = "is it unlikely by chance?"; effect size = "is it big enough to matter?". Large n makes tiny effects significant.', 'RQ7'],
    ['Out-of-sample R²', 'share of variation explained on data the model never saw (2025). 1 = perfect, 0 = no better than the average.', 'RQ12'],
    ['Ecological analysis', 'conclusions about places, not individuals (no "ecological fallacy").', 'RQ1, 11'],
], [33 * mm, 105 * mm, 32 * mm]))

# ---------------------------------------------------------------- 11 limits
story.append(P('11. Limitations to state honestly', 'h1'))
story += bullets([
    '**Correlation ≠ causation.** The co-location has an unmeasured shared driver (building age, density, income).',
    '**Permits ≠ work.** A permit is permission for a window of time. It does not record the days of actual work or a '
    'service shut-off.',
    '**Aggregation.** Neighborhood × month can hide effects that are very local (one block) or very short (a day).',
    '**Reporting bias.** H6 counts problems tenants report. Under-reporting differs between communities.',
    '**No population denominator.** Rates are per km², not per resident or housing unit.',
    '**Geometry imputation.** About 12% of permits were placed from other permits on the same segment or street, and '
    '1.0% (25,505) could not be placed.',
    '**Time window.** 4 years. Slower effects (new construction → new residents) would need longer.',
])
story.append(PageBreak())

# ---------------------------------------------------------------- 12 todo
story.append(P('12. Before submission: open tasks and per-member checklist', 'h1'))
story.append(table([
    ['#', 'Task', 'Owner'],
    ['1', 'Replace the contents of the team GitHub repo (Abdel-mohymen/project) with the finished `nyc-h6-t3-project` folder. The old `app.py` there uses generated data and must not be submitted.', 'Repo owner (Abdel-mohymen)'],
    ['2', 'Deploy on Render, test every control, and add the live URL to README line 8.', 'Mohamed Ahmed / repo owner'],
    ['3', 'Check the contribution table (README §7, NB01 header, website Team tab in `tools/rq_meta.py`). It is graded; adjust to what each person really did.', 'Everyone'],
    ['4', 'Each member re-runs or at least opens notebook 02 and reads their two RQs and the Q&A section.', 'Everyone'],
    ['5', 'Send the email to ICS503Data@gmail.com before 9 Nov 2026: all 6 IDs, repo link, deployment link, the 3 dataset links.', 'Team leader'],
    ['6', 'On evaluation day, open the Render link 2 minutes early (the free plan sleeps).', 'Presenter'],
], [8 * mm, 122 * mm, 40 * mm]))
story.append(P('Per-member preparation', 'h2'))
for m in TEXT['team']:
    story.append(Paragraph(md(f"**{m['name']}** ({m['id']}): {m['rqs']}. Data role: {m['role']}"), S['bullet'],
                           bulletText='☐'))
story.append(Spacer(1, 8))
story.append(P('Generated from the executed notebooks (full 2022–2025 data). Every number in this guide comes from '
               'notebook outputs.', 'small'))


def on_page(canvas, doc):
    if doc.page == 1:
        return
    canvas.saveState()
    canvas.setFont('DV', 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 10 * mm, 'NYC Homes × NYC Streets · Team Evaluation Guide')
    canvas.drawRightString(190 * mm, 10 * mm, f'{doc.page}')
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm,
                        bottomMargin=18 * mm, title='NYC Homes × NYC Streets: Team Evaluation Guide',
                        author='GIU DEV Winter 2026 team')
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print('written', OUT)
