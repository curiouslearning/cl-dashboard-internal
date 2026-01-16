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

Adds:
- book_language: canonical language name aligned to FTM naming (e.g. IsiZulu -> Zulu)

Grain: One row per (cr_user_id, book_id)
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_book_user_book_summary`
AS
WITH
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
        'Lug',   -- IMPORTANT: Luganda books sometimes use Lug (e.g. ColoursLugLv4)
        'En'
      ]
    ) AS suffix
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
    WHERE cr_user_id IS NOT NULL
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
      SAFE_CAST(REGEXP_EXTRACT(book_id, r'Lv(\d+)$') AS INT64) AS book_level,
      REGEXP_REPLACE(book_id, r'Lv\d+$', '') AS book_no_level
    FROM base
    WHERE book_id IS NOT NULL
  ),

  matched AS (
    SELECT
      p.*,
      s.suffix AS language_code
    FROM parsed p
    LEFT JOIN language_suffixes s
      ON ENDS_WITH(p.book_no_level, s.suffix)
    QUALIFY
      ROW_NUMBER() OVER (
        PARTITION BY p.cr_user_id, p.book_id
        ORDER BY LENGTH(s.suffix) DESC
      ) = 1
  ),

  user_book AS (
    SELECT
      cr_user_id,
      book_id,

      CASE
        WHEN language_code IS NOT NULL THEN
          REGEXP_REPLACE(book_no_level, CONCAT(r'(', language_code, r')$'), '')
        ELSE NULL
      END AS base_book_id,

      -- Raw suffix parsed from book_id (traceability)
      language_code,

      -- Canonical language aligned to FTM naming
      CASE
        WHEN language_code = 'IsiZulu' THEN 'Zulu'
        WHEN language_code IN ('En', 'English') THEN 'English'
        WHEN language_code = 'CVPortuguese' THEN 'Portuguese'
        WHEN language_code = 'CVCreole' THEN 'Creole'
        WHEN language_code = 'Nep' THEN 'Nepali'
        WHEN language_code = 'Ukr' THEN 'Ukrainian'
        WHEN language_code = 'Lug' THEN 'Luganda'   -- FIX
        ELSE language_code
      END AS book_language,

      book_level,
      COUNT(*) AS total_events,
      COUNT(DISTINCT event_date) AS active_days_for_book,
      MIN(event_date) AS first_access_date,
      MAX(event_date) AS last_access_date,
      MIN(event_time) AS first_access_time,
      MAX(event_time) AS last_access_time
    FROM matched
    GROUP BY
      cr_user_id, book_id, base_book_id, language_code, book_language, book_level
  )

SELECT * FROM user_book;
