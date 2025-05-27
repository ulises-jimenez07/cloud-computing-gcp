#!/usr/bin/env python3
"""
Advanced Google Cloud Pub/Sub Publisher Example

This script demonstrates advanced publishing features of Google Cloud Pub/Sub:
- Message ordering with ordering keys
- Batch settings for efficient publishing
- Retry settings for reliability
- Custom attributes for message filtering
- Publishing with callbacks
"""

import argparse
import json
import os
import random
import time
import uuid
from typing import Dict, List, Optional, Any

from google.api_core.exceptions import GoogleAPIError
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.publisher.futures import Future
from google.cloud.pubsub_v1.types import BatchSettings, PublisherOptions

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class PubSubPublisher:
    """A class for publishing messages to Google Cloud Pub/Sub with advanced features."""

    def __init__(
        self,
        project_id: str,
        topic_id: str,
        batch_settings: Optional[BatchSettings] = None,
        retry_settings: Optional[Dict[str, Any]] = None,
        enable_message_ordering: bool = False,
    ):
        """Initialize the PubSubPublisher.

        Args:
            project_id: Your Google Cloud project ID
            topic_id: The ID of the Pub/Sub topic to publish to
            batch_settings: Optional custom batch settings
            retry_settings: Optional custom retry settings
            enable_message_ordering: Whether to enable message ordering
        """
        self.project_id = project_id
        self.topic_id = topic_id

        # Configure publisher client options
        client_options = {}

        # Configure batch settings
        if batch_settings is None:
            # Default batch settings
            batch_settings = BatchSettings(
                max_messages=100,  # Maximum number of messages in a batch
                max_bytes=1024 * 1024,  # Maximum batch size in bytes (1 MB)
                max_latency=0.1,  # Maximum batch latency in seconds
            )

        # Configure retry settings
        if retry_settings is None:
            # Default retry settings
            retry_settings = {
                "initial_retry_delay": 0.1,  # seconds
                "retry_delay_multiplier": 1.3,
                "max_retry_delay": 60.0,  # seconds
                "initial_rpc_timeout": 5.0,  # seconds
                "rpc_timeout_multiplier": 1.0,
                "max_rpc_timeout": 600.0,  # seconds
                "total_timeout": 600.0,  # seconds
            }

        # Create publisher options
        publisher_options = PublisherOptions(
            enable_message_ordering=enable_message_ordering,
            flow_control=batch_settings,
        )

        # Initialize the publisher client
        self.publisher = pubsub_v1.PublisherClient(
            publisher_options=publisher_options,
            # client_options=client_options,
        )

        # Get the topic path
        self.topic_path = self.publisher.topic_path(project_id, topic_id)

        # Store futures for tracking published messages
        self.futures = []

    def get_callback(self, message_id: str, data: Dict) -> callable:
        """Create a callback for the published message future.

        Args:
            message_id: The ID of the message being published
            data: The message data

        Returns:
            A callback function that logs the result of the publish call
        """

        def callback(future: Future) -> None:
            try:
                # Get the message ID from the future
                published_message_id = future.result()
                print(
                    f"Message {message_id} published successfully with ID: {published_message_id}"
                )
                print(f"  Content: {json.dumps(data)[:50]}...")
            except Exception as e:
                print(f"Publishing message {message_id} failed with error: {e}")

        return callback

    def publish_message(
        self,
        data: Dict,
        ordering_key: Optional[str] = None,
        attributes: Optional[Dict[str, str]] = None,
    ) -> Future:
        """Publish a message to the Pub/Sub topic.

        Args:
            data: The message data to publish
            ordering_key: Optional key for ordering messages
            attributes: Optional message attributes

        Returns:
            A Future object representing the published message
        """
        # Convert the message data to JSON and encode as bytes
        message_json = json.dumps(data)
        message_bytes = message_json.encode("utf-8")

        # Prepare publish arguments
        publish_args = {
            "data": message_bytes,
        }

        # Add ordering key if provided
        if ordering_key:
            publish_args["ordering_key"] = ordering_key

        # Add attributes if provided
        if attributes:
            publish_args.update(attributes)

        # Generate a message ID for tracking
        message_id = str(uuid.uuid4())

        try:
            # Publish the message
            future = self.publisher.publish(self.topic_path, **publish_args)

            # Add a callback to the future
            future.add_done_callback(self.get_callback(message_id, data))

            # Store the future
            self.futures.append(future)

            return future

        except Exception as e:
            print(f"Error publishing message {message_id}: {e}")
            raise

    def publish_ordered_messages(
        self, messages: List[Dict], ordering_key: str, attributes: Optional[Dict[str, str]] = None
    ) -> None:
        """Publish multiple messages with the same ordering key.

        Args:
            messages: List of message data dictionaries to publish
            ordering_key: The key for ordering messages
            attributes: Optional message attributes
        """
        print(f"Publishing {len(messages)} ordered messages with key: {ordering_key}")

        try:
            for i, message in enumerate(messages):
                # Add sequence number to the message
                message["sequence_number"] = i + 1
                message["total_messages"] = len(messages)

                # Publish the message with the ordering key
                self.publish_message(message, ordering_key, attributes)

                # Small delay between messages
                time.sleep(0.01)

            print(f"All ordered messages with key {ordering_key} published successfully!")

        except Exception as e:
            print(f"Error publishing ordered messages: {e}")

            # Resume publishing for the ordering key if an error occurs
            self.publisher.resume_publish(ordering_key)

    def publish_with_attributes(
        self, messages: List[Dict], attribute_generators: Dict[str, callable]
    ) -> None:
        """Publish messages with dynamically generated attributes.

        Args:
            messages: List of message data dictionaries to publish
            attribute_generators: Dictionary of attribute name to generator function
        """
        print(f"Publishing {len(messages)} messages with dynamic attributes")

        for message in messages:
            # Generate attributes for this message
            attributes = {}
            for attr_name, generator_func in attribute_generators.items():
                attributes[attr_name] = generator_func()

            # Publish the message with the generated attributes
            self.publish_message(message, attributes=attributes)

        print(f"All messages with attributes published successfully!")

    def wait_for_all_messages(self) -> None:
        """Wait for all published messages to be acknowledged."""
        print(f"Waiting for {len(self.futures)} messages to be acknowledged...")

        # Process the futures in batches to avoid blocking
        for i, future in enumerate(self.futures):
            try:
                future.result()
                if (i + 1) % 10 == 0:
                    print(f"Processed {i + 1}/{len(self.futures)} messages")
            except Exception as e:
                print(f"Message {i} failed: {e}")

        print("All messages processed!")

        # Clear the futures list
        self.futures = []


