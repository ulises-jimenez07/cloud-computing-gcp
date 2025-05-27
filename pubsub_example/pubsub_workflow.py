#!/usr/bin/env python3
"""
Google Cloud Pub/Sub End-to-End Workflow Example

This script demonstrates a complete end-to-end workflow using Google Cloud Pub/Sub:
1. Data ingestion: Simulates data collection and publishes to an ingestion topic
2. Data processing: Subscribes to the ingestion topic, processes data, and publishes to a results topic
3. Data consumption: Subscribes to the results topic and consumes the processed data

This example shows how Pub/Sub can be used as a messaging backbone for event-driven architectures.
"""

import argparse
import json
import os
import random
import threading
import time
import uuid
from concurrent.futures import TimeoutError
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.subscriber.message import Message

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# Define data models
class EventType(Enum):
    """Types of events in the system."""

    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    ORDER_PLACED = "order.placed"
    ORDER_SHIPPED = "order.shipped"
    ORDER_DELIVERED = "order.delivered"
    ORDER_CANCELED = "order.canceled"
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"
    INVENTORY_UPDATED = "inventory.updated"
    PRODUCT_VIEWED = "product.viewed"
    PRODUCT_ADDED_TO_CART = "product.added_to_cart"
    PRODUCT_REMOVED_FROM_CART = "product.removed_from_cart"


@dataclass
class Event:
    """Base event model."""

    id: str
    type: EventType
    timestamp: float
    source: str
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary."""
        result = asdict(self)
        result["type"] = self.type.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create an event from a dictionary."""
        # Convert string type to enum
        data["type"] = EventType(data["type"])
        return cls(**data)


@dataclass
class ProcessedEvent:
    """Processed event model."""

    original_event_id: str
    event_type: str
    processed_timestamp: float
    processing_time_ms: float
    results: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the processed event to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProcessedEvent":
        """Create a processed event from a dictionary."""
        return cls(**data)


