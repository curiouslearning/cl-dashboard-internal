/*
===============================================================================
Table: cr_book_user_cohorts

Purpose:
--------
Canonical cohort table for comparing Curious Reader book engagement vs learning
outcomes in Feed the Monster (and other apps captured in cr_user_progress).

Includes BOTH:
- Book users: users present in cr_book_user_summary_all
- Non-book users: users in cr_user_progress who have no book usage record

User Universe:
--------------
cr_user_progress restricted to languages that have books (as observed from
canonical book_language), PLUS any known book users (handles language mismatches/holes).

Grain:
------
One row per cr_user_id in the selected universe.
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_book_user_cohorts` AS
WITH
  -- Use canonical language aligned to FTM (e.g., Zulu)
  book_languages AS (
    SELECT DISTINCT book_language
    FROM `dataexploration-193817.user_data.cr_book_user_summary_all`
    WHERE book_language IS NOT NULL
  ),

  book_users AS (
    SELECT
      cr_user_id,
      book_language AS book_language,   -- canonical (use for matching vs FTM)
      language_code AS book_language_code, -- raw suffix (debug only)

      distinct_books_accessed,
      total_book_events,
      total_active_book_days,
      books_with_2plus_days,
      first_access_date,
      last_access_date,
      book_span_days,
      most_read_book_id,
      most_read_book_events
    FROM `dataexploration-193817.user_data.cr_book_user_summary_all`
  ),

  user_universe AS (
    SELECT
      p.user_pseudo_id,
      p.cr_user_id,
      p.first_open,
      p.country,
      p.app_language,
      p.cohort_name,
      p.app,

      -- outcomes / progression
      p.max_user_level,
      p.max_game_level,
      p.la_date,
      p.ra_date,
      p.days_to_ra,
      p.furthest_event,
      p.gpc,

      -- engagement metrics
      p.engagement_event_count,
      p.total_time_minutes,
      p.avg_session_length_minutes,
      p.last_event_date,
      p.active_span,

      -- flags
      p.la_flag,
      p.ra_flag,
      p.gc_flag,
      p.lr_flag
    FROM `dataexploration-193817.user_data.cr_user_progress` p
    LEFT JOIN book_languages bl
      ON p.app_language = bl.book_language
    LEFT JOIN book_users bu
      ON p.cr_user_id = bu.cr_user_id
    WHERE
      p.cr_user_id IS NOT NULL
      AND (bl.book_language IS NOT NULL OR bu.cr_user_id IS NOT NULL)
  ),

  joined AS (
    SELECT
      u.*,

      bu.cr_user_id IS NOT NULL AS is_book_user,

      -- canonical + raw book language fields
      bu.book_language,
      bu.book_language_code,

      COALESCE(bu.distinct_books_accessed, 0) AS distinct_books_accessed,
      COALESCE(bu.total_book_events, 0) AS total_book_events,
      COALESCE(bu.total_active_book_days, 0) AS total_active_book_days,
      COALESCE(bu.books_with_2plus_days, 0) AS books_with_2plus_days,
      bu.first_access_date,
      bu.last_access_date,
      COALESCE(bu.book_span_days, 0) AS book_span_days,
      bu.most_read_book_id,
      bu.most_read_book_events
    FROM user_universe u
    LEFT JOIN book_users bu
      ON u.cr_user_id = bu.cr_user_id
  ),

  tiered AS (
    SELECT
      *,
      CASE
        WHEN NOT is_book_user THEN 0
        WHEN total_active_book_days = 1 THEN 1
        WHEN (
          total_active_book_days >= 2
          OR distinct_books_accessed >= 2
          OR books_with_2plus_days >= 1
        ) THEN 2
        WHEN (
          total_active_book_days >= 3
          AND (
            distinct_books_accessed >= 3
            OR books_with_2plus_days >= 2
            OR book_span_days >= 3
          )
        ) THEN 3
        ELSE 2
      END AS book_engagement_tier
    FROM joined
  )

SELECT * FROM tiered;
