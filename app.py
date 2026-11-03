"""
NYC Homes x NYC Streets: interactive explorer (Dash)
=====================================================
Housing Maintenance Code Complaints (H6, HPD, ygpa-z7cr)  x  Street Construction Permits (T3, DOT, tqtj-sjs8)
Integrated at neighborhood (NTA 2020) x month level by notebooks/01_cleaning_integration.ipynb.

Run locally:   python app.py            -> http://127.0.0.1:8050
Deploy:        gunicorn app:server      (see README.md, Render instructions)

Data used by the website (all REAL, produced by the notebooks; nothing is simulated):
    data/processed/integrated_nta_month.parquet   main table (one row per residential neighborhood per month)
    data/processed/borough_month.csv              complete borough totals (incl. permits without a neighborhood)
    data/processed/nta_boundaries.geojson         2020 NTA shapes for the map
    data/app/rq_figures/*.json                    the 12 research-question charts (written by notebook 02)
    data/app/story.json                           the story text / key numbers (written by notebook 02)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import dash
from dash import Input, Output, State, dcc, html, ctx

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from analysis import (BOROUGH_COLORS, COLOR_H6, COLOR_MUTED, COLOR_T3, H6_GROUPS, MONTH_NAMES,  # noqa: E402
                      T3_KINDS, TEMPLATE, spearman, two_way_demean)

PROCESSED = ROOT / 'data' / 'processed'
MAP_STYLE = os.environ.get('MAP_STYLE', 'carto-positron')   # 'white-bg' works fully offline
APP_DATA = ROOT / 'data' / 'app'

# ==============================================================================================
# 1. Load data once at start-up
# ==============================================================================================
INTEGRATED = pd.read_parquet(PROCESSED / 'integrated_nta_month.parquet')
for c in ('nta_code', 'nta_name', 'borough', 'cdta_code', 'season'):
    if c in INTEGRATED.columns:
        INTEGRATED[c] = INTEGRATED[c].astype(str)
INTEGRATED['year'] = INTEGRATED['year'].astype(int)
BOROUGH_MONTH = pd.read_csv(PROCESSED / 'borough_month.csv', parse_dates=['year_month'])
GEOJSON = json.loads((PROCESSED / 'nta_boundaries.geojson').read_text(encoding='utf-8'))
STORY = json.loads((APP_DATA / 'story.json').read_text(encoding='utf-8')) if (APP_DATA / 'story.json').exists() else {}
RQ_FIGURES = {}
for f in sorted((APP_DATA / 'rq_figures').glob('rq*.json')) if (APP_DATA / 'rq_figures').exists() else []:
    RQ_FIGURES[f.stem] = pio.from_json(f.read_text(encoding='utf-8'))



def _feature_bounds(feature):
    # bounding box (lon_min, lat_min, lon_max, lat_max) of one GeoJSON polygon / multipolygon
    coords = np.array([pt for poly in (feature['geometry']['coordinates'] if feature['geometry']['type'] == 'MultiPolygon'
                                       else [feature['geometry']['coordinates']]) for ring in poly for pt in ring])
    return coords[:, 0].min(), coords[:, 1].min(), coords[:, 0].max(), coords[:, 1].max()


NTA_BOUNDS = pd.DataFrame({f['properties']['nta_code']: _feature_bounds(f) for f in GEOJSON['features']},
                          index=['lon0', 'lat0', 'lon1', 'lat1']).T


def map_view(nta_codes):
    # centre + zoom that fit the selected neighborhoods (simple Web-Mercator approximation)
    b = NTA_BOUNDS.loc[NTA_BOUNDS.index.intersection(list(nta_codes))]
    if b.empty:
        return {'lat': 40.705, 'lon': -73.94}, 9.3
    lon0, lat0, lon1, lat1 = b['lon0'].min(), b['lat0'].min(), b['lon1'].max(), b['lat1'].max()
    span = max(lon1 - lon0, (lat1 - lat0) * 1.6, 0.01)
    zoom = float(np.clip(np.log2(360 / span) - 0.5, 8.5, 14))
    return {'lat': (lat0 + lat1) / 2, 'lon': (lon0 + lon1) / 2}, zoom


BOROUGHS = sorted(INTEGRATED['borough'].unique())
YEARS = sorted(INTEGRATED['year'].unique())
NEIGHBORHOODS = (INTEGRATED[['nta_code', 'nta_name', 'borough']].drop_duplicates()
                 .sort_values(['borough', 'nta_name']))
H6_OPTIONS = {k: v for k, v in H6_GROUPS.items() if k in INTEGRATED.columns}
T3_OPTIONS = {k: v for k, v in T3_KINDS.items() if k in INTEGRATED.columns}
N_MONTHS_TOTAL = INTEGRATED['year_month'].nunique()

# ==============================================================================================
# 2. Search mode: turn free text into filter values
# ==============================================================================================
BOROUGH_ALIASES = {'BROOKLYN': 'BROOKLYN', 'BK': 'BROOKLYN', 'KINGS': 'BROOKLYN', 'BRONX': 'BRONX', 'BX': 'BRONX',
                   'MANHATTAN': 'MANHATTAN', 'MN': 'MANHATTAN', 'QUEENS': 'QUEENS', 'QN': 'QUEENS',
                   'STATEN ISLAND': 'STATEN ISLAND', 'STATEN': 'STATEN ISLAND', 'SI': 'STATEN ISLAND',
                   'RICHMOND': 'STATEN ISLAND'}
# keyword -> H6 problem group (housing side)
H6_KEYWORDS = {'HEAT': 'h6_grp_heat_hot_water', 'HOT WATER': 'h6_grp_heat_hot_water', 'BOILER': 'h6_grp_heat_hot_water',
               'COLD': 'h6_grp_heat_hot_water', 'PLUMBING': 'h6_grp_water_plumbing', 'LEAK': 'h6_grp_water_plumbing',
               'PESTS': 'h6_grp_pests', 'PEST': 'h6_grp_pests', 'MICE': 'h6_grp_pests', 'ROACH': 'h6_grp_pests',
               'RATS': 'h6_grp_pests', 'MOLD': 'h6_grp_mold', 'MOULD': 'h6_grp_mold', 'ELECTRIC': 'h6_grp_electric',
               'STRUCTURE': 'h6_grp_structure', 'PLASTER': 'h6_grp_structure', 'CEILING': 'h6_grp_structure',
               'COMPLAINT': 'h6_problems', 'HOUSING': 'h6_problems'}
# keyword -> T3 work kind (street side)
T3_KEYWORDS = {'SEWER': 't3_kind_water_sewer', 'WATER MAIN': 't3_kind_water_sewer', 'PAVING': 't3_kind_paving',
               'RESURFACING': 't3_kind_paving', 'STEAM': 't3_kind_steam', 'TELECOM': 't3_kind_electric_telecom',
               'CABLE': 't3_kind_electric_telecom', 'FIBER': 't3_kind_electric_telecom',
               'SIDEWALK': 't3_kind_sidewalk_curb', 'CURB': 't3_kind_sidewalk_curb', 'TREE': 't3_kind_tree',
               'RECONSTRUCTION': 't3_kind_street_reconstruction', 'NEW BUILDING': 't3_kind_building_operation',
               'BUILDING': 't3_kind_building_operation', 'CONSTRUCTION': 't3_kind_building_operation',
               'CRANE': 't3_kind_occupancy_equipment', 'EQUIPMENT': 't3_kind_occupancy_equipment',
               'DUMPSTER': 't3_kind_refuse_container', 'CONTAINER': 't3_kind_refuse_container',
               'EXCAVATION': 't3_street_openings', 'OPENING': 't3_street_openings', 'DIG': 't3_street_openings',
               'EMERGENCY': 't3_emergency_permits', 'PERMIT': 't3_permits', 'STREET': 't3_permits'}
# words that belong to BOTH domains: 'gas' and 'water' set the matching category on each side
SHARED_KEYWORDS = {'GAS': ('h6_grp_gas', 't3_kind_gas'), 'WATER': ('h6_grp_water_plumbing', 't3_kind_water_sewer'),
                   'ELECTRICAL': ('h6_grp_electric', 't3_kind_electric_telecom')}


def parse_search(text: str) -> dict:
    """'Brooklyn 2022 new buildings heat' -> {'borough': 'BROOKLYN', 'year': 2022, 't3': ..., 'h6': ...}.

    Matching is done longest-keyword-first so that 'HOT WATER' wins over 'WATER' and
    'STATEN ISLAND' over 'STATEN'. Neighborhood names are matched last (e.g. 'Astoria', 'Fordham').
    """
    q = ' ' + re.sub(r'[^A-Z0-9 ]', ' ', (text or '').upper()) + ' '
    q = re.sub(r'\s+', ' ', q)
    found = {}

    def take(keyword_map, key):
        nonlocal q
        for kw in sorted(keyword_map, key=len, reverse=True):
            if re.search(rf'\b{kw}S?\b', q):
                q = re.sub(rf'\b{kw}S?\b', ' ', q)
                return keyword_map[kw]
        return None

    found['borough'] = take(BOROUGH_ALIASES, 'borough')
    m = re.search(r'\b(20\d\d)\b', q)
    if m and int(m.group(1)) in YEARS:
        found['year'] = int(m.group(1))
        q = q.replace(m.group(1), ' ')
    h6 = take(H6_KEYWORDS, 'h6')
    t3 = take(T3_KEYWORDS, 't3')
    shared = take({k: k for k in SHARED_KEYWORDS}, 'shared')
    if shared:
        h6 = h6 or SHARED_KEYWORDS[shared][0]
        t3 = t3 or SHARED_KEYWORDS[shared][1]
    found['h6'], found['t3'] = h6, t3
    # neighborhood: any remaining word of 4+ letters that appears in an NTA name
    words = [w for w in q.split() if len(w) >= 4]
    if words:
        names = NEIGHBORHOODS.assign(key=NEIGHBORHOODS['nta_name'].str.upper())
        hit = names[names['key'].apply(lambda n: all(w in n for w in words))]
        if hit.empty:
            hit = names[names['key'].apply(lambda n: any(w in n for w in words))]
        if not hit.empty:
            found['nta'] = hit['nta_code'].tolist()
            if found['borough'] is None and hit['borough'].nunique() == 1:
                found['borough'] = hit['borough'].iloc[0]
    return {k: v for k, v in found.items() if v is not None}


# ==============================================================================================
# 3. Chart builders (each takes the FILTERED data and the selected metrics)
# ==============================================================================================
def _layout(fig, title, height=430):
    fig.update_layout(template=TEMPLATE, height=height, title=dict(text=title, x=0.01, font=dict(size=14)),
                      margin=dict(l=50, r=20, t=60, b=45),
                      legend=dict(orientation='h', y=-0.22, x=0, xanchor='left', yanchor='top'))
    return fig


def empty_figure(message='No data for this selection'):
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=14, color='#777'))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _layout(fig, '')


def nta_level(df, h6_col, t3_col):
    n_years = max(df['year_month'].nunique(), 1) / 12
    g = df.groupby(['nta_code', 'nta_name', 'borough'], observed=True).agg(
        area=('area_km2', 'first'), h6=(h6_col, 'sum'), t3=(t3_col, 'sum'),
        h6_all=('h6_problems', 'sum'), t3_all=('t3_permits', 'sum')).reset_index()
    g['h6_density'] = g['h6'] / g['area'] / n_years
    g['t3_density'] = g['t3'] / g['area'] / n_years
    return g


def fig_map(df, h6_col, t3_col, layer):
    g = nta_level(df, h6_col, t3_col)
    if g.empty:
        return empty_figure()
    if layer == 'double':
        hq, tq = g['h6_density'].quantile(0.75), g['t3_density'].quantile(0.75)
        g['class'] = np.select([(g['h6_density'] >= hq) & (g['t3_density'] >= tq), g['h6_density'] >= hq,
                                g['t3_density'] >= tq],
                               ['Both high', 'Housing high only', 'Street work high only'], 'Neither')
        fig = px.choropleth_map(g, geojson=GEOJSON, locations='nta_code', featureidkey='properties.nta_code',
                                color='class', hover_name='nta_name',
                                category_orders={'class': ['Both high', 'Housing high only', 'Street work high only',
                                                           'Neither']},
                                color_discrete_map={'Both high': '#8b1e3f', 'Housing high only': COLOR_H6,
                                                    'Street work high only': COLOR_T3, 'Neither': '#dcdad2'},
                                hover_data={'nta_code': False, 'h6_density': ':.0f', 't3_density': ':.0f'},
                                labels={'class': '', 'h6_density': f'{H6_OPTIONS[h6_col]} /km²/yr',
                                        't3_density': f'{T3_OPTIONS[t3_col]} /km²/yr'})
        title = 'Map · Double burden: top-quartile neighborhoods for both selected metrics'
    else:
        col, name, scale = (('h6_density', H6_OPTIONS[h6_col], 'Blues') if layer == 'h6'
                            else ('t3_density', T3_OPTIONS[t3_col], 'Oranges'))
        g['log_value'] = np.log10(g[col].clip(lower=0.1))
        fig = px.choropleth_map(g, geojson=GEOJSON, locations='nta_code', featureidkey='properties.nta_code',
                                color='log_value', color_continuous_scale=scale, hover_name='nta_name',
                                hover_data={'nta_code': False, 'log_value': False, col: ':.1f', 'borough': True},
                                labels={col: f'{name} per km² per year'})
        fig.update_coloraxes(colorbar=dict(title='per km²/yr', tickvals=[-1, 0, 1, 2, 3, 4],
                                           ticktext=['0.1', '1', '10', '100', '1k', '10k']))
        title = f'Map · {name} per km² per year (log colour scale)'
    center, zoom = map_view(g['nta_code'])
    fig.update_layout(map_style=MAP_STYLE, map_zoom=zoom, map_center=center)
    fig.update_traces(marker_line_width=0.3, marker_line_color='white', marker_opacity=0.85)
    return _layout(fig, title, height=520)


def fig_scatter(df, h6_col, t3_col):
    g = nta_level(df, h6_col, t3_col)
    g = g[(g['h6'] > 0) & (g['t3'] > 0)]
    if len(g) < 3:
        return empty_figure('Not enough neighborhoods with both kinds of activity'), np.nan
    rho, p, n = spearman(g['t3_density'], g['h6_density'])
    fig = px.scatter(g, x='t3_density', y='h6_density', color='borough', log_x=True, log_y=True,
                     hover_name='nta_name', color_discrete_map=BOROUGH_COLORS,
                     labels={'t3_density': f'{T3_OPTIONS[t3_col]} per km² per year (log)',
                             'h6_density': f'{H6_OPTIONS[h6_col]} per km² per year (log)', 'borough': ''})
    fig.update_traces(marker=dict(size=9, opacity=0.8, line=dict(width=0.5, color='white')))
    return _layout(fig, f'Cross-domain · one dot = one neighborhood (Spearman ρ = {rho:.2f}, n = {n})'), rho


def fig_timeline(df, h6_col, t3_col):
    city = df.groupby('year_month')[[h6_col, t3_col]].sum()
    if city.empty or city.sum().sum() == 0:
        return empty_figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=city.index, y=city[h6_col], name=H6_OPTIONS[h6_col] + ' (H6)',
                             line=dict(color=COLOR_H6, width=2.5)))
    fig.add_trace(go.Scatter(x=city.index, y=city[t3_col], name=T3_OPTIONS[t3_col] + ' (T3)',
                             line=dict(color=COLOR_T3, width=2.5), yaxis='y2'))
    fig.update_layout(yaxis=dict(title=dict(text='Housing problems', font=dict(color=COLOR_H6))),
                      yaxis2=dict(title=dict(text='Street permits', font=dict(color=COLOR_T3)), overlaying='y',
                                  side='right', showgrid=False),
                      hovermode='x unified')
    fig = _layout(fig, 'Timeline · monthly totals (left axis = housing, right axis = streets)')
    fig.update_layout(legend=dict(orientation='h', y=-0.18, x=0, xanchor='left', yanchor='top'))
    return fig


def fig_heatmap(df, h6_col, t3_col):
    d = df.assign(m=df['year_month'].dt.month)
    g = d.groupby(['borough', 'm'])[[h6_col, t3_col]].sum()
    if g.empty:
        return empty_figure()
    ratio = (g[h6_col] / g[t3_col].replace(0, np.nan)).unstack('m').reindex(columns=range(1, 13))
    ratio.columns = MONTH_NAMES
    fig = px.imshow(ratio, text_auto='.2f', aspect='auto', color_continuous_scale='Blues',
                    labels=dict(x='Month of year', y='', color='ratio'))
    return _layout(fig, f'Heatmap · {H6_OPTIONS[h6_col]} per {T3_OPTIONS[t3_col].lower()} permit, by month',
                   height=380)


def fig_top(df, h6_col, t3_col, top=12):
    g = nta_level(df, h6_col, t3_col)
    g = g[(g['h6'] > 0) | (g['t3'] > 0)]
    if g.empty:
        return empty_figure()
    for c in ('h6_density', 't3_density'):
        v = np.log1p(g[c])
        g['z_' + c] = (v - v.mean()) / (v.std(ddof=0) or 1)
    g['index'] = (g['z_h6_density'] + g['z_t3_density']) / 2
    g = g.sort_values('index', ascending=False).head(top).iloc[::-1]
    g['label'] = g['nta_name'] + ' (' + g['borough'].str.title().str[:3] + '.)'
    fig = go.Figure()
    fig.add_trace(go.Bar(y=g['label'], x=g['z_h6_density'], orientation='h', name='Housing (z)', marker_color=COLOR_H6))
    fig.add_trace(go.Bar(y=g['label'], x=g['z_t3_density'], orientation='h', name='Streets (z)', marker_color=COLOR_T3))
    fig.update_layout(barmode='group', xaxis_title='z-score of log density within current selection')
    return _layout(fig, f'Ranking · top {top} neighborhoods under combined pressure', height=470)


def fig_lag(df, h6_col, t3_col):
    d = df.sort_values(['nta_code', 'year_month']).copy()
    if d['nta_code'].nunique() < 3 or d['year_month'].nunique() < 6:
        return empty_figure('Pick a wider selection (≥3 neighborhoods, ≥6 months) for the timing test')
    rows = []
    for lag in range(0, 4):
        d['_x'] = d.groupby('nta_code')[t3_col].shift(lag)
        s = d.dropna(subset=['_x'])
        rho, p, n = spearman(two_way_demean(s, '_x'), two_way_demean(s, h6_col))
        se = 1 / np.sqrt(max(n - 3, 1))
        rows.append({'lag': f'{lag} month' + ('s' if lag != 1 else '') + ' later', 'rho': rho,
                     'lo': rho - np.tanh(np.arctanh(rho) - 1.96 * se) if np.isfinite(rho) else 0,
                     'hi': np.tanh(np.arctanh(rho) + 1.96 * se) - rho if np.isfinite(rho) else 0})
    t = pd.DataFrame(rows)
    fig = px.bar(t, x='lag', y='rho', error_y='hi', error_y_minus='lo', color_discrete_sequence=[COLOR_T3],
                 labels={'lag': f'{H6_OPTIONS[h6_col]} measured …', 'rho': 'within-neighborhood ρ'})
    fig.add_hline(y=0, line_color='#555', line_width=1)
    return _layout(fig, f'Timing test · does {T3_OPTIONS[t3_col].lower()} come before more '
                        f'{H6_OPTIONS[h6_col].lower()}? (95% CI)')


def fig_box(df):
    d = df[(df['h6_problems'] >= 5) & df['h6_median_days_to_close'].notna()].copy()
    if len(d) < 20:
        return empty_figure('Not enough neighborhood-months with ≥5 problems')
    d['tier'] = pd.qcut(d['t3_permits_per_km2_z_borough'].rank(method='first'), 4,
                        labels=['Q1 lowest', 'Q2', 'Q3', 'Q4 highest'])
    fig = px.box(d, x='tier', y='h6_median_days_to_close', color='tier', points=False,
                 category_orders={'tier': ['Q1 lowest', 'Q2', 'Q3', 'Q4 highest']},
                 color_discrete_sequence=['#fbd3bf', '#f6a57a', '#eb6834', '#a8441a'],
                 labels={'tier': 'Street-work intensity (quartile within borough & month)',
                         'h6_median_days_to_close': 'Median days to close'})
    fig.update_layout(showlegend=False)
    return _layout(fig, 'Service · days to close housing problems by street-work intensity')


# ==============================================================================================
# 4. Layout
# ==============================================================================================
app = dash.Dash(__name__, title='NYC Homes × NYC Streets', suppress_callback_exceptions=True)
server = app.server  # used by gunicorn on Render

TEAM = STORY.get('team', [])


def card(children, cls='card'):
    return html.Div(children, className=cls)


def kpi(label, value, sub=''):
    return html.Div([html.Div(label, className='kpi-label'), html.Div(value, className='kpi-value'),
                     html.Div(sub, className='kpi-sub')], className='kpi')


controls = card([
    html.Div([
        html.Div([html.Label('Borough'), dcc.Dropdown(id='f-borough', options=[{'label': 'All boroughs', 'value': 'ALL'}]
                 + [{'label': b.title(), 'value': b} for b in BOROUGHS], value='ALL', clearable=False)]),
        html.Div([html.Label('Year'), dcc.Dropdown(id='f-year', options=[{'label': 'All years', 'value': 'ALL'}]
                 + [{'label': str(y), 'value': y} for y in YEARS], value='ALL', clearable=False)]),
        html.Div([html.Label('Housing problem type (H6)'),
                  dcc.Dropdown(id='f-h6', options=[{'label': v, 'value': k} for k, v in H6_OPTIONS.items()],
                               value='h6_problems', clearable=False)]),
        html.Div([html.Label('Street work kind (T3)'),
                  dcc.Dropdown(id='f-t3', options=[{'label': v, 'value': k} for k, v in T3_OPTIONS.items()],
                               value='t3_permits', clearable=False)]),
        html.Div([html.Label('Neighborhood(s) (optional)'),
                  dcc.Dropdown(id='f-nta', multi=True, placeholder='All neighborhoods',
                               options=[{'label': f"{r.nta_name} ({r.borough.title()})", 'value': r.nta_code}
                                        for r in NEIGHBORHOODS.itertuples()])]),
    ], className='filter-grid'),
    html.Div([
        dcc.Input(id='search', type='text', debounce=False, n_submit=0, className='search',
                  placeholder='Search mode, e.g. "Brooklyn 2022 new buildings", "Bronx heat gas", '
                              '"Astoria water sewer 2024"'),
        html.Button('Generate Report', id='btn-report', n_clicks=0, className='btn-primary'),
        html.Button('Reset', id='btn-reset', n_clicks=0, className='btn-secondary'),
    ], className='search-row'),
    html.Div(id='banner', className='banner'),
])

explorer_tab = html.Div([
    controls,
    html.Div(id='kpis', className='kpi-row'),
    card([dcc.RadioItems(id='map-layer', value='double', inline=True, className='radio',
                         options=[{'label': ' Double burden', 'value': 'double'},
                                  {'label': ' Housing density', 'value': 'h6'},
                                  {'label': ' Street-work density', 'value': 't3'}]),
          dcc.Graph(id='g-map', config={'scrollZoom': True}, style={'height': '520px'})]),
    html.Div([card(dcc.Loading(dcc.Graph(id='g-scatter'))), card(dcc.Loading(dcc.Graph(id='g-time')))],
             className='grid-2'),
    html.Div([card(dcc.Loading(dcc.Graph(id='g-lag'))), card(dcc.Loading(dcc.Graph(id='g-top')))],
             className='grid-2'),
    html.Div([card(dcc.Loading(dcc.Graph(id='g-heat'))), card(dcc.Loading(dcc.Graph(id='g-box')))],
             className='grid-2'),
])


def story_tab():
    s = STORY
    blocks = []
    for key, title in [('question', 'The question'), ('data', 'The data and how we connected it'),
                       ('discovery', 'What we found'), ('limits', 'What the data cannot tell us'),
                       ('impact', 'Who can use this, and how')]:
        items = s.get(key, [])
        items = [items] if isinstance(items, str) else items
        blocks.append(card([html.H3(title), html.Ul([html.Li(dcc.Markdown(i)) for i in items])
                            if len(items) > 1 else dcc.Markdown(items[0] if items else '')], 'card story'))
    return html.Div(blocks)


def rq_tab():
    if not RQ_FIGURES:
        return card(html.P('Run notebooks/02_research_questions.ipynb to generate the 12 research-question charts.'))
    rq_text = {r['id']: r for r in STORY.get('research_questions', [])}
    out = []
    for key in sorted(RQ_FIGURES, key=lambda k: int(k[2:])):
        meta = rq_text.get(key, {})
        out.append(card([
            html.Div(f"{key.upper()} · {meta.get('member', '')}", className='rq-tag'),
            html.H3(meta.get('question', '')),
            dcc.Graph(figure=RQ_FIGURES[key]),
            dcc.Markdown(meta.get('answer', ''), className='rq-answer')]))
    return html.Div(out)


def team_tab():
    rows = [html.Tr([html.Th(h) for h in ['Member', 'ID', 'Research questions', 'Contribution']])]
    for m in TEAM:
        rows.append(html.Tr([html.Td(m['name']), html.Td(m['id']), html.Td(m['rqs']), html.Td(m['role'])]))
    links = STORY.get('links', {})
    return html.Div([card([html.H3('Team contributions'), html.Table(rows, className='team')]),
                     card([html.H3('Datasets'), html.Ul([html.Li(html.A(k, href=v, target='_blank'))
                                                         for k, v in links.items()])])])


app.layout = html.Div([
    html.Header([
        html.Div('GIU · Data Engineering & Visualization · Winter 2026 · Milestone 1', className='eyebrow'),
        html.H1('NYC Homes × NYC Streets'),
        html.P(STORY.get('subtitle', 'Do neighborhoods with more street construction also report more housing '
                                     'maintenance problems? HPD complaints (H6) meet DOT street permits (T3), '
                                     'neighborhood by neighborhood, month by month, 2022–2025.')),
    ], className='hero'),
    html.Main([
        dcc.Tabs(id='tabs', value='explorer', className='tabs', children=[
            dcc.Tab(label='Interactive report', value='explorer', children=explorer_tab),
            dcc.Tab(label='Our story', value='story', children=story_tab()),
            dcc.Tab(label='12 research questions', value='rqs', children=rq_tab()),
            dcc.Tab(label='Team & data', value='team', children=team_tab()),
        ]),
    ], className='main'),
    html.Footer('Data: NYC Open Data (HPD ygpa-z7cr, DOT tqtj-sjs8, DCP NTA 2020). Correlation is not causation.',
                className='footer'),
])


# ==============================================================================================
# 5. Callbacks
# ==============================================================================================
def apply_filters(borough, year, ntas):
    df = INTEGRATED
    if borough and borough != 'ALL':
        df = df[df['borough'] == borough]
    if year and year != 'ALL':
        df = df[df['year'] == int(year)]
    if ntas:
        df = df[df['nta_code'].isin(ntas)]
    return df


@app.callback(
    Output('f-borough', 'value'), Output('f-year', 'value'), Output('f-h6', 'value'), Output('f-t3', 'value'),
    Output('f-nta', 'value'), Output('search', 'value'),
    Output('banner', 'children'), Output('kpis', 'children'),
    Output('g-map', 'figure'), Output('g-scatter', 'figure'), Output('g-time', 'figure'),
    Output('g-lag', 'figure'), Output('g-top', 'figure'), Output('g-heat', 'figure'), Output('g-box', 'figure'),
    Input('btn-report', 'n_clicks'), Input('search', 'n_submit'), Input('btn-reset', 'n_clicks'),
    Input('map-layer', 'value'),
    State('f-borough', 'value'), State('f-year', 'value'), State('f-h6', 'value'), State('f-t3', 'value'),
    State('f-nta', 'value'), State('search', 'value'),
)
def generate_report(_clicks, _submit, _reset, layer, borough, year, h6_col, t3_col, ntas, query):
    """The central 'Generate Report' callback.

    1. If the user typed a search, parse it and OVERRIDE the matching dropdowns (so the user sees what was applied).
    2. Filter the integrated table.
    3. Rebuild every chart and KPI from the filtered data.
    The map-layer radio also triggers it, so switching map layers is instant.
    """
    note = ''
    if ctx.triggered_id == 'btn-reset':
        borough, year, h6_col, t3_col, ntas, query = 'ALL', 'ALL', 'h6_problems', 't3_permits', None, ''
    elif query and query.strip() and ctx.triggered_id in ('btn-report', 'search'):
        # a new search starts from the defaults, so filters from an earlier search do not stick
        parsed = parse_search(query)
        borough = parsed.get('borough', 'ALL')
        year = parsed.get('year', 'ALL')
        h6_col = parsed.get('h6', 'h6_problems')
        t3_col = parsed.get('t3', 't3_permits')
        ntas = parsed.get('nta')
        note = f'Search “{query.strip()}” understood as: ' + (', '.join(
            f'{k}={v if not isinstance(v, list) else f"{len(v)} neighborhood(s)"}' for k, v in parsed.items())
            or 'nothing recognised, dropdowns unchanged') + '. '

    df = apply_filters(borough, year, ntas)
    if df.empty:
        figs = [empty_figure()] * 7
        return (borough, year, h6_col, t3_col, ntas, query, note + 'No rows match this selection.', [], *figs)

    scatter, rho = fig_scatter(df, h6_col, t3_col)
    figs = [fig_map(df, h6_col, t3_col, layer), scatter, fig_timeline(df, h6_col, t3_col),
            fig_lag(df, h6_col, t3_col), fig_top(df, h6_col, t3_col), fig_heatmap(df, h6_col, t3_col), fig_box(df)]

    months = df['year_month'].nunique()
    h6_total, t3_total = int(df[h6_col].sum()), int(df[t3_col].sum())
    days = df.loc[df['h6_problems'] >= 1, 'h6_median_days_to_close'].median()
    kpis = [kpi(H6_OPTIONS[h6_col], f'{h6_total:,}', 'housing problems (H6)'),
            kpi(T3_OPTIONS[t3_col], f'{t3_total:,}', 'street permits issued (T3)'),
            kpi('Neighborhoods', f"{df['nta_code'].nunique()}", f'{months} months'),
            kpi('Spatial link', f'ρ = {rho:.2f}' if np.isfinite(rho) else '–', 'Spearman, density vs density'),
            kpi('Median days to close', f'{days:.1f}' if pd.notna(days) else '–', 'housing problems')]
    scope = [borough.title() if borough != 'ALL' else 'All boroughs', str(year) if year != 'ALL' else '2022–2025',
             H6_OPTIONS[h6_col], T3_OPTIONS[t3_col]] + ([f'{len(ntas)} neighborhood(s)'] if ntas else [])
    banner = note + 'Report for: ' + ' · '.join(scope)
    return (borough, year, h6_col, t3_col, ntas, query, banner, kpis, *figs)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8050)), debug=False)
