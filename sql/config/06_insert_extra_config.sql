INSERT INTO
`${PROJECT_ID}.retail_dev_config.ExtraConfig`
(
  provider_id,
  rule_name,
  rule_type,
  rule_condition,
  severity,
  active,
  created_at,
  updated_at
)
VALUES
(
  'provider_retail',
  'required_invoice_no',
  'VALIDATION',
  'InvoiceNo IS NOT NULL',
  'ERROR',
  TRUE,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
),

(
  'provider_retail',
  'required_stock_code',
  'VALIDATION',
  'StockCode IS NOT NULL',
  'ERROR',
  TRUE,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
),

(
  'provider_retail',
  'positive_quantity',
  'VALIDATION',
  'Quantity > 0',
  'ERROR',
  TRUE,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
),

(
  'provider_retail',
  'positive_unit_price',
  'VALIDATION',
  'UnitPrice >= 0',
  'ERROR',
  TRUE,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
),

(
  'provider_retail',
  'valid_invoice_date',
  'VALIDATION',
  'InvoiceDate IS NOT NULL',
  'ERROR',
  TRUE,
  CURRENT_TIMESTAMP(),
  CURRENT_TIMESTAMP()
);