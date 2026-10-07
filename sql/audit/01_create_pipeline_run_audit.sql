CREATE TABLE IF NOT EXISTS
`${PROJECT_ID}.retail_dev_audit.pipeline_run_audit`
(
  run_id STRING NOT NULL,
  pipeline_name STRING NOT NULL,
  environment STRING NOT NULL,
  provider_id STRING NOT NULL,

  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP,

  status STRING NOT NULL,

  source_file_count INT64,
  source_record_count INT64,

  valid_record_count INT64,
  rejected_record_count INT64,
  silver_record_count INT64,

  watermark_start TIMESTAMP,
  watermark_end TIMESTAMP,

  error_message STRING,

  created_at TIMESTAMP NOT NULL
);