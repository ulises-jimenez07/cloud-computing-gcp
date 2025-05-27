#!/bin/bash
# Script to run Dataflow examples locally and on Google Cloud

# Exit on any error
set -e

# Set up environment variables (replace with your own values)
PROJECT_ID="your-gcp-project-id"
BUCKET_NAME="your-gcp-bucket-name"
REGION="us-central1"

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Function to run the word count example
run_wordcount() {
    echo "Running Word Count example..."
    
    # Run locally
    echo "Running locally..."
    python wordcount_pipeline.py \
        --input=data/sample_text.txt \
        --output=data/output/wordcount_local \
        --runner=DirectRunner
    
    echo "Local output saved to data/output/wordcount_local"
    
    # Run on Dataflow (commented out - uncomment to run on GCP)
    echo "To run on Dataflow, uncomment and run:"
    echo "python wordcount_pipeline.py \\"
    echo "    --project=$PROJECT_ID \\"
    echo "    --region=$REGION \\"
    echo "    --runner=DataflowRunner \\"
    echo "    --temp_location=gs://$BUCKET_NAME/temp/ \\"
    echo "    --input=gs://$BUCKET_NAME/data/sample_text.txt \\"
    echo "    --output=gs://$BUCKET_NAME/data/output/wordcount"
}

# Function to run the transform example
run_transform() {
    echo "Running Transform example..."
    
    # Create output directory if it doesn't exist
    mkdir -p data/output
    
    # Run locally
    echo "Running locally..."
    python transform_pipeline.py \
        --input=data/sample_data.csv \
        --output=data/output/transform_local \
        --min_price=50 \
        --runner=DirectRunner
    
    echo "Local output saved to data/output/transform_local"
    
    # Run on Dataflow (commented out - uncomment to run on GCP)
    echo "To run on Dataflow, uncomment and run:"
    echo "python transform_pipeline.py \\"
    echo "    --project=$PROJECT_ID \\"
    echo "    --region=$REGION \\"
    echo "    --runner=DataflowRunner \\"
    echo "    --temp_location=gs://$BUCKET_NAME/temp/ \\"
    echo "    --input=gs://$BUCKET_NAME/data/sample_data.csv \\"
    echo "    --output=gs://$BUCKET_NAME/data/output/transform \\"
    echo "    --min_price=50"
}

# Function to explain streaming example (can't run locally without Pub/Sub)
explain_streaming() {
    echo "Streaming Pipeline Example"
    echo "-------------------------"
    echo "The streaming example requires a Pub/Sub subscription and BigQuery table."
    echo "To run on Dataflow, use the following command after setting up the required resources:"
    echo ""
    echo "python streaming_pipeline.py \\"
    echo "    --project=$PROJECT_ID \\"
    echo "    --region=$REGION \\"
    echo "    --runner=DataflowRunner \\"
    echo "    --temp_location=gs://$BUCKET_NAME/temp/ \\"
    echo "    --subscription=projects/$PROJECT_ID/subscriptions/YOUR_SUBSCRIPTION \\"
    echo "    --dataset=YOUR_DATASET \\"
    echo "    --table=YOUR_TABLE \\"
    echo "    --window_size=60"
    echo ""
    echo "For testing, you can publish messages to your Pub/Sub topic using the Google Cloud Console"
    echo "or the gcloud command-line tool."
}

# Function to upload data to Google Cloud Storage
upload_to_gcs() {
    echo "Uploading sample data to Google Cloud Storage..."
    echo "To upload data to GCS, run:"
    echo "gsutil cp data/sample_text.txt gs://$BUCKET_NAME/data/"
    echo "gsutil cp data/sample_data.csv gs://$BUCKET_NAME/data/"
}

# Function to display help
show_help() {
    echo "Dataflow Examples Runner"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  wordcount    Run the Word Count example"
    echo "  transform    Run the Data Transformation example"
    echo "  streaming    Show instructions for the Streaming example"
    echo "  upload       Show instructions to upload data to GCS"
    echo "  all          Run all local examples"
    echo "  help         Show this help message"
}

# Main script logic
case "$1" in
    wordcount)
        run_wordcount
        ;;
    transform)
        run_transform
        ;;
    streaming)
        explain_streaming
        ;;
    upload)
        upload_to_gcs
        ;;
    all)
        run_wordcount
        run_transform
        explain_streaming
        ;;
    help|"")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac

# Deactivate virtual environment
deactivate

echo "Done!"