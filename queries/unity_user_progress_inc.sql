-- Declare rolling window for incremental update
DECLARE run_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY);
DECLARE run_end_date DATE DEFAULT CURRENT_DATE();

-- Step 1: Delete existing overlapping data
DELETE FROM `dataexploration-193817.user_data.unity_user_progress_inc`
WHERE first_open BETWEEN run_start_date AND run_end_date;

-- Step 2: Insert fresh data
INSERT INTO `dataexploration-193817.user_data.unity_user_progress_inc` (
  user_pseudo_id,
  app_id,
  first_open,
  country,
  app_language,
  max_user_level,
  max_game_level,
  app_version,
  la_date,
  furthest_event,
  gpc
)
WITH
  all_events_raw AS (
    SELECT * FROM `ftm-b9d99.analytics_159643920.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-afrikaans.analytics_177200876.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-hindi.analytics_174638281.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-brazilian-portuguese.analytics_161789655.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-english.analytics_152408808.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-french.analytics_173880465.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-isixhosa.analytics_180747962.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-kinayrwanda.analytics_177922191.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-oromo.analytics_167539175.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-swahili.analytics_160694316.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-somali.analytics_159630038.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-sepedi.analytics_180755978.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-zulu.analytics_155849122.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-southafricanenglish.analytics_173750850.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
    UNION ALL SELECT * FROM `ftm-spanish.analytics_158656398.events_*`
    WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
  ),

  all_events AS (
    SELECT
      DISTINCT(user_pseudo_id),
      app_info.id AS app_id,
      CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
      geo.country AS country,
      LOWER(REGEXP_EXTRACT(app_info.id, r'(?i)feedthemonster(.*)')) AS app_language,
      MIN(app_info.version) AS app_version,
      b.max_level AS max_game_level,
      MIN(
        CASE
          WHEN event_name = 'GamePlay' AND params.key = 'action'
            AND params.value.string_value LIKE 'LevelSuccess%'
          THEN PARSE_DATE('%Y%m%d', event_date)
          ELSE NULL
        END
      ) AS la_date,
      MAX(
        CASE
          WHEN event_name = 'GamePlay' AND params.key = 'action'
            AND params.value.string_value LIKE 'LevelSuccess%'
          THEN CAST(SUBSTR(params.value.string_value, (STRPOS(params.value.string_value, '_') + 1)) AS INT64)
          ELSE 0
        END
      ) AS max_user_level,
      SUM(CASE
          WHEN event_name = 'GamePlay' AND params.value.string_value LIKE 'LevelSuccess%' THEN 1
          ELSE 0
      END) AS level_completed_count,
      SUM(CASE
          WHEN event_name = 'GamePlay' AND params.value.string_value LIKE 'SegmentSuccess%' THEN 1
          ELSE 0
      END) AS puzzle_completed_count,
      SUM(CASE
          WHEN event_name = 'session_start' THEN 1
          ELSE 0
      END) AS session_start_count
    FROM
      all_events_raw a
    CROSS JOIN UNNEST(event_params) AS params
    LEFT JOIN (
      SELECT app_language, max_level
      FROM `dataexploration-193817.user_data.language_max_level`
      GROUP BY app_language, max_level
    ) b ON b.app_language = LOWER(REGEXP_EXTRACT(app_info.id, r'(?i)feedthemonster(.*)'))
    WHERE
      (
        (event_name = 'GamePlay' AND params.key = 'action'
          AND (params.value.string_value LIKE 'LevelSuccess%' OR params.value.string_value LIKE 'SegmentSuccess%'))
        OR event_name = 'session_start'
      )
      AND LOWER(app_info.id) LIKE '%feedthemonster%'
      AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE)
        BETWEEN run_start_date AND run_end_date
    GROUP BY
      user_pseudo_id,
      app_id,
      first_open,
      country,
      app_language,
      b.max_level
  )

SELECT
  user_pseudo_id,
  app_id,
  first_open,
  country,
  app_language,
  max_user_level,
  max_game_level,
  app_version,
  la_date,
  CASE
    WHEN level_completed_count > 0 THEN 'level_completed'
    WHEN puzzle_completed_count > 0 THEN 'puzzle_completed'
    WHEN session_start_count > 0 THEN 'session_start'
    ELSE NULL
  END AS furthest_event,
  SAFE_DIVIDE(MAX(max_user_level), max_game_level) * 100 AS gpc
FROM
  all_events
GROUP BY
  1, 2, 3, 4, 5, 6, 7, 8, 9, 10;
