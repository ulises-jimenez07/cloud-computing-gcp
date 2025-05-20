import time
import json
import random
import os
from google.cloud import pubsub_v1


class PubSubPublisher:
    """
    A module for publishing messages to a Google Cloud Pub/Sub topic.
    """

    def __init__(self, project_id: str, topic_id: str):
        """
        Initializes the PubSubPublisher.

        Args:
            project_id: The ID of your Google Cloud project.
            topic_id: The ID of the Pub/Sub topic.
        """
        self.project_id = project_id
        self.topic_id = topic_id
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_id)
        self.order_counters = {}

    def publish_audio_chunk(self, user_id: str, chunk_data: str) -> None:
        """
        Publishes an audio chunk to Pub/Sub.

        Args:
            user_id: The ID of the user.
            chunk_data: The audio chunk data (e.g., base64 encoded).
        """
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
        """
        Publishes an end-of-stream message to Pub/Sub.

        Args:
            user_id: The ID of the user.
        """
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
        """
        Simulates sending audio chunks and an end-of-stream message.

        Args:
            user_id: The ID of the user.
            audio_chunks: A list of audio chunk data.
            delay: The delay in seconds between chunks.
        """
        print(f"Simulating audio stream for user: {user_id}")
        for chunk in audio_chunks:
            self.publish_audio_chunk(user_id, chunk)
            time.sleep(delay)

        print(f"Simulating end of stream for user: {user_id}")
        self.publish_end_of_stream(user_id)
        print(f"Publishing complete for user: {user_id}")


if __name__ == "__main__":
    project_id = "[PROJECT_ID]"
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
