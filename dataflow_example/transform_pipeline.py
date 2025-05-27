#!/usr/bin/env python
"""
Data Transformation Example using Apache Beam and Google Cloud Dataflow

This pipeline demonstrates various data transformations including:
- Filtering
- Mapping
- FlatMapping
- Combining
- Custom ParDo functions
"""

import argparse
import csv
import logging
import os
from typing import Dict, List, Tuple, Any, Iterable

import apache_beam as beam
from apache_beam.io import ReadFromText, WriteToText
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions, StandardOptions


class TransformOptions(PipelineOptions):
    """Options for the transformation pipeline."""

    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument(
            "--input",
            required=True,
            help="Path to the input CSV file (e.g., gs://bucket/path/to/data.csv)",
        )
        parser.add_argument(
            "--output",
            required=True,
            help="Path to the output directory (e.g., gs://bucket/path/to/output/)",
        )
        parser.add_argument(
            "--min_price", type=float, default=0.0, help="Minimum price threshold for filtering"
        )


class ParseCsvFn(beam.DoFn):
    """Parse CSV records into dictionaries."""

    def process(self, element: str) -> Iterable[Dict[str, Any]]:
        """
        Parse a CSV line into a dictionary.

        Args:
            element: A line from the CSV file.

        Returns:
            A dictionary representing the CSV record.
        """
        try:
            # Skip header row
            if element.startswith("id,") or element.startswith("ID,"):
                return

            # Parse CSV line
            reader = csv.reader([element])
            row = next(reader)

            # Create a dictionary with field names
            # Assuming CSV format: id,name,category,price,quantity,date
            if len(row) >= 6:
                record = {
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "price": float(row[3]) if row[3] else 0.0,
                    "quantity": int(row[4]) if row[4] else 0,
                    "date": row[5],
                }
                yield record
        except Exception as e:
            logging.error(f"Error parsing CSV row: {e}, row: {element}")
            # Skip malformed rows
            pass


