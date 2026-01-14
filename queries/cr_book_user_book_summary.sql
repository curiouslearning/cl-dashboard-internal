/*
===============================================================================
Table: cr_book_user_book_summary

Purpose:
--------
Canonical USER–BOOK summary for Curious Reader book interactions.
Derives engagement signals (active days, first/last access) and parses:
- book_id from page_location
- book_level from trailing "Lv#"
- language_code via suffix matching (no delimiter in book_id)
- base_book_id by removing the matched language suffix

Grain: One row per (cr_user_id, book_id)
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_book_user_book_summary`
AS
WITH
  -- 1) Maintain a suffix list of known language tokens appearing at the end of book IDs.
  --    IMPORTANT: Put longer/multi-token suffixes here (e.g., IsiZulu, CVPortuguese) so
  --    we can safely choose the LONGEST match.
  language_suffixes AS (
    SELECT * FROM UNNEST(
      [
        'CVPortuguese',
        'CVCreole',
        'IsiZulu',
        'Ukrainian',
        'Luganda',
        'Nepali',
        'Swahili',
        'Marathi',
        'Amharic',
        'Tigirigna',
        'Somali',
        'Oromo',
        'Hausa',
        'Wolof',
        'Bangla',
        'Hindi',
        'Portuguese',
        'Ukr',
        'Nep',
        'Lug',
        'En']) AS suffix
  ),
  base AS (
    SELECT
      cr_user_id,
      event_name,
      event_date,
      event_time,
      page_location,
      REGEXP_EXTRACT(page_location, r'[?&]book=([^&]+)') AS book_id
    FROM `dataexploration-193817.user_data.cr_book_users`
    WHERE
      cr_user_id IS NOT NULL
      AND page_location IS NOT NULL
  ),
  parsed AS (
    SELECT
      cr_user_id,
      event_name,
      event_date,
      event_time,
      page_location,
      book_id,

      -- Level number (Lv4 -> 4), if present
      SAFE_CAST(REGEXP_EXTRACT(book_id, r'Lv(\d+)$') AS INT64) AS book_level,

      -- Strip trailing Lv# for language parsing
      REGEXP_REPLACE(book_id, r'Lv\d+$', '') AS book_no_level
    FROM base
    WHERE book_id IS NOT NULL
  ),

  -- 2) Match the LONGEST language suffix that appears at the end of book_no_level.
  matched AS (
    SELECT
      p.*,
      s.suffix AS language_code
    FROM parsed p
    LEFT JOIN language_suffixes s
      ON ENDS_WITH(p.book_no_level, s.suffix)
    QUALIFY
      ROW_NUMBER()
        OVER (
          PARTITION BY p.cr_user_id, p.book_id
          ORDER BY LENGTH(s.suffix) DESC
        )
      = 1
  ),
  user_book AS (
    SELECT
      cr_user_id,
      book_id,

      -- Remove the matched suffix from the end to get base_book_id.
      -- If no suffix matched, base_book_id will be NULL (we can handle later).
      CASE
        WHEN language_code IS NOT NULL
          THEN
            REGEXP_REPLACE(
              book_no_level, CONCAT(r'(', language_code, r')$'), '')
        ELSE NULL
        END AS base_book_id,
      language_code,
      book_level,
      COUNT(*) AS total_events,
      COUNT(DISTINCT event_date) AS active_days_for_book,
      MIN(event_date) AS first_access_date,
      MAX(event_date) AS last_access_date,
      MIN(event_time) AS first_access_time,
      MAX(event_time) AS last_access_time
    FROM matched
    -- Optional restriction if page_view is the only reliable signal:
    -- WHERE event_name = 'page_view'
    GROUP BY
      cr_user_id, book_id, base_book_id, language_code, book_level
  )
SELECT * FROM user_book;
