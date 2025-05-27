#!/usr/bin/env python3
"""
spark_sql_example.py - Example Spark SQL job for Google Cloud Dataproc

This script demonstrates how to use Spark SQL to query and analyze structured data.
It reads a CSV file, creates a temporary view, and performs SQL queries on the data.

Usage:
    spark-submit spark_sql_example.py [input_csv] [output_dir]

Example:
    spark-submit spark_sql_example.py gs://my-bucket/data/sample_data.csv gs://my-bucket/output/sql_results
"""

import sys

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, sum, count, max, min, year, month


def main():
    """
    Main function to run the Spark SQL job.
    """
    if len(sys.argv) != 3:
        print("Usage: spark_sql_example.py <input_csv> <output_dir>")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_dir = sys.argv[2]

    # Create a Spark session
    spark = SparkSession.builder.appName("Spark SQL Example").getOrCreate()

    # Read the CSV file with header
    df = spark.read.option("header", "true").option("inferSchema", "true").csv(input_csv)

    # Print the schema
    print("Schema:")
    df.printSchema()

    # Show the first few rows
    print("\nSample data:")
    df.show(5)

    # Register the DataFrame as a temporary view
    df.createOrReplaceTempView("employees")

    # Example 1: Basic SQL query
    print("\nExample 1: Basic SQL query - Top 5 highest paid employees")
    result1 = spark.sql(
        """
        SELECT name, department, salary
        FROM employees
        ORDER BY salary DESC
        LIMIT 5
    """
    )
    result1.show()

    # Example 2: Aggregation query
    print("\nExample 2: Aggregation - Average salary by department")
    result2 = spark.sql(
        """
        SELECT department, 
               COUNT(*) as employee_count,
               AVG(salary) as avg_salary,
               MIN(salary) as min_salary,
               MAX(salary) as max_salary
        FROM employees
        GROUP BY department
        ORDER BY avg_salary DESC
    """
    )
    result2.show()

    # Example 3: Using DataFrame API
    print("\nExample 3: Using DataFrame API - Employees hired after 2018")
    # Convert hire_date from string to date type
    df_with_date = df.withColumn("hire_date", col("hire_date").cast("date"))

    recent_hires = (
        df_with_date.filter(year(col("hire_date")) >= 2019)
        .select("name", "department", "hire_date")
        .orderBy("hire_date")
    )

    recent_hires.show()

    # Example 4: Complex analysis
    print("\nExample 4: Complex analysis - Department statistics")
    dept_stats = (
        df.groupBy("department")
        .agg(
            count("*").alias("employee_count"),
            avg("age").alias("avg_age"),
            avg("salary").alias("avg_salary"),
            sum("salary").alias("total_salary"),
        )
        .orderBy("department")
    )

    dept_stats.show()

    # Save results to output directory
    print(f"\nSaving results to {output_dir}")

    # Save each result to a separate subdirectory
    result1.write.mode("overwrite").parquet(f"{output_dir}/highest_paid")
    result2.write.mode("overwrite").parquet(f"{output_dir}/dept_avg_salary")
    recent_hires.write.mode("overwrite").parquet(f"{output_dir}/recent_hires")
    dept_stats.write.mode("overwrite").parquet(f"{output_dir}/dept_stats")

    # Save the original data as a partitioned table
    print("\nSaving data as a partitioned table by department")
    df.write.mode("overwrite").partitionBy("department").parquet(f"{output_dir}/employees_by_dept")

    spark.stop()


if __name__ == "__main__":
    main()
