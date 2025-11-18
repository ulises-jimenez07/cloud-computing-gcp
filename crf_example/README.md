# interproteccion-resident
Repository for examples for interproteccion engagement

## Trigger Cloud Function 

To trigger the analysis of files, once the file has been uploaded to a bucket the following APIs need to be enabled.

1. Pub/Sub
2. Cloud Run Functions (2nd gen)
3. Cloud Storage
4. Vertex AI

### Create the required resources

1. Create Pub Sub topic
   ```bash
    TOPIC_NAME="documents" 
    gcloud pubsub topics create $TOPIC_NAME    
   ```
2. Add notifications to the bucket
   ```bash
    BUCKET_NAME="bucket-up-app"

    gcloud storage buckets notifications create gs://$BUCKET_NAME --topic=$TOPIC_NAME
   ```
3. Deploy Cloud Run Function (2nd gen) with [code](CF_upload_file/)
   ```bash
   gcloud functions deploy process-document \
     --gen2 \
     --runtime=python311 \
     --region=us-central1 \
     --source=CF_upload_file \
     --entry-point=process_pubsub_message \
     --trigger-topic=$TOPIC_NAME \
     --memory=512MB \
     --timeout=540s
   ```