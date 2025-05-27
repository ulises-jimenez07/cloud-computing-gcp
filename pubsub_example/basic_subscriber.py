#!/usr/bin/env python3
"""
Basic Google Cloud Pub/Sub Subscriber Example

This script demonstrates how to subscribe to and receive messages from a Google Cloud Pub/Sub subscription.
It shows the fundamental concepts of subscribing with minimal configuration.
"""

import argparse
import json
import os
import time
from concurrent.futures import TimeoutError
from typing import Dict, Optional

from google.cloud import pubsub_v1

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def process_message(message_data: Dict) -> None:
    """Process the received message data.

    In a real application, this is where you would implement your business logic
    to handle the message.

    Args:
        message_data: The parsed message data
    """
    # Print the message details
    print(f"Received message: {json.dumps(message_data, indent=2)}")

    # Simulate processing time
    processing_time = 0.5  # seconds
    print(f"Processing message for {processing_time} seconds...")
    time.sleep(processing_time)

    print(f"Successfully processed message: {message_data.get('message_id', 'unknown')}")


def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    """Process received messages from a Pub/Sub subscription.

    Args:
        message: The received Pub/Sub message
    """
    print(f"\n{'=' * 50}")
    print(f"Received message with ID: {message.message_id}")

    # Print message attributes if any
    if message.attributes:
        print("Message attributes:")
        for key, value in message.attributes.items():
            print(f"  {key}: {value}")

    # Decode and parse the message data
    try:
        message_data = json.loads(message.data.decode("utf-8"))

        # Process the message
        process_message(message_data)

        # Acknowledge the message
        message.ack()
        print(f"Message acknowledged: {message.message_id}")

    except json.JSONDecodeError as e:
        print(f"Error decoding message data: {e}")
        # Negative acknowledge the message
        message.nack()
        print(f"Message negatively acknowledged: {message.message_id}")

    except Exception as e:
        print(f"Error processing message: {e}")
        # Negative acknowledge the message
        message.nack()
        print(f"Message negatively acknowledged: {message.message_id}")

    print(f"{'=' * 50}\n")


def subscribe_with_flow_control(
    project_id: str,
    subscription_id: str,
    timeout: Optional[int] = None,
    max_messages: Optional[int] = None,
) -> None:
    """Subscribe to a Pub/Sub subscription with flow control.

    Args:
        project_id: Your Google Cloud project ID
        subscription_id: The ID of the Pub/Sub subscription to subscribe to
        timeout: How long to run the subscriber in seconds (None for indefinite)
        max_messages: Maximum number of messages to receive (None for unlimited)
    """
    # Initialize the subscriber client
    subscriber = pubsub_v1.SubscriberClient()

    # Get the subscription path
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    # Configure flow control settings
    flow_control = pubsub_v1.types.FlowControl(
        max_messages=10,  # Maximum number of messages to hold in memory
        max_bytes=10 * 1024 * 1024,  # Maximum size of messages to hold in memory (10 MB)
    )

    # Message counter for max_messages limit
    message_count = 0

    def wrapped_callback(message):
        nonlocal message_count
        callback(message)
        message_count += 1

        # Stop after receiving max_messages if specified
        if max_messages is not None and message_count >= max_messages:
            print(f"Reached maximum message count ({max_messages}). Stopping...")
            streaming_pull_future.cancel()

    # Subscribe to the subscription
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=wrapped_callback,
        flow_control=flow_control,
    )

    print(f"Listening for messages on {subscription_path}...")
    print("(Press Ctrl+C to stop)")

    # Keep the main thread alive
    try:
        if timeout is not None:
            print(f"Subscriber will run for {timeout} seconds...")
            time.sleep(timeout)
            streaming_pull_future.cancel()
            print(f"Subscriber stopped after {timeout} seconds")
        else:
            # Run indefinitely
            streaming_pull_future.result()
    except TimeoutError:
        streaming_pull_future.cancel()
        print("Subscriber timed out")
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
        print("\nSubscriber stopped by user")
    finally:
        subscriber.close()
        print("Subscriber client closed")


def main():
    """Main function to demonstrate Pub/Sub subscribing."""
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
        default="basic-pull-subscription",
    )
    parser.add_argument(
        "--timeout",
        help="How long to run the subscriber in seconds (0 for indefinite)",
        type=int,
        default=60,
    )
    parser.add_argument(
        "--max-messages",
        help="Maximum number of messages to receive (0 for unlimited)",
        type=int,
        default=0,
    )
    args = parser.parse_args()

    # Convert 0 to None for indefinite/unlimited
    timeout = None if args.timeout == 0 else args.timeout
    max_messages = None if args.max_messages == 0 else args.max_messages

    # Start subscribing
    subscribe_with_flow_control(
        args.project_id,
        args.subscription_id,
        timeout,
        max_messages,
    )


if __name__ == "__main__":
    main()
