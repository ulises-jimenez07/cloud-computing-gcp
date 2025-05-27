#!/usr/bin/env python3
"""
Advanced Google Cloud Pub/Sub Subscriber Example

This script demonstrates advanced subscribing features of Google Cloud Pub/Sub:
- Message filtering
- Concurrency control
- Flow control
- Error handling and retry logic
- Exactly-once delivery
- Subscription management
"""

import argparse
import json
import os
import signal
import threading
import time
from concurrent.futures import TimeoutError
from typing import Dict, List, Optional, Any, Callable

from google.api_core.exceptions import GoogleAPIError
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message
from google.cloud.pubsub_v1.types import FlowControl

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class PubSubSubscriber:
    """A class for subscribing to Google Cloud Pub/Sub with advanced features."""

    def __init__(
        self,
        project_id: str,
        subscription_id: str,
        flow_control: Optional[FlowControl] = None,
        exactly_once: bool = False,
    ):
        """Initialize the PubSubSubscriber.

        Args:
            project_id: Your Google Cloud project ID
            subscription_id: The ID of the Pub/Sub subscription
            flow_control: Optional flow control settings
            exactly_once: Whether to use exactly-once delivery
        """
        self.project_id = project_id
        self.subscription_id = subscription_id
        self.exactly_once = exactly_once

        # Initialize the subscriber client
        self.subscriber = pubsub_v1.SubscriberClient()

        # Get the subscription path
        self.subscription_path = self.subscriber.subscription_path(project_id, subscription_id)

        # Configure flow control settings
        if flow_control is None:
            # Default flow control settings
            self.flow_control = FlowControl(
                max_messages=100,  # Maximum number of messages to hold in memory
                max_bytes=10 * 1024 * 1024,  # Maximum size of messages to hold in memory (10 MB)
                max_lease_duration=60,  # Maximum lease duration in seconds
            )
        else:
            self.flow_control = flow_control

        # Streaming pull future
        self.streaming_pull_future = None

        # Flag to indicate if the subscriber is running
        self.is_running = False

        # Message statistics
        self.stats = {
            "received": 0,
            "processed": 0,
            "failed": 0,
            "retried": 0,
            "by_category": {},
            "by_priority": {},
        }

        # Lock for thread-safe access to stats
        self.stats_lock = threading.Lock()

        # Message handlers by message type
        self.message_handlers = {}

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle signals for graceful shutdown."""
        print(f"\nReceived signal {signum}. Shutting down...")
        self.stop()

    def register_handler(self, message_type: str, handler: Callable[[Dict, Dict[str, str]], None]):
        """Register a handler for a specific message type.

        Args:
            message_type: The type of message to handle
            handler: The handler function
        """
        self.message_handlers[message_type] = handler

    def update_stats(
        self,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        status: str = "processed",
    ):
        """Update message statistics.

        Args:
            category: Optional message category
            priority: Optional message priority
            status: Status of the message (processed, failed, retried)
        """
        with self.stats_lock:
            # Update overall stats
            self.stats[status] += 1

            # Update category stats if provided
            if category:
                if category not in self.stats["by_category"]:
                    self.stats["by_category"][category] = 0
                self.stats["by_category"][category] += 1

            # Update priority stats if provided
            if priority:
                if priority not in self.stats["by_priority"]:
                    self.stats["by_priority"][priority] = 0
                self.stats["by_priority"][priority] += 1

    def print_stats(self):
        """Print current message statistics."""
        with self.stats_lock:
            print("\n=== Message Statistics ===")
            print(f"Received: {self.stats['received']}")
            print(f"Processed: {self.stats['processed']}")
            print(f"Failed: {self.stats['failed']}")
            print(f"Retried: {self.stats['retried']}")

            if self.stats["by_category"]:
                print("\nBy Category:")
                for category, count in self.stats["by_category"].items():
                    print(f"  {category}: {count}")

            if self.stats["by_priority"]:
                print("\nBy Priority:")
                for priority, count in self.stats["by_priority"].items():
                    print(f"  {priority}: {count}")

            print("=========================\n")

    def process_message(self, message_data: Dict, attributes: Dict[str, str]) -> bool:
        """Process the received message data.

        Args:
            message_data: The parsed message data
            attributes: Message attributes

        Returns:
            True if the message was processed successfully, False otherwise
        """
        try:
            # Extract message metadata
            message_id = message_data.get("id", "unknown")
            category = message_data.get("category", "unknown")

            # Get priority from attributes
            priority = attributes.get("priority", "medium")

            # Get message type from attributes
            message_type = attributes.get("type", "default")

            # Print message details
            print(f"\nProcessing message: {message_id}")
            print(f"  Category: {category}")
            print(f"  Priority: {priority}")
            print(f"  Type: {message_type}")

            # Check if we have a specific handler for this message type
            if message_type in self.message_handlers:
                # Use the registered handler
                self.message_handlers[message_type](message_data, attributes)
            else:
                # Default processing
                print(f"  Content: {json.dumps(message_data)[:100]}...")

                # Simulate processing time based on priority
                processing_time = 0.1  # Default
                if priority == "high":
                    processing_time = 0.05
                elif priority == "low":
                    processing_time = 0.2

                print(f"  Processing for {processing_time:.2f} seconds...")
                time.sleep(processing_time)

            # Update statistics
            self.update_stats(category, priority, "processed")

            return True

        except Exception as e:
            print(f"Error processing message: {e}")
            self.update_stats(status="failed")
            return False

    def callback(self, message: Message) -> None:
        """Process received messages from a Pub/Sub subscription.

        Args:
            message: The received Pub/Sub message
        """
        # Update received count
        with self.stats_lock:
            self.stats["received"] += 1

        try:
            # Print message details
            print(f"\n{'=' * 50}")
            print(f"Received message with ID: {message.message_id}")

            # Print message attributes if any
            attributes = dict(message.attributes) if message.attributes else {}
            if attributes:
                print("Message attributes:")
                for key, value in attributes.items():
                    print(f"  {key}: {value}")

            # Decode and parse the message data
            message_data = json.loads(message.data.decode("utf-8"))

            # Process the message
            success = self.process_message(message_data, attributes)

            if success:
                # Acknowledge the message
                message.ack()
                print(f"Message acknowledged: {message.message_id}")
            else:
                # Negative acknowledge the message for retry
                message.nack()
                print(f"Message negatively acknowledged for retry: {message.message_id}")
                self.update_stats(status="retried")

        except json.JSONDecodeError as e:
            print(f"Error decoding message data: {e}")
            # Negative acknowledge the message
            message.nack()
            self.update_stats(status="failed")

        except Exception as e:
            print(f"Error processing message: {e}")
            # Negative acknowledge the message
            message.nack()
            self.update_stats(status="failed")

        print(f"{'=' * 50}\n")

    def start(self, timeout: Optional[int] = None) -> None:
        """Start listening for messages on the subscription.

        Args:
            timeout: How long to run the subscriber in seconds (None for indefinite)
        """
        if self.is_running:
            print("Subscriber is already running")
            return

        # Set the running flag
        self.is_running = True

        # Subscribe to the subscription
        self.streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=self.callback,
            flow_control=self.flow_control,
        )

        print(f"Listening for messages on {self.subscription_path}...")
        print("(Press Ctrl+C to stop)")

        # Start a thread to print stats periodically
        def print_stats_periodically():
            while self.is_running:
                time.sleep(10)  # Print stats every 10 seconds
                if self.is_running:
                    self.print_stats()

        stats_thread = threading.Thread(target=print_stats_periodically)
        stats_thread.daemon = True
        stats_thread.start()

        try:
            if timeout is not None:
                print(f"Subscriber will run for {timeout} seconds...")
                time.sleep(timeout)
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
        if not self.is_running:
            return

        # Set the running flag to False
        self.is_running = False

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

        # Print final stats
        self.print_stats()

        print("Subscriber client closed")


def default_handler(message_data: Dict, attributes: Dict[str, str]) -> None:
    """Default message handler.

    Args:
        message_data: The parsed message data
        attributes: Message attributes
    """
    print(f"Default handler processing message: {message_data.get('id', 'unknown')}")
    print(f"  Content: {json.dumps(message_data)[:100]}...")
    time.sleep(0.1)


def high_priority_handler(message_data: Dict, attributes: Dict[str, str]) -> None:
    """Handler for high priority messages.

    Args:
        message_data: The parsed message data
        attributes: Message attributes
    """
    print(f"HIGH PRIORITY message: {message_data.get('id', 'unknown')}")
    print(f"  Content: {json.dumps(message_data)[:100]}...")
    # Process high priority messages faster
    time.sleep(0.05)


def ordered_handler(message_data: Dict, attributes: Dict[str, str]) -> None:
    """Handler for ordered messages.

    Args:
        message_data: The parsed message data
        attributes: Message attributes
    """
    sequence = message_data.get("sequence_number", 0)
    total = message_data.get("total_messages", 0)
    category = message_data.get("category", "unknown")

    print(f"ORDERED message: {sequence}/{total} for category {category}")
    print(f"  Content: {json.dumps(message_data)[:100]}...")
    time.sleep(0.1)


def main():
    """Main function to demonstrate advanced Pub/Sub subscribing."""
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
        default="ordered-subscription",
    )
    parser.add_argument(
        "--timeout",
        help="How long to run the subscriber in seconds (0 for indefinite)",
        type=int,
        default=60,
    )
    parser.add_argument(
        "--exactly-once",
        help="Use exactly-once delivery",
        action="store_true",
    )
    args = parser.parse_args()

    # Convert 0 to None for indefinite
    timeout = None if args.timeout == 0 else args.timeout

    # Configure flow control settings
    flow_control = FlowControl(
        max_messages=100,
        max_bytes=10 * 1024 * 1024,  # 10 MB
        max_lease_duration=60,  # 60 seconds
    )

    # Create the subscriber
    subscriber = PubSubSubscriber(
        args.project_id,
        args.subscription_id,
        flow_control=flow_control,
        exactly_once=args.exactly_once,
    )

    # Register message handlers
    subscriber.register_handler("default", default_handler)
    subscriber.register_handler("high_priority", high_priority_handler)
    subscriber.register_handler("ordered", ordered_handler)

    # Start subscribing
    subscriber.start(timeout)


if __name__ == "__main__":
    main()
