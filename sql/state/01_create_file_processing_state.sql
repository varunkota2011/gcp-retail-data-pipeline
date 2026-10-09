CREATE TABLE IF NOT EXISTS
`varun2011-510908.retail_dev_state.FileProcessingState`
(
  provider_id STRING NOT NULL,
  source_uri STRING NOT NULL,
  source_file STRING NOT NULL,
  source_date DATE,
  source_checksum STRING NOT NULL,

  status STRING NOT NULL,

  run_id STRING,

  first_processed_at TIMESTAMP,
  last_processed_at TIMESTAMP,

  record_count INT64,
  valid_record_count INT64,
  rejected_record_count INT64,

  error_message STRING,

  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);