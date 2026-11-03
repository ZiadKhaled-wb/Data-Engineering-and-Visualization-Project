"""
Research-question analysis for the NYC H6 (housing complaints) x T3 (street permits) project.

Every research question (RQ) has one function that returns
    (result_table: pd.DataFrame, figure: plotly Figure, stats: dict)
so the same code is used by the notebook (02_research_questions.ipynb) and can be
re-used by the website. All inputs are the outputs of 01_cleaning_integration.ipynb.

Key ideas used throughout (explained in the notebook):
* Densities are per km2 per year, because big / busy neighborhoods have more of everything.
* Spearman rank correlation (rho) is used instead of Pearson because counts are very skewed.
* "Within-borough" versions of a statistic remove the borough-level confounder
  (e.g. Manhattan has both very dense permits and very dense housing).
* Two-way demeaning (remove each neighborhood's average and each month's average) is used for
  timing questions, so a correlation is not just "busy places are busy" or "winter is winter".
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats as sps

# ----------------------------------------------------------------------------------------------
# Constants shared with the website
# ----------------------------------------------------------------------------------------------
COLOR_H6 = '#2a78d6'      # blue   = housing complaints (H6)
COLOR_T3 = '#eb6834'      # orange = street permits (T3)
COLOR_MUTED = '#a3a29c'
BOROUGH_COLORS = {'BRONX': '#2a78d6', 'BROOKLYN': '#eb6834', 'MANHATTAN': '#1baf7a',
                  'QUEENS': '#8c5bd6', 'STATEN ISLAND': '#d6a02a'}
TEMPLATE = 'plotly_white'
MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

H6_GROUPS = {'h6_problems': 'All housing problems', 'h6_grp_heat_hot_water': 'Heat / hot water',
             'h6_grp_water_plumbing': 'Water / plumbing', 'h6_grp_gas': 'Gas', 'h6_grp_pests': 'Pests',
             'h6_grp_mold': 'Mold', 'h6_grp_electric': 'Electric', 'h6_grp_structure': 'Structure',
             'h6_grp_other': 'Other'}
T3_KINDS = {'t3_permits': 'All street permits', 't3_street_openings': 'Street openings (dug up)',
            't3_kind_gas': 'Gas work', 't3_kind_water_sewer': 'Water / sewer work', 't3_kind_steam': 'Steam',
            't3_kind_electric_telecom': 'Electric / telecom', 't3_kind_paving': 'Paving',
            't3_kind_street_reconstruction': 'Street reconstruction',
            't3_kind_building_operation': 'Building operations', 't3_kind_sidewalk_curb': 'Sidewalk / curb',
            't3_kind_occupancy_equipment': 'Occupancy / equipment', 't3_kind_refuse_container': 'Refuse container',
            't3_kind_tree': 'Tree work', 't3_kind_other': 'Other street work',
            't3_emergency_permits': 'Emergency permits'}


def load_outputs(processed_dir: str | Path):
    """Load the tables written by notebook 01."""
    p = Path(processed_dir)
    integrated = pd.read_parquet(p / 'integrated_nta_month.parquet')
    street = pd.read_parquet(p / 'street_month.parquet')
    borough_month = pd.read_csv(p / 'borough_month.csv', parse_dates=['year_month'])
    geo = json.loads((p / 'nta_boundaries.geojson').read_text(encoding='utf-8'))
    for df in (integrated, street, borough_month):
        for c in ('borough', 'nta_code', 'nta_name'):
            if c in df.columns:
                df[c] = df[c].astype(str)
    return integrated, street, borough_month, geo


def spearman(x, y):
    """Spearman rho, p-value and n, ignoring missing pairs."""
    d = pd.DataFrame({'x': x, 'y': y}).dropna()
    if len(d) < 5 or d['x'].nunique() < 2 or d['y'].nunique() < 2:
        return np.nan, np.nan, len(d)
    rho, p = sps.spearmanr(d['x'], d['y'])
    return float(rho), float(p), len(d)


def nta_totals(integrated: pd.DataFrame) -> pd.DataFrame:
    """One row per neighborhood with totals and per-km2-per-year densities for the whole window."""
    n_years = integrated['year_month'].nunique() / 12
    agg = integrated.groupby(['nta_code', 'nta_name', 'borough'], observed=True).agg(
        area_km2=('area_km2', 'first'),
        h6_problems=('h6_problems', 'sum'), h6_heat=('h6_grp_heat_hot_water', 'sum'),
        h6_emergency=('h6_emergency_problems', 'sum'), h6_violations=('h6_violations', 'sum'),
        h6_no_violation=('h6_no_violation', 'sum'), h6_no_access=('h6_no_access', 'sum'),
        h6_buildings=('h6_buildings', 'sum'),
        h6_median_days_to_close=('h6_median_days_to_close', 'median'),
        t3_permits=('t3_permits', 'sum'), t3_openings=('t3_street_openings', 'sum'),
        t3_emergency=('t3_emergency_permits', 'sum'), t3_utility=('t3_utility_permits', 'sum'),
        t3_new_jobs=('t3_new_jobs', 'sum'), t3_active_days=('t3_active_permit_days', 'sum'),
        t3_median_duration_days=('t3_median_duration_days', 'median'),
    ).reset_index()
    per = agg['area_km2'] * n_years
    agg['h6_per_km2_year'] = agg['h6_problems'] / per
    agg['heat_per_km2_year'] = agg['h6_heat'] / per
    agg['t3_per_km2_year'] = agg['t3_permits'] / per
    agg['openings_per_km2_year'] = agg['t3_openings'] / per
    agg['h6_heat_share'] = agg['h6_heat'] / agg['h6_problems'].replace(0, np.nan)
    agg['h6_emergency_share'] = agg['h6_emergency'] / agg['h6_problems'].replace(0, np.nan)
    agg['h6_violation_rate'] = agg['h6_violations'] / (agg['h6_violations'] + agg['h6_no_violation']).replace(0, np.nan)
    agg['h6_no_access_rate'] = agg['h6_no_access'] / agg['h6_problems'].replace(0, np.nan)
    agg['t3_emergency_share'] = agg['t3_emergency'] / agg['t3_permits'].replace(0, np.nan)
    agg['t3_utility_share'] = agg['t3_utility'] / agg['t3_permits'].replace(0, np.nan)
    agg['t3_new_job_share'] = agg['t3_new_jobs'] / agg['t3_permits'].replace(0, np.nan)
    return agg


def _within_borough_z(s: pd.Series, borough: pd.Series) -> pd.Series:
    """z-score of log(1+s) inside each borough (removes the borough level)."""
    v = np.log1p(s.astype(float))
    return v.groupby(borough).transform(lambda g: (g - g.mean()) / (g.std(ddof=0) or np.nan))


def two_way_demean(df: pd.DataFrame, col: str, unit='nta_code', time='year_month') -> pd.Series:
    """x - unit mean - time mean + grand mean (a simple two-way fixed-effects transform)."""
    x = df[col].astype(float)
    return (x - x.groupby(df[unit]).transform('mean') - x.groupby(df[time]).transform('mean') + x.mean())


def _style(fig, title, height=480):
    fig.update_layout(template=TEMPLATE, title=dict(text=title, x=0.01, xanchor='left', font=dict(size=15)),
                      height=height, margin=dict(l=60, r=30, t=70, b=60),
                      legend=dict(orientation='h', yanchor='bottom', y=1.0, x=1, xanchor='right'))
    return fig


# ==============================================================================================
# Member 1
# ==============================================================================================
def rq1_density_scatter(integrated):
    """RQ1: Are neighborhoods with denser street work also neighborhoods with denser housing complaints?"""
    t = nta_totals(integrated)
    t = t[(t['h6_problems'] > 0) & (t['t3_permits'] > 0)]
    rho, p, n = spearman(t['t3_per_km2_year'], t['h6_per_km2_year'])
    within = {b: spearman(g['t3_per_km2_year'], g['h6_per_km2_year'])[0] for b, g in t.groupby('borough')}
    fig = px.scatter(t, x='t3_per_km2_year', y='h6_per_km2_year', color='borough', log_x=True, log_y=True,
                     color_discrete_map=BOROUGH_COLORS, hover_name='nta_name',
                     hover_data={'t3_per_km2_year': ':.0f', 'h6_per_km2_year': ':.0f', 'borough': False},
                     labels={'t3_per_km2_year': 'Street permits per km² per year (T3, log scale)',
                             'h6_per_km2_year': 'Housing problems per km² per year (H6, log scale)',
                             'borough': 'Borough'})
    fig.update_traces(marker=dict(size=9, opacity=0.8, line=dict(width=0.5, color='white')))
    _style(fig, f'RQ1 · Street-work density vs housing-complaint density (one dot = one neighborhood)'
                f'<br><sup>Spearman ρ = {rho:.2f} across {n} residential neighborhoods</sup>')
    table = pd.DataFrame({'borough': list(within), 'spearman_rho_within_borough': list(within.values())})
    return table, fig, {'rho': rho, 'p': p, 'n': n, 'within': within}


def rq2_seasonal_cycles(integrated):
    """RQ2: Do the two domains peak in the same months of the year, or in opposite seasons?"""
    city = integrated.groupby('year_month')[['h6_problems', 't3_permits', 't3_street_openings',
                                            'h6_grp_heat_hot_water']].sum()
    idx = city / city.mean() * 100                     # index: average month = 100
    moy = city.groupby(city.index.month).mean()
    moy_idx = moy / moy.mean() * 100
    rho, p, n = spearman(city['h6_problems'], city['t3_permits'])
    fig = go.Figure()
    for yr in sorted(set(city.index.year)):
        fig.add_vrect(x0=f'{yr}-01-01', x1=f'{yr}-05-31', fillcolor='#2a78d6', opacity=0.05, line_width=0)
        fig.add_vrect(x0=f'{yr}-10-01', x1=f'{yr}-12-31', fillcolor='#2a78d6', opacity=0.05, line_width=0)
    fig.add_trace(go.Scatter(x=idx.index, y=idx['h6_problems'], name='Housing problems (H6)',
                             line=dict(color=COLOR_H6, width=2.5)))
    fig.add_trace(go.Scatter(x=idx.index, y=idx['t3_permits'], name='Street permits (T3)',
                             line=dict(color=COLOR_T3, width=2.5)))
    fig.update_yaxes(title='Index (average month = 100)')
    fig.update_xaxes(title='Month')
    _style(fig, 'RQ2 · Monthly city-wide activity, both domains on one index scale'
                f'<br><sup>Shaded = NYC heat season (Oct–May). Month-to-month Spearman ρ = {rho:.2f}</sup>')
    peak = {'h6_peak_month': MONTH_NAMES[int(moy_idx['h6_problems'].idxmax()) - 1],
            't3_peak_month': MONTH_NAMES[int(moy_idx['t3_permits'].idxmax()) - 1],
            'h6_low_month': MONTH_NAMES[int(moy_idx['h6_problems'].idxmin()) - 1],
            't3_low_month': MONTH_NAMES[int(moy_idx['t3_permits'].idxmin()) - 1]}
    table = moy_idx.round(1)
    table.index = [MONTH_NAMES[m - 1] for m in table.index]
    return table, fig, {'rho': rho, 'p': p, 'n': n, **peak}


# ==============================================================================================
# Member 2
# ==============================================================================================
def rq3_same_street_gas(street):
    """RQ3: On the SAME street, are heat/gas complaints higher in months with gas-main work than in months without?"""
    s = street.copy()
    s['h6_heat_gas'] = s['h6_heat_hot_water'] + s['h6_gas']
    s['gas_work'] = s['t3_kind_gas'] > 0
    s['season'] = np.where(s['year_month'].dt.month.isin([10, 11, 12, 1, 2, 3, 4, 5]), 'Heat season (Oct–May)',
                           'Summer (Jun–Sep)')
    rows = []
    for season, g in s.groupby('season'):
        m = g.groupby(['borough', 'street_key', 'gas_work'])['h6_heat_gas'].mean().unstack()
        m = m.dropna()                                  # streets that have months WITH and WITHOUT gas work
        if m.empty:
            continue
        w = sps.wilcoxon(m[True], m[False]) if len(m) > 10 and (m[True] != m[False]).any() else None
        rows.append({'season': season, 'streets_compared': len(m),
                     'mean_without_gas_work': m[False].mean(), 'mean_with_gas_work': m[True].mean(),
                     'ratio_with_vs_without': m[True].mean() / m[False].mean() if m[False].mean() else np.nan,
                     'share_streets_higher_with_work': (m[True] > m[False]).mean(),
                     'wilcoxon_p': w.pvalue if w is not None else np.nan})
    table = pd.DataFrame(rows)
    long = table.melt(id_vars='season', value_vars=['mean_without_gas_work', 'mean_with_gas_work'],
                      var_name='month_type', value_name='complaints')
    long['month_type'] = long['month_type'].map({'mean_without_gas_work': 'Months WITHOUT gas work',
                                                 'mean_with_gas_work': 'Months WITH gas work'})
    fig = px.bar(long, x='season', y='complaints', color='month_type', barmode='group', text_auto='.2f',
                 color_discrete_map={'Months WITHOUT gas work': COLOR_MUTED, 'Months WITH gas work': COLOR_T3},
                 labels={'complaints': 'Avg heat + gas complaints per street-month', 'season': '',
                         'month_type': ''})
    _style(fig, 'RQ3 · Same street, different months: heat/gas complaints with vs without gas-main permits'
                '<br><sup>Paired comparison: only streets that had both kinds of months are used</sup>')
    return table, fig, {}


def rq4_lagged_utility_links(integrated, max_lag=3):
    """RQ4: Does utility street work come BEFORE matching indoor complaints (0-3 month lags)?"""
    pairs = [('t3_kind_water_sewer', 'h6_grp_water_plumbing', 'Water/sewer work → water/plumbing complaints'),
             ('t3_kind_gas', 'h6_grp_heat_hot_water', 'Gas work → heat/hot-water complaints'),
             ('t3_kind_gas', 'h6_grp_gas', 'Gas work → gas complaints'),
             ('t3_street_openings', 'h6_problems', 'Street openings → all complaints')]
    df = integrated.sort_values(['nta_code', 'year_month']).copy()
    rows = []
    for x, y, label in pairs:
        for lag in range(max_lag + 1):
            df['_x'] = df.groupby('nta_code', observed=True)[x].shift(lag)
            d = df.dropna(subset=['_x'])
            xd = two_way_demean(d, '_x')
            yd = two_way_demean(d, y)
            rho, p, n = spearman(xd, yd)
            se = 1 / np.sqrt(max(n - 3, 1))             # Fisher-z standard error
            lo, hi = np.tanh(np.arctanh(rho) - 1.96 * se), np.tanh(np.arctanh(rho) + 1.96 * se)
            rows.append({'pair': label, 'lag_months': lag, 'rho': rho, 'ci_low': lo, 'ci_high': hi, 'p': p, 'n': n})
    df.drop(columns='_x', inplace=True)
    table = pd.DataFrame(rows)
    table['lag'] = 'lag ' + table['lag_months'].astype(str)
    fig = px.bar(table, x='pair', y='rho', color='lag', barmode='group',
                 error_y=table['ci_high'] - table['rho'], error_y_minus=table['rho'] - table['ci_low'],
                 color_discrete_sequence=['#f6b38f', '#eb6834', '#b84a1c', '#6e2a0f'],
                 labels={'rho': 'Spearman ρ after removing neighborhood & month averages', 'pair': '', 'lag': ''})
    fig.add_hline(y=0, line_color='#555', line_width=1)
    _style(fig, 'RQ4 · Does street utility work precede matching indoor problems? (lag 0–3 months)'
                '<br><sup>Bars = within-neighborhood correlation, error bars = 95% CI</sup>', height=520)
    return table, fig, {}


# ==============================================================================================
# Member 3
# ==============================================================================================
def rq5_double_burden_map(integrated, geo, map_style='white-bg'):
    """RQ5: Which neighborhoods carry a 'double burden' (top quartile for BOTH housing problems and street work)?"""
    t = nta_totals(integrated)
    h_q = t['h6_per_km2_year'].quantile(0.75)
    t_q = t['t3_per_km2_year'].quantile(0.75)
    hi_h, hi_t = t['h6_per_km2_year'] >= h_q, t['t3_per_km2_year'] >= t_q
    t['burden'] = np.select([hi_h & hi_t, hi_h & ~hi_t, ~hi_h & hi_t],
                            ['Both high (double burden)', 'Housing complaints high only', 'Street work high only'],
                            'Neither in top quartile')
    order = ['Both high (double burden)', 'Housing complaints high only', 'Street work high only',
             'Neither in top quartile']
    colors = {'Both high (double burden)': '#8b1e3f', 'Housing complaints high only': COLOR_H6,
              'Street work high only': COLOR_T3, 'Neither in top quartile': '#e4e2da'}
    fig = px.choropleth_map(t, geojson=geo, locations='nta_code', featureidkey='properties.nta_code', color='burden',
                        category_orders={'burden': order}, color_discrete_map=colors, hover_name='nta_name',
                        hover_data={'nta_code': False, 'borough': True, 'h6_per_km2_year': ':.0f',
                                    't3_per_km2_year': ':.0f', 'burden': False},
                        labels={'h6_per_km2_year': 'Housing problems /km²/yr', 't3_per_km2_year': 'Permits /km²/yr',
                                'burden': ''},
                        map_style=map_style, center={'lat': 40.705, 'lon': -73.94}, zoom=9.2, opacity=0.85)
    fig.update_traces(marker_line_width=0.4, marker_line_color='white')
    _style(fig, 'RQ5 · Where housing distress and street disruption overlap'
                '<br><sup>Top quartile (per km² per year) among residential neighborhoods, 2022–2025</sup>',
           height=620)
    fig.update_layout(legend=dict(orientation='v', y=0.98, x=0.01, xanchor='left', yanchor='top'))
    counts = t['burden'].value_counts().reindex(order).fillna(0).astype(int)
    double = t[t['burden'] == order[0]].sort_values('h6_per_km2_year', ascending=False)
    return double[['nta_name', 'borough', 'h6_per_km2_year', 't3_per_km2_year']], fig, {
        'counts': counts.to_dict(), 'by_borough': double['borough'].value_counts().to_dict(),
        'expected_if_independent': round(len(t) * 0.25 * 0.25, 1), 'n': len(t)}


def rq6_complaints_per_permit_heatmap(borough_month):
    """RQ6: How many housing problems are reported per street permit, by borough and calendar month?"""
    b = borough_month.copy()
    b['month'] = b['year_month'].dt.month
    g = b.groupby(['borough', 'month'])[['h6_problems', 't3_permits']].sum()
    g['ratio'] = g['h6_problems'] / g['t3_permits'].replace(0, np.nan)
    mat = g['ratio'].unstack('month').reindex(columns=range(1, 13))
    mat.columns = MONTH_NAMES
    fig = px.imshow(mat, text_auto='.2f', aspect='auto', color_continuous_scale='Blues',
                    labels=dict(color='H6 problems per T3 permit', x='Month of year', y='Borough'))
    _style(fig, 'RQ6 · Housing problems reported per street permit issued (borough × month, 2022–2025 pooled)',
           height=420)
    return mat, fig, {}


# ==============================================================================================
# Member 4
# ==============================================================================================
def rq7_close_time_by_intensity(integrated, min_problems=5):
    """RQ7: Are housing complaints closed more slowly in neighborhood-months with heavy street work?"""
    d = integrated[(integrated['h6_problems'] >= min_problems) & integrated['h6_median_days_to_close'].notna()].copy()
    # intensity tier = quartile of street-work density compared with the SAME borough in the SAME month
    d['tier'] = pd.qcut(d['t3_permits_per_km2_z_borough'].rank(method='first'), 4,
                        labels=['Q1 lowest', 'Q2', 'Q3', 'Q4 highest'])
    kw = sps.kruskal(*[g['h6_median_days_to_close'].values for _, g in d.groupby('tier', observed=True)])
    rho, p, n = spearman(d['t3_permits_per_km2_z_borough'], d['h6_median_days_to_close'])
    fig = px.box(d, x='tier', y='h6_median_days_to_close', color='tier', points=False,
                 category_orders={'tier': ['Q1 lowest', 'Q2', 'Q3', 'Q4 highest']},
                 color_discrete_sequence=['#fbd3bf', '#f6a57a', '#eb6834', '#a8441a'],
                 labels={'tier': 'Street-work intensity (quartile within borough & month)',
                         'h6_median_days_to_close': 'Median days to close a housing problem'})
    fig.update_layout(showlegend=False)
    _style(fig, 'RQ7 · Time to close housing problems vs street-work intensity'
                f'<br><sup>Kruskal–Wallis p = {kw.pvalue:.3g}; Spearman ρ = {rho:.2f} (n = {n:,} neighborhood-months)</sup>')
    table = d.groupby('tier', observed=True)['h6_median_days_to_close'].describe()[['count', '25%', '50%', '75%']]
    return table, fig, {'kruskal_p': kw.pvalue, 'rho': rho, 'p': p, 'n': n}


def rq8_top_stress_neighborhoods(integrated, top=15):
    """RQ8: Which 15 neighborhoods are most stressed on BOTH dimensions relative to their own borough?"""
    t = nta_totals(integrated)
    t['z_h6'] = _within_borough_z(t['h6_per_km2_year'], t['borough'])
    t['z_t3'] = _within_borough_z(t['t3_per_km2_year'], t['borough'])
    t['stress_index'] = (t['z_h6'] + t['z_t3']) / 2
    top_t = t.sort_values('stress_index', ascending=False).head(top).iloc[::-1]
    top_t['label'] = top_t['nta_name'] + ' (' + top_t['borough'].str.title() + ')'
    fig = go.Figure()
    fig.add_trace(go.Bar(y=top_t['label'], x=top_t['z_h6'], name='Housing-complaint density (z)', orientation='h',
                         marker_color=COLOR_H6))
    fig.add_trace(go.Bar(y=top_t['label'], x=top_t['z_t3'], name='Street-permit density (z)', orientation='h',
                         marker_color=COLOR_T3))
    fig.update_layout(barmode='group', xaxis_title='Standard deviations above the borough average (log density)')
    _style(fig, f'RQ8 · Top {top} "double-stress" neighborhoods (ranked by the average of both z-scores)',
           height=620)
    return top_t.iloc[::-1][['nta_name', 'borough', 'z_h6', 'z_t3', 'stress_index']], fig, {}


# ==============================================================================================
# Member 5
# ==============================================================================================
def rq9_work_mix_by_heat_quintile(integrated):
    """RQ9: Is the MIX of street work different in neighborhoods with the most heat complaints?"""
    t = nta_totals(integrated)
    t['heat_quintile'] = pd.qcut(t['heat_per_km2_year'].rank(method='first'), 5,
                                 labels=['Q1 fewest', 'Q2', 'Q3', 'Q4', 'Q5 most'])
    kinds = ['t3_kind_gas', 't3_kind_water_sewer', 't3_kind_steam', 't3_kind_electric_telecom', 't3_kind_paving',
             't3_kind_street_reconstruction', 't3_kind_building_operation', 't3_kind_sidewalk_curb',
             't3_kind_occupancy_equipment', 't3_kind_refuse_container', 't3_kind_tree']
    kinds = [k for k in kinds if k in integrated.columns]   # 'other' is < 0.1% of permits -> left out of the chart
    by_nta = integrated.groupby('nta_code', observed=True)[kinds].sum()
    mix = by_nta.join(t.set_index('nta_code')['heat_quintile']).groupby('heat_quintile', observed=True)[kinds].sum()
    share = mix.div(mix.sum(axis=1), axis=0) * 100
    long = share.reset_index().melt(id_vars='heat_quintile', var_name='kind', value_name='share')
    long['kind'] = long['kind'].map(T3_KINDS)
    fig = px.bar(long, x='heat_quintile', y='share', color='kind',
                 color_discrete_sequence=px.colors.qualitative.Safe,
                 labels={'heat_quintile': 'Neighborhoods grouped by heat/hot-water complaints per km² (quintiles)',
                         'share': '% of street permits', 'kind': 'Street work kind'})
    fig.update_layout(barmode='stack', legend=dict(orientation='v', x=1.02, y=1, xanchor='left', yanchor='top'))
    _style(fig, 'RQ9 · What kind of street work happens where heat complaints are worst?', height=520)
    fig.update_layout(legend=dict(orientation='v', x=1.02, y=1, xanchor='left', yanchor='top'),
                      margin=dict(r=200))
    share.columns = [T3_KINDS[k] for k in share.columns]
    return share.round(1), fig, {}


def rq10_change_on_change(integrated, start_year=None, end_year=None):
    """RQ10: Did neighborhoods where street work GREW the most also see housing complaints grow?"""
    years = sorted(integrated['year'].unique())
    a, b = start_year or years[0], end_year or years[-1]
    y = integrated[integrated['year'].isin([a, b])].groupby(['nta_code', 'nta_name', 'borough', 'year'],
                                                                observed=True)[['h6_problems', 't3_permits']].sum()
    y = y.unstack('year')
    y = y[(y[('h6_problems', a)] >= 50) & (y[('t3_permits', a)] >= 20)]   # stable baselines only
    out = pd.DataFrame({'h6_change_pct': (y[('h6_problems', b)] / y[('h6_problems', a)] - 1) * 100,
                        't3_change_pct': (y[('t3_permits', b)] / y[('t3_permits', a)] - 1) * 100}).reset_index()
    rho, p, n = spearman(out['t3_change_pct'], out['h6_change_pct'])
    fig = px.scatter(out, x='t3_change_pct', y='h6_change_pct', color='borough', hover_name='nta_name',
                     color_discrete_map=BOROUGH_COLORS,
                     labels={'t3_change_pct': f'Change in street permits {a}→{b} (%)',
                             'h6_change_pct': f'Change in housing problems {a}→{b} (%)', 'borough': 'Borough'})
    fig.add_hline(y=0, line_color='#888', line_width=1)
    fig.add_vline(x=0, line_color='#888', line_width=1)
    fig.update_traces(marker=dict(size=9, opacity=0.8, line=dict(width=0.5, color='white')))
    _style(fig, f'RQ10 · Growth vs growth: did more street work come with more complaints? ({a} vs {b})'
                f'<br><sup>Spearman ρ = {rho:.2f} across {n} neighborhoods (baseline ≥ 50 problems and ≥ 20 permits)</sup>')
    quad = pd.crosstab(out['t3_change_pct'] > 0, out['h6_change_pct'] > 0)
    return out, fig, {'rho': rho, 'p': p, 'n': n, 'quadrants': quad, 'years': (a, b)}


# ==============================================================================================
# Member 6
# ==============================================================================================
CORR_METRICS = {'h6_per_km2_year': 'H6 problems /km²', 'h6_heat_share': 'H6 heat share',
                'h6_emergency_share': 'H6 emergency share', 'h6_violation_rate': 'H6 violation rate',
                'h6_no_access_rate': 'H6 no-access rate', 'h6_median_days_to_close': 'H6 days to close',
                't3_per_km2_year': 'T3 permits /km²', 'openings_per_km2_year': 'T3 openings /km²',
                't3_utility_share': 'T3 utility share', 't3_emergency_share': 'T3 emergency share',
                't3_new_job_share': 'T3 new-job share', 't3_median_duration_days': 'T3 work duration'}


def rq11_correlation_matrix(integrated):
    """RQ11: Which housing metrics move together with which street metrics across neighborhoods?"""
    t = nta_totals(integrated)
    m = t[list(CORR_METRICS)].rename(columns=CORR_METRICS).corr(method='spearman')
    fig = px.imshow(m, text_auto='.2f', zmin=-1, zmax=1, color_continuous_scale='RdBu_r', aspect='auto',
                    labels=dict(color='Spearman ρ'))
    fig.add_shape(type='rect', x0=5.5, x1=11.5, y0=-0.5, y1=5.5, line=dict(color='#111', width=2))
    _style(fig, 'RQ11 · Cross-domain correlation matrix (neighborhood level, Spearman ρ)'
                '<br><sup>Black box = the cross-domain block (housing rows × street columns)</sup>', height=640)
    cross = m.iloc[:6, 6:]
    strongest = cross.stack().abs().sort_values(ascending=False).head(5)
    return m.round(2), fig, {'strongest_cross_pairs': [(a, b, round(cross.loc[a, b], 2)) for (a, b) in strongest.index]}


def rq12_predictive_value(integrated, test_year=None):
    """RQ12: Does knowing last months' street work help PREDICT next month's housing complaints?"""
    df = integrated.sort_values(['nta_code', 'year_month']).copy()
    test_year = test_year or int(df['year'].max())
    df['y'] = np.log1p(df['h6_problems'])
    for k in (1, 2, 3, 12):
        df[f'y_lag{k}'] = df.groupby('nta_code', observed=True)['y'].shift(k)
    t3_feats = []
    for col in ['t3_permits', 't3_street_openings', 't3_kind_gas', 't3_kind_water_sewer', 't3_emergency_permits']:
        for k in (1, 2, 3):
            name = f'log_{col}_lag{k}'
            df[name] = np.log1p(df.groupby('nta_code', observed=True)[col].shift(k))
            t3_feats.append(name)
    month_dummies = pd.get_dummies(df['month'], prefix='m', drop_first=True).astype(float)
    df = pd.concat([df, month_dummies], axis=1)
    base_feats = ['y_lag1', 'y_lag2', 'y_lag3', 'y_lag12'] + list(month_dummies.columns)
    df = df.dropna(subset=base_feats + t3_feats)
    train, test = df[df['year'] < test_year], df[df['year'] == test_year]

    def fit_score(feats):
        X = np.column_stack([np.ones(len(train)), train[feats].to_numpy(float)])
        beta, *_ = np.linalg.lstsq(X, train['y'].to_numpy(float), rcond=None)
        Xt = np.column_stack([np.ones(len(test)), test[feats].to_numpy(float)])
        pred = Xt @ beta
        yt = test['y'].to_numpy(float)
        r2 = 1 - ((yt - pred) ** 2).sum() / ((yt - yt.mean()) ** 2).sum()
        mae = np.abs(np.expm1(pred) - np.expm1(yt)).mean()
        return r2, mae

    models = {'Seasonality only (month dummies)': list(month_dummies.columns),
              'Housing history (own lags + season)': base_feats,
              'Housing history + street-work lags': base_feats + t3_feats,
              'Street-work lags + season only': t3_feats + list(month_dummies.columns)}
    rows = [{'model': k, **dict(zip(['test_R2', 'test_MAE_problems'], fit_score(v))), 'n_features': len(v)}
            for k, v in models.items()]
    table = pd.DataFrame(rows)
    fig = px.bar(table, x='model', y='test_R2', text_auto='.3f',
                 color='model', color_discrete_sequence=[COLOR_MUTED, COLOR_H6, '#5b3fa0', COLOR_T3],
                 labels={'test_R2': f'Out-of-sample R² on {test_year} (log scale target)', 'model': ''})
    fig.update_layout(showlegend=False, yaxis_range=[0, 1])
    _style(fig, f'RQ12 · How well can we predict a neighborhood\'s housing problems next month? (train < {test_year}, test = {test_year})')
    return table, fig, {'train_rows': len(train), 'test_rows': len(test), 'test_year': test_year}
