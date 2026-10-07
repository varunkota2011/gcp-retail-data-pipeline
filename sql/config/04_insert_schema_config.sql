INSERT INTO
`${PROJECT_ID}.retail_dev_config.SchemaConfig`
(
  provider_id,
  table_name,
  column_name,
  column_order,
  data_type,
  nullable,
  description,
  active,
  created_at,
  updated_at
)
VALUES
('provider_retail', 'retail_sales', 'InvoiceNo',    1, 'STRING',    FALSE, 'Invoice transaction identifier', TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('provider_retail', 'retail_sales', 'StockCode',    2, 'STRING',    FALSE, 'Product identifier',             TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('provider_retail', 'retail_sales', 'Description',  3, 'STRING',    TRUE,  'Product description',             TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('provider_retail', 'retail_sales', 'Quantity',     4, 'INT64',     FALSE, 'Number of units',                 TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('provider_retail', 'retail_sales', 'InvoiceDate',  5, 'TIMESTAMP', FALSE, 'Transaction timestamp',           TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('provider_retail', 'retail_sales', 'UnitPrice',    6, 'FLOAT64',   FALSE, 'Unit price',                      TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('provider_retail', 'retail_sales', 'CustomerID',   7, 'STRING',    TRUE,  'Customer identifier',             TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()),
('provider_retail', 'retail_sales', 'Country',      8, 'STRING',    FALSE, 'Customer country',                TRUE, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP());