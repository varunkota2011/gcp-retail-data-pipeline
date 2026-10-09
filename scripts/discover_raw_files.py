import argparse
import re
import subprocess
import sys
from datetime import datetime


FILENAME_PATTERN = re.compile(
    r"^retail_sales_(\d{8})\.csv$"
)


def run_command(command):
    if command and command[0] == "gcloud" and sys.platform.startswith("win"):
        command[0] = "gcloud.cmd"

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    return result.stdout


def extract_source_date(filename):
    match = FILENAME_PATTERN.match(filename)

    if not match:
        return None

    date_string = match.group(1)

    try:
        return datetime.strptime(
            date_string,
            "%Y%m%d"
        ).date()
    except ValueError:
        return None


def discover_files(raw_path):
    raw_path = raw_path.rstrip("/") + "/"

    print("=" * 70)
    print("RAW FILE DISCOVERY")
    print("=" * 70)
    print(f"RAW path: {raw_path}")
    print()

    output = run_command(
        [
            "gcloud",
            "storage",
            "ls",
            "--recursive",
            raw_path,
        ]
    )

    discovered = []

    for line in output.splitlines():
        uri = line.strip()

        if not uri:
            continue

        # Only CSV files
        if not uri.lower().endswith(".csv"):
            continue

        # Exclude controlled test files
        if "/test/" in uri:
            continue

        # Extract filename
        filename = uri.rsplit("/", 1)[-1]

        source_date = extract_source_date(filename)

        # Ignore files that don't follow production naming convention
        if source_date is None:
            print(f"SKIP - invalid filename: {uri}")
            continue

        discovered.append(
            {
                "source_uri": uri,
                "source_file": filename,
                "source_date": source_date,
            }
        )

    discovered.sort(
        key=lambda x: (
            x["source_date"],
            x["source_file"],
        )
    )

    print("-" * 70)
    print(f"Files discovered : {len(discovered)}")

    if discovered:
        print(
            f"First file       : "
            f"{discovered[0]['source_file']}"
        )

        print(
            f"Last file        : "
            f"{discovered[-1]['source_file']}"
        )

    print("-" * 70)

    for index, item in enumerate(discovered, start=1):
        print(
            f"{index:03d} | "
            f"{item['source_date']} | "
            f"{item['source_uri']}"
        )

    print("=" * 70)

    return discovered


def main():
    parser = argparse.ArgumentParser(
        description="Discover production RAW files."
    )

    parser.add_argument(
        "--raw-path",
        required=True,
        help="GCS RAW provider path",
    )

    args = parser.parse_args()

    try:
        files = discover_files(args.raw_path)

        if not files:
            print("No production files discovered.")
            return 1

        return 0

    except Exception as exc:
        print()
        print("=" * 70)
        print("RAW FILE DISCOVERY FAILED")
        print("=" * 70)
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())