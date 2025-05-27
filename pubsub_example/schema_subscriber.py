#!/usr/bin/env python3
"""
Google Cloud Pub/Sub Schema Subscriber Example

This script demonstrates how to subscribe to and receive messages from a Google Cloud Pub/Sub
subscription with schema validation. It shows how to process messages that conform to an Avro schema.
"""

import argparse
import json
import os
import time
from concurrent.futures import TimeoutError
from typing import Dict, Optional, Any

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class SchemaSubscriber:
    """A class for subscribing to a Google Cloud Pub/Sub topic with schema validation."""

    def __init__(self, project_id: str, subscription_id: str, timeout: Optional[int] = None):
        """Initialize the SchemaSubscriber.

        Args:
            project_id: Your Google Cloud project ID
            subscription_id: The ID of the Pub/Sub subscription
            timeout: How long to run the subscriber in seconds (None for indefinite)
        """
        self.project_id = project_id
        self.subscription_id = subscription_id
        self.timeout = timeout

        # Initialize the subscriber client
        self.subscriber = pubsub_v1.SubscriberClient()

        # Get the subscription path
        self.subscription_path = self.subscriber.subscription_path(project_id, subscription_id)

        # Get the subscription to check if it has a schema
        try:
            # Get the subscription
            subscription = self.subscriber.get_subscription(
                request={"subscription": self.subscription_path}
            )

            # Get the topic
            topic_path = subscription.topic
            topic = self.subscriber.get_topic(request={"topic": topic_path})

            # Check if the topic has a schema
            if hasattr(topic, "schema_settings") and topic.schema_settings:
                print(f"Topic has schema: {topic.schema_settings.schema}")
                print(f"Schema encoding: {topic.schema_settings.encoding}")
                self.has_schema = True
                self.schema_encoding = topic.schema_settings.encoding
            else:
                print(f"Topic does not have a schema attached")
                self.has_schema = False
                self.schema_encoding = None

        except Exception as e:
            print(f"Error getting subscription or topic: {e}")
            self.has_schema = False
            self.schema_encoding = None

        # Streaming pull future
        self.streaming_pull_future = None

        # Message count
        self.message_count = 0

    def process_user_message(self, user_data: Dict[str, Any]) -> None:
        """Process a user message that conforms to the User schema.

        Args:
            user_data: The user data from the message
        """
        # Extract user information
        user_id = user_data.get("id", "unknown")
        name = user_data.get("name", "unknown")
        email = user_data.get("email", "unknown")
        age = user_data.get("age", 0)
        active = user_data.get("active", False)

        # Print user details
        print(f"\nProcessing user: {name} (ID: {user_id})")
        print(f"  Email: {email}")
        print(f"  Age: {age}")
        print(f"  Active: {active}")

        # Process address if available
        address = user_data.get("address")
        if address:
            print(
                f"  Address: {address.get('street')}, {address.get('city')}, {address.get('state')} {address.get('zip')}, {address.get('country')}"
            )

        # Process phone numbers if available
        phone_numbers = user_data.get("phone_numbers", [])
        if phone_numbers:
            print("  Phone Numbers:")
            for phone in phone_numbers:
                print(f"    {phone.get('type')}: {phone.get('number')}")

        # Process preferences if available
        preferences = user_data.get("preferences", {})
        if preferences:
            print("  Preferences:")
            for key, value in preferences.items():
                print(f"    {key}: {value}")

        # Process tags if available
        tags = user_data.get("tags", [])
        if tags:
            print(f"  Tags: {', '.join(tags)}")

        # Simulate processing time
        processing_time = 0.2
        print(f"  Processing for {processing_time} seconds...")
        time.sleep(processing_time)

        print(f"  User {user_id} processed successfully!")

    def callback(self, message: Message) -> None:
        """Process received messages from a Pub/Sub subscription.

        Args:
            message: The received Pub/Sub message
        """
        self.message_count += 1

        try:
            print(f"\n{'=' * 50}")
            print(f"Received message {self.message_count} with ID: {message.message_id}")

            # Print message attributes if any
            if message.attributes:
                print("Message attributes:")
                for key, value in message.attributes.items():
                    print(f"  {key}: {value}")

            # Decode and parse the message data
            if self.schema_encoding == "JSON":
                # For JSON encoding, parse the JSON data
                message_data = json.loads(message.data.decode("utf-8"))
            else:
                # For other encodings, just decode as UTF-8 (simplified)
                message_data = json.loads(message.data.decode("utf-8"))

            # Process the message based on the schema
            self.process_user_message(message_data)

            # Acknowledge the message
            message.ack()
            print(f"Message acknowledged: {message.message_id}")

        except json.JSONDecodeError as e:
            print(f"Error decoding message data: {e}")
            # Negative acknowledge the message
            message.nack()

        except Exception as e:
            print(f"Error processing message: {e}")
            # Negative acknowledge the message
            message.nack()

        print(f"{'=' * 50}\n")

    def start(self) -> None:
        """Start listening for messages on the subscription."""
        # Configure flow control settings
        flow_control = pubsub_v1.types.FlowControl(
            max_messages=10,  # Maximum number of messages to hold in memory
            max_bytes=10 * 1024 * 1024,  # Maximum size of messages to hold in memory (10 MB)
        )

        # Subscribe to the subscription
        self.streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self.callback,
            flow_control=flow_control,
        )

        print(f"Listening for messages on {self.subscription_path}...")
        print("(Press Ctrl+C to stop)")

        try:
            if self.timeout is not None:
                print(f"Subscriber will run for {self.timeout} seconds...")
                time.sleep(self.timeout)
                self.stop()
            else:
                # Run indefinitely
                self.streaming_pull_future.result()
        except TimeoutError:
            self.stop("Subscriber timed out")
        except KeyboardInterrupt:
            self.stop("Subscriber interrupted by user")
        except Exception as e:
            self.stop(f"Subscriber error: {e}")

    def stop(self, reason: str = "Subscriber stopped") -> None:
        """Stop the subscriber and cancel the streaming pull future.

        Args:
            reason: The reason for stopping
        """
        print(f"\n{reason}")

        # Cancel the streaming pull future
        if self.streaming_pull_future:
            self.streaming_pull_future.cancel()
            try:
                self.streaming_pull_future.result()
            except Exception as e:
                print(f"Error during shutdown: {e}")

        # Close the subscriber client
        self.subscriber.close()

        print(f"Processed {self.message_count} messages")
        print("Subscriber client closed")


def main():
    """Main function to demonstrate Pub/Sub schema subscribing."""
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
        "--subscription-id",
        help="The ID of the Pub/Sub subscription to subscribe to",
        default="schema-subscription",
    )
    parser.add_argument(
        "--timeout",
        help="How long to run the subscriber in seconds (0 for indefinite)",
        type=int,
        default=60,
    )
    args = parser.parse_args()

    # Convert 0 to None for indefinite
    timeout = None if args.timeout == 0 else args.timeout

    try:
        # Create the schema subscriber
        subscriber = SchemaSubscriber(
            args.project_id,
            args.subscription_id,
            timeout,
        )

        # Start subscribing
        subscriber.start()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
