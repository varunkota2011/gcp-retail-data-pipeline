CREATE TABLE IF NOT EXISTS
`${PROJECT_ID}.retail_dev_config.DataConfig`
(
  provider_id STRING NOT NULL,
  raw_path STRING NOT NULL,
  bronze_path STRING NOT NULL,
  silver_path STRING NOT NULL,
  quarantine_path STRING NOT NULL,

  file_format STRING NOT NULL,
  delimiter STRING,

  write_mode STRING NOT NULL,
  header BOOLEAN,

  ingestion_frequency STRING NOT NULL,
  active BOOLEAN NOT NULL,

  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);