class EnrichDataFn(beam.DoFn):
    """Enrich data with additional fields."""

    def process(self, element: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        """
        Add derived fields to the record.

        Args:
            element: A dictionary representing a record.

        Returns:
            An enriched dictionary.
        """
        # Calculate total value
        element["total_value"] = element["price"] * element["quantity"]

        # Add price tier
        if element["price"] < 10:
            element["price_tier"] = "low"
        elif element["price"] < 50:
            element["price_tier"] = "medium"
        else:
            element["price_tier"] = "high"

        yield element


def filter_by_price(record: Dict[str, Any], min_price: float) -> bool:
    """
    Filter records by price.

    Args:
        record: A dictionary representing a record.
        min_price: Minimum price threshold.

    Returns:
        True if the record's price is >= min_price, False otherwise.
    """
    return record["price"] >= min_price


def extract_categories(record: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Extract categories from a record for grouping.

    Args:
        record: A dictionary representing a record.

    Returns:
        A list of (category, record) tuples.
    """
    # Split the category field by comma or semicolon if it contains multiple categories
    categories = [cat.strip() for cat in record["category"].replace(";", ",").split(",")]
    return [(category, record) for category in categories if category]


def format_category_stats(element: Tuple[str, Dict[str, Any]]) -> str:
    """
    Format category statistics as a string.

    Args:
        element: A tuple of (category, stats dictionary).

    Returns:
        A formatted string with category statistics.
    """
    category, stats = element
    return (
        f"Category: {category}\n"
        f"  Total Items: {stats['count']}\n"
        f"  Average Price: ${stats['avg_price']:.2f}\n"
        f"  Total Value: ${stats['total_value']:.2f}\n"
        f"  Min Price: ${stats['min_price']:.2f}\n"
        f"  Max Price: ${stats['max_price']:.2f}"
    )


class CalculateCategoryStatsFn(beam.CombineFn):
    """Combine function to calculate statistics for each category."""

    def create_accumulator(self) -> Dict[str, Any]:
        return {
            "count": 0,
            "price_sum": 0.0,
            "total_value": 0.0,
            "min_price": float("inf"),
            "max_price": float("-inf"),
        }

    def add_input(
        self, accumulator: Dict[str, Any], input_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        accumulator["count"] += 1
        accumulator["price_sum"] += input_record["price"]
        accumulator["total_value"] += input_record["total_value"]
        accumulator["min_price"] = min(accumulator["min_price"], input_record["price"])
        accumulator["max_price"] = max(accumulator["max_price"], input_record["price"])
        return accumulator

    def merge_accumulators(self, accumulators: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        merged = self.create_accumulator()
        for acc in accumulators:
            merged["count"] += acc["count"]
            merged["price_sum"] += acc["price_sum"]
            merged["total_value"] += acc["total_value"]
            merged["min_price"] = min(merged["min_price"], acc["min_price"])
            merged["max_price"] = max(merged["max_price"], acc["max_price"])
        return merged

    def extract_output(self, accumulator: Dict[str, Any]) -> Dict[str, Any]:
        # Calculate average price
        avg_price = 0.0
        if accumulator["count"] > 0:
            avg_price = accumulator["price_sum"] / accumulator["count"]

        # Handle edge case where no records were processed
        if accumulator["min_price"] == float("inf"):
            accumulator["min_price"] = 0.0
        if accumulator["max_price"] == float("-inf"):
            accumulator["max_price"] = 0.0

        return {
            "count": accumulator["count"],
            "avg_price": avg_price,
            "total_value": accumulator["total_value"],
            "min_price": accumulator["min_price"],
            "max_price": accumulator["max_price"],
        }


def run(argv=None):
    """Main entry point; defines and runs the transformation pipeline."""

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    known_args, pipeline_args = parser.parse_known_args(argv)

    # Create the pipeline options
    options = TransformOptions(pipeline_args)
    options.view_as(SetupOptions).save_main_session = True

    # Create the pipeline
    with beam.Pipeline(options=options) as p:
        # Read the CSV file into a PCollection
        lines = p | "ReadCSV" >> ReadFromText(options.input, skip_header_lines=1)

        # Parse CSV records
        records = lines | "ParseCSV" >> beam.ParDo(ParseCsvFn())

        # Filter records by price
        filtered_records = records | "FilterByPrice" >> beam.Filter(
            filter_by_price, options.min_price
        )

        # Enrich data with additional fields
        enriched_records = filtered_records | "EnrichData" >> beam.ParDo(EnrichDataFn())

        # Write the enriched records to a file
        enriched_records | "FormatEnriched" >> beam.Map(
            lambda record: f"{record['id']},{record['name']},{record['category']},"
            f"{record['price']:.2f},{record['quantity']},{record['date']},"
            f"{record['total_value']:.2f},{record['price_tier']}"
        ) | "WriteEnriched" >> WriteToText(
            os.path.join(options.output, "enriched"),
            file_name_suffix=".csv",
            header="id,name,category,price,quantity,date,total_value,price_tier",
        )

        # Group by category and calculate statistics
        category_stats = (
            enriched_records
            | "ExtractCategories" >> beam.FlatMap(extract_categories)
            | "GroupByCategory" >> beam.GroupByKey()
            | "CalculateStats" >> beam.CombinePerKey(CalculateCategoryStatsFn())
            | "FormatStats" >> beam.Map(format_category_stats)
        )

        # Write category statistics to a file
        category_stats | "WriteStats" >> WriteToText(
            os.path.join(options.output, "category_stats"), file_name_suffix=".txt"
        )

        # Group by price tier
        price_tier_counts = (
            enriched_records
            | "ExtractPriceTier" >> beam.Map(lambda record: (record["price_tier"], 1))
            | "CountByPriceTier" >> beam.CombinePerKey(sum)
            | "FormatPriceTier" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]}")
        )

        # Write price tier counts to a file
        price_tier_counts | "WritePriceTiers" >> WriteToText(
            os.path.join(options.output, "price_tiers"),
            file_name_suffix=".csv",
            header="price_tier,count",
        )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()
