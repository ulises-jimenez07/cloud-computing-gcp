import numpy as np  # Import numpy for numerical operations
from locust import HttpLocust, TaskSet, task  # Import locust library for load testing
from sklearn import datasets  # Import scikit-learn for loading the iris dataset


class UserBehavior(TaskSet):
    """
    Defines the behavior of a user interacting with the API.
    """

    def on_start(self):
        """
        Initializes the TaskSet by loading the iris dataset.
        This is called once per user at the beginning of their test.
        """
        self.iris = datasets.load_iris().data

    @task(1)
    def predict(self):
        """
        Simulates a user sending a prediction request to the API.
        This task has a weight of 1, meaning it's the only task and will be executed proportionally.
        """
        rnd = np.random.randint(
            0, self.iris.shape[0], 1
        )  # Select a random data point from the iris dataset
        dict_data = dict(
            zip(["p_l", "p_w", "s_l", "s_w"], self.iris[rnd].tolist()[0])
        )  # Create a dictionary with feature names and values
        headers = {
            "content-type": "application/json"
        }  # Set the request headers to JSON
        with self.client.post(
            "/predict", json=dict_data, headers=headers, catch_response=True
        ) as response:  # Send a POST request to /predict with the data and headers, catching the response
            if (
                response.status_code == 200
            ):  # Check if the response status code is 200 (OK)
                response.success()  # Mark the request as successful if the status code is 200


class WebsiteUser(HttpLocust):
    """
    Represents a user interacting with the website.
    """

    task_set = UserBehavior  # Defines the tasks that the user will perform
    min_wait = 5000  # Minimum wait time between tasks (in milliseconds)
    max_wait = 9000  # Maximum wait time between tasks (in milliseconds)


# Example command to run Locust:
# locust -f 020_api/test/locustfile.py --host=http://127.0.0.1:5000 --no-web -c 1000 -r 100
# -c specifies the number of Locust users to spawn.
# -r specifies the hatch rate (number of users to spawn per second).
