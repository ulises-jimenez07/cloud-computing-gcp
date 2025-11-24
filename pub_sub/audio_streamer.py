# This script simulates users streaming audio data to Cloud Pub/Sub by generating random chunks and publishing them.

import time
import json
import random
import os
from google.cloud import pubsub_v1


class PubSubPublisher:
    """Publishes messages to a Google Cloud Pub/Sub topic."""

    def __init__(self, project_id: str, topic_id: str):
        """Initializes the publisher with project and topic IDs."""
        self.project_id = project_id
        self.topic_id = topic_id
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_id)
        self.order_counters = {}

    def publish_audio_chunk(self, user_id: str, chunk_data: str) -> None:
        """Publishes a single audio chunk for a specific user."""
        if user_id not in self.order_counters:
            self.order_counters[user_id] = 0
        order_number = self.order_counters[user_id]
        self.order_counters[user_id] += 1

        message = {
            "userId": user_id,
            "type": "audioChunk",
            "data": chunk_data,
            "order": order_number,
        }
        message_data = json.dumps(message).encode("utf-8")
        future = self.publisher.publish(self.topic_path, message_data)
        print(f"Published message ID: {future.result()}")

    def publish_end_of_stream(self, user_id: str) -> None:
        """Publishes an end-of-stream message to signal completion."""
        message = {
            "userId": user_id,
            "type": "endOfStream",
        }
        message_data = json.dumps(message).encode("utf-8")
        future = self.publisher.publish(self.topic_path, message_data)
        print(f"Published end-of-stream message ID: {future.result()}")

    def simulate_audio_stream(
        self, user_id: str, audio_chunks: list[str], delay: float = 0.5
    ) -> None:
        """Simulates sending a sequence of audio chunks followed by an end-of-stream message."""
        print(f"Simulating audio stream for user: {user_id}")
        for chunk in audio_chunks:
            self.publish_audio_chunk(user_id, chunk)
            time.sleep(delay)

        print(f"Simulating end of stream for user: {user_id}")
        self.publish_end_of_stream(user_id)
        print(f"Publishing complete for user: {user_id}")


if __name__ == "__main__":
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        raise ValueError("PROJECT_ID environment variable is not set")
    topic_id = "audio-stream-topic"

    users = ["user123", "user456", "user789", "user101"]
    all_chunks = {}

    for user in users:
        num_chunks = random.randint(3, 10)  # Random number of chunks.
        chunks = [f"chunk_{i}_data_for_{user}" for i in range(num_chunks)]
        all_chunks[user] = chunks

    publisher = PubSubPublisher(project_id, topic_id)

    for user, chunks in all_chunks.items():
        publisher.simulate_audio_stream(
            user, chunks, delay=random.uniform(0.3, 1.5)
        )  # Random delays.
        time.sleep(random.uniform(1, 3))  # random delay between users.
