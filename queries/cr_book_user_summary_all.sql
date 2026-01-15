/*
===============================================================================
Table: cr_book_user_summary_all

Purpose:
--------
Canonical USER-level summary of Curious Reader book engagement.
Each row represents one user who has interacted with at least one book.

Language normalization:
----------------------
Uses book_language (canonical, aligned to FTM naming; e.g., IsiZulu -> Zulu).
Keeps language_code (raw suffix parsed from book_id) for traceability.

IMPORTANT:
----------
To avoid mismatched combinations for multilingual users, we select the most
common (book_language, language_code) PAIR per user, not each field independently.
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_book_user_summary_all` AS
WITH base AS (
  SELECT
    cr_user_id,
    book_id,
    book_language,
    language_code,
    total_events,
    active_days_for_book,
    first_access_date,
    last_access_date,

    -- frequency of the (book_language, language_code) pair for this user
    COUNT(*) OVER (PARTITION BY cr_user_id, book_language, language_code) AS cnt_pair
  FROM `dataexploration-193817.user_data.cr_book_user_book_summary`
),

user_rollup AS (
  SELECT
    cr_user_id,

    -- Choose the dominant (book_language, language_code) pair together
    (ARRAY_AGG(STRUCT(book_language, language_code)
      ORDER BY cnt_pair DESC, book_language, language_code LIMIT 1
    ))[OFFSET(0)].book_language AS book_language,

    (ARRAY_AGG(STRUCT(book_language, language_code)
      ORDER BY cnt_pair DESC, book_language, language_code LIMIT 1
    ))[OFFSET(0)].language_code AS language_code,

    COUNT(DISTINCT book_id) AS distinct_books_accessed,
    SUM(total_events) AS total_book_events,

    SUM(active_days_for_book) AS total_active_book_days,
    COUNTIF(active_days_for_book >= 2) AS books_with_2plus_days,

    MIN(first_access_date) AS first_access_date,
    MAX(last_access_date) AS last_access_date,
    DATE_DIFF(MAX(last_access_date), MIN(first_access_date), DAY) AS book_span_days
  FROM base
  GROUP BY cr_user_id
),

most_read AS (
  SELECT
    cr_user_id,
    book_id AS most_read_book_id,
    MAX(total_events) AS most_read_book_events
  FROM `dataexploration-193817.user_data.cr_book_user_book_summary`
  GROUP BY cr_user_id, book_id
  QUALIFY
    ROW_NUMBER() OVER (
      PARTITION BY cr_user_id
      ORDER BY most_read_book_events DESC, book_id
    ) = 1
)

SELECT
  u.cr_user_id,
  u.book_language,
  u.language_code,
  u.distinct_books_accessed,
  u.total_book_events,
  u.total_active_book_days,
  u.books_with_2plus_days,
  u.first_access_date,
  u.last_access_date,
  u.book_span_days,
  m.most_read_book_id,
  m.most_read_book_events
FROM user_rollup u
LEFT JOIN most_read m
  USING (cr_user_id);
