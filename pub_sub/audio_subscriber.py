import json
import time
import os
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1


class PubSubSubscriber:
    """
    A module for subscribing to a Google Cloud Pub/Sub topic and processing messages.
    """

    def __init__(self, project_id: str, subscription_id: str, temp_dir: str = "temp_audio_chunks"):
        """
        Initializes the PubSubSubscriber.

        Args:
            project_id: The ID of your Google Cloud project.
            subscription_id: The ID of the Pub/Sub subscription.
        """
        self.project_id = project_id
        self.subscription_id = subscription_id
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(
            project_id, subscription_id
        )
        self.streaming_pull_future = None
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        self.user_buffers = {}

    def callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        """
        Callback function for receiving and processing messages.

        Args:
            message: The received Pub/Sub message.
        """
        try:
            data = json.loads(message.data.decode("utf-8"))
            user_id = data.get("userId")
            if user_id is None:
                raise KeyError("userId not found")

            if data.get("type") == "audioChunk":
                order = data.get("order")
                if order is None:
                    raise KeyError("order not found")
                file_path = os.path.join(self.temp_dir, f"{user_id}_{order}.json")
                with open(file_path, "w") as f:
                    json.dump(data, f)
                print(f"Saved chunk for {user_id} with order {order}")

            elif data.get("type") == "endOfStream":
                print(f"End of stream detected for user: {user_id}")
                self.process_user_chunks(user_id)
            message.ack()

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            message.nack()
        except KeyError as e:
            print(f"Error accessing key in JSON: {e}")
            message.nack()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            message.nack()

    def process_user_chunks(self, user_id: str):
        """Processes and prints the chunks for a given user in order."""
        chunks = []
        index = 0
        while True:
            file_path = os.path.join(self.temp_dir, f"{user_id}_{index}.json")
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    chunk = json.load(f)
                    chunks.append(chunk["data"])
                os.remove(file_path)
                index += 1
            else:
                break
        print(f"Ordered chunks for {user_id}:")
        print("".join(chunks))

    def start_listening(self, timeout: int = 10) -> None:
        """
        Starts listening for messages on the subscription.

        Args:
            timeout: The time in seconds to keep the subscriber alive.
        """
        self.streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path, callback=self.callback
        )
        print(f"Listening for messages on {self.subscription_path}...\n")

        try:
            time.sleep(timeout)
            self.stop_listening()
        except TimeoutError:
            self.stop_listening("Subscriber timed out")
        except KeyboardInterrupt:
            self.stop_listening("Subscriber interrupted.")
        finally:
            print("Subscriber stopped.")

    def stop_listening(self, reason: str = None) -> None:
        """
        Stops the subscriber and cancels the streaming pull future.
        """
        if self.streaming_pull_future:
            self.streaming_pull_future.cancel()
            try:
                self.streaming_pull_future.result()
            except Exception as e:
                if reason:
                    print(f"{reason}: {e}")
                else:
                    print(f"Error during shutdown: {e}")
        time.sleep(1) 

if __name__ == "__main__":
    project_id = "[PROJECT_ID]" 
    subscription_id = "audio-stream-subscription"  # Replace with your subscription ID

    subscriber = PubSubSubscriber(project_id, subscription_id)
    subscriber.start_listening(timeout=30)  # adjust timeout as needed.