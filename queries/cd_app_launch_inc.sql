-- Declare rolling window for incremental update
DECLARE run_start_date DATE DEFAULT DATE_SUB(CURRENT_DATE(), INTERVAL 3 DAY);
DECLARE run_end_date DATE DEFAULT CURRENT_DATE();

-- Step 1: Delete existing overlapping data
DELETE FROM `dataexploration-193817.user_data.cr_app_launch_inc`
WHERE first_open BETWEEN run_start_date AND run_end_date;

-- Step 2: Insert fresh data
INSERT INTO `dataexploration-193817.user_data.cr_app_launch_inc` (
  user_pseudo_id,
  cr_user_id,
  country,
  app_id,
  app_language,
  first_open
)
SELECT
  user_pseudo_id,
  cr_user_id_params.value.string_value AS cr_user_id,
  geo.country AS country,
  app_info.id AS app_id,
  LOWER(REGEXP_EXTRACT(language_params.value.string_value, '[?&]cr_lang=([^&]+)')) AS app_language,
  CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE) AS first_open
FROM
  `ftm-b9d99.analytics_159643920.events_*` AS A
  , UNNEST(event_params) AS language_params
  , UNNEST(event_params) AS cr_user_id_params
WHERE
  _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', run_start_date) AND FORMAT_DATE('%Y%m%d', run_end_date)
  AND app_info.id = 'org.curiouslearning.container'
  AND language_params.value.string_value LIKE 'https://feedthemonster.curiouscontent.org%'
  AND event_name = 'app_launch'
  AND language_params.key = 'web_app_url'
  AND cr_user_id_params.key = 'cr_user_id'
  AND CAST(DATE(TIMESTAMP_MICROS(user_first_touch_timestamp)) AS DATE)
      BETWEEN run_start_date AND run_end_date
GROUP BY
  1, 2, 3, 4, 5, 6;
