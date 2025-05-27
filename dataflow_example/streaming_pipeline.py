#!/usr/bin/env python
"""
Streaming Pipeline Example using Apache Beam and Google Cloud Dataflow

This pipeline reads messages from a Pub/Sub subscription,
processes them in real-time, and writes results to BigQuery.
"""

import argparse
import json
import logging
import time
from datetime import datetime

import apache_beam as beam
from apache_beam.io import ReadFromPubSub, WriteToBigQuery
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions, StandardOptions
from apache_beam.transforms.window import FixedWindows


class StreamingOptions(PipelineOptions):
    """Options for the streaming pipeline."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument(
            "--subscription",
            required=True,
            help='Pub/Sub subscription to read from, in the format "projects/<PROJECT>/subscriptions/<SUBSCRIPTION>"',
        )
        parser.add_argument("--dataset", required=True, help="BigQuery dataset to write to")
        parser.add_argument("--table", required=True, help="BigQuery table to write to")
        parser.add_argument("--window_size", type=int, default=60, help="Window size in seconds")


class ParseMessageFn(beam.DoFn):
    """Parse Pub/Sub message and extract relevant fields."""

    def process(self, element):
        """
        Process a Pub/Sub message.

        Args:
            element: The Pub/Sub message data.

        Returns:
            A dictionary with parsed message data.
        """
        try:
            # Parse the JSON message
            message = json.loads(element.decode("utf-8"))

            # Add processing timestamp
            message["processing_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            yield message
        except Exception as e:
            logging.error(f"Error parsing message: {e}")
            # Skip malformed messages
            pass


class CalculateStatisticsFn(beam.DoFn):
    """Calculate statistics on windowed data."""

    def process(self, element):
        """
        Process a windowed group of elements.

        Args:
            element: A tuple of (key, iterable of values).

        Returns:
            A dictionary with calculated statistics.
        """
        key, values = element
        values_list = list(values)

        # Calculate statistics
        count = len(values_list)
        if count > 0:
            numeric_values = [float(v.get("value", 0)) for v in values_list if "value" in v]
            if numeric_values:
                avg = sum(numeric_values) / len(numeric_values)
                max_val = max(numeric_values)
                min_val = min(numeric_values)
            else:
                avg, max_val, min_val = 0, 0, 0

            # Create result record
            result = {
                "key": key,
                "count": count,
                "average": avg,
                "max": max_val,
                "min": min_val,
                "window_end": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            yield result


def run(argv=None):
    """Main entry point; defines and runs the streaming pipeline."""

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    known_args, pipeline_args = parser.parse_known_args(argv)

    # Create the pipeline options
    options = StreamingOptions(pipeline_args)
    options.view_as(SetupOptions).save_main_session = True

    # Set streaming mode
    options.view_as(StandardOptions).streaming = True

    # Define the BigQuery schema
    schema = {
        "fields": [
            {"name": "key", "type": "STRING", "mode": "REQUIRED"},
            {"name": "count", "type": "INTEGER", "mode": "REQUIRED"},
            {"name": "average", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "max", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "min", "type": "FLOAT", "mode": "NULLABLE"},
            {"name": "window_end", "type": "TIMESTAMP", "mode": "REQUIRED"},
        ]
    }

    # Create the pipeline
    with beam.Pipeline(options=options) as p:
        # Read from Pub/Sub
        messages = p | "ReadFromPubSub" >> ReadFromPubSub(subscription=options.subscription)

        # Process and window the data
        results = (
            messages
            | "ParseMessages" >> beam.ParDo(ParseMessageFn())
            | "AddEventTimestamps"
            >> beam.Map(lambda x: beam.window.TimestampedValue(x, time.time()))
            | "WindowData" >> beam.WindowInto(FixedWindows(options.window_size))
            | "ExtractKey" >> beam.Map(lambda x: (x.get("category", "unknown"), x))
            | "GroupByKey" >> beam.GroupByKey()
            | "CalculateStatistics" >> beam.ParDo(CalculateStatisticsFn())
        )

        # Write results to BigQuery
        results | "WriteToBigQuery" >> WriteToBigQuery(
            table=f"{options.dataset}.{options.table}",
            schema=schema,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()
