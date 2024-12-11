import asyncio

import logging

# Configure logging format and level
FORMAT = "[%(asctime)-15s][%(levelname)-8s]%(message)s"
logging.basicConfig(format=FORMAT, level=logging.INFO)
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting Example")


async def get_model(model_name, time_to_sleep):
    # Simulates calling a microservice with a specified delay
    logger.info("[get_model][{}] Calling microservice".format(model_name))
    await asyncio.sleep(time_to_sleep)  # Simulate a time-consuming operation
    logger.info("[get_model][{}] Returns result".format(model_name))


import aiohttp


async def do_request(url):
    # Makes an HTTP GET request to the specified URL
    logger.info("[do_request][{}] Calling web".format(url))
    async with aiohttp.ClientSession() as session:  # Create a client session
        async with session.get(url) as response:  # Make the GET request
            logger.info(
                "[do_request][{}] Returns result:{}".format(url, response.status)
            )
            return response


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Example of running two "microservice calls" concurrently with asyncio.sleep
    loop.run_until_complete(
        asyncio.gather(get_model("Modelo A", 2), get_model("Modelo B", 1))
    )

    # Example of making concurrent HTTP requests
    logger.info(
        "\n*************************************************************\nHTTP REQUESTS\n"
    )
    loop.run_until_complete(
        asyncio.gather(
            do_request("http://www.fakeresponse.com/api/?sleep=1"),
            do_request("http://google.es"),
        )
    )

    loop.close()
