# Google Cloud Dataproc Example

This directory contains examples and instructions for using Google Cloud Dataproc, a fully managed cloud service for running Apache Spark and Apache Hadoop clusters.

## What is Dataproc?

Google Cloud Dataproc is a managed Apache Spark and Apache Hadoop service that lets you take advantage of open source data tools for batch processing, querying, streaming, and machine learning. Dataproc automation helps you create clusters quickly, manage them easily, and save money by turning clusters off when you don't need them.

## Prerequisites

Before using these examples, you should have:

1. A Google Cloud Platform account with billing enabled
2. The [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
3. Appropriate IAM permissions to create and manage Dataproc clusters
4. Basic familiarity with Apache Spark and/or Hadoop

## Directory Structure

```
dataproc_example/
├── README.md                   # This file
├── create_cluster.py           # Python script to create a Dataproc cluster
├── submit_jobs.py              # Python script to submit jobs to a Dataproc cluster
├── pyspark_wordcount.py        # Example PySpark job
├── spark_sql_example.py        # Example Spark SQL job
├── jupyter_setup.py            # Script to set up Jupyter notebooks with Dataproc
├── dataproc_workflow.py        # Example of Dataproc Workflows
├── dataproc_commands.sh        # Useful gcloud commands for Dataproc
├── requirements.txt            # Python dependencies
└── data/                       # Sample data directory
    ├── sample_text.txt         # Sample text data for word count
    └── sample_data.csv         # Sample structured data for Spark SQL
```

## Creating a Dataproc Cluster

You can create a Dataproc cluster using the Google Cloud Console, the `gcloud` command-line tool, or programmatically using the Dataproc API.

### Using the Google Cloud Console

1. Go to the [Dataproc page](https://console.cloud.google.com/dataproc) in the Google Cloud Console
2. Click "Create Cluster"
3. Configure your cluster settings (name, region, zone, etc.)
4. Click "Create"

### Using the gcloud Command-Line Tool

```bash
gcloud dataproc clusters create my-cluster \
    --region=us-central1 \
    --zone=us-central1-a \
    --master-machine-type=n1-standard-4 \
    --master-boot-disk-size=500 \
    --num-workers=2 \
    --worker-machine-type=n1-standard-4 \
    --worker-boot-disk-size=500 \
    --image-version=2.0-debian10
```

### Using Python

See the `create_cluster.py` script in this directory for a detailed example.

## Submitting Jobs to Dataproc

Dataproc supports several job types:

- Spark
- PySpark
- SparkR
- Spark SQL
- Hive
- Pig
- Hadoop

### Using the gcloud Command-Line Tool

```bash
# Submit a PySpark job
gcloud dataproc jobs submit pyspark pyspark_wordcount.py \
    --cluster=my-cluster \
    --region=us-central1 \
    -- gs://my-bucket/data/sample_text.txt gs://my-bucket/output/wordcount

# Submit a Spark SQL job
gcloud dataproc jobs submit spark-sql \
    --cluster=my-cluster \
    --region=us-central1 \
    --execute="SELECT * FROM my_table LIMIT 10"
```

### Using Python

See the `submit_jobs.py` script in this directory for a detailed example.

## Using Jupyter Notebooks with Dataproc

Dataproc offers a Component Gateway that provides web interfaces for Hadoop, Spark, and other components. You can enable Jupyter notebooks when creating a cluster:

```bash
gcloud dataproc clusters create my-jupyter-cluster \
    --region=us-central1 \
    --zone=us-central1-a \
    --master-machine-type=n1-standard-4 \
    --num-workers=2 \
    --worker-machine-type=n1-standard-4 \
    --optional-components=JUPYTER,ZEPPELIN \
    --enable-component-gateway
```

See the `jupyter_setup.py` script in this directory for a detailed example.

## Dataproc Workflows

Dataproc Workflows allow you to manage a directed acyclic graph (DAG) of jobs. This is useful for complex data processing pipelines.

See the `dataproc_workflow.py` script in this directory for a detailed example.

## Best Practices

1. **Ephemeral Clusters**: Create clusters when needed and delete them when done to save costs
2. **Right-sizing**: Choose appropriate machine types and number of workers for your workload
3. **Preemptible VMs**: Use preemptible VMs for worker nodes to reduce costs
4. **Initialization Actions**: Use initialization actions to install additional software or configure your cluster
5. **Cloud Storage**: Store your data in Cloud Storage rather than HDFS for better durability and separation of compute and storage
6. **Autoscaling**: Enable autoscaling to automatically adjust the number of workers based on workload

## Additional Resources

- [Dataproc Documentation](https://cloud.google.com/dataproc/docs)
- [Dataproc API Reference](https://cloud.google.com/dataproc/docs/reference/rest)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Apache Hadoop Documentation](https://hadoop.apache.org/docs/)