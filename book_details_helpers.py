import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from colors import PALETTE

# ============================================================
# Constants
# ============================================================

STICKINESS_ORDER = ["Bounced", "Returned", "Hooked"]

STICKINESS_COLORS = {
    "Bounced":  PALETTE["pink"],
    "Returned": PALETTE["peach"],
    "Hooked":   PALETTE["blue"],
}

STICKINESS_DEFS = {
    "Bounced":  "Opened on 1 day only — never returned",
    "Returned": "Opened on exactly 2 distinct days",
    "Hooked":   "Opened on 3 or more distinct days",
}

TIER_LABELS = {
    0: "No book use",
    1: "Tried once",
    2: "Returning reader",
    3: "Highly engaged",
}

# ============================================================
# Language helpers
# ============================================================

@st.cache_data(show_spinner=False)
def get_book_languages_from_summary(df_book_summary: pd.DataFrame) -> list[str]:
    """Return sorted list of book languages from cr_book_user_book_summary."""
    langs = (
        df_book_summary["book_language"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda s: s.ne("")]
        .unique()
        .tolist()
    )
    return sorted(langs)


# ============================================================
# Core filtered view
# ============================================================

@st.cache_data(show_spinner=False)
def get_book_summary_for_language(
    df_book_summary: pd.DataFrame,
    languages: list[str],
) -> pd.DataFrame:
    """
    Filter cr_book_user_book_summary to selected book languages.
    Returns all rows (one per user × book_id) for those languages.
    """
    if not languages:
        return pd.DataFrame()
    return df_book_summary[
        df_book_summary["book_language"].isin(languages)
    ].copy()


# ============================================================
# Per-book popularity aggregation
# ============================================================

