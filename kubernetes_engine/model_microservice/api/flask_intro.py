from flask import Flask

# Initialize a Flask app instance
app = Flask(__name__)


# Define a route for the root URL ("/")
@app.route("/")
def hello_world():
    # Return "Hello World!" when the root URL is accessed
    return "Hello World!"


# Define a route with a dynamic component <name>
@app.route("/<name>")
def hello_name(name):
    # Return a personalized greeting using the provided name
    return "Hello {}!".format(name)


# Define a route for "/predict" that accepts GET requests
@app.route("/predict", methods=["GET"])
def predict():
    # Create a response object with the prediction message and a 200 OK status code
    response = app.response_class(response="Aquí viene la previsión", status=200)
    # Return the response
    return response


# Check if the script is being run directly (not imported as a module)
if __name__ == "__main__":
    # Start the Flask development server. This will listen on all available interfaces (0.0.0.0) and port 5000 by default.
    app.run()
