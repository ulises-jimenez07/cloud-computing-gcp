#!/usr/bin/env python3
"""
jupyter_setup.py - Example script to set up Jupyter notebooks with Google Cloud Dataproc

This script demonstrates how to create a Dataproc cluster with Jupyter notebook
support and how to access and use Jupyter notebooks on the cluster.
"""

import argparse
import time
import uuid
import webbrowser
from typing import Dict, List, Optional

from google.cloud import dataproc_v1
from google.cloud.dataproc_v1.types import clusters


def create_jupyter_cluster(
    project_id: str,
    region: str,
    cluster_name: str,
    num_workers: int = 2,
    master_machine_type: str = "n1-standard-4",
    worker_machine_type: str = "n1-standard-4",
    image_version: str = "2.0-debian10",
    idle_delete_ttl: Optional[int] = None,
    metadata: Optional[Dict[str, str]] = None,
    initialization_actions: Optional[List[str]] = None,
) -> clusters.Cluster:
    """
    Creates a Dataproc cluster with Jupyter notebook support.

    Args:
        project_id: Google Cloud project ID
        region: Region where the cluster will be created
        cluster_name: Name of the cluster
        num_workers: Number of worker nodes
        master_machine_type: Machine type for the master node
        worker_machine_type: Machine type for worker nodes
        image_version: Dataproc image version
        idle_delete_ttl: Time to live for idle clusters (seconds)
        metadata: Metadata to apply to the cluster
        initialization_actions: List of initialization action scripts

    Returns:
        The created cluster object
    """
    # Create the Dataproc client
    client = dataproc_v1.ClusterControllerClient(
        client_options={"api_endpoint": f"{region}-dataproc.googleapis.com:443"}
    )

    # Configure cluster config
    cluster_config = {
        "master_config": {
            "num_instances": 1,
            "machine_type_uri": master_machine_type,
            "disk_config": {
                "boot_disk_size_gb": 500,
            },
        },
        "worker_config": {
            "num_instances": num_workers,
            "machine_type_uri": worker_machine_type,
            "disk_config": {
                "boot_disk_size_gb": 500,
            },
        },
        "software_config": {
            "image_version": image_version,
            "optional_components": [
                clusters.Component.JUPYTER,
                clusters.Component.ANACONDA,
            ],
        },
        "endpoint_config": {
            "enable_http_port_access": True,
        },
    }

    # Add metadata if specified
    if metadata:
        cluster_config["software_config"]["properties"] = metadata

    # Add initialization actions if specified
    if initialization_actions:
        cluster_config["initialization_actions"] = [
            {"executable_file": action} for action in initialization_actions
        ]

    # Add idle delete TTL if specified
    if idle_delete_ttl:
        cluster_config["lifecycle_config"] = {"idle_delete_ttl": {"seconds": idle_delete_ttl}}

    # Create the cluster
    cluster = {
        "project_id": project_id,
        "cluster_name": cluster_name,
        "config": cluster_config,
    }

    operation = client.create_cluster(
        request={"project_id": project_id, "region": region, "cluster": cluster}
    )

    print(f"Creating cluster: {cluster_name}")
    result = operation.result()
    print(f"Cluster created successfully: {result.cluster_name}")

    return result


def get_jupyter_url(
    project_id: str,
    region: str,
    cluster_name: str,
) -> str:
    """
    Gets the URL for accessing Jupyter notebooks on a Dataproc cluster.

    Args:
        project_id: Google Cloud project ID
        region: Region where the cluster is located
        cluster_name: Name of the cluster

    Returns:
        The URL for accessing Jupyter notebooks
    """
    # The URL format for accessing Jupyter notebooks on Dataproc
    jupyter_url = f"https://{region}.dataproc.googleusercontent.com/jupyter/{cluster_name}/"

    print(f"Jupyter notebook URL: {jupyter_url}")
    print("Note: You need to be authenticated and have proper IAM permissions to access this URL.")

    return jupyter_url


def main():
    parser = argparse.ArgumentParser(description="Set up Jupyter notebooks with Dataproc")
    parser.add_argument("--project_id", required=True, help="Google Cloud project ID")
    parser.add_argument("--region", default="us-central1", help="Region for the cluster")
    parser.add_argument("--cluster_name", help="Name for the cluster")
    parser.add_argument("--num_workers", type=int, default=2, help="Number of worker nodes")
    parser.add_argument(
        "--master_machine_type", default="n1-standard-4", help="Machine type for master node"
    )
    parser.add_argument(
        "--worker_machine_type", default="n1-standard-4", help="Machine type for worker nodes"
    )
    parser.add_argument("--image_version", default="2.0-debian10", help="Dataproc image version")
    parser.add_argument(
        "--idle_delete_ttl",
        type=int,
        default=3600,  # 1 hour
        help="Time to live for idle clusters (in seconds)",
    )
    parser.add_argument(
        "--open_browser",
        action="store_true",
        help="Open the Jupyter notebook URL in a browser",
    )

    args = parser.parse_args()

    # Generate a random cluster name if not provided
    cluster_name = args.cluster_name or f"jupyter-cluster-{uuid.uuid4().hex[:8]}"

    # Create the cluster with Jupyter support
    cluster = create_jupyter_cluster(
        project_id=args.project_id,
        region=args.region,
        cluster_name=cluster_name,
        num_workers=args.num_workers,
        master_machine_type=args.master_machine_type,
        worker_machine_type=args.worker_machine_type,
        image_version=args.image_version,
        idle_delete_ttl=args.idle_delete_ttl,
    )

    # Wait for the component gateway to be ready
    print("Waiting for component gateway to be ready...")
    time.sleep(60)  # Wait for 60 seconds

    # Get the Jupyter URL
    jupyter_url = get_jupyter_url(
        project_id=args.project_id,
        region=args.region,
        cluster_name=cluster_name,
    )

    # Open the Jupyter URL in a browser if requested
    if args.open_browser:
        print("Opening Jupyter notebook in browser...")
        webbrowser.open(jupyter_url)

    print("\nUsage Instructions:")
    print("1. Access the Jupyter notebook using the URL above")
    print("2. Create a new notebook (Python 3 or PySpark)")
    print("3. Use the following code to create a Spark session:")
    print(
        """
    from pyspark.sql import SparkSession
    
    spark = SparkSession.builder.appName("Jupyter Notebook").getOrCreate()
    """
    )
    print("4. Now you can use Spark in your notebook!")
    print("5. Remember to delete the cluster when you're done to avoid unnecessary charges:")
    print(f"   gcloud dataproc clusters delete {cluster_name} --region={args.region}")


if __name__ == "__main__":
    main()
