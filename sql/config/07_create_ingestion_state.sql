CREATE TABLE IF NOT EXISTS
`${PROJECT_ID}.retail_dev_state.IngestionState`
(
  provider_id STRING NOT NULL,
  layer STRING NOT NULL,

  last_processed_event_time TIMESTAMP,
  max_event_time_seen TIMESTAMP,

  lookback_minutes INT64 NOT NULL,

  last_run_status STRING NOT NULL,
  last_run_id STRING,

  last_run_time TIMESTAMP,

  updated_at TIMESTAMP NOT NULL
);