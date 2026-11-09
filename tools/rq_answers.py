"""Answers / limits per RQ and the story text, written from the FULL-data run (2022-01 .. 2025-12).

Numbers quoted here come from notebooks/02_research_questions.ipynb outputs. If the data is re-downloaded and the
numbers move, update this file and re-run tools/make_text.py + the notebook.
"""
ANSWERS = {
    'rq1': (
        'Yes, strongly at city level: Spearman ρ = 0.65 across 197 residential neighborhoods (p < 0.001). '
        'The places with the most street permits per km² are also the places with the most housing problems per km². '
        'The within-borough picture is the real discovery, though. The link is strong in the Bronx (ρ = 0.82), '
        'Queens (0.77) and Staten Island (0.65), weak in Brooklyn (0.19), and **reversed in Manhattan (ρ = −0.78)**. '
        "Manhattan's most permit-dense areas are commercial cores like Midtown–Times Square (about 7,500 permits/km²/yr) "
        'with few tenants filing complaints (about 500 problems/km²/yr). Its complaint hot-spots, Harlem, Hamilton '
        'Heights and Washington Heights (about 9,000–10,000 problems/km²/yr), have only about 1,500 permits/km²/yr.',
        'Both densities are driven by how built-up and residential a place is, which is a shared cause and not one '
        'causing the other. Density per km² ignores population and the number of housing units, because no population '
        'table was joined.'),
    'rq2': (
        'They peak in different seasons. Housing problems peak in **December–January** (index about 155 and 152, '
        'average month = 100) and bottom out in **June** (66). The swing is driven by heat/hot-water complaints, which '
        'are about 15× higher in December than in August. Street permits are much flatter (73–123) and peak in '
        '**March** and June, with their low in **February**. Month to month, the two series are slightly negatively '
        'related (ρ = −0.28, p = 0.05). Street crews and housing inspectors are busiest at different times of the year.',
        'This is city-wide, so it says nothing about any single neighborhood. Permits measure permission to work, not '
        'the days work actually happened.'),
    'rq3': (
        '**No.** In 4,505 streets compared with themselves during heat season, heat + gas complaints averaged 6.61 per '
        'street-month in months **with** gas-main permits and 6.91 in months **without**, slightly *lower* with work '
        '(ratio 0.96). In summer (3,962 streets) it was 1.20 vs 1.20, no difference. The simple story that gas work cuts '
        'off heat and causes complaints is not visible at street-month level.',
        'Street names are matched by name, so a long avenue such as Broadway is one "street" across many neighborhoods. '
        'A permit does not say whether service was actually shut off. Very short outages may be fixed before tenants '
        'complain to HPD.'),
    'rq4': (
        "**No timing link.** After removing each neighborhood's own average and each month's city-wide average, every "
        'one of the 16 tested correlations (4 work→problem pairs × lags 0–3 months) lies between −0.022 and +0.015. All '
        'of them are practically zero, and 15 of 16 are not statistically significant. Unusual utility work in a '
        'neighborhood is not followed by unusual matching complaints there.',
        'Monthly granularity could hide effects that last only days. Neighborhoods average many streets, so a very '
        'local effect could be diluted. A null result means "no detectable effect at this scale", not "proven zero".'),
    'rq5': (
        '**18 neighborhoods carry a double burden** (top quartile for both housing problems and street permits per km²). '
        'If the two were unrelated we would expect about 12, so overlap is about 1.5× chance. They are concentrated in '
        'the West/Central Bronx (Fordham Heights, Mount Hope, Mount Eden-Claremont, Concourse, University Heights, West '
        'Farms), Upper Manhattan (Harlem South, Inwood and others) and a few Brooklyn areas. On the map these form two '
        'connected clusters around the Harlem River.',
        'Quartile cut-offs are a choice: a different threshold changes the count but not the clusters. Density is per '
        'area, not per resident.'),
    'rq6': (
        'The ratio is highest in the **Bronx in winter**: 6.6 housing problems per street permit in January, against '
        '1.9 in June. It is lowest on **Staten Island** (0.16–0.57). Every borough follows the same winter-high, '
        'summer-low pattern, because complaints swing with the heat season while permits stay flat (RQ2). The Bronx '
        'ratio is about 3× Brooklyn and about 3.5× Manhattan in every month. There, housing distress outweighs street '
        'activity far more than anywhere else.',
        'The ratio mixes two different things (complaints and permissions), so it is a comparison index, not a rate. '
        'It is pooled over four years.'),
    'rq7': (
        '**Practically no.** The tiers differ statistically (Kruskal–Wallis p = 0.001, n = 9,399 neighborhood-months), '
        'but the size is tiny: the median time to close is 4.63 days in the lowest street-work quartile and 4.84 days in '
        'the highest. That is about 5 hours, and the correlation is ρ = 0.03. With 9,000+ observations even meaningless '
        'differences become "significant". Effect size is what matters here.',
        'The value is the median per neighborhood-month, not per complaint. Closing a complaint depends mostly on '
        'landlords and HPD workload, which we do not observe.'),
    'rq8': (
        'Relative to their own borough, the most pressured neighborhoods are **Astoria (Central)** and **Old '
        'Astoria-Hallets Point** in Queens, **Mount Hope** and **Fordham Heights** in the Bronx, and **St. George-New '
        'Brighton** and **Tompkinsville-Stapleton** on Staten Island, followed by **Corona** (Queens). Using '
        'within-borough z-scores surfaces places a city-wide ranking would hide: Staten Island\'s North Shore is '
        'unremarkable city-wide but stands out strongly inside its borough.',
        'The index weighs both sides equally. Long Island City reaches the top 15 almost only through street work '
        '(housing z below 0), so always read both bars and not just the rank.'),
    'rq9': (
        'Yes. The mix shifts from utility work to **building operations**. In the 20% of neighborhoods with the fewest '
        'heat complaints per km², building-operation permits are 18% of all street permits. In the 20% with the most, '
        'they are **48%**. Over the same range, gas work falls from 12% to 8%, water/sewer from 5% to 3%, paving from 8% '
        'to 4% and sidewalk work from 11% to 7%. High-heat-complaint areas are dense residential areas full of '
        'building-side work (scaffolds, sheds, renovations), not areas with unusually much gas or steam work.',
        'Work kinds are our grouping of DOT permit types (documented in notebook 01). Shares hide volume: dense '
        'neighborhoods have more of every kind in absolute terms.'),
    'rq10': (
        '**No.** Across 196 neighborhoods, the change in street permits from 2022 to 2025 is unrelated to the change in '
        'housing problems (ρ = −0.01, p = 0.91). Housing problems grew city-wide (+17%, from 732k to 854k), so most '
        'neighborhoods sit above zero whatever happened to their street work. Of the 108 neighborhoods where permits '
        'grew, 78 saw complaints grow. Of the 88 where permits fell, 60 still saw complaints grow. That is almost the '
        'same share.',
        'A change between two years is noisy for small neighborhoods. A 4-year window may be too short for slower '
        'effects such as new construction attracting new residents.'),
    'rq11': (
        'The strongest cross-domain link is simple density: housing problems/km² vs permits/km² (ρ = 0.65) and vs '
        'street openings/km² (0.60). Neighborhoods with dense housing complaints also have a *lower* share of utility '
        '(−0.46), emergency (−0.35) and new-job (−0.48) permits. Their street activity is more routine and more '
        'renewal-heavy. Inside H6, dense-complaint areas have higher violation rates (0.50) and fewer "no access" '
        'inspections (−0.57). Complaints there are more often confirmed, so they reflect real conditions and not just '
        'more reporting.',
        'These are correlations between 197 neighborhoods (an ecological analysis). They describe places, not '
        'individual buildings or tenants.'),
    'rq12': (
        "**Street permits add no predictive power.** A model using only a neighborhood's own complaint history plus "
        'season predicts 2025 out-of-sample with **R² = 0.924**. Adding 15 street-work lag features gives **0.925**, '
        'an improvement of 0.0001, and mean absolute error barely moves (67.6 → 67.5 problems). Street-work lags plus '
        'season alone reach only R² = 0.13. That is the same as "where is it dense", because permits also mark busy '
        'places. This is the clearest evidence that the spatial link in RQ1 comes from shared neighborhood '
        'characteristics, not a street-to-home mechanism.',
        'These are linear models on log counts. A non-linear model could find small effects, but the gap would have '
        'to be large to matter in practice. The test covers one year (2025).'),
}

