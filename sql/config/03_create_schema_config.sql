CREATE TABLE IF NOT EXISTS
`${PROJECT_ID}.retail_dev_config.SchemaConfig`
(
  provider_id STRING NOT NULL,
  table_name STRING NOT NULL,
  column_name STRING NOT NULL,

  column_order INT64 NOT NULL,
  data_type STRING NOT NULL,

  nullable BOOLEAN NOT NULL,
  description STRING,

  active BOOLEAN NOT NULL,

  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);