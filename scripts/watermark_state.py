from datetime import datetime, timedelta
from typing import Optional

from google.cloud import bigquery
from google.cloud.bigquery import ScalarQueryParameter


PROJECT_ID = "varun2011-510908"
DATASET_ID = "retail_dev_state"
TABLE_ID = "IngestionState"


def get_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT_ID)


def get_state(
    provider_id: str,
    layer: str,
) -> Optional[dict]:
    client = get_client()

    query = f"""
        SELECT
            provider_id,
            layer,
            last_processed_event_time,
            max_event_time_seen,
            lookback_minutes,
            last_run_status,
            last_run_id,
            last_run_time,
            updated_at
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        WHERE provider_id = @provider_id
          AND layer = @layer
        LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            ScalarQueryParameter(
                "provider_id",
                "STRING",
                provider_id,
            ),
            ScalarQueryParameter(
                "layer",
                "STRING",
                layer,
            ),
        ]
    )

    rows = list(
        client.query(
            query,
            job_config=job_config,
        ).result()
    )

    if not rows:
        return None

    row = rows[0]

    return {
        "provider_id": row.provider_id,
        "layer": row.layer,
        "last_processed_event_time": row.last_processed_event_time,
        "max_event_time_seen": row.max_event_time_seen,
        "lookback_minutes": row.lookback_minutes,
        "last_run_status": row.last_run_status,
        "last_run_id": row.last_run_id,
        "last_run_time": row.last_run_time,
        "updated_at": row.updated_at,
    }


def calculate_processing_window(
    state: dict,
    min_available_event_time: datetime,
    max_available_event_time: datetime,
) -> tuple[datetime, datetime]:

    if state["last_run_status"] == "NEVER_RUN":
        lower_bound = min_available_event_time

    else:
        last_processed = state["last_processed_event_time"]

        if last_processed is None:
            lower_bound = min_available_event_time

        else:
            lower_bound = (
                last_processed
                - timedelta(minutes=state["lookback_minutes"])
            )

    upper_bound = max_available_event_time

    return lower_bound, upper_bound


def start_run(
    provider_id: str,
    layer: str,
    run_id: str,
) -> None:
    client = get_client()

    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        SET
            last_run_status = 'RUNNING',
            last_run_id = @run_id,
            last_run_time = CURRENT_TIMESTAMP(),
            updated_at = CURRENT_TIMESTAMP()
        WHERE provider_id = @provider_id
          AND layer = @layer
          AND last_run_status != 'RUNNING'
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            ScalarQueryParameter(
                "provider_id",
                "STRING",
                provider_id,
            ),
            ScalarQueryParameter(
                "layer",
                "STRING",
                layer,
            ),
            ScalarQueryParameter(
                "run_id",
                "STRING",
                run_id,
            ),
        ]
    )

    query_job = client.query(
        query,
        job_config=job_config,
    )

    query_job.result()

    if query_job.num_dml_affected_rows != 1:
        raise RuntimeError(
            f"Could not start run {run_id}. "
            f"Another run may already be RUNNING."
        )

    print(f"Started run: {run_id}")


def complete_success(
    provider_id: str,
    layer: str,
    run_id: str,
    max_event_time: datetime,
) -> None:
    client = get_client()

    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        SET
            last_processed_event_time = @max_event_time,
            max_event_time_seen = @max_event_time,
            last_run_status = 'SUCCESS',
            last_run_id = @run_id,
            last_run_time = CURRENT_TIMESTAMP(),
            updated_at = CURRENT_TIMESTAMP()
        WHERE provider_id = @provider_id
          AND layer = @layer
          AND last_run_id = @run_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            ScalarQueryParameter(
                "provider_id",
                "STRING",
                provider_id,
            ),
            ScalarQueryParameter(
                "layer",
                "STRING",
                layer,
            ),
            ScalarQueryParameter(
                "run_id",
                "STRING",
                run_id,
            ),
            ScalarQueryParameter(
                "max_event_time",
                "TIMESTAMP",
                max_event_time,
            ),
        ]
    )

    client.query(
        query,
        job_config=job_config,
    ).result()


def complete_failure(
    provider_id: str,
    layer: str,
    run_id: str,
    error_message: str,
) -> None:
    client = get_client()

    query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        SET
            last_run_status = 'FAILED',
            last_run_id = @run_id,
            last_run_time = CURRENT_TIMESTAMP(),
            updated_at = CURRENT_TIMESTAMP()
        WHERE provider_id = @provider_id
          AND layer = @layer
          AND last_run_id = @run_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            ScalarQueryParameter(
                "provider_id",
                "STRING",
                provider_id,
            ),
            ScalarQueryParameter(
                "layer",
                "STRING",
                layer,
            ),
            ScalarQueryParameter(
                "run_id",
                "STRING",
                run_id,
            ),
        ]
    )

    client.query(
        query,
        job_config=job_config,
    ).result()

    print(f"Run failed: {run_id}")
    print(f"Error: {error_message}")


if __name__ == "__main__":
    provider_id = "provider_retail"
    layer = "SILVER"

    state = get_state(
        provider_id=provider_id,
        layer=layer,
    )

    if state is None:
        raise RuntimeError(
            f"No IngestionState found for {provider_id}/{layer}"
        )

    print("Current IngestionState")
    print("=" * 60)

    for key, value in state.items():
        print(f"{key}: {value}")
