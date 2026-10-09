import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from file_processing_state import FileProcessingState


FILENAME_PATTERN = re.compile(
    r"^retail_sales_(\d{4})(\d{2})(\d{2})\.csv$"
)


def run_command(command):
    """Run a command and raise an error if it fails."""

    if command and command[0] == "gcloud" and os.name == "nt":
        command[0] = "gcloud.cmd"

    print(f"Running: {' '.join(command)}")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            f"{' '.join(command)}"
        )

    return result


def validate_source_filename(source_file):
    """Extract YYYY/MM/DD from the expected source filename."""

    filename = Path(source_file).name

    match = FILENAME_PATTERN.match(filename)

    if not match:
        raise ValueError(
            f"Unexpected source filename: {filename}. "
            f"Expected format: retail_sales_YYYYMMDD.csv"
        )

    year, month, day = match.groups()

    return year, month, day


def calculate_sha256(file_path):
    """Calculate SHA-256 checksum for a local file."""

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def validate_with_existing_validator(input_file, output_dir):
    """
    Run validate_raw.py and return its result without raising.

    A non-zero return code represents a data/file validation outcome
    that this orchestration layer must handle.
    """

    validator = Path("scripts") / "validate_raw.py"

    command = [
        sys.executable,
        str(validator),
        "--input",
        str(input_file),
        "--output-dir",
        str(output_dir),
    ]

    print(f"Running: {' '.join(command)}")

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    return result


def count_csv_records(file_path):
    """Count data records excluding the CSV header."""

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return max(sum(1 for _ in file) - 1, 0)


