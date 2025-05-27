#!/usr/bin/env python3
"""
create_cluster.py - Example script to create a Google Cloud Dataproc cluster

This script demonstrates how to create a Dataproc cluster programmatically
using the Google Cloud Python client library.
"""

import argparse
import uuid
from typing import Dict, List, Optional

from google.cloud import dataproc_v1
from google.cloud.dataproc_v1.types import clusters


def create_cluster(
    project_id: str,
    region: str,
    cluster_name: str,
    num_workers: int = 2,
    master_machine_type: str = "n1-standard-4",
    worker_machine_type: str = "n1-standard-4",
    master_disk_size: int = 500,
    worker_disk_size: int = 500,
    network: Optional[str] = None,
    subnetwork: Optional[str] = None,
    image_version: str = "2.0-debian10",
    optional_components: Optional[List[str]] = None,
    initialization_actions: Optional[List[str]] = None,
    labels: Optional[Dict[str, str]] = None,
    service_account: Optional[str] = None,
    enable_component_gateway: bool = True,
    idle_delete_ttl: Optional[int] = None,
    temp_bucket: Optional[str] = None,
) -> clusters.Cluster:
    """
    Creates a Dataproc cluster.

    Args:
        project_id: Google Cloud project ID
        region: Region where the cluster will be created
        cluster_name: Name of the cluster
        num_workers: Number of worker nodes
        master_machine_type: Machine type for the master node
        worker_machine_type: Machine type for worker nodes
        master_disk_size: Boot disk size for the master node (GB)
        worker_disk_size: Boot disk size for worker nodes (GB)
        network: VPC network to use
        subnetwork: Subnetwork to use
        image_version: Dataproc image version
        optional_components: List of optional components to install
        initialization_actions: List of initialization action scripts
        labels: Labels to apply to the cluster
        service_account: Service account to use for the cluster
        enable_component_gateway: Whether to enable component gateway
        idle_delete_ttl: Time to live for idle clusters (seconds)
        temp_bucket: Temporary bucket for cluster operation

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
                "boot_disk_size_gb": master_disk_size,
            },
        },
        "worker_config": {
            "num_instances": num_workers,
            "machine_type_uri": worker_machine_type,
            "disk_config": {
                "boot_disk_size_gb": worker_disk_size,
            },
        },
        "software_config": {
            "image_version": image_version,
        },
    }

    # Add optional components if specified
    if optional_components:
        cluster_config["software_config"]["optional_components"] = [
            getattr(clusters.Component, component) for component in optional_components
        ]

    # Add component gateway if enabled
    if enable_component_gateway:
        cluster_config["endpoint_config"] = {"enable_http_port_access": True}

    # Add network configuration if specified
    if network or subnetwork:
        cluster_config["gce_cluster_config"] = {}
        if network:
            cluster_config["gce_cluster_config"]["network_uri"] = network
        if subnetwork:
            cluster_config["gce_cluster_config"]["subnetwork_uri"] = subnetwork

    # Add service account if specified
    if service_account:
        if "gce_cluster_config" not in cluster_config:
            cluster_config["gce_cluster_config"] = {}
        cluster_config["gce_cluster_config"]["service_account"] = service_account

    # Add initialization actions if specified
    if initialization_actions:
        cluster_config["initialization_actions"] = [
            {"executable_file": action} for action in initialization_actions
        ]

    # Add idle delete TTL if specified
    if idle_delete_ttl:
        cluster_config["lifecycle_config"] = {"idle_delete_ttl": {"seconds": idle_delete_ttl}}

    # Add temp bucket if specified
    if temp_bucket:
        cluster_config["config_bucket"] = temp_bucket

    # Create the cluster
    cluster = {
        "project_id": project_id,
        "cluster_name": cluster_name,
        "config": cluster_config,
    }

    # Add labels if specified
    if labels:
        cluster["labels"] = labels

    operation = client.create_cluster(
        request={"project_id": project_id, "region": region, "cluster": cluster}
    )

    print(f"Creating cluster: {cluster_name}")
    result = operation.result()
    print(f"Cluster created successfully: {result.cluster_name}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Create a Dataproc cluster")
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
        "--optional_components",
        nargs="+",
        help="Optional components to install (e.g., JUPYTER, ZEPPELIN)",
    )
    parser.add_argument(
        "--enable_component_gateway",
        action="store_true",
        help="Enable component gateway for web interfaces",
    )
    parser.add_argument(
        "--idle_delete_ttl",
        type=int,
        help="Time to live for idle clusters (in seconds)",
    )

    args = parser.parse_args()

    # Generate a random cluster name if not provided
    cluster_name = args.cluster_name or f"dataproc-cluster-{uuid.uuid4().hex[:8]}"

    # Convert optional components to uppercase
    optional_components = None
    if args.optional_components:
        optional_components = [comp.upper() for comp in args.optional_components]

    create_cluster(
        project_id=args.project_id,
        region=args.region,
        cluster_name=cluster_name,
        num_workers=args.num_workers,
        master_machine_type=args.master_machine_type,
        worker_machine_type=args.worker_machine_type,
        image_version=args.image_version,
        optional_components=optional_components,
        enable_component_gateway=args.enable_component_gateway,
        idle_delete_ttl=args.idle_delete_ttl,
    )


if __name__ == "__main__":
    main()
