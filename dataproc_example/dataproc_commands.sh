#!/bin/bash
# dataproc_commands.sh - Useful gcloud commands for Google Cloud Dataproc
#
# This script contains examples of common gcloud commands for working with
# Google Cloud Dataproc. These commands can be run individually in your
# terminal or you can modify and run this script.
#
# Before running these commands, make sure you have:
# 1. Installed the Google Cloud SDK (https://cloud.google.com/sdk/docs/install)
# 2. Authenticated with gcloud: gcloud auth login
# 3. Set your project: gcloud config set project YOUR_PROJECT_ID

# Set these variables before running the commands
PROJECT_ID="your-project-id"
REGION="us-central1"
ZONE="us-central1-a"
CLUSTER_NAME="my-dataproc-cluster"
BUCKET_NAME="gs://your-bucket-name"

# Print the current configuration
echo "Current gcloud configuration:"
gcloud config list

# List available Dataproc regions
echo -e "\nAvailable Dataproc regions:"
gcloud dataproc regions list

# List available Dataproc image versions
echo -e "\nAvailable Dataproc image versions:"
gcloud dataproc images list

# Create a Dataproc cluster
echo -e "\nCreating a Dataproc cluster..."
gcloud dataproc clusters create ${CLUSTER_NAME} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --zone=${ZONE} \
    --master-machine-type=n1-standard-4 \
    --master-boot-disk-size=500 \
    --num-workers=2 \
    --worker-machine-type=n1-standard-4 \
    --worker-boot-disk-size=500 \
    --image-version=2.0-debian10 \
    --optional-components=JUPYTER,ZEPPELIN \
    --enable-component-gateway

# List clusters in the region
echo -e "\nListing Dataproc clusters in ${REGION}:"
gcloud dataproc clusters list --region=${REGION}

# Describe the cluster
echo -e "\nDescribing cluster ${CLUSTER_NAME}:"
gcloud dataproc clusters describe ${CLUSTER_NAME} --region=${REGION}

# Submit a PySpark job
echo -e "\nSubmitting a PySpark job..."
gcloud dataproc jobs submit pyspark pyspark_wordcount.py \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --cluster=${CLUSTER_NAME} \
    -- ${BUCKET_NAME}/data/sample_text.txt ${BUCKET_NAME}/output/wordcount

# Submit a Spark SQL job
echo -e "\nSubmitting a Spark SQL job..."
gcloud dataproc jobs submit spark-sql \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --cluster=${CLUSTER_NAME} \
    --execute="SELECT * FROM default.sample_table LIMIT 10"

# List jobs in the region
echo -e "\nListing Dataproc jobs in ${REGION}:"
gcloud dataproc jobs list --region=${REGION}

# Create a workflow template
echo -e "\nCreating a workflow template..."
gcloud dataproc workflow-templates create my-workflow-template \
    --project=${PROJECT_ID} \
    --region=${REGION}

# Add a cluster to the workflow template
echo -e "\nAdding a cluster to the workflow template..."
gcloud dataproc workflow-templates set-managed-cluster my-workflow-template \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --cluster-name=workflow-cluster \
    --master-machine-type=n1-standard-4 \
    --worker-machine-type=n1-standard-4 \
    --num-workers=2 \
    --image-version=2.0-debian10

# Add a job to the workflow template
echo -e "\nAdding a job to the workflow template..."
gcloud dataproc workflow-templates add-job pyspark pyspark_wordcount.py \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --step-id=wordcount \
    --workflow-template=my-workflow-template \
    -- ${BUCKET_NAME}/data/sample_text.txt ${BUCKET_NAME}/output/wordcount

# Instantiate the workflow template
echo -e "\nInstantiating the workflow template..."
gcloud dataproc workflow-templates instantiate my-workflow-template \
    --project=${PROJECT_ID} \
    --region=${REGION}

# Scale up a cluster (add workers)
echo -e "\nScaling up the cluster..."
gcloud dataproc clusters update ${CLUSTER_NAME} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --num-workers=4

# Scale down a cluster (remove workers)
echo -e "\nScaling down the cluster..."
gcloud dataproc clusters update ${CLUSTER_NAME} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --num-workers=2

# Update cluster labels
echo -e "\nUpdating cluster labels..."
gcloud dataproc clusters update ${CLUSTER_NAME} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --update-labels=environment=dev,owner=username

# SSH into the master node
echo -e "\nSSH into the master node..."
gcloud compute ssh ${CLUSTER_NAME}-m \
    --project=${PROJECT_ID} \
    --zone=${ZONE}

# Copy files to the cluster
echo -e "\nCopying files to the cluster..."
gcloud compute scp local_file.py ${CLUSTER_NAME}-m:~ \
    --project=${PROJECT_ID} \
    --zone=${ZONE}

# Create a cluster with autoscaling
echo -e "\nCreating a cluster with autoscaling..."
gcloud dataproc clusters create autoscaling-cluster \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --zone=${ZONE} \
    --master-machine-type=n1-standard-4 \
    --worker-machine-type=n1-standard-4 \
    --num-workers=2 \
    --worker-min-num-instances=2 \
    --worker-max-num-instances=10 \
    --enable-autoscaling-scale-up \
    --enable-autoscaling-scale-down \
    --autoscaling-policy=autoscaling-policy

# Create a cluster with initialization actions
echo -e "\nCreating a cluster with initialization actions..."
gcloud dataproc clusters create init-actions-cluster \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --zone=${ZONE} \
    --master-machine-type=n1-standard-4 \
    --worker-machine-type=n1-standard-4 \
    --num-workers=2 \
    --initialization-actions=gs://goog-dataproc-initialization-actions-${REGION}/python/pip-install.sh \
    --metadata=PIP_PACKAGES="pandas scikit-learn"

# Create a cluster with preemptible VMs as workers
echo -e "\nCreating a cluster with preemptible VMs..."
gcloud dataproc clusters create preemptible-cluster \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --zone=${ZONE} \
    --master-machine-type=n1-standard-4 \
    --worker-machine-type=n1-standard-4 \
    --num-workers=2 \
    --num-secondary-workers=4 \
    --secondary-worker-type=preemptible

# Delete a cluster
echo -e "\nDeleting cluster ${CLUSTER_NAME}..."
gcloud dataproc clusters delete ${CLUSTER_NAME} \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --quiet

# Delete a workflow template
echo -e "\nDeleting workflow template..."
gcloud dataproc workflow-templates delete my-workflow-template \
    --project=${PROJECT_ID} \
    --region=${REGION} \
    --quiet

echo -e "\nAll commands completed."