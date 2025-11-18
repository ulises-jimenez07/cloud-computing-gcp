import json
import os
import base64
import functions_framework
from google.cloud import storage

import vertexai
from vertexai.generative_models import GenerativeModel, Part

PROJECT_ID = "cc-up-2025-q4-ulises"
REGION = "us-central1"
MODEL_NAME = "gemini-2.0-flash-001"

vertexai.init(project=PROJECT_ID, location=REGION)


def get_prompt_for_summary() -> str:
    prompt = """
        You are a very professional document summarization specialist.
        Please summarize the given document.
    """
    return prompt


def get_summary(src_bucket: str, file_name: str) -> str:

    model = GenerativeModel(MODEL_NAME)

    prompt = get_prompt_for_summary()
    if not prompt:
        return ""

    pdf_file_uri = f"gs://{src_bucket}/{file_name}"
    pdf_file = Part.from_uri(pdf_file_uri, mime_type="application/pdf")
    contents = [pdf_file, prompt]

    response = model.generate_content(contents)
    return response.text


@functions_framework.cloud_event
def on_document_added(cloud_event):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
        cloud_event: event payload
    """

    pubsub_message = json.loads(
        base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
    )

    if pubsub_message["contentType"] != "application/pdf":
        raise ValueError("Only PDF files are supported, aborting")

    src_bucket = pubsub_message["bucket"]
    src_fname = pubsub_message["name"]
    print(f"Processing file: gs://{src_bucket}/{src_fname}")

    summary = get_summary(src_bucket, src_fname)
    print("Summary:", summary)
