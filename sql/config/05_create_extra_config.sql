CREATE TABLE IF NOT EXISTS
`${PROJECT_ID}.retail_dev_config.ExtraConfig`
(
  provider_id STRING NOT NULL,
  rule_name STRING NOT NULL,

  rule_type STRING NOT NULL,
  rule_condition STRING NOT NULL,

  severity STRING NOT NULL,

  active BOOLEAN NOT NULL,

  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);