import sys
from pyspark.sql import SparkSession
import re


def main():
    """
    A simple PySpark job that counts words in a text file.
    """
    # Initialize Spark Session
    spark = SparkSession.builder.appName("SimpleWordCount").getOrCreate()

    # Get input/output paths from arguments or use defaults for local testing
    input_path = sys.argv[1] if len(sys.argv) > 1 else "data/sample_text.txt"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "output_wordcount"

    print(f"Reading from: {input_path}")
    print(f"Writing to: {output_path}")

    # Read lines from the file
    lines = spark.read.text(input_path).rdd.map(lambda r: r[0])

    # Perform word count
    word_counts = (
        lines.flatMap(lambda line: re.findall(r"\w+", line.lower()))
        .map(lambda word: (word, 1))
        .reduceByKey(lambda a, b: a + b)
        .sortBy(lambda x: x[1], ascending=False)
    )

    # Save results
    # We use coalesce(1) to get a single output file for this small example
    word_counts.toDF(["word", "count"]).coalesce(1).write.csv(
        output_path, header=True, mode="overwrite"
    )

    print("Job finished successfully.")
    spark.stop()


if __name__ == "__main__":
    main()
