import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


# ============================================================
# Configuration
# ============================================================

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

REQUIRED_COLUMNS = {
    "InvoiceNo",
    "StockCode",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "Country",
}


# ============================================================
# Validation Result
# ============================================================

@dataclass
class ValidationResult:
    input_file: str
    total_records: int
    valid_records: int
    rejected_records: int
    file_valid: bool
    file_error: Optional[str] = None


# ============================================================
# File Reading
# ============================================================

def read_csv(input_file: Path) -> pd.DataFrame:
    """
    Read a source CSV while preserving identifier columns as strings.
    """

    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file does not exist: {input_file}"
        )

    try:
        return pd.read_csv(
            input_file,
            dtype={
                "InvoiceNo": "string",
                "StockCode": "string",
                "Description": "string",
                "CustomerID": "string",
                "Country": "string",
            },
        )

    except Exception as exc:
        raise RuntimeError(
            f"Unable to read CSV '{input_file}': {exc}"
        ) from exc


# ============================================================
# Schema Validation
# ============================================================

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate that the incoming file matches the expected schema.

    Raises:
        ValueError: if columns are missing or unexpected.
    """

    actual_columns = list(df.columns)

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in actual_columns
    ]

    unexpected_columns = [
        column
        for column in actual_columns
        if column not in EXPECTED_COLUMNS
    ]

    if missing_columns:
        raise ValueError(
            f"Missing expected columns: {missing_columns}"
        )

    if unexpected_columns:
        raise ValueError(
            f"Unexpected columns found: {unexpected_columns}"
        )


# ============================================================
# Type Conversion
# ============================================================

def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert source fields into the expected logical data types.

    Invalid numeric values become NaN.
    Invalid timestamps become NaT.
    """

    df = df.copy()

    df["Quantity"] = pd.to_numeric(
        df["Quantity"],
        errors="coerce",
    )

    df["UnitPrice"] = pd.to_numeric(
        df["UnitPrice"],
        errors="coerce",
    )

    df["InvoiceDate"] = pd.to_datetime(
        df["InvoiceDate"],
        errors="coerce",
    )

    return df


# ============================================================
# Rejection Reason Handling
# ============================================================

def add_rejection_reason(
    rejection_reasons: pd.Series,
    mask: pd.Series,
    reason: str,
) -> pd.Series:
    """
    Add a validation reason without overwriting
    previously detected reasons.
    """

    rejection_reasons = rejection_reasons.copy()

    rejection_reasons.loc[mask] = rejection_reasons.loc[mask].apply(
        lambda current: (
            reason
            if current == ""
            else f"{current};{reason}"
        )
    )

    return rejection_reasons


# ============================================================
# Record Validation
# ============================================================

