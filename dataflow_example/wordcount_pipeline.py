#!/usr/bin/env python
"""
Word Count Example using Apache Beam and Google Cloud Dataflow

This pipeline reads text files, counts the occurrences of each word,
and writes the results to output files.
"""

import argparse
import logging
import re

import apache_beam as beam
from apache_beam.io import ReadFromText, WriteToText
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions, StandardOptions


class WordCountOptions(PipelineOptions):
    """Options for the word count pipeline."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument(
            "--input",
            required=True,
            help="Path to the input file pattern (e.g., gs://bucket/path/to/*.txt)",
        )
        parser.add_argument(
            "--output",
            required=True,
            help="Path to the output file (e.g., gs://bucket/path/to/output)",
        )


class ExtractWordsFn(beam.DoFn):
    """Parse each line of text into words."""

    def process(self, element):
        """
        Returns an iterator over the words in the line.

        Args:
            element: The line of text to process.

        Returns:
            An iterator over the words in the line.
        """
        # Replace non-alphanumeric characters with spaces
        text_line = re.sub(r"[^\w\s]", " ", element.strip().lower())
        # Split the line into words
        words = text_line.split()
        # Output each word encountered
        return words


def format_result(word_count):
    """Format the word count result as a string."""
    word, count = word_count
    return f"{word}: {count}"


def run(argv=None):
    """Main entry point; defines and runs the wordcount pipeline."""

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    known_args, pipeline_args = parser.parse_known_args(argv)

    # Create the pipeline options
    options = WordCountOptions(pipeline_args)
    options.view_as(SetupOptions).save_main_session = True
    options.view_as(StandardOptions).runner = (
        "DataflowRunner"  # Use 'DirectRunner' for local testing
    )

    # Create the pipeline
    with beam.Pipeline(options=options) as p:
        # Read the text file[pattern] into a PCollection
        lines = p | "ReadLines" >> ReadFromText(options.input)

        # Count the occurrences of each word
        counts = (
            lines
            | "ExtractWords" >> beam.ParDo(ExtractWordsFn())
            | "PairWithOne" >> beam.Map(lambda x: (x, 1))
            | "GroupAndSum" >> beam.CombinePerKey(sum)
        )

        # Format the counts into a PCollection of strings
        output = counts | "FormatResults" >> beam.Map(format_result)

        # Write the output using a "Write" transform
        output | "WriteResults" >> WriteToText(options.output)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()