# Data Ingestion Component
class DataIngestionPublisher:
    """Component that simulates data collection and publishes to an ingestion topic."""

    def __init__(self, project_id: str, topic_id: str):
        """Initialize the DataIngestionPublisher.

        Args:
            project_id: Your Google Cloud project ID
            topic_id: The ID of the ingestion Pub/Sub topic
        """
        self.project_id = project_id
        self.topic_id = topic_id

        # Initialize the publisher client
        self.publisher = pubsub_v1.PublisherClient()

        # Get the topic path
        self.topic_path = self.publisher.topic_path(project_id, topic_id)

        # Track published events
        self.published_events: List[Event] = []

    def publish_event(self, event: Event) -> str:
        """Publish an event to the ingestion topic.

        Args:
            event: The event to publish

        Returns:
            The published message ID
        """
        # Convert the event to a dictionary
        event_dict = event.to_dict()

        # Convert to JSON and encode as bytes
        message_json = json.dumps(event_dict)
        message_bytes = message_json.encode("utf-8")

        # Add attributes for filtering
        attributes = {
            "event_type": event.type.value,
            "source": event.source,
            "timestamp": str(int(event.timestamp)),
        }

        try:
            # Publish the message
            future = self.publisher.publish(self.topic_path, data=message_bytes, **attributes)
            message_id = future.result()

            print(f"Published event: {event.type.value} with ID: {message_id}")

            # Track the published event
            self.published_events.append(event)

            return message_id

        except Exception as e:
            print(f"Error publishing event: {e}")
            raise

    def generate_random_event(self) -> Event:
        """Generate a random event for simulation.

        Returns:
            A randomly generated event
        """
        # Choose a random event type
        event_type = random.choice(list(EventType))

        # Generate a random event ID
        event_id = str(uuid.uuid4())

        # Generate a timestamp
        timestamp = time.time()

        # Choose a random source
        sources = ["web", "mobile", "api", "system", "iot"]
        source = random.choice(sources)

        # Generate event data based on the event type
        data: Dict[str, Any] = {}

        if event_type.value.startswith("user."):
            data = {
                "user_id": str(uuid.uuid4()),
                "username": f"user_{random.randint(1000, 9999)}",
                "email": f"user{random.randint(1000, 9999)}@example.com",
            }

        elif event_type.value.startswith("order."):
            data = {
                "order_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "total_amount": round(random.uniform(10.0, 500.0), 2),
                "items": [
                    {
                        "product_id": str(uuid.uuid4()),
                        "quantity": random.randint(1, 5),
                        "price": round(random.uniform(5.0, 100.0), 2),
                    }
                    for _ in range(random.randint(1, 5))
                ],
            }

        elif event_type.value.startswith("payment."):
            data = {
                "payment_id": str(uuid.uuid4()),
                "order_id": str(uuid.uuid4()),
                "amount": round(random.uniform(10.0, 500.0), 2),
                "payment_method": random.choice(["credit_card", "paypal", "bank_transfer"]),
            }

        elif event_type.value.startswith("inventory."):
            data = {
                "product_id": str(uuid.uuid4()),
                "quantity": random.randint(0, 100),
                "warehouse_id": f"wh-{random.randint(1, 5)}",
            }

        elif event_type.value.startswith("product."):
            data = {
                "product_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()),
                "category": random.choice(["electronics", "clothing", "books", "home"]),
            }

        # Create the event
        event = Event(
            id=event_id,
            type=event_type,
            timestamp=timestamp,
            source=source,
            data=data,
        )

        return event

    def simulate_data_ingestion(self, count: int, delay: float = 0.5) -> None:
        """Simulate data ingestion by publishing random events.

        Args:
            count: Number of events to publish
            delay: Delay between events in seconds
        """
        print(f"Simulating data ingestion: {count} events")

        for i in range(count):
            # Generate a random event
            event = self.generate_random_event()

            # Publish the event
            self.publish_event(event)

            # Wait before publishing the next event
            time.sleep(delay)

        print(f"Data ingestion complete: {count} events published")