@st.cache_data(show_spinner=False)
def build_book_popularity(df_filtered: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate per-book popularity metrics.

    Returns one row per base_book_id with:
      - unique_readers
      - total_events
      - avg_active_days   (mean active_days_for_book across readers)
      - stickiness counts: n_bounced, n_returned, n_hooked
      - stickiness pct:    pct_bounced, pct_returned, pct_hooked
    """
    if df_filtered.empty:
        return pd.DataFrame()

    df = df_filtered.copy()
    df["base_book_id"] = df["base_book_id"].fillna(df["book_id"])

    agg = (
        df.groupby("base_book_id", as_index=False)
        .agg(
            unique_readers=("cr_user_id", "nunique"),
            total_events=("total_events", "sum"),
            avg_active_days=("active_days_for_book", "mean"),
            n_bounced=("stickiness", lambda s: (s == "Bounced").sum()),
            n_returned=("stickiness", lambda s: (s == "Returned").sum()),
            n_hooked=("stickiness", lambda s: (s == "Hooked").sum()),
        )
        .sort_values("unique_readers", ascending=False)
    )

    # Build comma-separated language list per book
    lang_agg = (
        df.dropna(subset=["book_language"])
        .groupby("base_book_id")["book_language"]
        .agg(lambda s: ", ".join(sorted(s.unique())))
        .reset_index()
        .rename(columns={"book_language": "languages"})
    )
    agg = agg.merge(lang_agg, on="base_book_id", how="left")
    agg["languages"] = agg["languages"].fillna("Unknown")

    total = agg["unique_readers"]
    agg["pct_bounced"]  = agg["n_bounced"]  / total
    agg["pct_returned"] = agg["n_returned"] / total
    agg["pct_hooked"]   = agg["n_hooked"]   / total
    agg["avg_active_days"] = agg["avg_active_days"].round(2)

    return agg.reset_index(drop=True)


# ============================================================
# Stickiness stacked bar chart
# ============================================================

@st.cache_data(show_spinner=False)
def build_stickiness_chart(
    df_popularity: pd.DataFrame,
    min_readers: int = 10,
    sort_by: str = "Hooked",
) -> go.Figure:
    """
    Horizontal stacked bar chart of stickiness distribution per book,
    sorted by the chosen stickiness level descending.

    sort_by: one of "Hooked", "Returned", "Bounced"
    """
    if df_popularity.empty:
        return go.Figure()

    df = df_popularity[df_popularity["unique_readers"] >= min_readers].copy()

    if df.empty:
        return go.Figure()

    sort_col = f"pct_{sort_by.lower()}"
    df = df.sort_values(sort_col, ascending=True)  # ascending for horizontal bar

    fig = go.Figure()

    for stick in STICKINESS_ORDER:
        col = f"pct_{stick.lower()}"
        n_col = f"n_{stick.lower()}"
        fig.add_trace(go.Bar(
            name=stick,
            y=df["base_book_id"],
            x=df[col],
            orientation="h",
            marker_color=STICKINESS_COLORS[stick],
            customdata=df[[n_col, "unique_readers", "languages"]].values,
            hovertemplate=(
                f"<b>{stick}</b><br>"
                "%{x:.1%} of readers<br>"
                "%{customdata[0]:,} / %{customdata[1]:,} users<br>"
                "Languages: %{customdata[2]}<br>"
                f"<i>{STICKINESS_DEFS[stick]}</i>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        barmode="stack",
        title="Book stickiness distribution (% of readers)",
        xaxis=dict(tickformat=".0%", title="Share of readers"),
        yaxis=dict(title=""),
        legend=dict(title="Stickiness", traceorder="normal"),
        margin=dict(l=20, r=20, t=55, b=20),
        height=max(300, len(df) * 28 + 80),
    )

    return fig


# ============================================================
# Per-book FTM outcomes (Hooked readers vs non-readers)
# ============================================================

@st.cache_data(show_spinner=False)
def build_book_ftm_outcomes(
    df_filtered: pd.DataFrame,
    df_cr_users: pd.DataFrame,
    ra_level_threshold: int = 25,
    stickiness_filter: str = "Hooked",
) -> pd.DataFrame:
    """
    For each base_book_id, compare FTM outcomes for readers at the
    given stickiness level vs non-readers (LA users in mapped universe).

    Returns one row per base_book_id with:
      - readers / non_readers count
      - avg_level_readers / avg_level_non_readers
      - pct_ra_readers / pct_ra_non_readers
      - lift_avg_level / lift_pct_ra
    """
    if df_filtered.empty or df_cr_users.empty:
        return pd.DataFrame()

    df = df_filtered.copy()
    df["base_book_id"] = df["base_book_id"].fillna(df["book_id"])

    # LA users in the mapped universe
    ftm = df_cr_users[df_cr_users["la_flag"] == 1][
        ["cr_user_id", "max_user_level", "ra_flag"]
    ].copy()
    ftm["is_ra"] = (
        (pd.to_numeric(ftm["max_user_level"], errors="coerce") >= ra_level_threshold)
        | (ftm["ra_flag"].fillna(0).astype(int) == 1)
    )

    all_reader_ids = set(
        df[df["stickiness"] == stickiness_filter]["cr_user_id"].unique()
    )

    records = []
    for book, grp in df.groupby("base_book_id"):
        reader_ids = set(
            grp[grp["stickiness"] == stickiness_filter]["cr_user_id"].unique()
        )
        if not reader_ids:
            continue

        non_reader_ids = all_reader_ids - reader_ids  # other book readers at same stickiness

        readers_ftm    = ftm[ftm["cr_user_id"].isin(reader_ids)]
        non_readers_ftm = ftm[ftm["cr_user_id"].isin(non_reader_ids)]

        def safe_mean(s): return float(s.mean()) if len(s) else 0.0
        def safe_pct(s):  return float(s.mean()) if len(s) else 0.0

        avg_lvl_r  = safe_mean(readers_ftm["max_user_level"].dropna())
        avg_lvl_nr = safe_mean(non_readers_ftm["max_user_level"].dropna())
        pct_ra_r   = safe_pct(readers_ftm["is_ra"])
        pct_ra_nr  = safe_pct(non_readers_ftm["is_ra"])

        records.append({
            "base_book_id":         book,
            "readers":              len(reader_ids),
            "avg_level_readers":    avg_lvl_r,
            "avg_level_others":     avg_lvl_nr,
            "lift_avg_level":       avg_lvl_r - avg_lvl_nr,
            "pct_ra_readers":       pct_ra_r,
            "pct_ra_others":        pct_ra_nr,
            "lift_pct_ra":          pct_ra_r - pct_ra_nr,
        })

    if not records:
        return pd.DataFrame()

    return (
        pd.DataFrame(records)
        .sort_values("lift_avg_level", ascending=False)
        .reset_index(drop=True)
    )


# ============================================================
# Book drill-down: stickiness × user tier cross-tab
# ============================================================

@st.cache_data(show_spinner=False)
def build_book_tier_crosstab(
    df_filtered: pd.DataFrame,
    df_cr_book_user_cohorts: pd.DataFrame,
    base_book_id: str,
) -> pd.DataFrame:
    """
    For a selected base_book_id, return a cross-tab of:
      rows    = book_engagement_tier (user-level tier 0–3)
      columns = stickiness (Bounced / Returned / Hooked)
      values  = user count
    """
    df = df_filtered.copy()
    df["base_book_id"] = df["base_book_id"].fillna(df["book_id"])

    book_rows = df[df["base_book_id"] == base_book_id][
        ["cr_user_id", "stickiness"]
    ].drop_duplicates(subset=["cr_user_id"])

    if book_rows.empty:
        return pd.DataFrame()

    # Join user-level tier
    tier_lookup = df_cr_book_user_cohorts[
        ["cr_user_id", "book_engagement_tier"]
    ].drop_duplicates(subset=["cr_user_id"])

    merged = book_rows.merge(tier_lookup, on="cr_user_id", how="left")
    merged["book_engagement_tier"] = (
        pd.to_numeric(merged["book_engagement_tier"], errors="coerce")
        .fillna(0)
        .astype(int)
    )
    # Exclude tier 0 — users who appear as non-book-users overall should not appear
    # in a per-book cross-tab since they are actual readers of this specific book.
    # Tier 0 in this context means the cohort table join returned no match or tier data.
    merged = merged[merged["book_engagement_tier"] > 0]
    if merged.empty:
        return pd.DataFrame()
    merged["tier_label"] = merged["book_engagement_tier"].map(TIER_LABELS).fillna("Unknown")

    crosstab = (
        merged.groupby(["tier_label", "stickiness"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=STICKINESS_ORDER, fill_value=0)
    )

    # Tier label ordering
    tier_order = [TIER_LABELS[i] for i in sorted(TIER_LABELS.keys())]
    crosstab = crosstab.reindex(
        [t for t in tier_order if t in crosstab.index]
    )

    return crosstab


# ============================================================
# Book drill-down: level (Lv1, Lv2, ...) reader counts
# ============================================================

@st.cache_data(show_spinner=False)
def build_book_level_breakdown(
    df_filtered: pd.DataFrame,
    base_book_id: str,
) -> pd.DataFrame:
    """
    For a selected base_book_id, return reader counts per book_level.
    Useful for seeing if users engage with higher-level versions of the same book.
    """
    df = df_filtered.copy()
    df["base_book_id"] = df["base_book_id"].fillna(df["book_id"])

    book_rows = df[df["base_book_id"] == base_book_id].copy()

    if book_rows.empty:
        return pd.DataFrame()

    # Filter to rows that actually have a level — books without Lv# suffix have null book_level
    book_rows = book_rows[book_rows["book_level"].notna()]
    if book_rows.empty:
        return pd.DataFrame()

    agg = (
        book_rows.groupby("book_level", as_index=False)
        .agg(
            unique_readers=("cr_user_id", "nunique"),
            total_events=("total_events", "sum"),
            avg_active_days=("active_days_for_book", "mean"),
            n_bounced=("stickiness", lambda s: (s == "Bounced").sum()),
            n_returned=("stickiness", lambda s: (s == "Returned").sum()),
            n_hooked=("stickiness", lambda s: (s == "Hooked").sum()),
        )
        .sort_values("book_level")
    )

    agg["avg_active_days"] = agg["avg_active_days"].round(2)
    return agg.reset_index(drop=True)