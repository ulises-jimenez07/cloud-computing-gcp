import asyncio
import json
import time
import aiohttp

from flask import Flask, request, Response

import logging

# Configure logging
FORMAT = "[%(asctime)-15s][%(levelname)-8s]%(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting Example")

# Constants for request durations
REQUEST_DURATION = 5  # Timeout for individual model requests
TOTAL_DURATION = 10  # Maximum total time to wait for responses

# Initialize Flask app
app = Flask(__name__)


async def make_request(url, data, timeout, session):
    """Makes an asynchronous POST request to a given URL with data and timeout."""
    logger.info(f"[make_request][{url}] Calling web")
    try:
        async with session.post(url, timeout=timeout, json=data) as resp:
            response_text = await resp.text()
            logger.info(f"[make_request][{url}] Returns result:{response_text}")
            return [response_text, url]
    except asyncio.TimeoutError as ex:
        logger.warning(f"[make_request][{url}]Timeout captured:{ex}")
        return None
    except Exception as ex:
        logger.error(f"[make_request][{url}]Exception:{ex}")
        return None


async def wait_for_responses(models):
    """Waits for responses from multiple asynchronous requests, with a total timeout."""
    results = []
    start_time = time.time()
    for completed_request in asyncio.as_completed(models):
        response = await completed_request
        print(response)
        results.append(response)
        elapsed_time = time.time() - start_time
        if elapsed_time > TOTAL_DURATION:
            logger.error("Total response wait time exceeded")
            break
    return results


async def call_models(session, data):
    """Calls multiple models concurrently using asynchronous requests."""
    model_calls = []
    model_calls.append(
        make_request("http://canary:5001/predict", data, REQUEST_DURATION, session)
    )
    model_calls.append(
        make_request("http://model:5000/predict", data, REQUEST_DURATION, session)
    )
    return model_calls


def process_results(results):
    """Processes the results from model calls, prioritizing the main model's response."""
    response = "No model results"
    for result in results:
        print(result)
        if result is not None:
            if result[1] == "http://model:5000/predict":
                response = result[0]
    return response


async def get_data(data):
    """Orchestrates the process of calling models and processing their responses."""
    processed_results = []
    async with aiohttp.ClientSession() as session:
        logger.info("Calling models")
        model_calls = await call_models(session, data)

        logger.info("Waiting for models")
        results = await wait_for_responses(model_calls)

        logger.info("Processing results")
        processed_results = process_results(results)

    return processed_results


# Get the event loop
loop = asyncio.get_event_loop()


@app.route("/predict", methods=["POST"])
def predict():
    """Flask endpoint for handling prediction requests."""
    try:
        logger.debug(request)
        data = request.get_json()
        response = loop.run_until_complete(get_data(data))

        return Response(status=200, response=json.dumps(response))
    except Exception as ex:
        return Response(status=400, response=str(ex))


if __name__ == "__main__":
    logger.info("Elector")
    app.run(host="0.0.0.0", port=5002)
    loop.close()

# Example curl command:
# curl -H "Content-Type: application/json" --request POST --data "{\"s_l\":5.9,\"s_w\":3,\"p_l\":5.1,\"p_w\":1.8}" http://127.0.0.1:5002/predict
