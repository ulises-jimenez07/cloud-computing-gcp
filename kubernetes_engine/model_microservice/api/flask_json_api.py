import pandas as pd
import pickle

from flask import Flask, Response
from flask import json
from flask import request


# Initialize Flask app
app = Flask(__name__)

# Load the trained model from the pickle file
# Note: Relative paths can be tricky within containers.  It's generally better to use absolute paths or mount the model file.
filename = "../010_model/iris_model.pkl"
loaded_model = pickle.load(open(filename, "rb"))


def predict_data(data_dict):
    """
    Makes a prediction using the loaded model.

    Args:
        data_dict (dict): A dictionary containing the input features for prediction.

    Returns:
        list: A list of prediction probabilities for each class.
    """
    data = pd.DataFrame(data_dict, index=[0])  # Convert the dictionary to a DataFrame
    prediction = loaded_model.predict_proba(data)  # Get prediction probabilities
    return prediction.tolist()[0]


def is_data_correct(data):
    """
    Checks if the input data has the correct number of features.
    Assumes the model expects 4 features (like the iris dataset).

    Args:
        data (dict): The input data as a dictionary.

    Returns:
        bool: True if the data has the correct number of features, False otherwise.
    """
    if len(data) == 4:
        return True
    return False


@app.route("/predict", methods=["POST"])
def predict():
    """
    Flask route for handling prediction requests.

    Expects a JSON payload with input features in the request body.

    Returns:
        flask.Response: A JSON response containing the prediction probabilities and the original input data.
        Returns a 400 error response if the input data is invalid or if an exception occurs.
    """
    response = Response(
        status=400, response="INFORMACION ERRONEA"
    )  # Initialize a default error response
    try:
        data = request.get_json()  # Parse JSON data from the request body
        print(data)  # Print the received data (useful for debugging)

        if is_data_correct(data):
            prediction = {}
            prediction["Scores"] = predict_data(data)  # Get prediction probabilities
            prediction["Input"] = (
                data  # Include the input data in the response for verification
            )
            response = app.response_class(
                response=json.dumps(prediction), status=200, mimetype="application/json"
            )  # Create a successful response with JSON payload

        return response
    except Exception as ex:
        return Response(
            status=400, response=str(ex)
        )  # Return an error response with the exception details


if __name__ == "__main__":
    # Run the Flask app.  0.0.0.0 makes it accessible from any IP address on the host machine.
    app.run(host="0.0.0.0", port=5000)


# Example curl commands for testing (replace with your actual IP/hostname if not running locally):
# Windows Curl: (doesn't like single quotes)
# curl -H "Content-Type: application/json" --request POST --data "{\"s_l\":5.9,\"s_w\":3,\"p_l\":5.1,\"p_w\":1.8}" http://127.0.0.1:5000/predict

# Linux curl:
# curl -i -X POST  -H "Content-Type:application/json"  -d  '{"s_l":5.9,"s_w":3,"p_l":5.1,"p_w":1.8}' 'http://127.0.0.1:5000/predict'
