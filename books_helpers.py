import pandas as pd
import numpy as np
import streamlit as st


# ============================================================
# Basic string utilities
# ============================================================

def clean_str_aligned(s: pd.Series) -> pd.Series:
    """
    Clean string series WITHOUT changing index alignment.
    Used for language matching.
    """
    return s.fillna("").astype(str).str.strip()


def truncate_csv(text: str, max_chars: int = 120) -> str:
    """
    Truncate long comma-separated text cleanly.
    Used for captions.
    """
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    if "," in cut:
        cut = cut.rsplit(",", 1)[0]
    return cut + "…"


# ============================================================
# Language selection + mapping
# ============================================================

@st.cache_data(show_spinner=False)
def get_book_languages(df_cr_book_user_cohorts: pd.DataFrame) -> list[str]:
    """
    Return cleaned, sorted list of available book languages.
    """
    langs = (
        clean_str_aligned(df_cr_book_user_cohorts["app_language_book"])
        .loc[lambda s: s.ne("")]
        .unique()
        .tolist()
    )
    return sorted(langs)


@st.cache_data(show_spinner=False)
def compute_lang_map(df_cr_book_user_cohorts: pd.DataFrame) -> pd.DataFrame:
    """
    Build unique mapping table:
        app_language_book → app_language (FTM language)
    """
    lang_map = df_cr_book_user_cohorts[["app_language_book", "app_language"]].copy()

    lang_map["app_language_book"] = clean_str_aligned(lang_map["app_language_book"])
    lang_map["app_language"] = clean_str_aligned(lang_map["app_language"])

    lang_map = lang_map.loc[
        (lang_map["app_language_book"] != "") &
        (lang_map["app_language"] != "")
    ]

    return lang_map.drop_duplicates()


@st.cache_data(show_spinner=False)
def mapped_ftm_languages_for_books(
    lang_map: pd.DataFrame,
    effective_book_languages: list[str]
) -> list[str]:
    """
    Given selected book languages,
    return the corresponding mapped FTM languages.
    """
    return (
        lang_map.loc[
            lang_map["app_language_book"].isin(effective_book_languages),
            "app_language"
        ]
        .unique()
        .tolist()
    )


# ============================================================
# Eligible universe
# ============================================================

@st.cache_data(show_spinner=False)
def eligible_ftm_users(
    df_cr_users: pd.DataFrame,
    mapped_ftm_languages: list[str]
) -> pd.DataFrame:
    """
    Return unique users whose FTM language
    matches the selected book-language mapping.
    """
    df = df_cr_users[["cr_user_id", "app_language"]].copy()
    df["app_language_clean"] = clean_str_aligned(df["app_language"])

    out = df.loc[
        df["app_language_clean"].isin(mapped_ftm_languages),
        ["cr_user_id", "app_language"]
    ]

    return out.drop_duplicates(subset=["cr_user_id"])


# ============================================================
# Tier mapping
# ============================================================

@st.cache_data(show_spinner=False)
def tier_df_language_mapped(
    df_cr_book_user_cohorts: pd.DataFrame,
    effective_book_languages: list[str]
) -> pd.DataFrame:
    """
    Assign book engagement tier for users
    whose BOOK LANGUAGE matches selected languages.

    Users not present later will be treated as tier 0.
    """
    df = df_cr_book_user_cohorts.copy()

    df["app_language_book_clean"] = clean_str_aligned(df["app_language_book"])

    tier_df = (
        df.loc[
            df["app_language_book_clean"].isin(effective_book_languages),
            ["cr_user_id", "book_engagement_tier"]
        ]
        .drop_duplicates(subset=["cr_user_id"])
        .copy()
    )

    tier_df["book_engagement_tier"] = (
        pd.to_numeric(tier_df["book_engagement_tier"], errors="coerce")
        .fillna(0)
        .astype(int)
        .clip(0, 3)
    )

    return tier_df


# ============================================================
# FTM comparison (LA-only universe)
# ============================================================