def generate_sample_messages(count: int, categories: List[str]) -> List[Dict]:
    """Generate sample messages for demonstration.

    Args:
        count: Number of messages to generate
        categories: List of categories to choose from

    Returns:
        List of message dictionaries
    """
    messages = []

    for i in range(count):
        # Generate a random message
        message = {
            "id": str(uuid.uuid4()),
            "index": i,
            "category": random.choice(categories),
            "value": random.randint(1, 1000),
            "timestamp": time.time(),
            "is_valid": random.random() > 0.1,  # 10% chance of being invalid
            "nested": {
                "field1": random.random(),
                "field2": "sample text",
                "field3": [random.randint(1, 100) for _ in range(3)],
            },
        }

        messages.append(message)

    return messages


def main():
    """Main function to demonstrate advanced Pub/Sub publishing."""
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
        default="ordered-topic",
    )
    parser.add_argument(
        "--count",
        help="Number of messages to publish per group",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--enable-ordering",
        help="Enable message ordering",
        action="store_true",
    )
    args = parser.parse_args()

    # Configure batch settings for efficient publishing
    batch_settings = BatchSettings(
        max_messages=100,
        max_bytes=1024 * 1024,  # 1 MB
        max_latency=0.1,  # 100 ms
    )

    # Create the publisher
    publisher = PubSubPublisher(
        args.project_id,
        args.topic_id,
        batch_settings=batch_settings,
        enable_message_ordering=args.enable_ordering,
    )

    # Categories for sample messages
    categories = ["sports", "news", "entertainment", "technology", "science"]

    # Generate sample messages
    messages = generate_sample_messages(args.count, categories)

    # Demonstrate publishing with ordering keys (if enabled)
    if args.enable_ordering:
        # Group messages by category
        messages_by_category = {}
        for message in messages:
            category = message["category"]
            if category not in messages_by_category:
                messages_by_category[category] = []
            messages_by_category[category].append(message)

        # Publish messages with ordering by category
        for category, category_messages in messages_by_category.items():
            # Use category as the ordering key
            publisher.publish_ordered_messages(
                category_messages,
                ordering_key=category,
                attributes={"type": "ordered", "category": category},
            )
    else:
        # Demonstrate publishing with dynamic attributes
        def random_priority():
            return random.choice(["high", "medium", "low"])

        def random_region():
            return random.choice(["us", "eu", "asia"])

        def random_device_type():
            return random.choice(["mobile", "desktop", "tablet", "iot"])

        # Define attribute generators
        attribute_generators = {
            "priority": random_priority,
            "region": random_region,
            "device_type": random_device_type,
            "timestamp": lambda: str(int(time.time())),
        }

        # Publish messages with dynamic attributes
        publisher.publish_with_attributes(messages, attribute_generators)

    # Wait for all messages to be acknowledged
    publisher.wait_for_all_messages()


if __name__ == "__main__":
    main()
