# GCP Pub/Sub Audio Streaming Demo

A simple demo showing how to stream audio chunks through Google Cloud Pub/Sub. Think of it as simulating multiple users sending voice recordings that get processed in real-time.

## Why Pub/Sub?

In real applications, you often have multiple services that need to talk to each other without being tightly coupled. Imagine a voice messaging app where users are constantly uploading audio. You don't want your upload service waiting around for the transcription service to finish processing before accepting the next upload.

Pub/Sub solves this by acting as a message broker. Publishers send data without knowing who's listening, and subscribers process messages at their own pace. If your transcription service crashes, messages wait in the queue instead of being lost. Need to scale up during peak hours? Add more subscribers. Want to add a new feature like sentiment analysis? Just add another subscriber to the same topic.

This demo simulates that pattern with streaming audio chunks, showing how multiple producers can send data that gets reliably delivered and processed by consumers, even when things arrive out of order or at different rates.

## What it does

- **Streamer** ([audio_streamer.py](audio_streamer.py)) - Simulates 4 users sending audio chunks with random delays (like they're speaking)
- **Subscriber** ([audio_subscriber.py](audio_subscriber.py)) - Receives the chunks, saves them temporarily, and reconstructs the full audio stream for each user

## Quick Setup

1. **Install dependencies**
   ```bash
   pip install google-cloud-pubsub
   ```

2. **Set up GCP authentication**
   ```bash
   gcloud auth application-default login
   ```

3. **Get your Project ID**
   ```bash
   export PROJECT_ID=$(gcloud config get-value project)
   ```

4. **Create the Pub/Sub infrastructure**

   Run the following commands to set up your topics and subscriptions:

   Create the topic:
   ```bash
   gcloud pubsub topics create audio-stream-topic --project=$PROJECT_ID
   ```

   Create the subscription:
   ```bash
   gcloud pubsub subscriptions create audio-stream-subscription \
       --topic=audio-stream-topic \
       --project=$PROJECT_ID
   ```

   Verify resources:
   ```bash
   gcloud pubsub topics list --project=$PROJECT_ID
   gcloud pubsub subscriptions list --project=$PROJECT_ID
   ```

5. **Update the scripts**

   The scripts are configured to use the `PROJECT_ID` environment variable you exported in Step 3. No manual file editing is required.

## Running the Demo

Open two terminals:

**Terminal 1 - Start the subscriber:**
```bash
python audio_subscriber.py
```

**Terminal 2 - Run the streamer:**
```bash
python audio_streamer.py
```

You'll see chunks being published in terminal 2 and received/processed in terminal 1. When a user's stream ends, the subscriber reconstructs and displays their complete audio data.

## What to expect

The streamer will publish messages like:
```
Published message ID: 123456789
```

The subscriber will show:
```
Saved chunk for user123 with order 0
End of stream detected for user: user123
Ordered chunks for user123:
chunk_0_data_for_user123chunk_1_data_for_user123...
```

## Cleanup

To avoid incurring charges, delete the resources when you're done:

```bash
# Delete the subscription
gcloud pubsub subscriptions delete audio-stream-subscription --project=$PROJECT_ID

# Delete the topic
gcloud pubsub topics delete audio-stream-topic --project=$PROJECT_ID
```

