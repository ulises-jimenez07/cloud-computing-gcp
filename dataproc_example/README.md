# Simple Dataproc (PySpark) Example

A simplified example showing how to run a Spark job using Google Cloud Dataproc. This script counts words in a text file.

## What it does

- **Input**: Reads text from a file (default: `data/sample_text.txt`)
- **Process**: Uses PySpark to split text into words and count them
- **Output**: Writes the word counts to a CSV file in the output directory

## Quick Setup

1. **Install dependencies (for local run)**
   You need Java (JDK 8 or 11) installed. Then install PySpark:
   ```bash
   pip install pyspark
   ```

2. **GCP Authentication (Optional for local run)**
   If you plan to interact with GCS buckets:
   ```bash
   gcloud auth application-default login
   ```

## Running the Demo

**Run locally:**
```bash
python simple_spark_job.py
```

**Run on Dataproc (Cloud):**
Assuming you have a Dataproc cluster named `my-cluster` and a bucket `my-bucket`:

```bash
gcloud dataproc jobs submit pyspark simple_spark_job.py \
    --cluster=my-cluster \
    --region=us-central1 \
    -- gs://my-bucket/data/sample_text.txt gs://my-bucket/output/
```

## What to expect

After running, check the output directory. You will find a CSV file (e.g., `part-00000...csv`) containing:

```csv
word,count
dataproc,5
google,3
cloud,3
...
```

## Cleanup

If you created a Dataproc cluster and used GCS buckets, remember to delete them to avoid charges:

```bash
# Delete the Dataproc cluster
gcloud dataproc clusters delete my-cluster --region=us-central1

# Delete the output from the bucket
gsutil rm -r gs://my-bucket/output/
```
