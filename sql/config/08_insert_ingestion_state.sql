INSERT INTO
`${PROJECT_ID}.retail_dev_state.IngestionState`
(
  provider_id,
  layer,
  last_processed_event_time,
  max_event_time_seen,
  lookback_minutes,
  last_run_status,
  last_run_id,
  last_run_time,
  updated_at
)
VALUES
(
  'provider_retail',
  'SILVER',
  TIMESTAMP('1970-01-01 00:00:00 UTC'),
  TIMESTAMP('1970-01-01 00:00:00 UTC'),
  1440,
  'NEVER_RUN',
  NULL,
  NULL,
  CURRENT_TIMESTAMP()
);