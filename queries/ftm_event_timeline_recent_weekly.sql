  -- Feed The Monster: Weekly event timeline build (no DECLAREs)
  -- Writes to ftm_event_timeline_recent (WRITE_TRUNCATE)
WITH
  events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS event_date,
    TIMESTAMP_MICROS(event_timestamp) AS event_ts,
    event_name,
    SAFE_CAST((
      SELECT
        value.int_value
      FROM
        UNNEST(event_params)
      WHERE
        KEY = 'level_number' ) AS INT64) + 1 AS level_number,
    -- level +1 for dashboard
    SAFE_CAST((
      SELECT
        value.int_value
      FROM
        UNNEST(event_params)
      WHERE
        KEY = 'puzzle_number' ) AS INT64) AS puzzle_number,
    SAFE_CAST((
      SELECT
        value.int_value
      FROM
        UNNEST(event_params)
      WHERE
        KEY = 'number_of_successful_puzzles' ) AS INT64) AS number_of_successful_puzzles,
    (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'success_or_failure' ) AS raw_success_or_failure,
    geo.country AS country,
    LOWER(REGEXP_EXTRACT((
        SELECT
          value.string_value
        FROM
          UNNEST(event_params)
        WHERE
          KEY = 'page_location'), r'[?&]cr_lang=([^&]+)' )) AS app_language,
    (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'ftm_language') AS ftm_language,
    (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'version_number') AS app_version,
    (
    SELECT
      value.double_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'json_version_number') AS json_version,
    device.web_info.hostname AS hostname,
    -- ✅ APP NAME LOGIC (matches nightly query)
    CASE
      WHEN device.web_info.hostname = 'appassets.androidplatform.net' THEN 'WBS-standalone'
      WHEN REGEXP_CONTAINS(device.web_info.hostname, r'^([a-z-]+)-ftm-standalone\.androidplatform\.net$') THEN REGEXP_EXTRACT(device.web_info.hostname, r'^([a-z-]+)-ftm-standalone\.androidplatform\.net$') || '-standalone'
      ELSE 'CR'
  END
    AS app,
    user_pseudo_id,
    (
    SELECT
      value.string_value
    FROM
      UNNEST(event_params)
    WHERE
      KEY = 'cr_user_id') AS cr_user_id
  FROM
    `ftm-b9d99.analytics_159643920.events_*`
  WHERE
    _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY))
    AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
    AND ( (device.web_info.hostname LIKE 'feedthemonster.curiouscontent.org%'
        AND (
        SELECT
          value.string_value
        FROM
          UNNEST(event_params)
        WHERE
          KEY = 'page_location' ) LIKE '%https://feedthemonster.curiouscontent.org%')
      OR REGEXP_CONTAINS(device.web_info.hostname, r'^[a-z-]+-ftm-standalone\.androidplatform\.net$')
      OR device.web_info.hostname = 'appassets.androidplatform.net' )
    AND event_name IN ( 'session_start',
      'session_end',
      'download_completed',
      'tapped_start',
      'selected_level',
      'puzzle_completed',
      'level_completed' ) ),
  -- 🧠 Normalize success/failure logic
  normalized AS (
  SELECT
    *,
    CASE
      WHEN event_name = 'level_completed' AND SAFE_CAST(number_of_successful_puzzles AS INT64) >= 3 THEN 'success'
      ELSE raw_success_or_failure
  END
    AS success_or_failure
  FROM
    events ),
  -- 🧹 Deduplicate multiple level_completed events per user/level
  deduped_levels AS (
  SELECT
    ARRAY_AGG(n
    ORDER BY
      CASE
        WHEN n.success_or_failure = 'success' THEN 1
        ELSE 2
    END
      , n.event_ts ASC
    LIMIT
      1)[
  OFFSET
    (0)] AS ROW
  FROM
    normalized n
  WHERE
    n.event_name = 'level_completed'
  GROUP BY
    n.cr_user_id,
    n.level_number ),
  -- Combine deduped level events with all others
  combined AS (
  SELECT
    *
  FROM
    normalized
  WHERE
    event_name != 'level_completed'
  UNION ALL
  SELECT
    row.*
  FROM
    deduped_levels ),
  -- 🕒 Compute minutes between successful level completions
  success_intervals AS (
  SELECT
    cr_user_id,
    event_ts,
    level_number,
    ROUND( TIMESTAMP_DIFF( event_ts, LAG(event_ts) OVER (PARTITION BY cr_user_id ORDER BY event_ts ), SECOND ) / 60.0, 2 ) AS minutes_since_prev_success
  FROM
    combined
  WHERE
    event_name = 'level_completed'
    AND success_or_failure = 'success' ),
  -- 🧩 Merge timing data back into main events
  final_with_spans AS (
  SELECT
    c.*,
    si.minutes_since_prev_success
  FROM
    combined c
  LEFT JOIN
    success_intervals si
  USING
    (cr_user_id,
      event_ts,
      level_number) )
  -- ✅ Final output
  -- ✅ Final output
SELECT
  TO_HEX(MD5(CONCAT( CAST(UNIX_MICROS(event_ts) AS STRING), '|', COALESCE(cr_user_id, ''), '|', COALESCE(event_name, ''), '|', CAST(COALESCE(level_number, -1) AS STRING), '|', CAST(COALESCE(puzzle_number, -1) AS STRING) ))) AS row_id,
  event_date,
  event_ts,
  event_name,
  level_number,
  puzzle_number,
  number_of_successful_puzzles,
  success_or_failure,
  minutes_since_prev_success,
  country,
  app_language,
  ftm_language,
  hostname,
  -- 🔁 same app logic as cr_user_progress
  CASE
    WHEN hostname = 'appassets.androidplatform.net' THEN 'WBS-standalone'
    WHEN REGEXP_CONTAINS(hostname, r'^([a-z-]+)-ftm-standalone\.androidplatform\.net$') THEN REGEXP_EXTRACT(hostname, r'^([a-z-]+)-ftm-standalone\.androidplatform\.net$') || '-standalone'
    ELSE 'CR'
END
  AS app,
  user_pseudo_id,
  cr_user_id
FROM
  final_with_spans
WHERE
  cr_user_id IS NOT NULL
ORDER BY
  cr_user_id,
  event_ts;