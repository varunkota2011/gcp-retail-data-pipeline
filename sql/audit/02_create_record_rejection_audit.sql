CREATE TABLE IF NOT EXISTS
`${PROJECT_ID}.retail_dev_audit.record_rejection_audit`
(
  run_id STRING NOT NULL,
  provider_id STRING NOT NULL,

  source_file STRING NOT NULL,
  record_identifier STRING,

  rule_name STRING NOT NULL,
  rejection_reason STRING NOT NULL,

  rejected_at TIMESTAMP NOT NULL,

  environment STRING NOT NULL
);