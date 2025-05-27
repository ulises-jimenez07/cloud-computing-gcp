#!/usr/bin/env python3
"""
Google Cloud Pub/Sub Schema Publisher Example

This script demonstrates how to publish messages to a Google Cloud Pub/Sub topic
with schema validation. It shows how to create and use Avro schemas for message validation.
"""

import argparse
import json
import os
import random
import time
import uuid
from typing import Dict, List, Optional

from google.cloud import pubsub_v1
from google.api_core.exceptions import InvalidArgument

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class SchemaPublisher:
    """A class for publishing messages to a Google Cloud Pub/Sub topic with schema validation."""

    def __init__(self, project_id: str, topic_id: str, encoding: str = "JSON"):
        """Initialize the SchemaPublisher.

        Args:
            project_id: Your Google Cloud project ID
            topic_id: The ID of the Pub/Sub topic to publish to
            encoding: The encoding type (JSON or BINARY)
        """
        self.project_id = project_id
        self.topic_id = topic_id
        self.encoding = encoding

        # Initialize the publisher client
        self.publisher = pubsub_v1.PublisherClient()

        # Get the topic path
        self.topic_path = self.publisher.topic_path(project_id, topic_id)

        # Get the topic to check if it has a schema
        try:
            self.topic = self.publisher.get_topic(request={"topic": self.topic_path})
            if hasattr(self.topic, "schema_settings") and self.topic.schema_settings:
                print(f"Topic {topic_id} has schema: {self.topic.schema_settings.schema}")
                print(f"Schema encoding: {self.topic.schema_settings.encoding}")
            else:
                print(f"Topic {topic_id} does not have a schema attached")
        except Exception as e:
            print(f"Error getting topic: {e}")
            raise

    def publish_message(self, message_data: Dict) -> str:
        """Publish a message to the Pub/Sub topic with schema validation.

        Args:
            message_data: The message data to publish

        Returns:
            The published message ID
        """
        # Convert the message data to the appropriate format based on encoding
        if self.encoding == "JSON":
            # For JSON encoding, convert to JSON string and encode as bytes
            message_bytes = json.dumps(message_data).encode("utf-8")
        else:
            # For BINARY encoding, you would use Avro or Protobuf serialization
            # This example only implements JSON encoding
            raise NotImplementedError("BINARY encoding is not implemented in this example")

        try:
            # Publish the message
            future = self.publisher.publish(self.topic_path, data=message_bytes)
            message_id = future.result()
            print(f"Published message with ID: {message_id}")
            print(f"  Content: {json.dumps(message_data)[:100]}...")
            return message_id

        except InvalidArgument as e:
            print(f"Schema validation error: {e}")
            # Print the message that failed validation
            print(f"Invalid message: {json.dumps(message_data)}")
            raise

        except Exception as e:
            print(f"Error publishing message: {e}")
            raise

    def publish_multiple_messages(self, messages: List[Dict]) -> List[str]:
        """Publish multiple messages to the Pub/Sub topic.

        Args:
            messages: List of message data dictionaries to publish

        Returns:
            List of published message IDs
        """
        message_ids = []

        for i, message in enumerate(messages):
            try:
                message_id = self.publish_message(message)
                message_ids.append(message_id)

                # Small delay between messages
                time.sleep(0.1)

            except Exception as e:
                print(f"Failed to publish message {i}: {e}")

        print(f"Published {len(message_ids)}/{len(messages)} messages successfully")
        return message_ids