def validate_records(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply record-level data-quality rules.

    Returns:
        valid_df
        rejected_df
    """

    rejection_reasons = pd.Series(
        "",
        index=df.index,
        dtype="string",
    )

    # --------------------------------------------------------
    # Required InvoiceNo
    # --------------------------------------------------------

    mask = (
        df["InvoiceNo"].isna()
        | df["InvoiceNo"].str.strip().eq("")
    )

    rejection_reasons = add_rejection_reason(
        rejection_reasons,
        mask,
        "required_invoice_no",
    )

    # --------------------------------------------------------
    # Required StockCode
    # --------------------------------------------------------

    mask = (
        df["StockCode"].isna()
        | df["StockCode"].str.strip().eq("")
    )

    rejection_reasons = add_rejection_reason(
        rejection_reasons,
        mask,
        "required_stock_code",
    )

    # --------------------------------------------------------
    # Valid Quantity
    #
    # Normal transaction:
    #     Quantity > 0
    #
    # Cancellation:
    #     InvoiceNo starts with C
    # --------------------------------------------------------

    quantity_invalid = (
        df["Quantity"].isna()
        | (
            (df["Quantity"] <= 0)
            & ~df["InvoiceNo"]
            .fillna("")
            .str.startswith("C")
        )
    )

    rejection_reasons = add_rejection_reason(
        rejection_reasons,
        quantity_invalid,
        "valid_quantity",
    )

    # --------------------------------------------------------
    # Valid UnitPrice
    # --------------------------------------------------------

    mask = (
        df["UnitPrice"].isna()
        | (df["UnitPrice"] < 0)
    )

    rejection_reasons = add_rejection_reason(
        rejection_reasons,
        mask,
        "positive_unit_price",
    )

    # --------------------------------------------------------
    # Valid InvoiceDate
    # --------------------------------------------------------

    mask = df["InvoiceDate"].isna()

    rejection_reasons = add_rejection_reason(
        rejection_reasons,
        mask,
        "valid_invoice_date",
    )

    # --------------------------------------------------------
    # Required Country
    # --------------------------------------------------------

    mask = (
        df["Country"].isna()
        | df["Country"].str.strip().eq("")
    )

    rejection_reasons = add_rejection_reason(
        rejection_reasons,
        mask,
        "required_country",
    )

    # --------------------------------------------------------
    # Split records
    # --------------------------------------------------------

    rejected_mask = rejection_reasons.ne("")

    valid_mask = ~rejected_mask

    valid_df = df.loc[valid_mask].copy()

    rejected_df = df.loc[rejected_mask].copy()

    # --------------------------------------------------------
    # Add rejection metadata
    # --------------------------------------------------------

    if not rejected_df.empty:

        rejected_df.insert(
            0,
            "record_number",
            rejected_df.index + 2,
        )

        rejected_df.insert(
            1,
            "record_identifier",
            rejected_df["InvoiceNo"]
            .fillna("UNKNOWN")
            .astype(str),
        )

        rejected_df.insert(
            2,
            "rejection_reason",
            rejection_reasons.loc[
                rejected_mask
            ].values,
        )

    return valid_df, rejected_df


# ============================================================
# Output Writer
# ============================================================

def write_outputs(
    input_file: Path,
    output_dir: Path,
    valid_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
) -> None:
    """
    Write valid and rejected records.
    """

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    valid_file = (
        output_dir
        / f"{input_file.stem}_valid.csv"
    )

    rejected_file = (
        output_dir
        / f"{input_file.stem}_rejected.csv"
    )

    valid_df.to_csv(
        valid_file,
        index=False,
    )

    if not rejected_df.empty:

        rejected_df.to_csv(
            rejected_file,
            index=False,
        )

    print(
        f"Valid output    : {valid_file}"
    )

    if not rejected_df.empty:

        print(
            f"Rejected output : {rejected_file}"
        )

    else:

        print(
            "Rejected output : None"
        )


# ============================================================
# Main Validation Engine
# ============================================================

def validate_file(
    input_file: Path,
    output_dir: Path,
) -> ValidationResult:

    print("=" * 70)
    print("RAW FILE VALIDATION")
    print("=" * 70)

    print(
        f"Input file : {input_file}"
    )

    try:

        # ----------------------------------------------------
        # Read
        # ----------------------------------------------------

        df = read_csv(input_file)

        print(
            f"Records read: {len(df):,}"
        )

        # ----------------------------------------------------
        # File-level validation
        # ----------------------------------------------------

        validate_schema(df)

        # ----------------------------------------------------
        # Force expected column order
        # ----------------------------------------------------

        df = df[EXPECTED_COLUMNS]

        # ----------------------------------------------------
        # Type conversion
        # ----------------------------------------------------

        df = convert_data_types(df)

        # ----------------------------------------------------
        # Record-level validation
        # ----------------------------------------------------

        valid_df, rejected_df = validate_records(df)

        # ----------------------------------------------------
        # Outputs
        # ----------------------------------------------------

        write_outputs(
            input_file,
            output_dir,
            valid_df,
            rejected_df,
        )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        result = ValidationResult(
            input_file=str(input_file),
            total_records=len(df),
            valid_records=len(valid_df),
            rejected_records=len(rejected_df),
            file_valid=True,
        )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        print()
        print("-" * 70)
        print("VALIDATION SUMMARY")
        print("-" * 70)

        print(
            f"Total records   : {result.total_records:,}"
        )

        print(
            f"Valid records   : {result.valid_records:,}"
        )

        print(
            f"Rejected records: {result.rejected_records:,}"
        )

        if not rejected_df.empty:

            print()
            print("Rejection reasons:")

            reason_counts = (
                rejected_df["rejection_reason"]
                .str.split(";")
                .explode()
                .value_counts()
            )

            for reason, count in reason_counts.items():

                print(
                    f"  {reason}: {count:,}"
                )

        print("=" * 70)

        return result

    except Exception as exc:

        print()
        print("-" * 70)
        print("FILE VALIDATION FAILED")
        print("-" * 70)

        print(
            f"Error: {exc}"
        )

        print("=" * 70)

        return ValidationResult(
            input_file=str(input_file),
            total_records=0,
            valid_records=0,
            rejected_records=0,
            file_valid=False,
            file_error=str(exc),
        )


# ============================================================
# CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Validate a RAW retail CSV file."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input CSV file",
    )

    parser.add_argument(
        "--output-dir",
        default="validation_output",
        help=(
            "Directory for validation outputs"
        ),
    )

    args = parser.parse_args()

    result = validate_file(
        Path(args.input),
        Path(args.output_dir),
    )

    # --------------------------------------------------------
    # Exit codes
    #
    # 0 = validation completed
    # 1 = file-level validation failure
    # --------------------------------------------------------

    if not result.file_valid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()