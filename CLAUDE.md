# CLAUDE.md — Curious Learning Internal Dashboard

## Project Overview

A **Streamlit multi-page analytics dashboard** for Curious Learning, tracking literacy app engagement across two apps — **FTM (Feed the Monster)** and **Curious Reader (CR)**. It surfaces funnel metrics, reader acquisition outcomes, book engagement cohorts, and cohort histories for internal data/product teams.

---

## Tech Stack

| Layer | Library / Service |
|---|---|
| Framework | Streamlit 1.48 (multi-page via `st_pages` + `.streamlit/pages.toml`) |
| Data storage | Google Cloud Storage (Parquet, partitioned by `run_date=YYYY-MM-DD`) |
| Analytical DB | BigQuery (`dataexploration-193817`) |
| Secrets | GCP Secret Manager |
| Charts | Plotly Express + Plotly Graph Objects |
| Auth | GCP Service Account via `google-oauth2` |
| Containerization | Docker + `entrypoint.sh` |
| Profiling | `pyinstrument` (logged at debug level on data load) |

---

## Entry Points

```
main.py              # st.set_page_config + st_pages navigation
entrypoint.sh        # runs add_ga.py then streamlit run main.py --server.port=8501
```

Pages are declared in `.streamlit/pages.toml` and routed by `st.navigation()`.

---

## Page Files

| File | Purpose |
|---|---|
| `single_funnel.py` | Single-cohort funnel view — LR → FTMI → DC → TS → SL → PC → LA → RA → GC (CR); LR → FTMI → PC → LA → RA → GC (other) |
| `engagement_over_time.py` | Multi-cohort engagement trends (total time, session count) |
| `levels_reached.py` | Level distribution across apps and cohorts via `st.pills` |
| `time_to_ra.py` | Days-to-RA distribution, ECDF, histogram for RA users |
| `cohort_history.py` | Per-user FTM event timeline with pagination; book access summary. Lists **all** cohort members (members with no `cr_user_progress` row are added as empty rows → render as "No progress") |

---

## Module Map

### `settings.py`
- `get_gcp_credentials()` → returns `(Credentials, bq_client)`, `@st.cache_resource(ttl="1d")`
- `get_logger()` → returns a named Python logger, `@st.cache_resource(ttl="1d")`
- `initialize()` → sets pandas copy-on-write mode and display options; call at the top of every page
- `default_daterange` → `[datetime(2021-01-01), date.today()]`

### `users.py`
Core data loading and session state management.

**GCS loaders** (all `@st.cache_data(ttl="1d")`):
- `load_parquet_from_gcs(file_pattern)` — glob GCS, auto-selects latest `run_date=*` partition
- `load_cr_user_progress_from_gcs()` — main FTM user progress per user
- `load_unity_user_progress_from_gcs()` — Unity app user progress
- `load_cr_app_launch_from_gcs()` — CR app-launch events (LR source for CR)
- `load_cr_book_user_cohorts_from_gcs()` — user-level book engagement cohorts
- `load_cr_book_user_book_summary_from_gcs()` — per-user × per-book summary

**Initialization** (call once per page):
- `ensure_user_data_initialized()` — checks `st.session_state["user_data_initialized"]`; calls `init_user_data()` if absent; wraps in `st.error` + `st.stop()` on failure
- `init_user_data()` — loads all DataFrames, fixes date columns, deduplicates Unity users, cleans languages, stores into `st.session_state`

**Session state keys set by `init_user_data()`**:
```python
st.session_state["df_cr_users"]                  # FTM user progress (deduped to single language)
st.session_state["df_unity_users"]               # Unity users (max level deduped)
st.session_state["df_cr_app_launch"]             # CR app-launch events
st.session_state["df_cr_book_user_cohorts"]      # Book engagement cohort table
st.session_state["df_cr_cohorts"]                # Named cohort definitions
st.session_state["df_cr_book_user_book_summary"] # Per-user × per-book summary
```

**BigQuery helpers** (`@st.cache_data(ttl="1d")`):
- `get_language_list()` → from `user_data.language_max_level`
- `get_country_list()` → from `user_data.active_countries`
- `get_cohort_list()` → from `st.session_state["df_cr_cohorts"]`
- `get_cohort_user_ids(cohort_name)` → from `user_data.cr_cohorts`
- `get_users_ftm_event_timeline(cr_user_id_list)` → from `user_data.ftm_event_timeline_all`
- `get_book_summary_for_cohort(cohort_ids)` → parameterized query on `cr_book_user_cohorts`
- `get_books_for_user(cr_user_id)` → per-book detail from `cr_book_user_book_summary`

**Language cleanup**:
- `clean_language_column()` — normalizes typos (`ukranian`, `malgache`, `arabictest`, `farsitest`)
- `clean_cr_users_to_single_language()` — deduplicates multi-language/country CR users by furthest progress

