from file_processing_state import FileProcessingState


PROJECT_ID = "varun2011-510908"

PROVIDER_ID = "provider_retail"

SOURCE_URI = (
    "gs://varun2011-510908-retail-dev-raw/"
    "provider_retail/retail_sales_20101201.csv"
)

SOURCE_FILE = "retail_sales_20101201.csv"

SOURCE_DATE = "2010-12-01"

SOURCE_CHECKSUM = (
    "1f5d8bff5ec0e98fef42662fb86a59fb0c93ceadc10897da153c4b2539eba98e"
)


def main():
    state = FileProcessingState(PROJECT_ID)

    print("=== STEP 1: Check existing state ===")

    existing = state.get_state(
        provider_id=PROVIDER_ID,
        source_uri=SOURCE_URI,
        source_checksum=SOURCE_CHECKSUM,
    )

    print("Existing state:", existing)

    if existing is None:
        print("\nNo state exists yet.")
        print("Creating SUCCESS state to simulate a completed run.")

        state.upsert_processing_state(
            provider_id=PROVIDER_ID,
            source_uri=SOURCE_URI,
            source_file=SOURCE_FILE,
            source_date=SOURCE_DATE,
            source_checksum=SOURCE_CHECKSUM,
            run_id="idempotency_test_001",
            status="SUCCESS",
        )

        state.update_state(
            provider_id=PROVIDER_ID,
            source_uri=SOURCE_URI,
            source_checksum=SOURCE_CHECKSUM,
            status="SUCCESS",
            run_id="idempotency_test_001",
            record_count=3108,
            valid_record_count=3107,
            rejected_record_count=1,
        )

        print("SUCCESS state created.")

    print("\n=== STEP 2: Read state ===")

    existing = state.get_state(
        provider_id=PROVIDER_ID,
        source_uri=SOURCE_URI,
        source_checksum=SOURCE_CHECKSUM,
    )

    print("Current state:")
    print(existing)

    print("\n=== STEP 3: Apply idempotency decision ===")

    if existing and existing["status"] == "SUCCESS":
        print("IDEMPOTENCY RESULT: SKIP")
        print("Reason: Same source URI + same checksum + SUCCESS.")
    else:
        print("IDEMPOTENCY RESULT: PROCESS")


if __name__ == "__main__":
    main()