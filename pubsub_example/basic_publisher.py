#!/usr/bin/env python3
"""
Basic Google Cloud Pub/Sub Publisher Example

This script demonstrates how to publish messages to a Google Cloud Pub/Sub topic.
It shows the fundamental concepts of publishing messages with minimal configuration.
"""

import argparse
import json
import os
import time
from typing import Dict, List, Optional

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.publisher.futures import Future

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def get_callback(future: Future, message_id: str) -> callable:
    """Create a callback for the published message future.

    Args:
        future: The future returned from the publish call
        message_id: The ID of the message being published

    Returns:
        A callback function that logs the result of the publish call
    """

    def callback(future: Future) -> None:
        try:
            # Get the message ID from the future
            message_id = future.result()
            print(f"Message published successfully with ID: {message_id}")
        except Exception as e:
            print(f"Publishing message failed with error: {e}")

    return callback


def publish_message(
    project_id: str, topic_id: str, message_data: Dict, attributes: Optional[Dict[str, str]] = None
) -> Future:
    """Publish a message to a Pub/Sub topic.

    Args:
        project_id: Your Google Cloud project ID
        topic_id: The ID of the Pub/Sub topic to publish to
        message_data: The message data to publish (will be converted to JSON)
        attributes: Optional message attributes as key-value pairs

    Returns:
        A Future object representing the published message
    """
    # Initialize the publisher client
    publisher = pubsub_v1.PublisherClient()

    # Get the topic path
    topic_path = publisher.topic_path(project_id, topic_id)

    # Convert the message data to JSON and encode as bytes
    message_json = json.dumps(message_data)
    message_bytes = message_json.encode("utf-8")

    # Publish the message
    future = publisher.publish(topic_path, data=message_bytes, **attributes if attributes else {})

    # Add a callback to the future
    message_id = f"message-{time.time()}"
    future.add_done_callback(get_callback(future, message_id))

    return future


def publish_multiple_messages(
    project_id: str,
    topic_id: str,
    messages: List[Dict],
    attributes: Optional[Dict[str, str]] = None,
) -> None:
    """Publish multiple messages to a Pub/Sub topic.

    Args:
        project_id: Your Google Cloud project ID
        topic_id: The ID of the Pub/Sub topic to publish to
        messages: List of message data dictionaries to publish
        attributes: Optional message attributes as key-value pairs
    """
    # Keep track of futures
    futures = []

    # Publish each message
    for message in messages:
        future = publish_message(project_id, topic_id, message, attributes)
        futures.append(future)

    # Wait for all messages to be published
    for future in futures:
        future.result()

    print(f"Published {len(messages)} messages successfully!")


def main():
    """Main function to demonstrate Pub/Sub publishing."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project-id",
        help="Your Google Cloud project ID",
        default=os.getenv("GOOGLE_CLOUD_PROJECT", "YOUR_PROJECT_ID"),
    )
    parser.add_argument(
        "--topic-id",
        help="The ID of the Pub/Sub topic to publish to",
        default="basic-topic",
    )
    parser.add_argument(
        "--count",
        help="Number of messages to publish",
        type=int,
        default=10,
    )
    args = parser.parse_args()

    # Generate sample messages
    messages = []
    for i in range(args.count):
        message = {
            "message_id": f"msg-{i}",
            "text": f"This is message #{i}",
            "timestamp": time.time(),
            "importance": "high" if i % 3 == 0 else "medium" if i % 3 == 1 else "low",
        }
        messages.append(message)

    # Add some attributes to all messages
    attributes = {
        "source": "basic_publisher.py",
        "type": "example",
        "batch": "true",
    }

    # Publish the messages
    print(f"Publishing {args.count} messages to {args.topic_id}...")
    publish_multiple_messages(args.project_id, args.topic_id, messages, attributes)


if __name__ == "__main__":
    main()