SUMMARY_TABLE = '\n'.join([
    '| RQ | Member | Short answer |',
    '|---|---|---|',
    '| 1 | Takiee-Allah | Strong spatial link (ρ = 0.65), but reversed inside Manhattan (−0.78): commercial cores vs residential uptown |',
    '| 2 | Ziad | Opposite seasons: complaints peak Dec–Jan (heat), permits peak Mar and Jun; ρ = −0.28 |',
    '| 3 | Kirolous | Same street with vs without gas work: no increase in heat/gas complaints (ratio 0.96 in heat season) |',
    '| 4 | Kirolous | No lead–lag link at 0–3 months: all 16 within-neighborhood correlations ≈ 0 |',
    '| 5 | Takiee-Allah | 18 double-burden neighborhoods vs 12 expected; clusters in West Bronx and Upper Manhattan |',
    '| 6 | Ziad | Bronx in January has 6.6 problems per permit; Staten Island under 0.6 all year |',
    '| 7 | Ahmed Hany | Close times differ by about 5 hours between street-work quartiles: significant but irrelevant |',
    '| 8 | Ahmed Hany | Astoria, Mount Hope, Fordham Heights and the Staten Island North Shore top the within-borough index |',
    '| 9 | Abdallah | High-heat-complaint areas: building-operation permits 48% of permits (vs 18%); less utility work |',
    '| 10 | Abdallah | Growth in permits does not predict growth in complaints (ρ = −0.01) |',
    '| 11 | Mohamed | Density is the only strong cross-domain link; dense-complaint areas have more confirmed violations |',
    '| 12 | Mohamed | Adding street-work lags to prediction: R² 0.924 → 0.925, no practical gain |',
])

