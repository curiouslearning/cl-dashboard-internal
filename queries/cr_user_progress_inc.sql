DECLARE run_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY);
DECLARE run_end_date DATE DEFAULT CURRENT_DATE();

-- Delete existing rows for the range
DELETE FROM `dataexploration-193817.user_data.cr_user_progress_inc`
WHERE first_open BETWEEN run_start_date AND run_end_date;

-- Insert fresh data from last 3 days
INSERT INTO `dataexploration-193817.user_data.cr_user_progress_inc` (
  user_pseudo_id,
  cr_user_id,
  app_id,
  first_open,
  country,
  app_language,
  max_user_level,
  max_game_level,
  la_date,
  furthest_event,
  gpc
)
WITH
  all_events AS (
    SELECT
      user_pseudo_id,
      cr_user_id_params.value.string_value AS cr_user_id,
      "org.curiouslearning.container" AS app_id,
      CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open,
      geo.country AS country,
      LOWER(REGEXP_EXTRACT(app_params.value.string_value, '[?&]cr_lang=([^&]+)')) AS app_language,
      b.max_level AS max_game_level,
      MIN(
        CASE
          WHEN event_name = 'level_completed'
            AND success_params.key = 'success_or_failure'
            AND success_params.value.string_value = 'success'
            AND level_params.key = 'level_number'
          THEN PARSE_DATE('%Y%m%d', event_date)
          ELSE NULL
        END
      ) AS la_date,
      MAX(
        CASE
          WHEN event_name = 'level_completed'
            AND success_params.key = 'success_or_failure'
            AND success_params.value.string_value = 'success'
            AND level_params.key = 'level_number'
          THEN level_params.value.int_value + 1
          ELSE 0
        END
      ) AS max_user_level,
      SUM(CASE
          WHEN event_name = 'level_completed'
            AND success_params.key = 'success_or_failure'
            AND success_params.value.string_value = 'success'
            AND level_params.key = 'level_number'
          THEN 1 ELSE 0
      END) AS level_completed_count,
      SUM(CASE WHEN event_name = 'puzzle_completed' THEN 1 ELSE 0 END) AS puzzle_completed_count,
      SUM(CASE WHEN event_name = 'selected_level' THEN 1 ELSE 0 END) AS selected_level_count,
      SUM(CASE WHEN event_name = 'tapped_start' THEN 1 ELSE 0 END) AS tapped_start_count,
      SUM(CASE WHEN event_name = 'download_completed' THEN 1 ELSE 0 END) AS download_completed_count
    FROM
      `ftm-b9d99.analytics_159643920.events_*` AS a,
      UNNEST(event_params) AS app_params,
      UNNEST(event_params) AS success_params,
      UNNEST(event_params) AS level_params,
      UNNEST(event_params) AS cr_user_id_params
    LEFT JOIN (
      SELECT app_language, max_level
      FROM `dataexploration-193817.user_data.language_max_level`
      GROUP BY app_language, max_level
    ) b ON b.app_language = LOWER(REGEXP_EXTRACT(app_params.value.string_value, '[?&]cr_lang=([^&]+)'))
    WHERE
      _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date)
                      AND FORMAT_DATE('%Y%m%d', run_end_date)
      AND event_name IN (
        'download_completed',
        'tapped_start',
        'selected_level',
        'puzzle_completed',
        'level_completed'
      )
      AND app_params.key = 'page_location'
      AND app_params.value.string_value LIKE '%https://feedthemonster.curiouscontent.org%'
      AND device.web_info.hostname LIKE 'feedthemonster.curiouscontent.org%'
      AND cr_user_id_params.key = 'cr_user_id'
    GROUP BY
      user_pseudo_id,
      cr_user_id,
      app_id,
      first_open,
      country,
      app_language,
      b.max_level
  )
SELECT
  user_pseudo_id,
  cr_user_id,
  app_id,
  first_open,
  country,
  app_language,
  max_user_level,
  max_game_level,
  la_date,
  CASE
    WHEN level_completed_count > 0 THEN 'level_completed'
    WHEN puzzle_completed_count > 0 THEN 'puzzle_completed'
    WHEN selected_level_count > 0 THEN 'selected_level'
    WHEN tapped_start_count > 0 THEN 'tapped_start'
    WHEN download_completed_count > 0 THEN 'download_completed'
    ELSE NULL
  END AS furthest_event,
  SAFE_DIVIDE(MAX(max_user_level), max_game_level) * 100 AS gpc
FROM all_events
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10;
