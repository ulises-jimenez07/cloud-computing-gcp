#!/usr/bin/env python
"""
Pub/Sub Message Publisher for Testing Streaming Pipeline

This script publishes sample messages to a Google Cloud Pub/Sub topic
to test the streaming_pipeline.py example.
"""

import argparse
import json
import random
import time
from datetime import datetime

from google.cloud import pubsub_v1


def generate_message():
    """Generate a random sample message."""
    categories = ["electronics", "home", "sports", "fashion", "health"]

    message = {
        "id": f"msg-{random.randint(1000, 9999)}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": random.choice(categories),
        "value": round(random.uniform(1.0, 100.0), 2),
        "quantity": random.randint(1, 10),
        "status": random.choice(["active", "pending", "completed"]),
    }

    return message


def publish_messages(project_id, topic_id, num_messages, delay=1):
    """
    Publish messages to a Pub/Sub topic.

    Args:
        project_id: Google Cloud project ID
        topic_id: Pub/Sub topic ID
        num_messages: Number of messages to publish
        delay: Delay between messages in seconds
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    print(f"Publishing {num_messages} messages to {topic_path}")

    for i in range(num_messages):
        message = generate_message()
        data = json.dumps(message).encode("utf-8")

        future = publisher.publish(topic_path, data)
        message_id = future.result()

        print(f"Published message {i+1}/{num_messages}: {message_id}")
        print(f"Message content: {message}")

        if i < num_messages - 1:
            time.sleep(delay)

    print(f"Finished publishing {num_messages} messages")


def main():
    parser = argparse.ArgumentParser(description="Publish sample messages to a Pub/Sub topic")
    parser.add_argument("--project", required=True, help="Google Cloud project ID")
    parser.add_argument("--topic", required=True, help="Pub/Sub topic ID")
    parser.add_argument(
        "--messages", type=int, default=10, help="Number of messages to publish (default: 10)"
    )
    parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between messages in seconds (default: 1.0)"
    )

    args = parser.parse_args()

    publish_messages(args.project, args.topic, args.messages, args.delay)


if __name__ == "__main__":
    main()
