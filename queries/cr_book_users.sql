/*
===============================================================================
Table: cr_book_users

Purpose:
--------
Event-level table of Curious Reader book interactions derived from GA4/Firebase
export data.

Each row represents a single analytics event where:
- The page_location URL contains a `book=` query parameter
- A `cr_user_id` is parsed directly from the page_location query string

Identity Notes:
---------------
- `cr_user_id` is NOT a native GA4 event parameter.
- It is generated client-side and embedded in the page_location URL.
- Some valid-shaped cr_user_ids may never appear in cr_user_progress
  (e.g., book-only users who never enter the FTM/progress funnel).

Usage:
------
This table is the canonical raw input for:
- cr_book_user_book_summary
- cr_book_user_summary_all
- cr_book_user_cohorts

Downstream models may optionally restrict to users present in
cr_user_progress when analyzing learning outcomes.

Refresh:
--------
Full rebuild, scheduled nightly.

Grain:
------
One row per book-related analytics event.
===============================================================================
*/

CREATE OR REPLACE TABLE `dataexploration-193817.user_data.cr_book_users` AS
WITH base AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS event_date,
    TIMESTAMP_MICROS(event_timestamp) AS event_time,
    event_name,
    user_pseudo_id,
    (SELECT ep.value.string_value
     FROM UNNEST(event_params) ep
     WHERE ep.key = 'page_location') AS page_location
  FROM `ftm-b9d99.analytics_159643920.events_*`
)

SELECT
  REGEXP_EXTRACT(
    page_location,
    r'[?&]cr_user_id=([a-z0-9]+20\d{2}\d{5,10})'
  ) AS cr_user_id,
  user_pseudo_id,
  event_name,
  event_date,
  event_time,
  page_location
FROM base
WHERE page_location IS NOT NULL
  AND REGEXP_CONTAINS(page_location, r'[\?&]book=')
  AND REGEXP_CONTAINS(page_location, r'[\?&]cr_user_id=');
