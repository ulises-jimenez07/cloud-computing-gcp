#!/usr/bin/env python3
"""
Google Cloud Pub/Sub Dead Letter Topic Example

This script demonstrates how to use dead letter topics in Google Cloud Pub/Sub.
It shows how to:
1. Publish messages to a main topic
2. Subscribe to the main topic with a subscription that has a dead letter policy
3. Process messages and intentionally fail some to trigger the dead letter policy
4. Subscribe to the dead letter topic to process failed messages
"""

import argparse
import json
import os
import random
import threading
import time
import uuid
from concurrent.futures import TimeoutError
from typing import Dict, List, Optional, Any, Tuple

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class DeadLetterPublisher:
    """A class for publishing messages to a Google Cloud Pub/Sub topic for dead letter testing."""

    def __init__(self, project_id: str, topic_id: str):
        """Initialize the DeadLetterPublisher.

        Args:
            project_id: Your Google Cloud project ID
            topic_id: The ID of the Pub/Sub topic to publish to
        """
        self.project_id = project_id
        self.topic_id = topic_id

        # Initialize the publisher client
        self.publisher = pubsub_v1.PublisherClient()

        # Get the topic path
        self.topic_path = self.publisher.topic_path(project_id, topic_id)

    def publish_message(self, message_data: Dict, should_fail: bool = False) -> str:
        """Publish a message to the Pub/Sub topic.

        Args:
            message_data: The message data to publish
            should_fail: Whether this message should be marked to fail processing

        Returns:
            The published message ID
        """
        # Add a flag to indicate if the message should fail processing
        message_data["should_fail"] = should_fail

        # Convert the message data to JSON and encode as bytes
        message_json = json.dumps(message_data)
        message_bytes = message_json.encode("utf-8")

        # Add attributes
        attributes = {
            "source": "dead_letter_example.py",
            "should_fail": str(should_fail).lower(),
        }

        try:
            # Publish the message
            future = self.publisher.publish(self.topic_path, data=message_bytes, **attributes)
            message_id = future.result()

            status = "WILL FAIL" if should_fail else "should succeed"
            print(f"Published message with ID: {message_id} ({status})")

            return message_id

        except Exception as e:
            print(f"Error publishing message: {e}")
            raise

    def publish_test_messages(self, count: int, fail_rate: float = 0.3) -> Tuple[int, int]:
        """Publish test messages with some intentionally marked to fail.

        Args:
            count: Number of messages to publish
            fail_rate: Percentage of messages that should be marked to fail (0.0 to 1.0)

        Returns:
            Tuple of (success_count, fail_count)
        """
        success_count = 0
        fail_count = 0

        for i in range(count):
            # Determine if this message should fail
            should_fail = random.random() < fail_rate

            # Create a message
            message = {
                "id": str(uuid.uuid4()),
                "index": i,
                "timestamp": time.time(),
                "content": f"Test message #{i}",
                "retry_count": 0,
            }

            # Publish the message
            try:
                self.publish_message(message, should_fail)

                if should_fail:
                    fail_count += 1
                else:
                    success_count += 1

                # Small delay between messages
                time.sleep(0.1)

            except Exception as e:
                print(f"Failed to publish message {i}: {e}")

        print(f"\nPublished {count} messages:")
        print(f"  {success_count} messages should succeed")
        print(f"  {fail_count} messages should fail and go to dead letter topic")

        return success_count, fail_count


