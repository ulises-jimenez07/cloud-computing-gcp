#!/usr/bin/env python3
"""
pyspark_wordcount.py - Example PySpark word count job for Google Cloud Dataproc

This script demonstrates a simple PySpark word count job that can be submitted to
a Dataproc cluster. It reads text from a file, counts the occurrences of each word,
and writes the results to an output location.

Usage:
    spark-submit pyspark_wordcount.py [input_file] [output_dir]

Example:
    spark-submit pyspark_wordcount.py gs://my-bucket/data/sample_text.txt gs://my-bucket/output/wordcount
"""

import re
import sys
from operator import add

from pyspark.sql import SparkSession


def main():
    """
    Main function to run the word count job.
    """
    if len(sys.argv) != 3:
        print("Usage: pyspark_wordcount.py <input_file> <output_dir>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]

    # Create a Spark session
    spark = SparkSession.builder.appName("PySpark Word Count").getOrCreate()

    # Read the input file
    lines = spark.read.text(input_file).rdd.map(lambda r: r[0])

    # Split each line into words and count them
    counts = (
        lines.flatMap(lambda line: re.split(r"[^\w]+", line.lower()))
        .filter(lambda word: word and len(word) > 0)  # Filter out empty strings
        .map(lambda word: (word, 1))
        .reduceByKey(add)
        .sortBy(lambda x: x[1], ascending=False)  # Sort by count in descending order
    )

    # Convert to DataFrame for easier output
    df = counts.toDF(["word", "count"])

    # Write the results to the output directory
    df.write.csv(output_dir, header=True, mode="overwrite")

    # Print the top 20 words
    print("\nTop 20 words:")
    for row in df.take(20):
        print(f"{row['word']}: {row['count']}")

    spark.stop()


if __name__ == "__main__":
    main()
