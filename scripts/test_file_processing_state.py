from file_processing_state import FileProcessingState


PROVIDER_ID = "provider_retail"

SOURCE_URI = (
    "gs://varun2011-510908-retail-dev-raw/"
    "provider_retail/test/state_test.csv"
)

SOURCE_FILE = "state_test.csv"
SOURCE_DATE = "2010-12-03"
SOURCE_CHECKSUM = "test_checksum_12345"
RUN_ID = "manual_test_run_001"


def main():
    state = FileProcessingState()

    print("Checking existing state...")

    existing = state.get_state(
        provider_id=PROVIDER_ID,
        source_uri=SOURCE_URI,
        source_checksum=SOURCE_CHECKSUM,
    )

    print("Existing state:", existing)

    print("\nInserting PROCESSING state...")

    state.upsert_processing_state(
        provider_id=PROVIDER_ID,
        source_uri=SOURCE_URI,
        source_file=SOURCE_FILE,
        source_date=SOURCE_DATE,
        source_checksum=SOURCE_CHECKSUM,
        run_id=RUN_ID,
    )

    print("PROCESSING state inserted.")

    print("\nReading state again...")

    existing = state.get_state(
        provider_id=PROVIDER_ID,
        source_uri=SOURCE_URI,
        source_checksum=SOURCE_CHECKSUM,
    )

    print("State after insert:")
    print(existing)

    print("\nUpdating state to SUCCESS...")

    state.update_state(
        provider_id=PROVIDER_ID,
        source_uri=SOURCE_URI,
        source_checksum=SOURCE_CHECKSUM,
        status="SUCCESS",
        run_id=RUN_ID,
        record_count=100,
        valid_record_count=98,
        rejected_record_count=2,
    )

    print("SUCCESS state updated.")

    print("\nReading final state...")

    existing = state.get_state(
        provider_id=PROVIDER_ID,
        source_uri=SOURCE_URI,
        source_checksum=SOURCE_CHECKSUM,
    )

    print("Final state:")
    print(existing)


if __name__ == "__main__":
    main()