class DeadLetterSubscriber:
    """A class for subscribing to a Google Cloud Pub/Sub topic with dead letter handling."""

    def __init__(
        self,
        project_id: str,
        subscription_id: str,
        is_dead_letter: bool = False,
        timeout: Optional[int] = None,
    ):
        """Initialize the DeadLetterSubscriber.

        Args:
            project_id: Your Google Cloud project ID
            subscription_id: The ID of the Pub/Sub subscription
            is_dead_letter: Whether this is a subscription to a dead letter topic
            timeout: How long to run the subscriber in seconds (None for indefinite)
        """
        self.project_id = project_id
        self.subscription_id = subscription_id
        self.is_dead_letter = is_dead_letter
        self.timeout = timeout

        # Initialize the subscriber client
        self.subscriber = pubsub_v1.SubscriberClient()

        # Get the subscription path
        self.subscription_path = self.subscriber.subscription_path(project_id, subscription_id)

        # Get the subscription to check if it has a dead letter policy
        try:
            subscription = self.subscriber.get_subscription(
                request={"subscription": self.subscription_path}
            )

            if hasattr(subscription, "dead_letter_policy") and subscription.dead_letter_policy:
                dead_letter_topic = subscription.dead_letter_policy.dead_letter_topic
                max_delivery_attempts = subscription.dead_letter_policy.max_delivery_attempts

                print(f"Subscription has dead letter policy:")
                print(f"  Dead letter topic: {dead_letter_topic}")
                print(f"  Max delivery attempts: {max_delivery_attempts}")
            elif not is_dead_letter:
                print(f"Warning: Subscription does not have a dead letter policy")

        except Exception as e:
            print(f"Error getting subscription: {e}")

        # Streaming pull future
        self.streaming_pull_future = None

        # Message statistics
        self.stats = {
            "received": 0,
            "succeeded": 0,
            "failed": 0,
        }

    def process_message(self, message_data: Dict, attributes: Dict[str, str]) -> bool:
        """Process the received message data.

        Args:
            message_data: The parsed message data
            attributes: Message attributes

        Returns:
            True if the message was processed successfully, False otherwise
        """
        message_id = message_data.get("id", "unknown")
        should_fail = message_data.get("should_fail", False)

        # For dead letter topic, always succeed
        if self.is_dead_letter:
            print(f"Processing dead letter message: {message_id}")
            print(f"  Original message failed processing and was moved to dead letter topic")
            print(f"  Content: {message_data.get('content', '')}")

            # Simulate recovery processing
            time.sleep(0.5)
            print(f"  Dead letter message processed successfully")
            return True

        # For main topic, check if the message should fail
        if should_fail:
            print(f"Processing message: {message_id} (intentionally failing)")
            print(
                f"  This message will be sent to the dead letter topic after max delivery attempts"
            )

            # Simulate processing failure
            time.sleep(0.2)
            print(f"  Message processing failed")
            return False
        else:
            print(f"Processing message: {message_id}")
            print(f"  Content: {message_data.get('content', '')}")

            # Simulate successful processing
            time.sleep(0.2)
            print(f"  Message processed successfully")
            return True

    def callback(self, message: Message) -> None:
        """Process received messages from a Pub/Sub subscription.

        Args:
            message: The received Pub/Sub message
        """
        self.stats["received"] += 1

        try:
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
                self.stats["succeeded"] += 1
            else:
                # Negative acknowledge the message for retry or dead letter
                message.nack()
                print(f"Message negatively acknowledged: {message.message_id}")
                self.stats["failed"] += 1

        except json.JSONDecodeError as e:
            print(f"Error decoding message data: {e}")
            # Negative acknowledge the message
            message.nack()
            self.stats["failed"] += 1

        except Exception as e:
            print(f"Error processing message: {e}")
            # Negative acknowledge the message
            message.nack()
            self.stats["failed"] += 1

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

        topic_type = "dead letter" if self.is_dead_letter else "main"
        print(f"Listening for messages on {topic_type} subscription: {self.subscription_path}...")
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

        # Print statistics
        topic_type = "Dead letter" if self.is_dead_letter else "Main"
        print(f"\n{topic_type} topic statistics:")
        print(f"  Received: {self.stats['received']}")
        print(f"  Succeeded: {self.stats['succeeded']}")
        print(f"  Failed: {self.stats['failed']}")

        print("Subscriber client closed")


def run_demo(args):
    """Run the dead letter demo.

    Args:
        args: Command line arguments
    """
    # Create the publisher
    publisher = DeadLetterPublisher(args.project_id, args.main_topic_id)

    # Publish test messages
    publisher.publish_test_messages(args.count, args.fail_rate)

    # Create and start the main subscriber
    main_subscriber = DeadLetterSubscriber(
        args.project_id,
        args.main_subscription_id,
        is_dead_letter=False,
        timeout=args.timeout,
    )

    # Create and start the dead letter subscriber
    dead_letter_subscriber = DeadLetterSubscriber(
        args.project_id,
        args.dead_letter_subscription_id,
        is_dead_letter=True,
        timeout=args.timeout,
    )

    # Start the subscribers in separate threads
    main_thread = threading.Thread(target=main_subscriber.start, name="MainSubscriber")

    dead_letter_thread = threading.Thread(
        target=dead_letter_subscriber.start, name="DeadLetterSubscriber"
    )

    # Start the threads
    main_thread.start()
    dead_letter_thread.start()

    # Wait for the threads to complete
    main_thread.join()
    dead_letter_thread.join()

    print("\nDead letter demo completed!")


def main():
    """Main function to demonstrate Pub/Sub dead letter topics."""
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
        "--main-topic-id",
        help="The ID of the main Pub/Sub topic",
        default="main-topic",
    )
    parser.add_argument(
        "--main-subscription-id",
        help="The ID of the main Pub/Sub subscription",
        default="main-subscription",
    )
    parser.add_argument(
        "--dead-letter-topic-id",
        help="The ID of the dead letter Pub/Sub topic",
        default="dead-letter-topic",
    )
    parser.add_argument(
        "--dead-letter-subscription-id",
        help="The ID of the dead letter Pub/Sub subscription",
        default="dead-letter-subscription",
    )
    parser.add_argument(
        "--count",
        help="Number of messages to publish",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--fail-rate",
        help="Percentage of messages that should fail (0.0 to 1.0)",
        type=float,
        default=0.3,
    )
    parser.add_argument(
        "--timeout",
        help="How long to run the subscribers in seconds",
        type=int,
        default=30,
    )
    parser.add_argument(
        "--publish-only",
        help="Only publish messages, don't start subscribers",
        action="store_true",
    )
    args = parser.parse_args()

    try:
        if args.publish_only:
            # Create the publisher
            publisher = DeadLetterPublisher(args.project_id, args.main_topic_id)

            # Publish test messages
            publisher.publish_test_messages(args.count, args.fail_rate)
        else:
            # Run the full demo
            run_demo(args)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