### `metrics.py`
Funnel counting and user filtering.

**Funnel stages** (`get_metric_user_count(user_df, stat)`):
```
LR   Learner Reached     — reached source: app_launch (CR) / unity table (Unity) /
                           full cr_cohorts membership (cohort mode). NOT len(df_cr_users).
FTMI FTM Interacted       — produced an FTM gameplay event (count of the gameplay df).
                           LR → FTMI drop = opened the app but FTM never ran (offline-init bug).
DC   Download Completed
TS   Tapped Start
SL   Selected Level
PC   Puzzle Completed
LA   Learner Acquired    — max_user_level >= 1
RA   Reader Acquired     — max_user_level >= 25
GC   Game Completed      — max_user_level >= 1 AND gpc >= 90
```
FTMI is **omitted for Unity** (native app, not the FTM web layer) and can be forced
off via `create_engagement_funnel(show_ftmi=False)` — Compare App Funnels does this
for every column when any compared app is Unity. Cohort mode sources LR from
`df_cr_cohorts` so reached-but-no-gameplay members are counted; that membership df
has no language/country, so the gap can't render in the language-grouped Sideways view.

**Key functions**:
- `get_filtered_users(app, daterange, language, countries_list, cohort)` → `(user_cohort_df, cr_df_LR)` — primary filtering entry point for pages
- `get_engagement_metrics(user_df)` → dict of engagement KPIs for metric tiles
- `calculate_average_metric_per_user(user_df, column_name)` → scalar average
- `select_user_dataframe(app, stat)` → routes to correct session-state DataFrame
- `get_counts(user_cohort_df, groupby_col)` → aggregates LR/LA/RA/GC/GPP by language or country

### `ui_widgets.py`
Reusable Streamlit input widgets and display utilities.

**Selectors**:
- `single_selector(options, title, key, index, include_All)` — dropdown with optional "All" entry
- `multi_select_all(options, title, key)` — multiselect with Select All logic
- `calendar_selector(key, title, index)` — date range picker with preset options
- `convert_date_to_range(selected_date, option)` — converts picker output to `[start, end]`
- `get_apps()` — returns `["All", "CR", "Unity"]` (plus any additional apps)
- `pagination_controls(page, total_pages, page_user_ids, all_user_ids, page_key)` — prev/next buttons for cohort history

**Display**:
- `metric_tile(label, value, color, size, width)` — styled metric card using `st.markdown`
- `display_definitions_table(title, df)` — renders a definitions DataFrame as a table
- `derive_ftm_outcome(row)` — maps user row to outcome label (used in funnel logic)
- `convert_for_download(df)` → CSV bytes for `st.download_button`

### `ui_components.py`
Plotly chart builders and complex composite display functions.

**Funnel / engagement**:
- `create_engagement_funnel(user_df, cr_df_LR, key_prefix, funnel_size, app, show_ftmi=True)` — main funnel visualization (`show_ftmi=False` or `app=Unity` drops the FTMI step)
- `show_dual_metric_tiles(title, home_metrics, size)` — renders engagement KPI tiles in grid
- `display_metrics_for_users(user_page_df)` — per-user metrics table

**Charts**:
- `ftm_timeline_plot(subset, page_user_ids, x_axis_mode)` — event timeline; x-axis = timestamp or level progression
- `levels_reached_chart(selected_apps, selected_cohorts)` — level distribution histogram
- `days_to_ra_chart(df_ra, by_months)` — time-to-RA bar chart
- `ra_ecdf_curve(df_ra, by_months)` — empirical CDF of days to RA
- `ra_histogram_curve(df_ra, by_months)` — histogram of days to RA
- `avg_days_to_ra_by_dim_chart(df_ra, app)` — breakdown by language/country
- `engagement_over_time_chart(df_list_with_labels, metric)` — multi-cohort time series

### `books_helpers.py`
Book engagement analysis within the FTM/CR universe.

- `get_book_languages(df_cr_book_user_cohorts)` — available book languages
- `compute_lang_map(df_cr_book_user_cohorts)` → `app_language_book → app_language` mapping
- `mapped_ftm_languages_for_books(lang_map, effective_book_languages)` — reverse lookup
- `eligible_ftm_users(df_cr_users, mapped_ftm_languages)` — language-matched user universe
- `tier_df_language_mapped(df_cr_book_user_cohorts, effective_book_languages)` — assigns `book_engagement_tier` (0–3) per user
- `build_ftm_compare_la_only(df_cr_users, eligible_users_df, tier_df_mapped, ra_level_threshold)` → `(df_base, df_compare)` — FTM outcome comparison by book tier (LA users only)
- `build_days_to_ra_by_tier(df_users, df_cohorts)` — days-to-RA aggregated by book engagement tier

