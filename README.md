# NYC Homes × NYC Streets

**Housing Maintenance Code Complaints (H6) × Street Construction Permits (T3), NYC 2022–2025**

GIU · Faculty of Informatics and Computer Science · Data Engineering and Visualization, Winter 2026 · Milestone 1
Dr. Nada Sharaf · TAs Mariam Ali, May Magdy, Mohamed El dagla

> **Live website:** https://vercel-gamma-liart-26.vercel.app/

---

## 1. The story in one paragraph

Do the New York neighborhoods with the most street construction also suffer the most housing maintenance problems, and
does street work *cause* them? We cleaned **3.16 million** HPD housing problems and **2.58 million** DOT street permits
issued between January 2022 and December 2025. We placed every permit in one of NYC's official 2020 neighborhoods
(NTAs) with a spatial join and compared the two domains for 197 residential neighborhoods × 48 months.

- **Same places:** street-work density and housing-problem density are strongly linked (Spearman ρ = 0.65). 18
  neighborhoods in the West Bronx and Upper Manhattan are in the top quartile for both (12 would be expected by chance).
- **Surprise 1:** the link flips inside Manhattan (ρ = −0.78). Commercial Midtown has the most permits and few
  complaints, while residential Harlem and Washington Heights are the opposite.
- **Surprise 2:** there is no sign of a mechanism. On the same street, gas-main work does not raise heat complaints.
  Utility work is not followed by matching complaints 0–3 months later. Growth in permits does not track growth in
  complaints. Adding street-work data to a complaint forecast improves R² by only 0.0001.
- **So what:** the overlap reflects shared neighborhood characteristics (dense, older residential housing), not street
  work damaging homes. Agencies can use the double-burden map for joint outreach. For complaint forecasting, a
  neighborhood's own history and the heat season are enough (R² = 0.92).

## 2. Datasets

| Domain | Catalog ID | Dataset | Link | Raw columns | Rows used (2022–2025) |
|---|---|---|---|---|---|
| Housing & Development | **H6** | Housing Maintenance Code Complaints and Problems (HPD) | https://data.cityofnewyork.us/d/ygpa-z7cr | 33 | 3,160,386 → 3,153,693 after cleaning |
| Transportation | **T3** | Street Construction Permits 2022–Present (DOT) | https://data.cityofnewyork.us/d/tqtj-sjs8 | 39 | 2,577,722 → 2,575,684 after cleaning |
| Helper (boundaries only) | – | 2020 Neighborhood Tabulation Areas (DCP) | https://data.cityofnewyork.us/d/9nt8-h7nd | – | 262 NTAs (197 residential) |

**Integration key:** `nta_code × year_month`. H6 provides its NTA name. T3 has only a WKT street geometry, which we
convert to a point and spatially join to the NTA polygons. Permits without geometry are placed from other permits on the
same street segment. Two extra tables (`street × month` and `borough × month`) support the same-street question and the
borough totals.

## 3. Repository structure

```text
├── app.py                              Dash website (filters, search mode, Generate Report, 7 live charts, story, 12 RQs)
├── src/analysis.py                     one function per research question (used by notebook 02 AND the website)
├── notebooks/
│   ├── 01_cleaning_integration.ipynb   download → EDA → pre-cleaning → spatial join → integration → post-cleaning
│   └── 02_research_questions.ipynb     12 research questions, 12 charts, answers, limits, prompts used
├── data/
│   ├── reference/nta2020.geojson       NTA boundaries (offline fallback)
│   ├── metadata/                       dataset schemas from the Socrata API
│   ├── processed/                      outputs of notebook 01 (integrated table, street/borough tables, dictionary, log)
│   └── app/                            outputs of notebook 02 used by the website (12 chart JSONs, story.json)
├── visualizations/rq1.png … rq12.png   static copies of the 12 charts
├── tools/                              text of the research questions + generator for notebook 02
├── docs/Team_Evaluation_Guide.pdf      explainer for the evaluation
├── assets/style.css                    website styling
├── requirements.txt                    website dependencies (deployment)
├── requirements-notebooks.txt          everything needed to re-run the notebooks
├── vercel/                             slim copy of the website for Vercel (section 5)
├── Procfile, Dockerfile               other deployment options (any gunicorn host / Docker)
└── .gitignore                          excludes raw downloads and the big row-level parquet files
```

## 4. Run it locally

```bash
git clone <this repo> && cd <repo>
python -m venv .venv
.venv\Scripts\activate            # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements-notebooks.txt

# 1) Rebuild the data (downloads ~3.2M + ~2.6M rows, 45–90 min, resumable if interrupted)
jupyter nbconvert --to notebook --execute notebooks/01_cleaning_integration.ipynb --inplace --ExecutePreprocessor.timeout=-1
#    optional: set NYC_OPEN_DATA_APP_TOKEN=<token> for faster downloads
#    offline code check on the small starter CSVs: set NYC_DATA_MODE=starter  (counts are NOT real totals)

# 2) Research questions (writes visualizations/ and data/app/)
jupyter nbconvert --to notebook --execute notebooks/02_research_questions.ipynb --inplace

# 3) Website
python app.py                     # http://127.0.0.1:8050
```

The processed outputs are committed, so **step 3 works right after cloning**. Steps 1–2 are only needed to reproduce
the data.

## 5. Deploy (Vercel, free)

