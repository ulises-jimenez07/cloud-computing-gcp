#!/bin/bash
# Google Cloud Pub/Sub example commands
# Replace YOUR_PROJECT_ID with your actual GCP project ID

# Set your project ID here
PROJECT_ID="YOUR_PROJECT_ID"

# Function to create basic Pub/Sub resources
create_basic_resources() {
    echo "Creating basic Pub/Sub resources..."
    
    # Create a basic topic
    gcloud pubsub topics create basic-topic --project=$PROJECT_ID
    
    # Create a pull subscription
    gcloud pubsub subscriptions create basic-pull-subscription \
        --topic=basic-topic \
        --project=$PROJECT_ID
    
    # Create a push subscription (replace URL with your endpoint)
    # gcloud pubsub subscriptions create basic-push-subscription \
    #     --topic=basic-topic \
    #     --push-endpoint=https://your-endpoint.com/push \
    #     --project=$PROJECT_ID
    
    echo "Basic resources created successfully!"
}

# Function to create resources for ordered delivery example
create_ordered_resources() {
    echo "Creating resources for ordered delivery example..."
    
    # Create a topic for ordered messages
    gcloud pubsub topics create ordered-topic --project=$PROJECT_ID
    
    # Create a subscription with message ordering enabled
    gcloud pubsub subscriptions create ordered-subscription \
        --topic=ordered-topic \
        --project=$PROJECT_ID \
        --enable-message-ordering
    
    echo "Ordered delivery resources created successfully!"
}

# Function to create resources for schema validation example
create_schema_resources() {
    echo "Creating resources for schema validation example..."
    
    # Create an Avro schema
    gcloud pubsub schemas create user-schema \
        --type=AVRO \
        --definition-file=schemas/user.avsc \
        --project=$PROJECT_ID
    
    # Create a topic with schema validation
    gcloud pubsub topics create schema-topic \
        --schema=user-schema \
        --message-encoding=JSON \
        --project=$PROJECT_ID
    
    # Create a subscription
    gcloud pubsub subscriptions create schema-subscription \
        --topic=schema-topic \
        --project=$PROJECT_ID
    
    echo "Schema validation resources created successfully!"
}

# Function to create resources for dead letter example
create_dead_letter_resources() {
    echo "Creating resources for dead letter example..."
    
    # Create a main topic
    gcloud pubsub topics create main-topic --project=$PROJECT_ID
    
    # Create a dead letter topic
    gcloud pubsub topics create dead-letter-topic --project=$PROJECT_ID
    
    # Create a subscription with dead letter policy
    gcloud pubsub subscriptions create main-subscription \
        --topic=main-topic \
        --dead-letter-topic=projects/$PROJECT_ID/topics/dead-letter-topic \
        --max-delivery-attempts=5 \
        --project=$PROJECT_ID
    
    # Create a subscription for the dead letter topic
    gcloud pubsub subscriptions create dead-letter-subscription \
        --topic=dead-letter-topic \
        --project=$PROJECT_ID
    
    echo "Dead letter resources created successfully!"
}

# Function to create resources for filtering example
create_filtering_resources() {
    echo "Creating resources for filtering example..."
    
    # Create a topic
    gcloud pubsub topics create filtered-topic --project=$PROJECT_ID
    
    # Create subscriptions with filters
    gcloud pubsub subscriptions create high-priority-subscription \
        --topic=filtered-topic \
        --filter="attributes.priority = \"high\"" \
        --project=$PROJECT_ID
    
    gcloud pubsub subscriptions create error-subscription \
        --topic=filtered-topic \
        --filter="attributes.type = \"error\"" \
        --project=$PROJECT_ID
    
    gcloud pubsub subscriptions create user-events-subscription \
        --topic=filtered-topic \
        --filter="attributes.user_id != \"\"" \
        --project=$PROJECT_ID
    
    echo "Filtering resources created successfully!"
}

# Function to create resources for exactly-once delivery example
create_exactly_once_resources() {
    echo "Creating resources for exactly-once delivery example..."
    
    # Create a topic
    gcloud pubsub topics create exactly-once-topic --project=$PROJECT_ID
    
    # Create a subscription with exactly-once delivery
    gcloud pubsub subscriptions create exactly-once-subscription \
        --topic=exactly-once-topic \
        --project=$PROJECT_ID \
        --exactly-once-delivery
    
    echo "Exactly-once delivery resources created successfully!"
}

# Function to list all Pub/Sub resources
list_resources() {
    echo "Listing all Pub/Sub topics..."
    gcloud pubsub topics list --project=$PROJECT_ID
    
    echo -e "\nListing all Pub/Sub subscriptions..."
    gcloud pubsub subscriptions list --project=$PROJECT_ID
    
    echo -e "\nListing all Pub/Sub schemas..."
    gcloud pubsub schemas list --project=$PROJECT_ID
}

# Function to clean up all created resources
cleanup_resources() {
    echo "Cleaning up all Pub/Sub resources..."
    
    # Delete subscriptions
    gcloud pubsub subscriptions delete basic-pull-subscription --project=$PROJECT_ID
    # gcloud pubsub subscriptions delete basic-push-subscription --project=$PROJECT_ID
    gcloud pubsub subscriptions delete ordered-subscription --project=$PROJECT_ID
    gcloud pubsub subscriptions delete schema-subscription --project=$PROJECT_ID
    gcloud pubsub subscriptions delete main-subscription --project=$PROJECT_ID
    gcloud pubsub subscriptions delete dead-letter-subscription --project=$PROJECT_ID
    gcloud pubsub subscriptions delete high-priority-subscription --project=$PROJECT_ID
    gcloud pubsub subscriptions delete error-subscription --project=$PROJECT_ID
    gcloud pubsub subscriptions delete user-events-subscription --project=$PROJECT_ID
    gcloud pubsub subscriptions delete exactly-once-subscription --project=$PROJECT_ID
    
    # Delete topics
    gcloud pubsub topics delete basic-topic --project=$PROJECT_ID
    gcloud pubsub topics delete ordered-topic --project=$PROJECT_ID
    gcloud pubsub topics delete schema-topic --project=$PROJECT_ID
    gcloud pubsub topics delete main-topic --project=$PROJECT_ID
    gcloud pubsub topics delete dead-letter-topic --project=$PROJECT_ID
    gcloud pubsub topics delete filtered-topic --project=$PROJECT_ID
    gcloud pubsub topics delete exactly-once-topic --project=$PROJECT_ID
    
    # Delete schemas
    gcloud pubsub schemas delete user-schema --project=$PROJECT_ID
    
    echo "Cleanup completed!"
}

# Main script execution
case "$1" in
    create_basic_resources)
        create_basic_resources
        ;;
    create_ordered_resources)
        create_ordered_resources
        ;;
    create_schema_resources)
        create_schema_resources
        ;;
    create_dead_letter_resources)
        create_dead_letter_resources
        ;;
    create_filtering_resources)
        create_filtering_resources
        ;;
    create_exactly_once_resources)
        create_exactly_once_resources
        ;;
    list_resources)
        list_resources
        ;;
    cleanup_resources)
        cleanup_resources
        ;;
    create_all)
        create_basic_resources
        create_ordered_resources
        create_schema_resources
        create_dead_letter_resources
        create_filtering_resources
        create_exactly_once_resources
        ;;
    *)
        echo "Usage: $0 {create_basic_resources|create_ordered_resources|create_schema_resources|create_dead_letter_resources|create_filtering_resources|create_exactly_once_resources|list_resources|cleanup_resources|create_all}"
        exit 1
        ;;
esac

exit 0