def generate_valid_user(user_id: Optional[str] = None) -> Dict:
    """Generate a valid user record according to the schema.

    Args:
        user_id: Optional user ID to use

    Returns:
        A user record that conforms to the schema
    """
    # Generate a random user ID if not provided
    if user_id is None:
        user_id = str(uuid.uuid4())

    # List of possible first and last names
    first_names = ["John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson"]

    # Generate a random name
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    name = f"{first_name} {last_name}"

    # Generate a random email
    email = f"{first_name.lower()}.{last_name.lower()}@example.com"

    # Generate a random age between 18 and 80
    age = random.randint(18, 80)

    # Generate a random active status (mostly active)
    active = random.random() < 0.9

    # Generate a random created_at timestamp (within the last year)
    created_at = int(time.time() * 1000) - random.randint(0, 365 * 24 * 60 * 60 * 1000)

    # Generate a random address
    address = {
        "street": f"{random.randint(100, 999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine'])} St",
        "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
        "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
        "zip": f"{random.randint(10000, 99999)}",
        "country": "USA",
    }

    # Generate random phone numbers
    phone_count = random.randint(1, 3)
    phone_numbers = []
    for _ in range(phone_count):
        phone_type = random.choice(["HOME", "WORK", "MOBILE"])
        phone_number = (
            f"{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        )
        phone_numbers.append({"type": phone_type, "number": phone_number})

    # Generate random preferences
    preference_count = random.randint(0, 5)
    preferences = {}
    possible_preferences = {
        "theme": ["light", "dark", "system"],
        "notifications": ["all", "important", "none"],
        "language": ["en", "es", "fr", "de"],
        "timezone": ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"],
        "currency": ["USD", "EUR", "GBP", "JPY"],
    }

    for _ in range(preference_count):
        pref_key = random.choice(list(possible_preferences.keys()))
        if pref_key not in preferences:
            preferences[pref_key] = random.choice(possible_preferences[pref_key])

    # Generate random tags
    tag_count = random.randint(0, 5)
    possible_tags = [
        "premium",
        "new",
        "active",
        "developer",
        "admin",
        "beta",
        "tester",
        "customer",
    ]
    tags = random.sample(possible_tags, min(tag_count, len(possible_tags)))

    # Create the user record
    user = {
        "id": user_id,
        "name": name,
        "email": email,
        "age": age,
        "active": active,
        "created_at": created_at,
        "address": address,
        "phone_numbers": phone_numbers,
        "preferences": preferences,
        "tags": tags,
    }

    return user


def generate_invalid_user() -> Dict:
    """Generate an invalid user record that doesn't conform to the schema.

    Returns:
        An invalid user record
    """
    # Start with a valid user
    user = generate_valid_user()

    # Choose a random way to make it invalid
    invalid_type = random.randint(1, 5)

    if invalid_type == 1:
        # Invalid age (should be int, not string)
        user["age"] = f"{user['age']}"
    elif invalid_type == 2:
        # Missing required field
        del user["email"]
    elif invalid_type == 3:
        # Invalid phone type (not in enum)
        if user["phone_numbers"]:
            user["phone_numbers"][0]["type"] = "CELL"
    elif invalid_type == 4:
        # Invalid address (missing required field)
        del user["address"]["city"]
    elif invalid_type == 5:
        # Invalid created_at (should be long, not string)
        user["created_at"] = "2023-01-01T00:00:00Z"

    return user


def main():
    """Main function to demonstrate Pub/Sub schema publishing."""
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
        default="schema-topic",
    )
    parser.add_argument(
        "--count",
        help="Number of valid messages to publish",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--include-invalid",
        help="Include an invalid message to demonstrate schema validation",
        action="store_true",
    )
    args = parser.parse_args()

    try:
        # Create the schema publisher
        publisher = SchemaPublisher(args.project_id, args.topic_id)

        # Generate valid user messages
        valid_messages = [generate_valid_user() for _ in range(args.count)]

        # Add an invalid message if requested
        if args.include_invalid:
            invalid_message = generate_invalid_user()
            print("\nAdding an invalid message to demonstrate schema validation:")
            print(f"  {json.dumps(invalid_message)[:100]}...")
            valid_messages.append(invalid_message)

        # Publish the messages
        publisher.publish_multiple_messages(valid_messages)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
