# Google Cloud Pub/Sub Example

This directory contains comprehensive examples demonstrating how to use Google Cloud Pub/Sub for various messaging patterns and use cases.

## What is Pub/Sub?

Google Cloud Pub/Sub is a fully-managed real-time messaging service that allows you to send and receive messages between independent applications. It provides reliable, many-to-many, asynchronous messaging between applications.

Key concepts:
- **Topics**: A named resource to which messages are sent by publishers
- **Subscriptions**: A named resource representing the stream of messages from a single, specific topic
- **Publishers**: Applications that create and send messages to a topic
- **Subscribers**: Applications that receive messages from a subscription

## Features Demonstrated

These examples demonstrate the following Pub/Sub features:

1. Basic publishing and subscribing
2. Message attributes and filtering
3. Ordered message delivery
4. Schema validation (Avro and Protocol Buffers)
5. Dead letter topics
6. Push and pull subscriptions
7. Exactly-once delivery
8. Retry policies
9. Subscription expiration
10. Message retention

## Prerequisites

1. Google Cloud Platform account with Pub/Sub API enabled
2. Google Cloud SDK installed and configured
3. Python 3.7+ installed
4. Required Python packages (see `requirements.txt`)

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your GCP project and authentication:
   ```
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
4. Create the necessary Pub/Sub resources using the commands in `pubsub_commands.sh`

## Examples

### Basic Examples

- `basic_publisher.py`: Simple publisher that sends messages to a topic
- `basic_subscriber.py`: Simple subscriber that receives messages from a subscription

### Advanced Examples

- `advanced_publisher.py`: Publisher with message ordering, attributes, and batch settings
- `advanced_subscriber.py`: Subscriber with filtering, concurrency control, and error handling
- `schema_publisher.py`: Publisher with schema validation
- `schema_subscriber.py`: Subscriber with schema validation
- `dead_letter_example.py`: Example using dead letter topics for handling failed messages
- `pubsub_workflow.py`: End-to-end workflow example

## Running the Examples

### Basic Publishing and Subscribing

1. Create a topic and subscription:
   ```
   ./pubsub_commands.sh create_basic_resources
   ```

2. In one terminal, start the subscriber:
   ```
   python basic_subscriber.py
   ```

3. In another terminal, run the publisher:
   ```
   python basic_publisher.py
   ```

### Schema Validation

1. Create a topic with schema validation:
   ```
   ./pubsub_commands.sh create_schema_resources
   ```

2. Run the schema publisher:
   ```
   python schema_publisher.py
   ```

3. Run the schema subscriber:
   ```
   python schema_subscriber.py
   ```

## Common Patterns and Best Practices

### Fan-out Pattern

Multiple subscriptions can be attached to a single topic, allowing multiple services to process the same messages independently.

### Pub/Sub as an Event Bus

Pub/Sub can serve as an event bus for event-driven architectures, decoupling event producers from event consumers.

### Exactly-once Processing

Use Pub/Sub's exactly-once delivery feature for critical workloads that require messages to be processed exactly once.

### Message Ordering

For use cases requiring message ordering, use Pub/Sub's message ordering feature with ordering keys.

### Error Handling

Implement robust error handling in subscribers and consider using dead letter topics for messages that cannot be processed.

## Troubleshooting

- **Message not received**: Check subscription exists and is attached to the correct topic
- **Permission denied**: Verify IAM permissions for Pub/Sub
- **Schema validation errors**: Ensure message format matches the defined schema
- **Duplicate messages**: Review acknowledgement deadline and subscriber implementation

## Additional Resources

- [Google Cloud Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Pub/Sub Client Libraries](https://cloud.google.com/pubsub/docs/reference/libraries)
- [Pub/Sub Pricing](https://cloud.google.com/pubsub/pricing)
- [Pub/Sub Quotas and Limits](https://cloud.google.com/pubsub/quotas)