def process_file(
    provider,
    source_uri,
    bronze_path,
    quarantine_path,
):
    source_filename = Path(source_uri).name

    run_id = str(uuid.uuid4())

    state = FileProcessingState()

    checksum = None
    file_validation_failed = False

    print("=" * 70)
    print("RAW FILE PROCESSING")
    print("=" * 70)
    print(f"Run ID         : {run_id}")
    print(f"Provider       : {provider}")
    print(f"Source file    : {source_filename}")
    print(f"Source URI     : {source_uri}")
    print(f"Bronze path    : {bronze_path}")
    print(f"Quarantine path: {quarantine_path}")
    print()

    year, month, day = validate_source_filename(source_filename)

    source_date = f"{year}-{month}-{day}"

    print(f"Source date    : {source_date}")

    bronze_date_path = (
        f"{bronze_path.rstrip('/')}/{year}/{month}/{day}/"
    )

    quarantine_date_path = (
        f"{quarantine_path.rstrip('/')}/{year}/{month}/{day}/"
    )

    print(f"Bronze target  : {bronze_date_path}")
    print(f"Quarantine target: {quarantine_date_path}")
    print()

    temp_root = Path(
        tempfile.mkdtemp(
            prefix="retail_pipeline_"
        )
    )

    source_local = temp_root / source_filename
    validation_dir = temp_root / "validation"

    try:
        # ------------------------------------------------------------
        # 1. Download RAW file
        # ------------------------------------------------------------

        print("[1/7] Downloading RAW file...")

        run_command(
            [
                "gcloud",
                "storage",
                "cp",
                source_uri,
                str(source_local),
            ]
        )

        if not source_local.exists():
            raise FileNotFoundError(
                f"Downloaded file not found: {source_local}"
            )

        # ------------------------------------------------------------
        # 2. Calculate checksum
        # ------------------------------------------------------------

        print("[2/7] Calculating SHA-256 checksum...")

        checksum = calculate_sha256(source_local)

        print(f"SHA-256       : {checksum}")

        # ------------------------------------------------------------
        # 3. Idempotency check
        # ------------------------------------------------------------

        print("[3/7] Checking FileProcessingState...")

        existing_state = state.get_state(
            provider_id=provider,
            source_uri=source_uri,
            source_checksum=checksum,
        )

        if existing_state:
            print(
                f"Existing state : {existing_state['status']}"
            )

            if existing_state["status"] == "SUCCESS":
                print()
                print("=" * 70)
                print("IDEMPOTENCY CHECK")
                print("=" * 70)
                print("Same source URI + same checksum + SUCCESS.")
                print("ACTION         : SKIP")
                print("=" * 70)

                return

            print(
                "Existing state is not SUCCESS. "
                "File will be processed again."
            )
        else:
            print("No existing state found. File is NEW.")

        # ------------------------------------------------------------
        # 4. Mark file as PROCESSING
        # ------------------------------------------------------------

        print("[4/7] Marking file as PROCESSING...")

        state.upsert_processing_state(
            provider_id=provider,
            source_uri=source_uri,
            source_file=source_filename,
            source_date=source_date,
            source_checksum=checksum,
            run_id=run_id,
            status="PROCESSING",
        )

        print("File state: PROCESSING")

        # ------------------------------------------------------------
        # 5. Validate source file
        # ------------------------------------------------------------

        print("[5/7] Validating source file...")

        validation_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        validation_result = validate_with_existing_validator(
            source_local,
            validation_dir,
        )

        if validation_result.returncode != 0:

            file_validation_failed = True

            print()
            print("FILE-LEVEL VALIDATION FAILURE")
            print("The source file will NOT be written to Bronze.")
            print("The original source file will be quarantined.")

            quarantine_destination = (
                f"{quarantine_date_path}"
                f"{source_local.stem}_file_error.csv"
            )

            run_command(
                [
                    "gcloud",
                    "storage",
                    "cp",
                    str(source_local),
                    quarantine_destination,
                ]
            )

            state.update_state(
                provider_id=provider,
                source_uri=source_uri,
                source_checksum=checksum,
                status="FILE_VALIDATION_FAILED",
                run_id=run_id,
                error_message=(
                    "File-level validation failed. "
                    "Original source file moved to Quarantine."
                ),
            )

            print()
            print("=" * 70)
            print("FILE QUARANTINED")
            print("=" * 70)
            print(f"Source file : {source_filename}")
            print(f"Source date : {source_date}")
            print(f"SHA-256     : {checksum}")
            print("Reason      : File-level validation failure")
            print(f"Quarantine  : {quarantine_destination}")
            print("State       : FILE_VALIDATION_FAILED")
            print("=" * 70)

            raise RuntimeError(
                "File-level validation failed. "
                "Original source file moved to Quarantine."
            )

        # ------------------------------------------------------------
        # Prepare validation outputs
        # ------------------------------------------------------------

        valid_file = (
            validation_dir
            / f"{source_local.stem}_valid.csv"
        )

        rejected_file = (
            validation_dir
            / f"{source_local.stem}_rejected.csv"
        )

        # ------------------------------------------------------------
        # 6. Upload valid/rejected records
        # ------------------------------------------------------------

        print("[6/7] Routing validated records...")

        valid_count = 0
        rejected_count = 0

        # -------------------------
        # Upload valid records
        # -------------------------

        print()
        print("Uploading valid records to Bronze...")

        if valid_file.exists():

            valid_count = count_csv_records(
                valid_file
            )

            if valid_count > 0:

                bronze_destination = (
                    f"{bronze_date_path}"
                    f"{valid_file.name}"
                )

                run_command(
                    [
                        "gcloud",
                        "storage",
                        "cp",
                        str(valid_file),
                        bronze_destination,
                    ]
                )

                print(
                    f"Uploaded {valid_count} valid records."
                )

        else:
            print(
                "No valid output file generated."
            )

        # -------------------------
        # Upload rejected records
        # -------------------------

        print()
        print("Uploading rejected records to Quarantine...")

        if rejected_file.exists():

            rejected_count = count_csv_records(
                rejected_file
            )

            if rejected_count > 0:

                quarantine_destination = (
                    f"{quarantine_date_path}"
                    f"{rejected_file.name}"
                )

                run_command(
                    [
                        "gcloud",
                        "storage",
                        "cp",
                        str(rejected_file),
                        quarantine_destination,
                    ]
                )

                print(
                    f"Uploaded {rejected_count} "
                    f"rejected records."
                )

        else:
            print(
                "No rejected output file generated."
            )

        # ------------------------------------------------------------
        # 7. Final result + SUCCESS state
        # ------------------------------------------------------------

        total_count = (
            valid_count +
            rejected_count
        )

        state.update_state(
            provider_id=provider,
            source_uri=source_uri,
            source_checksum=checksum,
            status="SUCCESS",
            run_id=run_id,
            record_count=total_count,
            valid_record_count=valid_count,
            rejected_record_count=rejected_count,
        )

        print()
        print("[7/7] PROCESSING SUMMARY")
        print("-" * 70)
        print(f"Run ID           : {run_id}")
        print(f"Provider         : {provider}")
        print(f"Source file      : {source_filename}")
        print(f"Source date      : {source_date}")
        print(f"SHA-256          : {checksum}")
        print(f"Total records    : {total_count}")
        print(f"Valid records    : {valid_count}")
        print(f"Rejected records : {rejected_count}")
        print("Status           : SUCCESS")
        print("File state       : SUCCESS")
        print("=" * 70)

    except Exception as exc:

        # Do not overwrite FILE_VALIDATION_FAILED
        # with generic FAILED.

        if (
            checksum is not None
            and not file_validation_failed
        ):
            try:

                state.update_state(
                    provider_id=provider,
                    source_uri=source_uri,
                    source_checksum=checksum,
                    status="FAILED",
                    run_id=run_id,
                    error_message=str(exc)[:1000],
                )

                print(
                    "FileProcessingState updated to FAILED."
                )

            except Exception as state_error:

                print(
                    "WARNING: Failed to update "
                    "FileProcessingState to FAILED: "
                    f"{state_error}"
                )

        raise

    finally:

        # Always clean up temporary files.

        if temp_root.exists():
            shutil.rmtree(
                temp_root,
                ignore_errors=True,
            )

        print()
        print(
            f"Temporary workspace cleaned: "
            f"{temp_root}"
        )


def parse_arguments():

    parser = argparse.ArgumentParser(
        description=(
            "Process one RAW retail file through "
            "validation and GCS routing."
        )
    )

    parser.add_argument(
        "--provider",
        required=True,
        help="Provider ID, e.g. provider_retail",
    )

    parser.add_argument(
        "--source-uri",
        required=True,
        help="Exact GCS URI of the RAW source file",
    )

    parser.add_argument(
        "--bronze-path",
        required=True,
        help="GCS Bronze prefix",
    )

    parser.add_argument(
        "--quarantine-path",
        required=True,
        help="GCS Quarantine prefix",
    )

    return parser.parse_args()


def main():

    args = parse_arguments()

    try:

        process_file(
            provider=args.provider,
            source_uri=args.source_uri,
            bronze_path=args.bronze_path,
            quarantine_path=args.quarantine_path,
        )

        return 0

    except Exception as exc:

        print()
        print("=" * 70)
        print("PROCESSING FAILED")
        print("=" * 70)
        print(f"Error: {exc}")
        print("=" * 70)

        return 1


if __name__ == "__main__":
    sys.exit(main())