# This model provides a baseline to detect changes in input data and for comparison with other models.
import pandas as pd
import pickle

from flask import Flask, Response
from flask import json
from flask import request
from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB

app = Flask(__name__)


#########################################################################################
# Model Training
#########################################################################################
# Load the iris dataset
iris = datasets.load_iris()
# Split the dataset into training and testing sets
X_train, X_test, Y_train, Y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=0
)
# Initialize a Gaussian Naive Bayes model
loaded_model = GaussianNB()
# Train the model
loaded_model.fit(X_train, Y_train)


def predict_data(data_dict):
    # Convert the input dictionary to a Pandas DataFrame
    data = pd.DataFrame(data_dict, index=[0])
    # Make predictions using the trained model
    prediction = loaded_model.predict_proba(data)
    # Return the prediction probabilities as a list
    return prediction.tolist()[0]


def is_data_correct(data):
    # Check if the input data has the correct number of features (4 for iris dataset)
    if len(data) == 4:
        return True
    return False


@app.route("/predict", methods=["POST"])
def predict():
    # Initialize a default error response
    response = Response(status=400, response="INFORMACION ERRONEA")
    try:
        # Get the JSON data from the request
        data = request.get_json()
        print(data)  # Print the input data (for debugging)
        # Check if the input data is valid
        if is_data_correct(data):
            prediction = {}
            # Get the prediction probabilities
            prediction["Scores"] = predict_data(data)
            # Include the input data in the response
            prediction["Input"] = data
            # Create a successful response with the prediction
            response = app.response_class(response=json.dumps(prediction), status=200)
        return response
    except Exception as ex:
        # Return an error response if any exception occurs
        return Response(status=400, response=ex)


if __name__ == "__main__":
    # Run the Flask app on all available interfaces (0.0.0.0) and port 5001
    app.run(host="0.0.0.0", port=5001)


# Example curl commands for testing:
# Windows Curl: (doesn't like single quotes)
# curl -H "Content-Type: application/json" --request POST --data "{\"s_l\":5.9,\"s_w\":3,\"p_l\":5.1,\"p_w\":1.8}" http://127.0.0.1:5001/predict

# Linux curl:
# curl -i -X POST  -H "Content-Type:application/json"  -d  '{"s_l":5.9,"s_w":3,"p_l":5.1,"p_w":1.8}' 'http://127.0.0.1:5001/predict'
