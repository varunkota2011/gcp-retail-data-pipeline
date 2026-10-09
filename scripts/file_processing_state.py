from __future__ import annotations

from typing import Optional

from google.cloud import bigquery


PROJECT_ID = "varun2011-510908"
DATASET_ID = "retail_dev_state"
TABLE_ID = "FileProcessingState"

TABLE_REF = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"


class FileProcessingState:
    """
    Handles file-level processing state for the retail ingestion pipeline.

    The FileProcessingState table is the authoritative source for
    determining whether a source file has already been successfully
    processed.
    """

    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)

    def get_state(
        self,
        provider_id: str,
        source_uri: str,
        source_checksum: str,
    ) -> Optional[dict]:
        """
        Return the latest state for the same provider, source URI
        and checksum.

        Returns None when no matching state exists.
        """

        query = f"""
        SELECT
            provider_id,
            source_uri,
            source_file,
            source_date,
            source_checksum,
            status,
            run_id,
            first_processed_at,
            last_processed_at,
            record_count,
            valid_record_count,
            rejected_record_count,
            error_message,
            created_at,
            updated_at
        FROM `{TABLE_REF}`
        WHERE provider_id = @provider_id
          AND source_uri = @source_uri
          AND source_checksum = @source_checksum
        ORDER BY updated_at DESC
        LIMIT 1
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "provider_id", "STRING", provider_id
                ),
                bigquery.ScalarQueryParameter(
                    "source_uri", "STRING", source_uri
                ),
                bigquery.ScalarQueryParameter(
                    "source_checksum", "STRING", source_checksum
                ),
            ]
        )

        rows = list(
            self.client.query(
                query,
                job_config=job_config,
            ).result()
        )

        if not rows:
            return None

        return dict(rows[0].items())

    def upsert_processing_state(
        self,
        provider_id: str,
        source_uri: str,
        source_file: str,
        source_date: str,
        source_checksum: str,
        run_id: str,
        status: str = "PROCESSING",
    ) -> None:
        """
        Create or update a file processing state using BigQuery MERGE.

        This avoids the streaming-buffer problem caused by
        insert_rows_json() followed immediately by UPDATE.
        """

        query = f"""
        MERGE `{TABLE_REF}` AS target
        USING (
            SELECT
                @provider_id AS provider_id,
                @source_uri AS source_uri,
                @source_file AS source_file,
                CAST(@source_date AS DATE) AS source_date,
                @source_checksum AS source_checksum,
                @status AS status,
                @run_id AS run_id
        ) AS source
        ON target.provider_id = source.provider_id
           AND target.source_uri = source.source_uri
           AND target.source_checksum = source.source_checksum

        WHEN MATCHED THEN
            UPDATE SET
                status = source.status,
                run_id = source.run_id,
                last_processed_at = CURRENT_TIMESTAMP(),
                updated_at = CURRENT_TIMESTAMP()

        WHEN NOT MATCHED THEN
            INSERT (
                provider_id,
                source_uri,
                source_file,
                source_date,
                source_checksum,
                status,
                run_id,
                first_processed_at,
                last_processed_at,
                record_count,
                valid_record_count,
                rejected_record_count,
                error_message,
                created_at,
                updated_at
            )
            VALUES (
                source.provider_id,
                source.source_uri,
                source.source_file,
                source.source_date,
                source.source_checksum,
                source.status,
                source.run_id,
                CURRENT_TIMESTAMP(),
                CURRENT_TIMESTAMP(),
                NULL,
                NULL,
                NULL,
                NULL,
                CURRENT_TIMESTAMP(),
                CURRENT_TIMESTAMP()
            )
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "provider_id",
                    "STRING",
                    provider_id,
                ),
                bigquery.ScalarQueryParameter(
                    "source_uri",
                    "STRING",
                    source_uri,
                ),
                bigquery.ScalarQueryParameter(
                    "source_file",
                    "STRING",
                    source_file,
                ),
                bigquery.ScalarQueryParameter(
                    "source_date",
                    "STRING",
                    source_date,
                ),
                bigquery.ScalarQueryParameter(
                    "source_checksum",
                    "STRING",
                    source_checksum,
                ),
                bigquery.ScalarQueryParameter(
                    "status",
                    "STRING",
                    status,
                ),
                bigquery.ScalarQueryParameter(
                    "run_id",
                    "STRING",
                    run_id,
                ),
            ]
        )

        self.client.query(
            query,
            job_config=job_config,
        ).result()

    def update_state(
        self,
        provider_id: str,
        source_uri: str,
        source_checksum: str,
        status: str,
        run_id: str,
        record_count: Optional[int] = None,
        valid_record_count: Optional[int] = None,
        rejected_record_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Update an existing processing-state row.
        """

        query = f"""
        UPDATE `{TABLE_REF}`
        SET
            status = @status,
            run_id = @run_id,
            last_processed_at = CURRENT_TIMESTAMP(),
            record_count = @record_count,
            valid_record_count = @valid_record_count,
            rejected_record_count = @rejected_record_count,
            error_message = @error_message,
            updated_at = CURRENT_TIMESTAMP()
        WHERE provider_id = @provider_id
          AND source_uri = @source_uri
          AND source_checksum = @source_checksum
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter(
                    "status",
                    "STRING",
                    status,
                ),
                bigquery.ScalarQueryParameter(
                    "run_id",
                    "STRING",
                    run_id,
                ),
                bigquery.ScalarQueryParameter(
                    "record_count",
                    "INT64",
                    record_count,
                ),
                bigquery.ScalarQueryParameter(
                    "valid_record_count",
                    "INT64",
                    valid_record_count,
                ),
                bigquery.ScalarQueryParameter(
                    "rejected_record_count",
                    "INT64",
                    rejected_record_count,
                ),
                bigquery.ScalarQueryParameter(
                    "error_message",
                    "STRING",
                    error_message,
                ),
                bigquery.ScalarQueryParameter(
                    "provider_id",
                    "STRING",
                    provider_id,
                ),
                bigquery.ScalarQueryParameter(
                    "source_uri",
                    "STRING",
                    source_uri,
                ),
                bigquery.ScalarQueryParameter(
                    "source_checksum",
                    "STRING",
                    source_checksum,
                ),
            ]
        )

        job = self.client.query(
            query,
            job_config=job_config,
        )

        job.result()

        if job.num_dml_affected_rows != 1:
            raise RuntimeError(
                "Expected exactly one FileProcessingState row to be "
                f"updated, but updated {job.num_dml_affected_rows} rows."
            )