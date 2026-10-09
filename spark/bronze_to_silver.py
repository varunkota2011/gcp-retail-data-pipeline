from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import argparse
import re


SOURCE_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


def create_spark_session():
    return (
        SparkSession.builder
        .appName("retail-bronze-to-silver")
        .getOrCreate()
    )


def transform_bronze_to_silver(
    spark,
    input_path,
    output_path,
    pipeline_run_id,
    source_checksum,
):
    print("=" * 70)
    print("BRONZE → SILVER")
    print("=" * 70)

    print(f"Input path     : {input_path}")
    print(f"Output path    : {output_path}")
    print(f"Run ID         : {pipeline_run_id}")
    print(f"Source checksum: {source_checksum}")

    # ------------------------------------------------------------
    # Extract source filename
    # ------------------------------------------------------------
    source_file = input_path.rstrip("/").split("/")[-1]

    print(f"Source file    : {source_file}")

    # ------------------------------------------------------------
    # 1. Read Bronze
    # ------------------------------------------------------------
    print("\n[1/8] Reading Bronze...")

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "false")
        .csv(input_path)
    )

    source_count = df.count()

    print(f"Bronze records read: {source_count}")

    # ------------------------------------------------------------
    # 2. Validate source schema
    # ------------------------------------------------------------
    print("\n[2/8] Applying source schema...")

    missing_columns = [
        column
        for column in SOURCE_COLUMNS
        if column not in df.columns
    ]

    unexpected_columns = [
        column
        for column in df.columns
        if column not in SOURCE_COLUMNS
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if unexpected_columns:
        print(
            f"WARNING: Unexpected columns ignored: "
            f"{unexpected_columns}"
        )

    df = df.select(*SOURCE_COLUMNS)

    # ------------------------------------------------------------
    # 3. Cast data types
    # ------------------------------------------------------------
    print("\n[3/8] Casting data types...")

    df = (
        df
        .withColumn(
            "InvoiceNo",
            F.col("InvoiceNo").cast("string"),
        )
        .withColumn(
            "StockCode",
            F.col("StockCode").cast("string"),
        )
        .withColumn(
            "Description",
            F.col("Description").cast("string"),
        )
        .withColumn(
            "Quantity",
            F.col("Quantity").cast("long"),
        )
        .withColumn(
            "InvoiceDate",
            F.to_timestamp(F.col("InvoiceDate")),
        )
        .withColumn(
            "UnitPrice",
            F.col("UnitPrice").cast("double"),
        )
        .withColumn(
            "CustomerID",
            F.col("CustomerID").cast("string"),
        )
        .withColumn(
            "Country",
            F.col("Country").cast("string"),
        )
    )

    # ------------------------------------------------------------
    # 4. Create deterministic row hash
    # ------------------------------------------------------------
    print("\n[4/8] Creating row hash...")

    hash_columns = [
        F.coalesce(F.col("InvoiceNo"), F.lit("")),
        F.coalesce(F.col("StockCode"), F.lit("")),
        F.coalesce(F.col("Description"), F.lit("")),
        F.coalesce(
            F.col("Quantity").cast("string"),
            F.lit(""),
        ),
        F.coalesce(
            F.date_format(
                F.col("InvoiceDate"),
                "yyyy-MM-dd HH:mm:ss",
            ),
            F.lit(""),
        ),
        F.coalesce(
            F.col("UnitPrice").cast("string"),
            F.lit(""),
        ),
        F.coalesce(F.col("CustomerID"), F.lit("")),
        F.coalesce(F.col("Country"), F.lit("")),
    ]

    df = df.withColumn(
        "_row_hash",
        F.sha2(
            F.concat_ws("||", *hash_columns),
            256,
        ),
    )

    # ------------------------------------------------------------
    # 5. Remove exact duplicates
    # ------------------------------------------------------------
    print("\n[5/8] Removing exact duplicate rows...")

    before_dedup = df.count()

    df = df.dropDuplicates(["_row_hash"])

    after_dedup = df.count()

    duplicate_count = before_dedup - after_dedup

    print(f"Before dedup : {before_dedup}")
    print(f"After dedup  : {after_dedup}")
    print(f"Duplicates   : {duplicate_count}")

    # ------------------------------------------------------------
    # 6. Derived + masked columns
    # ------------------------------------------------------------
    print("\n[6/8] Creating derived and masked columns...")

    df = (
        df
        .withColumn(
            "LineAmount",
            F.round(
                F.col("Quantity") * F.col("UnitPrice"),
                2,
            ),
        )
        .withColumn(
            "IsCancellation",
            F.upper(
                F.substring(
                    F.col("InvoiceNo"),
                    1,
                    1,
                )
            ) == F.lit("C"),
        )
        .withColumn(
            "CustomerID",
            F.when(
                F.col("CustomerID").isNotNull(),
                F.sha2(
                    F.col("CustomerID"),
                    256,
                ),
            ).otherwise(F.lit(None)),
        )
    )

    # ------------------------------------------------------------
    # 7. Technical lineage columns
    # ------------------------------------------------------------
    print("\n[7/8] Adding lineage metadata...")

    df = (
    df
    .withColumn("SourceFile", F.lit(source_file))
    .withColumn(
        "SourceDate",
        F.to_date(F.col("InvoiceDate")).cast("date"),
    )
    .withColumn("SourceChecksum", F.lit(source_checksum))
    .withColumn("PipelineRunID", F.lit(pipeline_run_id))
    .withColumn("ProcessedAt", F.current_timestamp())
    )

    # ------------------------------------------------------------
    # 8. Final Silver projection
    # ------------------------------------------------------------
    print("\n[8/8] Writing Silver...")

    silver_df = df.select(
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
        "LineAmount",
        "IsCancellation",
        "SourceFile",
        "SourceDate",
        "SourceChecksum",
        "PipelineRunID",
        "ProcessedAt",
    )

    final_count = silver_df.count()

    print(f"Final Silver records: {final_count}")

    (
        silver_df
        .write
        .option("partitionOverwriteMode", "dynamic")
        .mode("overwrite")
        .partitionBy("SourceDate")
        .parquet(output_path)
    )

    print("=" * 70)
    print("BRONZE → SILVER COMPLETED")
    print("=" * 70)

    return {
        "source_count": source_count,
        "deduplicated_count": after_dedup,
        "duplicate_count": duplicate_count,
        "silver_count": final_count,
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True,
        help="Bronze input path",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Silver output path",
    )

    parser.add_argument(
        "--run-id",
        required=True,
        help="Pipeline run ID",
    )

    parser.add_argument(
        "--source-checksum",
        required=True,
        help="SHA-256 checksum of the original source file",
    )

    args = parser.parse_args()

    spark = create_spark_session()

    try:
        transform_bronze_to_silver(
            spark=spark,
            input_path=args.input,
            output_path=args.output,
            pipeline_run_id=args.run_id,
            source_checksum=args.source_checksum,
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()