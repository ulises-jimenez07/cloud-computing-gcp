#!/usr/bin/env python3
"""
submit_jobs.py - Example script to submit jobs to a Google Cloud Dataproc cluster

This script demonstrates how to submit different types of jobs to a Dataproc cluster
programmatically using the Google Cloud Python client library.
"""

import argparse
import time
from typing import Dict, List, Optional, Union

from google.cloud import dataproc_v1
from google.cloud.dataproc_v1.types import jobs


def submit_job(
    project_id: str,
    region: str,
    cluster_name: str,
    job_type: str,
    job_args: Dict[str, Union[str, List[str]]],
    job_name: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
) -> jobs.Job:
    """
    Submits a job to a Dataproc cluster.

    Args:
        project_id: Google Cloud project ID
        region: Region where the cluster is located
        cluster_name: Name of the cluster to submit the job to
        job_type: Type of job (pyspark, spark, hadoop, hive, pig, spark-sql, etc.)
        job_args: Arguments specific to the job type
        job_name: Name for the job (optional)
        labels: Labels to apply to the job (optional)

    Returns:
        The submitted job object
    """
    # Create the Dataproc client
    client = dataproc_v1.JobControllerClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )

    # Create the job config based on job type
    job_details = {}

    if job_type == "pyspark":
        job_details["pyspark_job"] = job_args
    elif job_type == "spark":
        job_details["spark_job"] = job_args
    elif job_type == "hadoop":
        job_details["hadoop_job"] = job_args
    elif job_type == "hive":
        job_details["hive_job"] = job_args
    elif job_type == "pig":
        job_details["pig_job"] = job_args
    elif job_type == "spark-sql":
        job_details["spark_sql_job"] = job_args
    else:
        raise ValueError(f"Unsupported job type: {job_type}")

    # Create the job
    job = {
        "placement": {"cluster_name": cluster_name},
        "reference": {"job_id": job_name} if job_name else {},
        **job_details,
    }

    # Add labels if specified
    if labels:
        job["labels"] = labels

    # Submit the job
    operation = client.submit_job(request={"project_id": project_id, "region": region, "job": job})

    job_id = operation.reference.job_id
    print(f"Submitted job: {job_id}")

    return operation


def wait_for_job(
    project_id: str,
    region: str,
    job_id: str,
    timeout_seconds: int = 3600,
    poll_interval_seconds: int = 10,
) -> jobs.Job:
    """
    Waits for a Dataproc job to complete.

    Args:
        project_id: Google Cloud project ID
        region: Region where the job is running
        job_id: ID of the job to wait for
        timeout_seconds: Maximum time to wait (in seconds)
        poll_interval_seconds: Time between status checks (in seconds)

    Returns:
        The completed job object
    """
    # Create the Dataproc client
    client = dataproc_v1.JobControllerClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )

    # Wait for the job to complete
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        job = client.get_job(
            request={"project_id": project_id, "region": region, "job_id": job_id}
        )

        state = job.status.state
        state_name = jobs.JobStatus.State(state).name

        if state == jobs.JobStatus.State.DONE:
            print(f"Job {job_id} completed successfully")
            return job
        elif state == jobs.JobStatus.State.ERROR or state == jobs.JobStatus.State.CANCELLED:
            error_details = job.status.details if job.status.details else "Unknown error"
            raise RuntimeError(f"Job {job_id} failed with state {state_name}: {error_details}")

        print(f"Job {job_id} is {state_name}")
        time.sleep(poll_interval_seconds)

    raise TimeoutError(f"Job {job_id} did not complete within {timeout_seconds} seconds")


def submit_pyspark_job(
    project_id: str,
    region: str,
    cluster_name: str,
    main_python_file: str,
    args: Optional[List[str]] = None,
    python_files: Optional[List[str]] = None,
    jar_files: Optional[List[str]] = None,
    file_uris: Optional[List[str]] = None,
    archive_uris: Optional[List[str]] = None,
    properties: Optional[Dict[str, str]] = None,
    job_name: Optional[str] = None,
    wait: bool = True,
) -> jobs.Job:
    """
    Submits a PySpark job to a Dataproc cluster.

    Args:
        project_id: Google Cloud project ID
        region: Region where the cluster is located
        cluster_name: Name of the cluster to submit the job to
        main_python_file: Main Python file to execute
        args: Arguments to pass to the Python file
        python_files: Additional Python files to include
        jar_files: Additional JAR files to include
        file_uris: Additional files to include
        archive_uris: Archives to include
        properties: Spark properties
        job_name: Name for the job
        wait: Whether to wait for the job to complete

    Returns:
        The submitted job object
    """
    job_args = {
        "main_python_file_uri": main_python_file,
    }

    if args:
        job_args["args"] = args

    if python_files:
        job_args["python_file_uris"] = python_files

    if jar_files:
        job_args["jar_file_uris"] = jar_files

    if file_uris:
        job_args["file_uris"] = file_uris

    if archive_uris:
        job_args["archive_uris"] = archive_uris

    if properties:
        job_args["properties"] = properties

    job = submit_job(
        project_id=project_id,
        region=region,
        cluster_name=cluster_name,
        job_type="pyspark",
        job_args=job_args,
        job_name=job_name,
    )

    if wait:
        return wait_for_job(project_id, region, job.reference.job_id)

    return job


