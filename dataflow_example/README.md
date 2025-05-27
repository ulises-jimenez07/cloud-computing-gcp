# Google Cloud Dataflow Example

This folder contains a complete example of using Google Cloud Dataflow for data processing pipelines. Dataflow is a fully managed service for executing [Apache Beam](https://beam.apache.org/) pipelines within the Google Cloud Platform ecosystem.

## What is Dataflow?

Google Cloud Dataflow is a serverless, fast, and cost-effective service for data processing pipelines. It offers:

- **Unified Stream and Batch Processing**: Process data of any size, whether bounded (batch) or unbounded (streaming)
- **Serverless and Fully Managed**: No infrastructure to manage, with autoscaling and dynamic work rebalancing
- **Real-time Insights**: Process data as it arrives for real-time analytics and ML
- **Cost Efficiency**: Pay only for resources used during pipeline execution

## Examples in this Repository

This repository includes:

1. **Word Count Pipeline** (`wordcount_pipeline.py`): A classic example that counts word occurrences in text files
2. **Streaming Pipeline** (`streaming_pipeline.py`): Demonstrates processing data from Pub/Sub in real-time
3. **Data Transformation** (`transform_pipeline.py`): Shows how to transform data with various Beam transforms

## Prerequisites

- Google Cloud Platform account with Dataflow API enabled
- Python 3.7+
- Google Cloud SDK installed and configured

## Setup Instructions

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Set up your GCP environment variables:
   ```bash
   export PROJECT_ID="your-gcp-project-id"
   export BUCKET_NAME="your-gcp-bucket-name"
   ```

3. Run a sample pipeline:
   ```bash
   python wordcount_pipeline.py \
     --project=$PROJECT_ID \
     --region=us-central1 \
     --runner=DataflowRunner \
     --temp_location=gs://$BUCKET_NAME/temp/ \
     --input=gs://$BUCKET_NAME/data/input.txt \
     --output=gs://$BUCKET_NAME/data/output
   ```

## Pipeline Descriptions

### Word Count Pipeline

The word count pipeline demonstrates the basic concepts of Beam pipelines:
- Reading data from files
- Applying transformations (splitting text into words)
- Aggregating results (counting occurrences)
- Writing results to output files

### Streaming Pipeline

The streaming pipeline shows how to:
- Read from a Pub/Sub subscription
- Process data in real-time
- Apply windowing to group data
- Output results to BigQuery

### Data Transformation Pipeline

This example demonstrates more advanced transformations:
- Filtering data
- Mapping and FlatMapping
- Combining and grouping data
- Using custom ParDo functions

## Additional Resources

- [Apache Beam Programming Guide](https://beam.apache.org/documentation/programming-guide/)
- [Google Cloud Dataflow Documentation](https://cloud.google.com/dataflow/docs)
- [Dataflow Templates](https://cloud.google.com/dataflow/docs/guides/templates/provided-templates)