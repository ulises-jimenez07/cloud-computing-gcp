-- This query calculates the duration of bike trips in minutes.
SELECT
  tripduration / 60 AS duration_trip_minutes -- Divides the tripduration by 60 to get minutes.
FROM
  `bigquery-public-data.new_york_citibike.citibike_trips` -- Uses the citibike_trips table from the public dataset.
WHERE tripduration IS NOT NULL  -- Filters out rows where tripduration is null.
LIMIT 200; -- Limits the results to 200 rows.

-- This query selects all columns except stoptime and end_station_id.
SELECT
  * EXCEPT(stoptime, end_station_id) -- Selects all columns except the specified ones.
FROM
  `bigquery-public-data.new_york_citibike.citibike_trips` --  Uses the citibike_trips table.
WHERE tripduration IS NOT NULL -- Filters out rows where tripduration is null.
LIMIT 200; -- Limits the results to 200 rows.


-- This query selects all data from a CTE (Common Table Expression) where gender is 'male'.
WITH all_data AS ( -- Defines a CTE called all_data.
  SELECT
    * EXCEPT(stoptime, end_station_id) -- Selects all columns except the specified ones.
  FROM
    `bigquery-public-data.new_york_citibike.citibike_trips` -- Uses the citibike_trips table.
  WHERE tripduration IS NOT NULL -- Filters out rows where tripduration is null.
  LIMIT 200 -- Limits the results to 200 rows.
)
SELECT * FROM all_data WHERE gender = 'male'; -- Filters the results from the CTE where gender is 'male'.


-- This query counts all rows in the citibike_trips table.
SELECT COUNT(*) FROM bigquery-public-data.new_york_citibike.citibike_trips;


-- This query counts the number of trips for each gender.
SELECT
  gender, -- Selects the gender column.
  COUNT(*) -- Counts the number of rows for each gender.
FROM
  bigquery-public-data.new_york_citibike.citibike_trips
GROUP BY gender; -- Groups the results by gender.



-- This query removes " at " from the name column.
SELECT
  REPLACE(name, ' at ', ' ') -- Replaces " at " with a space in the name column.
FROM
  bigquery-public-data.san_francisco.bikeshare_stations;


-- This query splits the name column into an array of strings.
SELECT
  SPLIT(REPLACE(name, ' at ', ' '), ' ') -- Replaces " at " with a space, then splits the string by spaces.
FROM
  bigquery-public-data.san_francisco.bikeshare_stations;

-- This query extracts the year from the installation_date column.
SELECT
  installation_date, -- Selects the installation_date column.
  EXTRACT(YEAR FROM installation_date) -- Extracts the year from the installation_date.
FROM
  bigquery-public-data.san_francisco.bikeshare_stations;


-- This query creates a partitioned and clustered table from the chicago_crime.crime table.
bq query \
 --use_legacy_sql=false \  -- Uses standard SQL.
 --destination_table partition_ds.crime_partition \ -- Specifies the destination table and dataset.
 --time_partitioning_field date \ -- Partitions the table by the date field.
 --time_partitioning_type MONTH \ -- Partitions by month.
 'Select * from `bigquery-public-data.chicago_crime.crime`' -- Selects all data from the chicago_crime.crime table.



-- This query selects data from the chicago_crime.crime table where the date is 2006-02-14 04:15:00 UTC.
SELECT * FROM `bigquery-public-data.chicago_crime.crime`
WHERE date = '2006-02-14 04:15:00 UTC';


-- This query selects data from the partitioned table where the date is 2006-02-14 04:15:00 UTC.
SELECT * FROM `testup-gcp.partition_ds.crime_partition`
WHERE date = '2006-02-14 04:15:00 UTC';

-- This query retrieves information about partitions in the crime_partition table.
SELECT *
FROM `testup-gcp.partition_ds.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'crime_partition';


-- This query selects data from the chicago_crime.crime table where the date is 2006-02-14 04:15:00 UTC and primary_type is 'INTIMIDATION'.
SELECT * FROM `bigquery-public-data.chicago_crime.crime`
WHERE date = '2006-02-14 04:15:00 UTC'
  AND primary_type = 'INTIMIDATION';


-- This query creates a partitioned and clustered table from the chicago_crime.crime table.
bq query \
 --use_legacy_sql=false \ -- Uses standard SQL
 --clustering_fields primary_type \ -- Clusters the table by primary_type.
 --destination_table partition_ds.crime_partition_cluster \  -- Specifies the destination table.
 --time_partitioning_field date \ -- Partitions by date.
 --time_partitioning_type MONTH \ -- Partitions by month.
 'Select * from `bigquery-public-data.chicago_crime.crime`' -- Selects all data from the source table.

