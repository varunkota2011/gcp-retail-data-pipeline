import argparse
import subprocess
import sys


def run_command(command):
    if command and command[0] == "python":
        command[0] = sys.executable

    print()
    print("-" * 70)
    print("Running:")
    print(" ".join(command))
    print("-" * 70)

    result = subprocess.run(
        command,
        check=False,
    )

    return result.returncode


def discover_files(raw_path):
    result = subprocess.run(
        [
            sys.executable,
            "scripts/discover_raw_files.py",
            "--raw-path",
            raw_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("RAW file discovery failed.")

    files = []

    for line in result.stdout.splitlines():
        line = line.strip()

        if "|" not in line:
            continue

        parts = line.split("|", 2)

        if len(parts) != 3:
            continue

        try:
            sequence = int(parts[0].strip())
        except ValueError:
            continue

        source_date = parts[1].strip()
        source_uri = parts[2].strip()

        files.append(
            {
                "sequence": sequence,
                "source_date": source_date,
                "source_uri": source_uri,
            }
        )

    return files


def main():
    parser = argparse.ArgumentParser(
        description="Process discovered RAW files sequentially."
    )

    parser.add_argument(
        "--provider",
        required=True,
    )

    parser.add_argument(
        "--raw-path",
        required=True,
    )

    parser.add_argument(
        "--bronze-path",
        required=True,
    )

    parser.add_argument(
        "--quarantine-path",
        required=True,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Maximum number of discovered files to process.",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("DISCOVERED FILE BATCH PROCESSING")
    print("=" * 70)

    files = discover_files(args.raw_path)

    print(f"Total discovered : {len(files)}")

    selected_files = files[:args.limit]

    print(f"Selected files   : {len(selected_files)}")
    print()

    if not selected_files:
        print("No files selected.")
        return 1

    successful = 0
    failed = 0

    for item in selected_files:
        print()
        print("=" * 70)
        print(
            f"PROCESSING {item['sequence']:03d} | "
            f"{item['source_date']}"
        )
        print("=" * 70)

        return_code = run_command(
            [
                "python",
                "scripts/process_raw_files.py",
                "--provider",
                args.provider,
                "--source-uri",
                item["source_uri"],
                "--bronze-path",
                args.bronze_path,
                "--quarantine-path",
                args.quarantine_path,
            ]
        )

        if return_code == 0:
            successful += 1
        else:
            failed += 1
            print(
                f"File processing failed: "
                f"{item['source_uri']}"
            )

    print()
    print("=" * 70)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 70)
    print(f"Selected files : {len(selected_files)}")
    print(f"Successful     : {successful}")
    print(f"Failed         : {failed}")
    print("=" * 70)

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())