# Data Processing Component
class DataProcessingService:
    """Component that processes events from the ingestion topic and publishes results to a results topic."""

    def __init__(
        self,
        project_id: str,
        ingestion_subscription_id: str,
        results_topic_id: str,
        timeout: Optional[int] = None,
    ):
        """Initialize the DataProcessingService.

        Args:
            project_id: Your Google Cloud project ID
            ingestion_subscription_id: The ID of the ingestion Pub/Sub subscription
            results_topic_id: The ID of the results Pub/Sub topic
            timeout: How long to run the service in seconds (None for indefinite)
        """
        self.project_id = project_id
        self.ingestion_subscription_id = ingestion_subscription_id
        self.results_topic_id = results_topic_id
        self.timeout = timeout

        # Initialize the subscriber client
        self.subscriber = pubsub_v1.SubscriberClient()

        # Get the subscription path
        self.subscription_path = self.subscriber.subscription_path(
            project_id, ingestion_subscription_id
        )

        # Initialize the publisher client
        self.publisher = pubsub_v1.PublisherClient()

        # Get the results topic path
        self.results_topic_path = self.publisher.topic_path(project_id, results_topic_id)

        # Streaming pull future
        self.streaming_pull_future = None

        # Track processed events
        self.processed_events: List[ProcessedEvent] = []

        # Set of event IDs that have been processed
        self.processed_event_ids: Set[str] = set()

    def process_event(self, event: Event) -> ProcessedEvent:
        """Process an event and generate results.

        Args:
            event: The event to process

        Returns:
            The processed event
        """
        # Record the start time
        start_time = time.time()

        # Simulate processing time based on event type
        if event.type.value.startswith("user."):
            processing_time = random.uniform(0.05, 0.2)
        elif event.type.value.startswith("order."):
            processing_time = random.uniform(0.1, 0.5)
        elif event.type.value.startswith("payment."):
            processing_time = random.uniform(0.2, 0.7)
        else:
            processing_time = random.uniform(0.01, 0.1)

        # Simulate processing
        time.sleep(processing_time)

        # Generate processing results based on event type
        results: Dict[str, Any] = {}

        if event.type == EventType.USER_CREATED:
            results = {
                "user_id": event.data.get("user_id"),
                "welcome_email_sent": True,
                "account_status": "active",
            }

        elif event.type == EventType.ORDER_PLACED:
            results = {
                "order_id": event.data.get("order_id"),
                "order_status": "confirmed",
                "estimated_delivery": (datetime.now().timestamp() + 86400 * 3),  # 3 days
                "inventory_reserved": True,
            }

        elif event.type == EventType.PAYMENT_RECEIVED:
            results = {
                "payment_id": event.data.get("payment_id"),
                "payment_status": "completed",
                "transaction_fee": round(event.data.get("amount", 0) * 0.029 + 0.30, 2),
            }

        elif event.type == EventType.INVENTORY_UPDATED:
            results = {
                "product_id": event.data.get("product_id"),
                "inventory_status": (
                    "in_stock" if event.data.get("quantity", 0) > 0 else "out_of_stock"
                ),
                "reorder_required": event.data.get("quantity", 0) < 10,
            }

        else:
            # Generic results for other event types
            results = {
                "event_processed": True,
                "event_type": event.type.value,
            }

        # Calculate processing time in milliseconds
        processing_time_ms = (time.time() - start_time) * 1000

        # Create metadata
        metadata = {
            "processor_id": f"processor-{os.getpid()}",
            "processing_timestamp": time.time(),
            "original_event_type": event.type.value,
            "original_source": event.source,
        }

        # Create the processed event
        processed_event = ProcessedEvent(
            original_event_id=event.id,
            event_type=event.type.value,
            processed_timestamp=time.time(),
            processing_time_ms=processing_time_ms,
            results=results,
            metadata=metadata,
        )

        return processed_event

    def publish_processed_event(self, processed_event: ProcessedEvent) -> str:
        """Publish a processed event to the results topic.

        Args:
            processed_event: The processed event to publish

        Returns:
            The published message ID
        """
        # Convert the processed event to a dictionary
        event_dict = processed_event.to_dict()

        # Convert to JSON and encode as bytes
        message_json = json.dumps(event_dict)
        message_bytes = message_json.encode("utf-8")

        # Add attributes for filtering
        attributes = {
            "event_type": processed_event.event_type,
            "original_event_id": processed_event.original_event_id,
            "processed_timestamp": str(int(processed_event.processed_timestamp)),
        }

        try:
            # Publish the message
            future = self.publisher.publish(
                self.results_topic_path, data=message_bytes, **attributes
            )
            message_id = future.result()

            print(
                f"Published processed event for: {processed_event.event_type} with ID: {message_id}"
            )

            # Track the processed event
            self.processed_events.append(processed_event)

            return message_id

        except Exception as e:
            print(f"Error publishing processed event: {e}")
            raise

    def callback(self, message: Message) -> None:
        """Process received messages from the ingestion subscription.

        Args:
            message: The received Pub/Sub message
        """
        try:
            print(f"\n{'=' * 50}")
            print(f"Received event with ID: {message.message_id}")

            # Print message attributes if any
            attributes = dict(message.attributes) if message.attributes else {}
            if attributes:
                print("Event attributes:")
                for key, value in attributes.items():
                    print(f"  {key}: {value}")

            # Decode and parse the message data
            event_dict = json.loads(message.data.decode("utf-8"))

            # Create an Event object
            event = Event.from_dict(event_dict)

            # Check if this event has already been processed (deduplication)
            if event.id in self.processed_event_ids:
                print(f"Event {event.id} has already been processed. Skipping.")
                message.ack()
                return

            print(f"Processing event: {event.type.value}")
            print(f"  Event ID: {event.id}")
            print(f"  Source: {event.source}")
            print(f"  Data: {json.dumps(event.data)[:100]}...")

            # Process the event
            processed_event = self.process_event(event)

            # Publish the processed event
            self.publish_processed_event(processed_event)

            # Add the event ID to the set of processed events
            self.processed_event_ids.add(event.id)

            # Acknowledge the message
            message.ack()
            print(f"Event processed and acknowledged: {event.id}")

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
        """Start the data processing service."""
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

        print(f"Data processing service started.")
        print(f"Listening for events on {self.subscription_path}...")
        print("(Press Ctrl+C to stop)")

        try:
            if self.timeout is not None:
                print(f"Service will run for {self.timeout} seconds...")
                time.sleep(self.timeout)
                self.stop()
            else:
                # Run indefinitely
                self.streaming_pull_future.result()
        except TimeoutError:
            self.stop("Service timed out")
        except KeyboardInterrupt:
            self.stop("Service interrupted by user")
        except Exception as e:
            self.stop(f"Service error: {e}")

    def stop(self, reason: str = "Service stopped") -> None:
        """Stop the data processing service.

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
        print(f"\nProcessed {len(self.processed_events)} events")

        print("Data processing service stopped")


# Data Consumption Component
class DataConsumptionService:
    """Component that consumes processed events from the results topic."""

    def __init__(
        self, project_id: str, results_subscription_id: str, timeout: Optional[int] = None
    ):
        """Initialize the DataConsumptionService.

        Args:
            project_id: Your Google Cloud project ID
            results_subscription_id: The ID of the results Pub/Sub subscription
            timeout: How long to run the service in seconds (None for indefinite)
        """
        self.project_id = project_id
        self.results_subscription_id = results_subscription_id
        self.timeout = timeout

        # Initialize the subscriber client
        self.subscriber = pubsub_v1.SubscriberClient()

        # Get the subscription path
        self.subscription_path = self.subscriber.subscription_path(
            project_id, results_subscription_id
        )

        # Streaming pull future
        self.streaming_pull_future = None

        # Track consumed events
        self.consumed_events: List[ProcessedEvent] = []

        # Statistics by event type
        self.stats_by_event_type: Dict[str, int] = {}

    def consume_event(self, processed_event: ProcessedEvent) -> None:
        """Consume a processed event.

        Args:
            processed_event: The processed event to consume
        """
        # Track the consumed event
        self.consumed_events.append(processed_event)

        # Update statistics
        event_type = processed_event.event_type
        if event_type not in self.stats_by_event_type:
            self.stats_by_event_type[event_type] = 0
        self.stats_by_event_type[event_type] += 1

        # Simulate consumption
        time.sleep(0.05)

    def callback(self, message: Message) -> None:
        """Process received messages from the results subscription.

        Args:
            message: The received Pub/Sub message
        """
        try:
            print(f"\n{'=' * 50}")
            print(f"Consuming result with ID: {message.message_id}")

            # Print message attributes if any
            attributes = dict(message.attributes) if message.attributes else {}
            if attributes:
                print("Result attributes:")
                for key, value in attributes.items():
                    print(f"  {key}: {value}")

            # Decode and parse the message data
            event_dict = json.loads(message.data.decode("utf-8"))

            # Create a ProcessedEvent object
            processed_event = ProcessedEvent.from_dict(event_dict)

            print(f"Consuming result for event type: {processed_event.event_type}")
            print(f"  Original event ID: {processed_event.original_event_id}")
            print(f"  Processing time: {processed_event.processing_time_ms:.2f} ms")
            print(f"  Results: {json.dumps(processed_event.results)[:100]}...")

            # Consume the event
            self.consume_event(processed_event)

            # Acknowledge the message
            message.ack()
            print(f"Result consumed and acknowledged")

        except json.JSONDecodeError as e:
            print(f"Error decoding message data: {e}")
            # Negative acknowledge the message
            message.nack()

        except Exception as e:
            print(f"Error consuming message: {e}")
            # Negative acknowledge the message
            message.nack()

        print(f"{'=' * 50}\n")

    def start(self) -> None:
        """Start the data consumption service."""
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

        print(f"Data consumption service started.")
        print(f"Listening for results on {self.subscription_path}...")
        print("(Press Ctrl+C to stop)")

        try:
            if self.timeout is not None:
                print(f"Service will run for {self.timeout} seconds...")
                time.sleep(self.timeout)
                self.stop()
            else:
                # Run indefinitely
                self.streaming_pull_future.result()
        except TimeoutError:
            self.stop("Service timed out")
        except KeyboardInterrupt:
            self.stop("Service interrupted by user")
        except Exception as e:
            self.stop(f"Service error: {e}")

    def stop(self, reason: str = "Service stopped") -> None:
        """Stop the data consumption service.

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
        print(f"\nConsumed {len(self.consumed_events)} events")

        if self.stats_by_event_type:
            print("\nEvents by type:")
            for event_type, count in self.stats_by_event_type.items():
                print(f"  {event_type}: {count}")

        print("Data consumption service stopped")


