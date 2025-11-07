# GCP Pub/Sub Audio Streaming Demo

A simple demo showing how to stream audio chunks through Google Cloud Pub/Sub. Think of it as simulating multiple users sending voice recordings that get processed in real-time.

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

3. **Create the Pub/Sub infrastructure**

   Edit [pub_sub_commands.sh](pub_sub_commands.sh) and replace `project-id` with your actual GCP project ID, then run:
   ```bash
   bash pub_sub_commands.sh
   ```

4. **Update the scripts**

   In both Python files, replace `[PROJECT_ID]` with your actual project ID.

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

That's it! Now you've got a working Pub/Sub streaming pipeline.