### `book_details_helpers.py`
Per-book drill-down analytics.

- `get_book_languages_from_summary(df_book_summary)` — languages in the book summary table
- `get_book_summary_for_language(df_book_summary, languages)` → filtered rows
- `build_book_popularity(df_filtered)` → per-book aggregation: unique readers, events, stickiness
- `build_stickiness_chart(df_popularity, min_readers, sort_by)` → Plotly horizontal stacked bar
- `build_book_ftm_outcomes(df_filtered, df_cr_users, ra_level_threshold, stickiness_filter)` → reader vs non-reader FTM outcome lift per book
- `build_book_tier_crosstab(df_filtered, df_cr_book_user_cohorts, base_book_id)` → stickiness × tier cross-tab
- `build_book_level_breakdown(df_filtered, base_book_id)` → reader counts per book level (Lv1, Lv2…)

### `colors.py`
Centralized color configuration. Import `PALETTE` for chart/tile colors.

```python
PALETTE = { "blue", "green", "teal", "peach", "purple", "pink" }
CHART_METRIC_COLORS   # keyed by metric_display label (Plotly charts)
TILE_METRIC_COLORS    # keyed by engagement metric label (KPI tiles)
```

---

## Key Data Concepts

### User Identity
- `cr_user_id` — canonical user ID across all CR/FTM tables
- `user_pseudo_id` — Firebase pseudo ID (Unity); may differ from `cr_user_id`
- Users with multiple language/country combinations are **deduplicated to their furthest-progress row** in `clean_cr_users_to_single_language()`

### Funnel Flags
Columns on `df_cr_users`: `lr_flag`, `la_flag`, `ra_flag`, `gc_flag`, `gpc`
`lr_flag == 1` for every row in `df_cr_users` (it means "has a gameplay row"), so it
drives the **FTMI** step — not LR. LR comes from a reached source (see Funnel stages).

### RA Definition
Reader Acquired = `max_user_level >= 25` **OR** `ra_flag == 1`. Both conditions are checked wherever RA is computed (see `build_ftm_compare_la_only`, `build_book_ftm_outcomes`).

### Book Engagement Tier (0–3)
Stored on `df_cr_book_user_cohorts.book_engagement_tier`:
```
0  No book use
1  Tried once
2  Returning reader
3  Highly engaged
```

### Book Stickiness (per book × user)
Stored on `df_cr_book_user_book_summary.stickiness`:
```
Bounced   opened on 1 day only
Returned  opened on exactly 2 distinct days
Hooked    opened on 3+ distinct days
```

### GCS Partition Pattern
All Parquet data lives under `user_data_parquet_cache/<dataset>/run_date=<YYYY-MM-DD>/`.
`load_parquet_from_gcs()` always selects the **latest** `run_date` partition automatically.

---

## Caching Strategy

| Decorator | Used for |
|---|---|
| `@st.cache_resource(ttl="1d")` | GCP credentials, BQ client, logger (shared singletons) |
| `@st.cache_data(ttl="1d")` | All data-loading and query functions |
| `@st.cache_data(show_spinner=False)` | Pure computation helpers (language maps, aggregations) |

Avoid passing large DataFrames between pages via function arguments without caching — prefer pulling from `st.session_state` after `ensure_user_data_initialized()`.

---

## Page Boilerplate

Every page should start with:

```python
from settings import initialize
from users import ensure_user_data_initialized

initialize()
ensure_user_data_initialized()
```

Then access DataFrames via `st.session_state["df_cr_users"]` etc.

---

## GCP Project

- **Project ID**: `dataexploration-193817`
- **Dataset**: `user_data`
- **Secret**: `projects/405806232197/secrets/service_account_json/versions/latest`

---

## Common Pitfalls

- **`active_span` can be negative** in raw data — clipped to 0 during init. Don't re-clip downstream.
- **CR LR uses `df_cr_app_launch`**, not `df_cr_users` — the first language-tagged event in CR is `app_launch`, not a game event. The `select_user_dataframe()` function handles this routing.
- **`base_book_id`** groups leveled book variants (e.g., `book_lv1`, `book_lv2`) under a shared ID. Always `fillna(book_id)` when `base_book_id` may be null: `df["base_book_id"] = df["base_book_id"].fillna(df["book_id"])`.
- **Unity users** are deduplicated to a single row by `max_user_level` during init — do not re-deduplicate downstream.
- **`days_to_ra`** is only present for RA users — always filter `df[df["days_to_ra"].notna()]` before computing time-to-RA metrics.
- **Language normalization typos** (`ukranian`, `malgache`, `arabictest`, `farsitest`) are corrected in `clean_language_column()` during init — do not re-correct downstream.