def run_workflow(args):
    """Run the end-to-end workflow.

    Args:
        args: Command line arguments
    """
    # Create the data ingestion publisher
    ingestion_publisher = DataIngestionPublisher(
        args.project_id,
        args.ingestion_topic_id,
    )

    # Create the data processing service
    processing_service = DataProcessingService(
        args.project_id,
        args.ingestion_subscription_id,
        args.results_topic_id,
        args.timeout,
    )

    # Create the data consumption service
    consumption_service = DataConsumptionService(
        args.project_id,
        args.results_subscription_id,
        args.timeout,
    )

    # Start the processing service in a separate thread
    processing_thread = threading.Thread(target=processing_service.start, name="ProcessingService")

    # Start the consumption service in a separate thread
    consumption_thread = threading.Thread(
        target=consumption_service.start, name="ConsumptionService"
    )

    # Start the services
    processing_thread.start()
    consumption_thread.start()

    # Wait a moment for the services to start
    time.sleep(2)

    # Simulate data ingestion
    ingestion_publisher.simulate_data_ingestion(args.count, args.delay)

    # Wait for the services to complete
    processing_thread.join()
    consumption_thread.join()

    print("\nWorkflow completed!")


def main():
    """Main function to demonstrate Pub/Sub workflow."""
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
        "--ingestion-topic-id",
        help="The ID of the ingestion Pub/Sub topic",
        default="ingestion-topic",
    )
    parser.add_argument(
        "--ingestion-subscription-id",
        help="The ID of the ingestion Pub/Sub subscription",
        default="ingestion-subscription",
    )
    parser.add_argument(
        "--results-topic-id",
        help="The ID of the results Pub/Sub topic",
        default="results-topic",
    )
    parser.add_argument(
        "--results-subscription-id",
        help="The ID of the results Pub/Sub subscription",
        default="results-subscription",
    )
    parser.add_argument(
        "--count",
        help="Number of events to publish",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--delay",
        help="Delay between events in seconds",
        type=float,
        default=0.5,
    )
    parser.add_argument(
        "--timeout",
        help="How long to run the services in seconds",
        type=int,
        default=30,
    )
    parser.add_argument(
        "--ingestion-only",
        help="Only run the ingestion component",
        action="store_true",
    )
    args = parser.parse_args()

    try:
        if args.ingestion_only:
            # Create the data ingestion publisher
            ingestion_publisher = DataIngestionPublisher(
                args.project_id,
                args.ingestion_topic_id,
            )

            # Simulate data ingestion
            ingestion_publisher.simulate_data_ingestion(args.count, args.delay)
        else:
            # Run the full workflow
            run_workflow(args)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
