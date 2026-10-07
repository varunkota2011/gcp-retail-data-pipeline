INSERT INTO
`${PROJECT_ID}.retail_dev_config.DataConfig`
(
  provider_id,
  raw_path,
  bronze_path,
  silver_path,
  quarantine_path,
  file_format,
  delimiter,
  write_mode,
  header,
  ingestion_frequency,
  active,
  created_at,
  updated_at
)
VALUES
(
  'provider_retail',

  'gs://varun2011-510908-retail-dev-raw/provider_retail/',
  'gs://varun2011-510908-retail-dev-bronze/provider_retail/',
  'gs://varun2011-510908-retail-dev-silver/provider_retail/',
  'gs://varun2011-510908-retail-dev-quarantine/provider_retail/',

  'CSV',
  ',',

  'APPEND',
  TRUE,

  'DAILY',
  TRUE,

  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);