def submit_spark_sql_job(
    project_id: str,
    region: str,
    cluster_name: str,
    query_file: Optional[str] = None,
    query: Optional[str] = None,
    script_variables: Optional[Dict[str, str]] = None,
    properties: Optional[Dict[str, str]] = None,
    jar_files: Optional[List[str]] = None,
    job_name: Optional[str] = None,
    wait: bool = True,
) -> jobs.Job:
    """
    Submits a Spark SQL job to a Dataproc cluster.

    Args:
        project_id: Google Cloud project ID
        region: Region where the cluster is located
        cluster_name: Name of the cluster to submit the job to
        query_file: File containing the SQL query
        query: SQL query string (alternative to query_file)
        script_variables: Variables to substitute in the query
        properties: Spark properties
        jar_files: Additional JAR files to include
        job_name: Name for the job
        wait: Whether to wait for the job to complete

    Returns:
        The submitted job object
    """
    if not query_file and not query:
        raise ValueError("Either query_file or query must be specified")

    job_args = {}

    if query_file:
        job_args["query_file_uri"] = query_file

    if query:
        job_args["query_list"] = {"queries": [query]}

    if script_variables:
        job_args["script_variables"] = script_variables

    if properties:
        job_args["properties"] = properties

    if jar_files:
        job_args["jar_file_uris"] = jar_files

    job = submit_job(
        project_id=project_id,
        region=region,
        cluster_name=cluster_name,
        job_type="spark-sql",
        job_args=job_args,
        job_name=job_name,
    )

    if wait:
        return wait_for_job(project_id, region, job.reference.job_id)

    return job


def main():
    parser = argparse.ArgumentParser(description="Submit a job to a Dataproc cluster")
    parser.add_argument("--project_id", required=True, help="Google Cloud project ID")
    parser.add_argument("--region", default="us-central1", help="Region for the cluster")
    parser.add_argument("--cluster_name", required=True, help="Name of the cluster")

    subparsers = parser.add_subparsers(dest="job_type", help="Type of job to submit")

    # PySpark job arguments
    pyspark_parser = subparsers.add_parser("pyspark", help="Submit a PySpark job")
    pyspark_parser.add_argument(
        "--main_python_file", required=True, help="Main Python file to execute"
    )
    pyspark_parser.add_argument("--args", nargs="+", help="Arguments to pass to the Python file")
    pyspark_parser.add_argument("--job_name", help="Name for the job")
    pyspark_parser.add_argument(
        "--no_wait", action="store_true", help="Don't wait for the job to complete"
    )

    # Spark SQL job arguments
    spark_sql_parser = subparsers.add_parser("spark-sql", help="Submit a Spark SQL job")
    spark_sql_group = spark_sql_parser.add_mutually_exclusive_group(required=True)
    spark_sql_group.add_argument("--query_file", help="File containing the SQL query")
    spark_sql_group.add_argument("--query", help="SQL query string")
    spark_sql_parser.add_argument("--job_name", help="Name for the job")
    spark_sql_parser.add_argument(
        "--no_wait", action="store_true", help="Don't wait for the job to complete"
    )

    args = parser.parse_args()

    if args.job_type == "pyspark":
        submit_pyspark_job(
            project_id=args.project_id,
            region=args.region,
            cluster_name=args.cluster_name,
            main_python_file=args.main_python_file,
            args=args.args,
            job_name=args.job_name,
            wait=not args.no_wait,
        )
    elif args.job_type == "spark-sql":
        submit_spark_sql_job(
            project_id=args.project_id,
            region=args.region,
            cluster_name=args.cluster_name,
            query_file=args.query_file,
            query=args.query,
            job_name=args.job_name,
            wait=not args.no_wait,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
