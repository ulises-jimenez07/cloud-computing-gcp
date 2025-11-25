import argparse
import logging
import re
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions


def run():
    # Set up simple argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", default="data/sample_text.txt", help="Input file to process"
    )
    parser.add_argument(
        "--output", default="output.txt", help="Output file for results"
    )
    args, beam_args = parser.parse_known_args()

    # Create pipeline options
    options = PipelineOptions(beam_args)

    # Define the pipeline
    with beam.Pipeline(options=options) as p:
        (
            p
            | "Read File" >> beam.io.ReadFromText(args.input)
            | "Find Words"
            >> beam.FlatMap(lambda line: re.findall(r"\w+", line.lower()))
            | "Count Words" >> beam.combiners.Count.PerElement()
            | "Format Output"
            >> beam.Map(lambda word_count: f"{word_count[0]}: {word_count[1]}")
            | "Write Results" >> beam.io.WriteToText(args.output)
        )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()
