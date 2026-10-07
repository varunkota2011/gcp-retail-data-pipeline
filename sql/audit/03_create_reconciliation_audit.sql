CREATE TABLE IF NOT EXISTS
`${PROJECT_ID}.retail_dev_audit.reconciliation_audit`
(
  run_id STRING NOT NULL,
  provider_id STRING NOT NULL,

  source_count INT64 NOT NULL,
  read_count INT64 NOT NULL,
  valid_count INT64 NOT NULL,
  rejected_count INT64 NOT NULL,
  target_count INT64 NOT NULL,

  reconciliation_status STRING NOT NULL,

  reconciliation_timestamp TIMESTAMP NOT NULL
);