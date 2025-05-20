# Replace $PROJECT_ID with your actual GCP project ID
PROJECT_ID=project-id
# Create the Pub/Sub topic for audio streams
gcloud pubsub topics create audio-stream-topic --project=$PROJECT_ID
gcloud pubsub topics create transcriptor-topic --project=$PROJECT_ID

# Create the Pub/Sub topic for summary results
gcloud pubsub topics create summary-results-topic --project=$PROJECT_ID

# Create the Pub/Sub subscription for audio forwarding service
gcloud pubsub subscriptions create audio-stream-subscription \
    --topic=audio-stream-topic \
    --project=$PROJECT_ID

# Create the Pub/Sub subscription for the backend service that sends summary to web app
gcloud pubsub subscriptions create summary-results-subscription \
    --topic=summary-results-topic \
    --project=$PROJECT_ID

# List the topics to verify
gcloud pubsub topics list --project=$PROJECT_ID

# List the subscriptions to verify
gcloud pubsub subscriptions list --project=$PROJECT_ID


gcloud pubsub subscriptions create transcriptor-subscription \
    --topic=topic-name \
    --project=$PROJECT_ID \
    --push-endpoint=https://url-cloud-run \
    --ack-deadline=600 \
    --push-auth-service-account=service-account
