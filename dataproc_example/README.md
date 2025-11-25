# Simple Dataproc (PySpark) Example

A simplified example showing how to run a Spark job using Google Cloud Dataproc. This script counts words in a text file.

## What it does

- **Input**: Reads text from a file (default: `data/sample_text.txt`)
- **Process**: Uses PySpark to split text into words and count them
- **Output**: Writes the word counts to a CSV file in the output directory

## Quick Setup

1. **Install dependencies (for local run)**

   **Java Installation (Required for local PySpark)**

   PySpark requires Java (JDK 8 or 11). Install Java based on your operating system:

   **macOS:**
   ```bash
   # Using Homebrew (recommended)
   brew install openjdk@11

   # Add Java to your PATH (add to ~/.zshrc or ~/.bash_profile)
   echo 'export PATH="/opt/homebrew/opt/openjdk@11/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc

   # Verify installation
   java -version
   ```

   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt update
   sudo apt install openjdk-11-jdk

   # Verify installation
   java -version
   ```

   **Windows:**
   - Download and install Java JDK 11 from [Adoptium](https://adoptium.net/)
   - Or use Chocolatey: `choco install openjdk11`

   **Install PySpark:**
   ```bash
   pip install pyspark
   ```

   > **Note:** If you only want to run jobs on Dataproc (cloud), you can skip the Java installation and run the job directly on the cluster using the cloud commands.

2. **GCP Authentication**
   ```bash
   gcloud auth application-default login
   ```

3. **Set up environment variables**

   Get your GCP project ID:
   ```bash
   export PROJECT_ID=$(gcloud config get-value project)
   ```

   Set your preferred region:
   ```bash
   export REGION="us-central1"
   ```

   Create a unique bucket name:
   ```bash
   export BUCKET_NAME="${PROJECT_ID}-dataproc-demo"
   ```

   Set cluster name:
   ```bash
   export CLUSTER_NAME="dataproc-cluster"
   ```

   Verify the values:
   ```bash
   echo "Project ID: $PROJECT_ID"
   echo "Region: $REGION"
   echo "Bucket: $BUCKET_NAME"
   echo "Cluster: $CLUSTER_NAME"
   ```

4. **Create GCS bucket**
   ```bash
   gsutil mb -l $REGION gs://$BUCKET_NAME
   ```

5. **Upload sample data to GCS** (if running on cloud):
   ```bash
   gsutil cp data/sample_text.txt gs://$BUCKET_NAME/data/sample_text.txt
   ```

6. **Create Dataproc cluster**
   ```bash
   gcloud dataproc clusters create $CLUSTER_NAME \
     --region=$REGION \
     --subnet=projects/${PROJECT_ID}/regions/${REGION}/subnetworks/default \
     --zone=${REGION}-c \
     --master-machine-type=n1-standard-2 \
     --worker-machine-type=n1-standard-2 \
     --num-workers=2 \
     --image-version=2.1-debian11 \
     --max-idle=30m
   ```

   **Notes:**
   - Cluster creation takes 3-5 minutes
   - The `--max-idle=30m` flag auto-deletes the cluster after 30 minutes of inactivity to save costs
   - Using explicit subnet path prevents "subnetwork not ready" errors
   - Specifying `--image-version` is recommended for production use

## Running the Demo

**Run locally:**
```bash
python simple_spark_job.py
```

**Run on Dataproc (Cloud):**

First, upload the PySpark script to GCS:
```bash
gsutil cp simple_spark_job.py gs://$BUCKET_NAME/scripts/simple_spark_job.py
```

Then submit the job to your Dataproc cluster:
```bash
gcloud dataproc jobs submit pyspark gs://$BUCKET_NAME/scripts/simple_spark_job.py \
    --cluster=$CLUSTER_NAME \
    --region=$REGION \
    -- gs://$BUCKET_NAME/data/sample_text.txt gs://$BUCKET_NAME/output/
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

To avoid incurring charges, clean up all created resources:

1. **List running Dataproc jobs** (if any):
   ```bash
   gcloud dataproc jobs list --region=$REGION --cluster=$CLUSTER_NAME --filter="status.state=ACTIVE"
   ```

2. **Cancel any running jobs** (if needed):
   ```bash
   # Get the job ID from the list command above
   gcloud dataproc jobs kill [JOB_ID] --region=$REGION
   ```

3. **Delete the Dataproc cluster**:
   ```bash
   gcloud dataproc clusters delete $CLUSTER_NAME --region=$REGION --quiet
   ```

4. **Delete GCS bucket contents and the bucket**:
   ```bash
   # Delete  bucket
   gsutil rm -r gs://$BUCKET_NAME/
   ```

5. **Clean up local output files** (if you ran locally):
   ```bash
   rm -rf output/
   ```
