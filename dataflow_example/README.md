# Simple Dataflow Pipeline Demo

A simplified example showing how to run a data processing pipeline using Apache Beam. This pipeline reads a text file, counts the words, and saves the results.

## What it does

- **Input**: Reads text from `data/sample_text.txt`
- **Process**: Splits text into words and counts them
- **Output**: Writes the word counts to `output.txt`

## Quick Setup

1. **Install dependencies**
   ```bash
   pip install apache-beam[gcp]
   ```

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
   export BUCKET_NAME="${PROJECT_ID}-dataflow-demo"
   ```

   Verify the values:
   ```bash
   echo "Project ID: $PROJECT_ID"
   echo "Region: $REGION"
   echo "Bucket: $BUCKET_NAME"
   ```

4. **Create GCS bucket**
   ```bash
   gsutil mb -l $REGION gs://$BUCKET_NAME
   ```

## Running the Demo

**Run locally:**
```bash
python simple_pipeline.py
```

**Run on Dataflow (Cloud):**
```bash
python simple_pipeline.py \
  --runner=DataflowRunner \
  --project=$PROJECT_ID \
  --region=$REGION \
  --temp_location=gs://$BUCKET_NAME/temp \
  --output=gs://$BUCKET_NAME/output
```

## What to expect

After running locally, you will see a new file named `output.txt-00000-of-00001` containing the word counts:

```
google: 3
cloud: 3
dataflow: 5
is: 1
...
```

## Cleanup

To avoid incurring charges, clean up all created resources:

1. **List running Dataflow jobs** (if you ran on Cloud):
   ```bash
   gcloud dataflow jobs list --region=$REGION --status=active
   ```

2. **Cancel any running Dataflow jobs** (if needed):
   ```bash
   # Get the job ID from the list command above
   gcloud dataflow jobs cancel [JOB_ID] --region=$REGION
   ```

3. **Delete GCS bucket contents and the bucket**:
   ```bash
   # Delete the bucket itself
   gsutil rb gs://$BUCKET_NAME
   ```

4. **Clean up local output files** (if you ran locally):
   ```bash
   rm -f output.txt-*
   ```