The `vercel/` folder is a slim copy of the website made for Vercel's free plan. It has the same `app.py` code
(as `dash_app.py`), the same data files and the same charts, but it leaves out `scipy` and `pyarrow` to stay under
Vercel's 500 MB limit. The live Spearman ρ is computed with pandas ranks (identical value), and parquet files are read
with the smaller `fastparquet`. The full pipeline and notebooks still use scipy and pyarrow.

1. On https://vercel.com choose **Add New → Project** and import this GitHub repository.
2. Set **Root Directory** to `vercel` (Vercel detects the Flask/Python app automatically) and click **Deploy**.
3. Open the URL and test: change the dropdowns, type `Bronx 2024 heat gas` in search, press **Generate Report**, switch
   map layers, and open the other tabs.
4. Put the URL at the top of this README and in the submission email.

If you change `app.py`, `src/analysis.py` or the data, copy them into `vercel/` again (`app.py` becomes
`vercel/dash_app.py`). `Procfile` and `Dockerfile` are kept for hosts that run a normal Python server.

## 6. Website features (requirement checklist)

| Requirement | Where |
|---|---|
| Multiple dropdown filters | Borough, Year, Housing problem type (H6), Street-work kind (T3), Neighborhood(s) |
| Search mode | Free text such as `Brooklyn 2022 new buildings`, `Bronx heat gas`, `Astoria water sewer 2024`. The parser recognizes boroughs (and aliases), years, housing keywords, street-work keywords and neighborhood names, then **sets the dropdowns** to what it understood |
| Central **Generate Report** button | Rebuilds the KPIs and all 7 charts from the current filters/search (Enter in the search box does the same) |
| Variety of interactive charts | Choropleth map (3 layers), log-log scatter, shared-index timeline (one axis), lag-correlation bars with CIs, ranked bars, heatmap, box plot. All have hover/zoom |
| Cross-domain visualization | Map "double burden" layer, scatter H6 vs T3 density, timing test, heatmap ratio |
| Story section | "Our story" tab: question, data, discovery, limits, impact |
| 12 research questions | "12 research questions" tab with the charts and answers from notebook 02 |

## 7. Team contributions (6 members → 12 research questions + 12 visualizations)

| Member | ID | Research questions & charts | Data engineering / website work |
|---|---|---|---|
| Takiee-Allah | 16001345 | RQ1 density scatter · RQ5 double-burden map | Socrata API download (paged, resumable), dataset overview, EDA of both datasets |
| Kirolous Bassem | 16002081 | RQ3 same-street gas test · RQ4 lag correlations | H6 pre-integration cleaning: text standardization, label harmonization, duplicates, imputation from the same building |
| Ziad Khaled Saber Abdullah | 17006438 | RQ2 seasonal timeline · RQ6 borough × month heatmap | T3 pre-integration cleaning: dates/durations, IQR outlier capping, WKT → points, spatial join to NTAs |
| Ahmed Hany | 16004257 | RQ7 close-time box plot · RQ8 top-15 ranking | Integration (NTA × month grid, street and borough tables), post-integration cleaning and validation |
| Abdallah Ahmed Mohamed | 16004141 | RQ9 work mix stacked bars · RQ10 change-on-change scatter | Dash website: dropdowns, search parser, Generate Report callback, map and chart components |
| Mohamed Ahmed | 16008868 | RQ11 correlation matrix · RQ12 prediction test | Feature engineering (densities, lags, z-scores), statistics, GitHub repository, Vercel deployment, README |

*(Team: adjust the role column if your real split was different. It is graded.)*

## 8. Research questions and short answers

| RQ | Question | Short answer |
|---|---|---|
| 1 | Is denser street work found where housing problems are denser? | Yes, ρ = 0.65. Bronx 0.82, Queens 0.77, **Manhattan −0.78** |
| 2 | Do both peak in the same season? | No. Complaints peak Dec–Jan (heat), permits Mar and Jun. ρ = −0.28 month to month |
| 3 | Same street: more heat/gas complaints in months with gas work? | No. 6.61 with vs 6.91 without (heat season, 4,505 streets) |
| 4 | Does utility work come 0–3 months before matching complaints? | No. All 16 within-neighborhood correlations between −0.02 and +0.02 |
| 5 | Which neighborhoods carry a double burden? | 18 (12 expected), clustered in West Bronx and Upper Manhattan |
| 6 | Housing problems per permit by borough × month? | Bronx in January 6.6, Staten Island under 0.6. Winter-high everywhere |
| 7 | Slower complaint closing where street work is heavy? | Statistically yes, practically no: 4.63 vs 4.84 median days |
| 8 | Top 15 combined-pressure neighborhoods (within borough)? | Astoria, Old Astoria, Mount Hope, Fordham Heights, St. George … |
| 9 | Different street-work mix where heat complaints are worst? | Building operations 48% vs 18%. Less gas, water and paving work |
| 10 | Does growth in permits go with growth in complaints? | No, ρ = −0.01 across 196 neighborhoods |
| 11 | Which metrics correlate across domains? | Only density strongly (0.65). Dense-complaint areas have more confirmed violations |
| 12 | Do street permits help predict next month's complaints? | No. R² 0.924 → 0.925 |

## 9. Limitations

Correlation is not causation. Permits are permissions, not observed work days or shut-offs. Monthly × neighborhood
aggregation can hide very short or very local effects. Complaints measure reporting. Densities are per km² because
population was not joined. Full discussion: notebook 01 section 15, notebook 02, and the website story tab.

## 10. Prompts used

AI assistance (Claude) was used. The prompts are listed in notebook 01 section 16 and at the end of notebook 02.