@st.cache_data(show_spinner=False)
def build_ftm_compare_la_only(
    df_cr_users: pd.DataFrame,
    eligible_users_df: pd.DataFrame,
    tier_df_mapped: pd.DataFrame,
    ra_level_threshold: int = 25,
):
    """
    Build FTM comparison by book engagement tier.

    Universe:
        • Eligible language-mapped FTM users
        • LA users only (la_flag == 1)

    Milestones (data-informed from survival curve):
        Level 2  → survived immediate friction
        Level 4  → completed early block
        Level 10 → entered long-tail persistence
        Level 25 → RA threshold
    """

    # -------------------------------------------------------
    # Pull only necessary columns from users table
    # -------------------------------------------------------
    users = df_cr_users[[
        "cr_user_id",
        "la_flag",
        "max_user_level",
        "total_time_minutes",
        "ra_flag",
        "active_span",
        "engagement_event_count",
        "avg_session_length_minutes",
    ]].copy()

    users["la_flag"] = users["la_flag"].fillna(0).astype(int)

    # -------------------------------------------------------
    # Merge universe + metrics + tier
    # -------------------------------------------------------
    df_base = (
        eligible_users_df[["cr_user_id", "app_language"]]
        .merge(users, on="cr_user_id", how="left")
        .merge(tier_df_mapped, on="cr_user_id", how="left")
    )

    # Restrict to LA users only
    df_base = df_base[df_base["la_flag"] == 1].copy()

    # Non-book users = tier 0
    df_base["book_engagement_tier"] = (
        pd.to_numeric(df_base["book_engagement_tier"], errors="coerce")
        .fillna(0)
        .astype(int)
        .clip(0, 3)
    )

    # Robust RA definition (offline-safe)
    df_base["is_ra"] = (
        (pd.to_numeric(df_base["max_user_level"], errors="coerce") >= ra_level_threshold)
        | (df_base["ra_flag"].fillna(0).astype(int) == 1)
    )

    # -------------------------------------------------------
    # Aggregation helpers
    # -------------------------------------------------------
    def pct_mean(s):
        s = s.dropna()
        return float(s.mean()) if len(s) else 0.0

    # -------------------------------------------------------
    # Tier-level aggregation
    # -------------------------------------------------------
    df_compare = (
        df_base
        .groupby("book_engagement_tier", as_index=False)
        .agg(
            users=("cr_user_id", "nunique"),

            avg_furthest_level=("max_user_level", "mean"),
            median_furthest_level=("max_user_level", "median"),

            avg_total_time_minutes=("total_time_minutes", "mean"),
            median_total_time_minutes=("total_time_minutes", "median"),

            pct_ra=("is_ra", pct_mean),

            # Data-informed milestone thresholds
            pct_reach_2=("max_user_level",
                         lambda s: float((s >= 2).mean()) if len(s) else 0.0),

            pct_reach_4=("max_user_level",
                         lambda s: float((s >= 4).mean()) if len(s) else 0.0),

            pct_reach_10=("max_user_level",
                          lambda s: float((s >= 10).mean()) if len(s) else 0.0),

            pct_reach_25=("max_user_level",
                          lambda s: float((s >= 25).mean()) if len(s) else 0.0),
        )
        .sort_values("book_engagement_tier")
    )

    # -------------------------------------------------------
    # Compute lift vs non-book baseline (tier 0)
    # -------------------------------------------------------
    if (df_compare["book_engagement_tier"] == 0).any():
        baseline = df_compare.loc[
            df_compare["book_engagement_tier"] == 0
        ].iloc[0]

        df_compare["lift_avg_furthest"] = (
            df_compare["avg_furthest_level"]
            - baseline["avg_furthest_level"]
        )

        df_compare["lift_pct_ra"] = (
            df_compare["pct_ra"]
            - baseline["pct_ra"]
        )

    return df_base, df_compare


def build_days_to_ra_by_tier(df_users, df_cohorts):
    # RA only
    df_ra = df_users[df_users["days_to_ra"].notna()].copy()

    # Join tier
    df = df_ra.merge(
        df_cohorts[["cr_user_id", "book_engagement_tier"]],
        on="cr_user_id",
        how="left"
    )

    # Drop missing tiers
    df = df[df["book_engagement_tier"].notna()]

    # Aggregate
    agg = (
        df.groupby("book_engagement_tier", as_index=False)
          .agg(
              avg_days_to_ra=("days_to_ra", "mean"),
              median_days_to_ra=("days_to_ra", "median"),
              users=("cr_user_id", "nunique")
          )
          .sort_values("book_engagement_tier")
    )

    return agg

