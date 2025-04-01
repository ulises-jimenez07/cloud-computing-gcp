#  Copyright 2024 Google. This software is provided as-is, without warranty or
#  representation for any use or purpose.
#  Your use of it is subject to your agreement with Google

import json
import os
import base64

from google.cloud import bigquery
from google.cloud import storage
from google.cloud import vision

import vertexai
from vertexai.generative_models import GenerativeModel, Part

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
REGION = os.getenv("GCP_REGION")
MODEL_NAME = "gemini-1.5-flash-001"

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


def on_document_added(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
        event: event payload
        context: metadata for the event.
    """
    pubsub_message = json.loads(base64.b64decode(event["data"]).decode("utf-8"))

    if pubsub_message["contentType"] != "application/pdf":
        raise ValueError("Only PDF files are supported, aborting")

    src_bucket = pubsub_message["bucket"]
    src_fname = pubsub_message["name"]
    print(f"Processing file: gs://{src_bucket}/{src_fname}")

    summary = get_summary(src_bucket, src_fname)
    print("Summary:", summary)
