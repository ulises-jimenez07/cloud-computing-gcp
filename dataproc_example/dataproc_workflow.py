#!/usr/bin/env python3
"""
dataproc_workflow.py - Example script for Google Cloud Dataproc Workflows

This script demonstrates how to create and manage Dataproc Workflows,
which allow you to define and execute a directed acyclic graph (DAG) of jobs.
"""

import argparse
import time
import uuid
from typing import Dict, List, Optional

from google.cloud import dataproc_v1
from google.cloud.dataproc_v1.types import workflow_templates


def create_workflow_template(
    project_id: str,
    region: str,
    template_id: str,
    cluster_name: str,
    num_workers: int = 2,
    master_machine_type: str = "n1-standard-4",
    worker_machine_type: str = "n1-standard-4",
    image_version: str = "2.0-debian10",
    zone: str = "us-central1-a",
    subnetwork: Optional[str] = None,
    service_account: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None,
) -> workflow_templates.WorkflowTemplate:
    """
    Creates a Dataproc Workflow Template.

    Args:
        project_id: Google Cloud project ID
        region: Region for the workflow template
        template_id: ID for the workflow template
        cluster_name: Name for the managed cluster
        num_workers: Number of worker nodes
        master_machine_type: Machine type for the master node
        worker_machine_type: Machine type for worker nodes
        image_version: Dataproc image version
        zone: Zone for the cluster
        subnetwork: Subnetwork to use
        service_account: Service account to use
        labels: Labels to apply to the template

    Returns:
        The created workflow template
    """
    # Create the Dataproc Workflow Template client
    client = dataproc_v1.WorkflowTemplateServiceClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )

    # Get the parent resource
    parent = f"projects/{project_id}/regions/{region}"

    # Configure the managed cluster
    managed_cluster = {
        "cluster_name": cluster_name,
        "config": {
            "gce_cluster_config": {
                "zone_uri": f"https://www.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}",
            },
            "master_config": {
                "num_instances": 1,
                "machine_type_uri": master_machine_type,
            },
            "worker_config": {
                "num_instances": num_workers,
                "machine_type_uri": worker_machine_type,
            },
            "software_config": {
                "image_version": image_version,
            },
        },
    }

    # Add subnetwork if specified
    if subnetwork:
        managed_cluster["config"]["gce_cluster_config"]["subnetwork_uri"] = subnetwork

    # Add service account if specified
    if service_account:
        managed_cluster["config"]["gce_cluster_config"]["service_account"] = service_account

    # Create the workflow template
    template = {
        "id": template_id,
        "placement": {
            "managed_cluster": managed_cluster,
        },
    }

    # Add labels if specified
    if labels:
        template["labels"] = labels

    # Create the workflow template
    response = client.create_workflow_template(request={"parent": parent, "template": template})

    print(f"Created workflow template: {response.id}")

    return response


def add_job_to_workflow_template(
    project_id: str,
    region: str,
    template_id: str,
    job_id: str,
    job_type: str,
    job_args: Dict,
    step_id: str,
    prerequisite_step_ids: Optional[List[str]] = None,
) -> workflow_templates.WorkflowTemplate:
    """
    Adds a job to a Dataproc Workflow Template.

    Args:
        project_id: Google Cloud project ID
        region: Region for the workflow template
        template_id: ID of the workflow template
        job_id: ID for the job
        job_type: Type of job (pyspark, spark, hadoop, hive, pig, spark-sql, etc.)
        job_args: Arguments specific to the job type
        step_id: ID for this step in the workflow
        prerequisite_step_ids: IDs of steps that must complete before this step

    Returns:
        The updated workflow template
    """
    # Create the Dataproc Workflow Template client
    client = dataproc_v1.WorkflowTemplateServiceClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )

    # Get the workflow template
    name = f"projects/{project_id}/regions/{region}/workflowTemplates/{template_id}"
    template = client.get_workflow_template(request={"name": name})

    # Create the job
    job = {
        "step_id": step_id,
        "job_id": job_id,
    }

    # Add job details based on job type
    if job_type == "pyspark":
        job["pyspark_job"] = job_args
    elif job_type == "spark":
        job["spark_job"] = job_args
    elif job_type == "hadoop":
        job["hadoop_job"] = job_args
    elif job_type == "hive":
        job["hive_job"] = job_args
    elif job_type == "pig":
        job["pig_job"] = job_args
    elif job_type == "spark-sql":
        job["spark_sql_job"] = job_args
    else:
        raise ValueError(f"Unsupported job type: {job_type}")

    # Add prerequisite steps if specified
    if prerequisite_step_ids:
        job["prerequisite_step_ids"] = prerequisite_step_ids

    # Add the job to the template
    template.jobs.append(job)

    # Update the workflow template
    response = client.update_workflow_template(request={"template": template})

    print(f"Added job {job_id} to workflow template {template_id}")

    return response


