/*
===============================================================================
Table: cr_book_user_summary_all

Purpose:
--------
Canonical USER-level summary of Curious Reader book engagement.
Each row represents one user who has interacted with at least one book.

Derived from:
- user_data.cr_book_user_book_summary (user–book grain)

Provides engagement signals without relying on time-on-task:
- distinct_books_accessed
- total_book_events
- total_active_book_days (sum of active days across books)
- books_with_2plus_days (count of books engaged with across 2+ distinct days)
- first/last access dates and overall engagement span
- most_read_book (by total_events)

Downstream Usage:
-----------------
- Joined to full user universe to create cr_book_user_cohorts (includes non-book users)
- Dashboard metrics and segmentation
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_book_user_summary_all`
AS
WITH
  user_rollup AS (
    SELECT
      cr_user_id,

      -- Book language derived from URL/book_id, not FTM.
      -- If a user has multiple book languages, we keep the most common one.
      (ARRAY_AGG(language_code ORDER BY cnt DESC, language_code LIMIT 1))[
        OFFSET(0)] AS language_code,
      COUNT(DISTINCT book_id) AS distinct_books_accessed,
      SUM(total_events) AS total_book_events,

      -- engagement strength
      SUM(active_days_for_book) AS total_active_book_days,
      COUNTIF(active_days_for_book >= 2) AS books_with_2plus_days,

      -- overall access window
      MIN(first_access_date) AS first_access_date,
      MAX(last_access_date) AS last_access_date,
      DATE_DIFF(MAX(last_access_date), MIN(first_access_date), DAY)
        AS book_span_days
    FROM
      (
        SELECT
          cr_user_id,
          book_id,
          language_code,
          total_events,
          active_days_for_book,
          first_access_date,
          last_access_date,
          COUNT(*) OVER (PARTITION BY cr_user_id, language_code) AS cnt
        FROM `dataexploration-193817.user_data.cr_book_user_book_summary`
      )
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
      ROW_NUMBER()
        OVER (
          PARTITION BY cr_user_id ORDER BY most_read_book_events DESC, book_id
        )
      = 1
  )
SELECT
  u.cr_user_id,
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
