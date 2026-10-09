from file_processing_state import FileProcessingState


PROJECT_ID = "varun2011-510908"

PROVIDER_ID = "provider_retail"

SOURCE_URI = (
    "gs://varun2011-510908-retail-dev-raw/"
    "provider_retail/test/failure_retry_test.csv"
)

SOURCE_FILE = "failure_retry_test.csv"

SOURCE_DATE = "2010-12-02"

SOURCE_CHECKSUM = "controlled_failure_checksum_001"

RUN_ID = "failure_test_run_001"


def main():
    state = FileProcessingState(PROJECT_ID)

    print("=== STEP 1: Create PROCESSING state ===")

    state.upsert_processing_state(
        provider_id=PROVIDER_ID,
        source_uri=SOURCE_URI,
        source_file=SOURCE_FILE,
        source_date=SOURCE_DATE,
        source_checksum=SOURCE_CHECKSUM,
        run_id=RUN_ID,
        status="PROCESSING",
    )

    print("State created: PROCESSING")

    print("\n=== STEP 2: Simulate processing failure ===")

    state.update_state(
        provider_id=PROVIDER_ID,
        source_uri=SOURCE_URI,
        source_checksum=SOURCE_CHECKSUM,
        status="FAILED",
        run_id=RUN_ID,
        error_message="CONTROLLED TEST FAILURE",
    )

    print("State updated: FAILED")

    print("\n=== STEP 3: Read state ===")

    existing = state.get_state(
        provider_id=PROVIDER_ID,
        source_uri=SOURCE_URI,
        source_checksum=SOURCE_CHECKSUM,
    )

    print(existing)

    print("\n=== STEP 4: Apply retry decision ===")

    if existing and existing["status"] == "SUCCESS":
        print("RETRY RESULT: SKIP")
    else:
        print("RETRY RESULT: PROCESS")
        print(
            "Reason: Previous execution did not finish successfully."
        )


if __name__ == "__main__":
    main()