def instantiate_workflow_template(
    project_id: str,
    region: str,
    template_id: str,
    parameters: Optional[Dict[str, str]] = None,
) -> None:
    """
    Instantiates a Dataproc Workflow Template.

    Args:
        project_id: Google Cloud project ID
        region: Region for the workflow template
        template_id: ID of the workflow template
        parameters: Parameters to pass to the workflow template
    """
    # Create the Dataproc Workflow Template client
    client = dataproc_v1.WorkflowTemplateServiceClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )

    # Get the workflow template name
    name = f"projects/{project_id}/regions/{region}/workflowTemplates/{template_id}"

    # Instantiate the workflow template
    operation = client.instantiate_workflow_template(
        request={"name": name, "parameters": parameters}
    )

    print(f"Instantiating workflow template: {template_id}")

    # Wait for the operation to complete
    result = operation.result()

    print(f"Workflow execution completed: {result}")


def create_and_run_example_workflow(
    project_id: str,
    region: str,
    zone: str,
    input_file: str,
    output_dir: str,
) -> None:
    """
    Creates and runs an example workflow with multiple jobs.

    Args:
        project_id: Google Cloud project ID
        region: Region for the workflow
        zone: Zone for the cluster
        input_file: Input file for the jobs
        output_dir: Output directory for the jobs
    """
    # Generate unique IDs
    template_id = f"workflow-{uuid.uuid4().hex[:8]}"
    cluster_name = f"workflow-cluster-{uuid.uuid4().hex[:8]}"

    # Create the workflow template
    create_workflow_template(
        project_id=project_id,
        region=region,
        template_id=template_id,
        cluster_name=cluster_name,
        zone=zone,
    )

    # Add a PySpark word count job
    add_job_to_workflow_template(
        project_id=project_id,
        region=region,
        template_id=template_id,
        job_id="wordcount",
        job_type="pyspark",
        job_args={
            "main_python_file_uri": "pyspark_wordcount.py",
            "args": [input_file, f"{output_dir}/wordcount"],
        },
        step_id="wordcount",
    )

    # Add a Spark SQL job that depends on the word count job
    add_job_to_workflow_template(
        project_id=project_id,
        region=region,
        template_id=template_id,
        job_id="sql-analysis",
        job_type="spark-sql",
        job_args={
            "query_list": {
                "queries": [
                    "CREATE EXTERNAL TABLE IF NOT EXISTS wordcount "
                    f"LOCATION '{output_dir}/wordcount'",
                    "SELECT * FROM wordcount ORDER BY count DESC LIMIT 10",
                ],
            },
        },
        step_id="sql-analysis",
        prerequisite_step_ids=["wordcount"],
    )

    # Instantiate the workflow template
    instantiate_workflow_template(
        project_id=project_id,
        region=region,
        template_id=template_id,
    )


def main():
    parser = argparse.ArgumentParser(description="Create and run Dataproc Workflows")
    parser.add_argument("--project_id", required=True, help="Google Cloud project ID")
    parser.add_argument("--region", default="us-central1", help="Region for the workflow")
    parser.add_argument("--zone", default="us-central1-a", help="Zone for the cluster")
    parser.add_argument("--input_file", required=True, help="Input file for the jobs")
    parser.add_argument("--output_dir", required=True, help="Output directory for the jobs")

    args = parser.parse_args()

    create_and_run_example_workflow(
        project_id=args.project_id,
        region=args.region,
        zone=args.zone,
        input_file=args.input_file,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
