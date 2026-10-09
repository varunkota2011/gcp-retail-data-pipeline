from pathlib import Path
import hashlib
import pandas as pd


# ============================================================
# Configuration
# ============================================================

SOURCE_DIR = Path("prepared_source")

MANIFEST_FILE = (
    SOURCE_DIR / "source_manifest.csv"
)

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
# SHA-256
# ============================================================

def calculate_sha256(file_path: Path) -> str:

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


# ============================================================
# Validate one source file
# ============================================================

def validate_file(
    file_path: Path,
    expected_count: int,
    expected_checksum: str,
    expected_date: str,
) -> None:

    df = pd.read_csv(
        file_path,
        dtype="string",
    )

    # --------------------------------------------------------
    # Schema validation
    # --------------------------------------------------------

    actual_columns = list(df.columns)

    if actual_columns != EXPECTED_COLUMNS:

        raise ValueError(
            f"Schema mismatch: {file_path}\n"
            f"Expected: {EXPECTED_COLUMNS}\n"
            f"Actual:   {actual_columns}"
        )

    # --------------------------------------------------------
    # Record count validation
    # --------------------------------------------------------

    actual_count = len(df)

    if actual_count != expected_count:

        raise ValueError(
            f"Record count mismatch: {file_path}\n"
            f"Expected: {expected_count}\n"
            f"Actual:   {actual_count}"
        )

    # --------------------------------------------------------
    # Check InvoiceDate
    # --------------------------------------------------------

    invoice_dates = pd.to_datetime(
        df["InvoiceDate"],
        errors="coerce",
    )

    if invoice_dates.isna().any():

        raise ValueError(
            f"Invalid InvoiceDate found: {file_path}"
        )

    # --------------------------------------------------------
    # Validate partition date
    # --------------------------------------------------------

    actual_dates = (
        invoice_dates
        .dt.strftime("%Y-%m-%d")
        .unique()
    )

    if len(actual_dates) != 1:

        raise ValueError(
            f"Multiple InvoiceDate dates found "
            f"in partition: {file_path}\n"
            f"Dates: {actual_dates}"
        )

    if actual_dates[0] != expected_date:

        raise ValueError(
            f"Partition date mismatch: {file_path}\n"
            f"Expected: {expected_date}\n"
            f"Actual:   {actual_dates[0]}"
        )

    # --------------------------------------------------------
    # Validate checksum
    # --------------------------------------------------------

    actual_checksum = calculate_sha256(
        file_path
    )

    if actual_checksum != expected_checksum:

        raise ValueError(
            f"Checksum mismatch: {file_path}"
        )


# ============================================================
# Main validation
# ============================================================

def main():

    if not MANIFEST_FILE.exists():

        raise FileNotFoundError(
            f"Manifest not found: "
            f"{MANIFEST_FILE}"
        )

    manifest = pd.read_csv(
        MANIFEST_FILE
    )

    print(
        f"Manifest contains "
        f"{len(manifest):,} files"
    )

    total_records = 0

    for _, row in manifest.iterrows():

        file_path = (
            SOURCE_DIR
            / row["relative_path"]
        )

        if not file_path.exists():

            raise FileNotFoundError(
                f"Source file missing: "
                f"{file_path}"
            )

        validate_file(
            file_path=file_path,
            expected_count=int(
                row["record_count"]
            ),
            expected_checksum=row["sha256"],
            expected_date=row["source_date"],
        )

        total_records += int(
            row["record_count"]
        )

    # --------------------------------------------------------
    # Final reconciliation
    # --------------------------------------------------------

    manifest_total = int(
        manifest["record_count"].sum()
    )

    if total_records != manifest_total:

        raise ValueError(
            "Manifest reconciliation failed."
        )

    print()
    print("=" * 70)
    print("SOURCE VALIDATION PASSED")
    print("=" * 70)
    print(f"Files validated : {len(manifest):,}")
    print(f"Records         : {total_records:,}")
    print("=" * 70)


if __name__ == "__main__":
    main()