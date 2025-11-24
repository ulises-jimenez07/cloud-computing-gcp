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

2. **GCP Authentication (Optional for local run)**
   If you plan to run on Google Cloud Dataflow:
   ```bash
   gcloud auth application-default login
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
  --project=[YOUR_PROJECT_ID] \
  --region=[YOUR_REGION] \
  --temp_location=gs://[YOUR_BUCKET]/temp \
  --output=gs://[YOUR_BUCKET]/output
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

If you ran the pipeline on Dataflow, remember to delete the output and temp files from your GCS bucket to avoid storage charges:

```bash
gsutil rm -r gs://[YOUR_BUCKET]/output
gsutil rm -r gs://[YOUR_BUCKET]/temp
```