STORY = dict(
    subtitle=('Do the New York neighborhoods with the most street construction also suffer the most housing '
              'maintenance problems, and does street work cause them? HPD complaints (H6) meet DOT street permits '
              '(T3) for 197 residential neighborhoods × 48 months, 2022–2025.'),
    question=[
        'Every year DOT issues more than 600,000 permits to dig up, block or build on NYC streets, and HPD receives '
        'about 750,000–850,000 tenant-reported housing problems. Gas mains, water mains, scaffolds and street openings '
        'sit right outside the buildings tenants complain about.',
        '**Our question:** are street disruption and housing distress concentrated in the same neighborhoods, and if '
        'so, does street work come *before* indoor problems (a mechanism), or do both simply reflect the same kind of '
        'place (a shared cause)?',
    ],
    data=[
        '**H6** Housing Maintenance Code Complaints and Problems (HPD, `ygpa-z7cr`): **3,160,386** problems received '
        '2022–2025, **3,153,693** after cleaning.',
        '**T3** Street Construction Permits (DOT, `tqtj-sjs8`): **2,577,722** permits issued 2022–2025, '
        '**2,575,684** after removing voided permits.',
        'There is no shared key. H6 carries a neighborhood (NTA) name. T3 carries only a street geometry (WKT), which '
        'we turned into points and **spatially joined** to the official 2020 NTA boundaries. Permits without geometry '
        'were placed from other permits on the same street segment.',
        'Both were aggregated to **neighborhood × month** (197 residential NTAs × 48 months = 9,456 rows). We also '
        'built a street × month table (same normalized street name) and a borough × month table.',
    ],
    discovery=[
        '**Same places:** neighborhoods with dense street work also have dense housing problems (ρ = 0.65). 18 '
        'neighborhoods, concentrated in the West Bronx and Upper Manhattan, are in the top quartile for both, against '
        '12 expected by chance.',
        '**Surprise 1, Manhattan flips:** inside Manhattan the link is *negative* (ρ = −0.78). Midtown has the most '
        'permits and few complaints, while Harlem and Washington Heights have the most complaints and fewer permits.',
        '**Surprise 2, no mechanism:** on the same street, months with gas-main work do not have more heat or gas '
        'complaints. Within neighborhoods, utility work is not followed by matching complaints 0–3 months later. '
        'Growth in permits does not go with growth in complaints. Adding street-work history to a forecasting model '
        'improves R² by only 0.0001.',
        '**Opposite seasons:** complaints peak in December–January (heat season), permits in March and June. In the '
        'Bronx in January there are 6.6 housing problems for every street permit.',
    ],
    limits=[
        '**Correlation is not causation.** The spatial overlap is best explained by shared drivers (dense, older, '
        'lower-income residential housing stock) that we did not measure, not by street work causing complaints.',
        'A permit is permission to work, not proof of the days work happened or of a service shut-off.',
        'Monthly and neighborhood aggregation can hide very short or very local effects. A null result means "not '
        'detectable at this scale".',
        'Complaints measure reporting, not all housing problems: tenants who do not call 311 are invisible.',
        'Densities are per km² because no population table was joined. Per-resident rates could change some rankings.',
    ],
    impact=[
        '**HPD and DOT planners:** the double-burden map and the within-borough ranking (RQ5, RQ8) show where '
        'residents face both problems. These are good places for joint outreach and for coordinating street work '
        'with housing inspections.',
        '**HPD staffing:** forecasting next month\'s complaints should rely on a neighborhood\'s own history and the '
        'heat season (R² 0.92). DOT permit feeds add nothing, which saves effort.',
        '**Tenant advocates:** concentrated problems in the West Bronx and Upper Manhattan are not "construction '
        'noise". Violation rates are higher there and no-access rates lower, so complaints reflect confirmed '
        'conditions.',
        '**Residents:** street work outside your building is unlikely to be what causes heat or plumbing failures '
        'inside it. Report those to HPD either way.',
    ],
)
