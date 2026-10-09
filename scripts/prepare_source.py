from pathlib import Path
import hashlib
import pandas as pd


# ============================================================
# Configuration
# ============================================================

INPUT_FILE = Path("online_retail_source.xlsx")

OUTPUT_DIR = Path("prepared_source")

EXPECTED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


# ============================================================
# SHA-256 checksum
# ============================================================

def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# Read source
# ============================================================

def read_source() -> pd.DataFrame:

    print(f"Reading source: {INPUT_FILE}")

    df = pd.read_excel(
        INPUT_FILE,
        sheet_name="Online Retail",
        engine="openpyxl",
    )

    print(f"Rows read: {len(df):,}")
    print(f"Columns read: {list(df.columns)}")

    return df


# ============================================================
# Validate source schema
# ============================================================

def validate_source_schema(df: pd.DataFrame) -> None:

    actual_columns = list(df.columns)

    if actual_columns != EXPECTED_COLUMNS:

        raise ValueError(
            "Source schema does not match expected schema.\n"
            f"Expected: {EXPECTED_COLUMNS}\n"
            f"Actual:   {actual_columns}"
        )

    print("Source schema validation: PASSED")


# ============================================================
# Standardize data types
# ============================================================

def standardize_data(df: pd.DataFrame) -> pd.DataFrame:

    # Identifiers remain strings.
    df["InvoiceNo"] = df["InvoiceNo"].astype("string")
    df["StockCode"] = df["StockCode"].astype("string")
    df["CustomerID"] = (
        df["CustomerID"]
        .astype("Int64")
        .astype("string")
    )

    # Text columns.
    df["Description"] = df["Description"].astype("string")
    df["Country"] = df["Country"].astype("string")

    # Numeric columns.
    df["Quantity"] = pd.to_numeric(
        df["Quantity"],
        errors="raise",
    ).astype("Int64")

    df["UnitPrice"] = pd.to_numeric(
        df["UnitPrice"],
        errors="raise",
    ).astype("float64")

    # Timestamp.
    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"],
        errors="raise",
    )

    return df


# ============================================================
# Create daily source files
# ============================================================

def create_daily_files(df: pd.DataFrame) -> list[dict]:

    manifest_records = []

    df["source_date"] = df["InvoiceDate"].dt.strftime(
        "%Y-%m-%d"
    )

    for source_date, daily_df in df.groupby(
        "source_date",
        sort=True,
    ):

        daily_df = daily_df[
            EXPECTED_COLUMNS
        ].copy()

        date_obj = pd.to_datetime(source_date)

        date_path = (
            OUTPUT_DIR
            / "provider_retail"
            / source_date
        )

        date_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = (
            date_path
            / f"retail_sales_{date_obj.strftime('%Y%m%d')}.csv"
        )

        daily_df.to_csv(
            output_file,
            index=False,
            encoding="utf-8",
        )

        checksum = calculate_sha256(
            output_file
        )

        manifest_records.append(
            {
                "provider_id": "provider_retail",
                "source_date": source_date,
                "file_name": output_file.name,
                "relative_path": str(
                    output_file.relative_to(
                        OUTPUT_DIR
                    )
                ).replace("\\", "/"),
                "record_count": len(daily_df),
                "sha256": checksum,
            }
        )

        print(
            f"Created {output_file} "
            f"({len(daily_df):,} records)"
        )

    return manifest_records


# ============================================================
# Create source manifest
# ============================================================

def create_manifest(
    records: list[dict],
) -> None:

    manifest = pd.DataFrame(records)

    manifest_file = (
        OUTPUT_DIR / "source_manifest.csv"
    )

    manifest.to_csv(
        manifest_file,
        index=False,
        encoding="utf-8",
    )

    print()
    print(
        f"Manifest created: {manifest_file}"
    )

    print(
        f"Files generated: {len(manifest):,}"
    )

    print(
        "Records represented by manifest: "
        f"{manifest['record_count'].sum():,}"
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found: "
            f"{INPUT_FILE.resolve()}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = read_source()

    validate_source_schema(df)

    df = standardize_data(df)

    records = create_daily_files(df)

    create_manifest(records)

    print()
    print("=" * 70)
    print("SOURCE PREPARATION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()