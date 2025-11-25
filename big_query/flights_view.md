# BigQuery Flight Data Ingestion and View Creation

## Overview
This guide demonstrates how to ingest US flight departure/arrival data into BigQuery and create a standardized view for analysis. The data comes from the Bureau of Transportation Statistics and is used in the book "Data Science on the Google Cloud Platform" by Valliappa Lakshmanan (O'Reilly, 2022).

## Dataset Description
- **Source**: US Department of Transportation, Bureau of Transportation Statistics
- **Content**: Monthly flight data including departure times, arrival times, delays, cancellations, and diversions
- **Years**: 2015 onwards (minimum 2015 required for the book exercises)
- **Format**: CSV files partitioned by year and month (e.g., 201501.csv, 201502.csv)

## Prerequisites

### Get your Project ID
```bash
export PROJECT_ID=$(gcloud config get-value project)
echo "Project ID: $PROJECT_ID"
```

### Create a Cloud Storage Bucket
Create a globally unique bucket name and create the bucket:
```bash
export BUCKET_NAME="flights-data-${PROJECT_ID}"
gsutil mb -p $PROJECT_ID gs://$BUCKET_NAME
```

Verify the bucket was created:
```bash
gsutil ls -p $PROJECT_ID
```

## Step 1: Clone the Repository and Ingest Data

### Clone the source repository
```bash
git clone https://github.com/GoogleCloudPlatform/data-science-on-gcp/
```

### Navigate to the ingest folder
```bash
cd data-science-on-gcp/02_ingest/
```

### Copy flight data from public GCP bucket to your bucket
This script copies all monthly CSV files for 2015 (Jan-Dec) plus January 2016 from the public bucket `gs://data-science-on-gcp/edition2/flights/raw` to your own bucket.

```bash
./ingest_from_crsbucket.sh $BUCKET_NAME
```

**What this does:**
- Uses `gsutil -m cp` for parallel multi-threaded copying
- Copies 13 CSV files (~6 million rows of flight data)
- Each CSV contains: flight dates, airlines, airports, departure/arrival times, delays, cancellations, distance, etc.

---

## Step 2: Create BigQuery Dataset and Load Data

### Create the BigQuery dataset
```bash
bq mk dsongcp
```

### Test loading a single month with auto-detect schema
```bash
bq load --autodetect --source_format=CSV \
   dsongcp.flights_auto \
   gs://$BUCKET_NAME/flights/raw/201501.csv
```

**Purpose:** Test that data loads correctly before loading all months.

### Load all months for 2015 with explicit schema
```bash
./bqload.sh $BUCKET_NAME 2015
```

**What this does:**
- Creates or verifies the `dsongcp` dataset exists
- Loads all 12 months of 2015 flight data into a table called `flights_raw`
- Uses **time partitioning** by `FlightDate` column (monthly partitions) for efficient querying
- Applies an explicit schema with 109 columns including:
  - **Time fields**: FlightDate, CRSDepTime, DepTime, ArrTime, etc.
  - **Location fields**: Origin, Dest, OriginAirportSeqID, DestAirportSeqID
  - **Delay metrics**: DepDelay, ArrDelay, CarrierDelay, WeatherDelay, NASDelay
  - **Status flags**: Cancelled, Diverted
  - **Flight info**: Reporting_Airline, Flight_Number, Distance, etc.
- Replaces existing partitions if re-run

---

## Step 3: Verify Date Handling with Test Query

Test query to compare date reconstruction methods:
```sql
SELECT
    FORMAT("%s-%02d-%02d",
        Year,
        CAST(Month AS INT64),
        CAST(DayofMonth AS INT64)) AS resurrect,
    FlightDate,
    CAST(EXTRACT(YEAR FROM FlightDate) AS INT64) AS ex_year,
    CAST(EXTRACT(MONTH FROM FlightDate) AS INT64) AS ex_month,
    CAST(EXTRACT(DAY FROM FlightDate) AS INT64) AS ex_day,
FROM dsongcp.flights_raw
LIMIT 5
```

**Purpose:** Verify that:
- The `FlightDate` DATE column is correctly parsed from CSV
- You can reconstruct dates from Year/Month/DayofMonth columns
- Date extraction functions work properly

**Expected result:** Both `resurrect` and `FlightDate` should match (e.g., "2015-01-01")

---

## Step 4: Create Standardized View

Create a clean view with standardized column names and data types:

```sql
CREATE OR REPLACE VIEW dsongcp.flights AS

SELECT
  FlightDate AS FL_DATE,
  Reporting_Airline AS UNIQUE_CARRIER,
  OriginAirportSeqID AS ORIGIN_AIRPORT_SEQ_ID,
  Origin AS ORIGIN,
  DestAirportSeqID AS DEST_AIRPORT_SEQ_ID,
  Dest AS DEST,
  CRSDepTime AS CRS_DEP_TIME,
  DepTime AS DEP_TIME,
  CAST(DepDelay AS FLOAT64) AS DEP_DELAY,
  CAST(TaxiOut AS FLOAT64) AS TAXI_OUT,
  WheelsOff AS WHEELS_OFF,
  WheelsOn AS WHEELS_ON,
  CAST(TaxiIn AS FLOAT64) AS TAXI_IN,
  CRSArrTime AS CRS_ARR_TIME,
  ArrTime AS ARR_TIME,
  CAST(ArrDelay AS FLOAT64) AS ARR_DELAY,
  IF(Cancelled = '1.00', True, False) AS CANCELLED,
  IF(Diverted = '1.00', True, False) AS DIVERTED,
  DISTANCE
FROM dsongcp.flights_raw;
```

**Purpose of the view:**
1. **Rename columns** to match legacy naming conventions used in the book/analysis
2. **Type conversions**:
   - Cast delay fields (DepDelay, ArrDelay, TaxiOut, TaxiIn) from STRING to FLOAT64
   - Convert boolean strings ('1.00') to actual boolean values for CANCELLED and DIVERTED
3. **Select only relevant columns** from the 109-column raw table (reduces query costs and complexity)
4. **Standardize field names** for consistency across chapters

**Key transformations:**
- `FlightDate` → `FL_DATE`: Flight date
- `Reporting_Airline` → `UNIQUE_CARRIER`: Airline code
- `DepDelay` (STRING) → `DEP_DELAY` (FLOAT64): Departure delay in minutes
- `ArrDelay` (STRING) → `ARR_DELAY` (FLOAT64): Arrival delay in minutes
- `Cancelled` ('1.00') → `CANCELLED` (Boolean)
- `Diverted` ('1.00') → `DIVERTED` (Boolean)

### Flight Status Classification Logic

The view enables flight status classification using this business logic:

```sql
CASE WHEN
(ARR_DELAY < 15)
THEN
"ON TIME"
ELSE
"LATE"
END
```

**Business rule:**
- Flights arriving **less than 15 minutes late** are considered "ON TIME"
- Flights arriving **15+ minutes late** are considered "LATE"
- This is the standard definition used by airlines and the Department of Transportation

**Test query:**
```sql
SELECT
  FL_DATE,
  UNIQUE_CARRIER,
  ORIGIN,
  DEST,
  ARR_DELAY,
  CASE WHEN ARR_DELAY < 15 THEN "ON TIME" ELSE "LATE" END AS flight_status
FROM dsongcp.flights
WHERE CANCELLED = FALSE AND DIVERTED = FALSE
LIMIT 100
```

---

## Step 5: Create Looker Studio Dashboard

### Connect BigQuery to Looker Studio

1. **Navigate to Looker Studio**
   - Go to [https://lookerstudio.google.com/](https://lookerstudio.google.com/)
   - Sign in with your Google Cloud account

2. **Create a new report**
   - Click **Create** → **Report**
   - Select **BigQuery** as the data source

3. **Connect to the flights view**
   - **Project**: Select your GCP project
   - **Dataset**: `dsongcp`
   - **Table**: `flights` (the view you created)
   - Click **Add** to connect

### Add the Computed Flight Status Field

1. **Create a calculated field**
   - In the Looker Studio report editor, click **Add a field** in the data panel
   - Name the field: `Flight_Status`
   - Enter the formula:
     ```
     CASE
       WHEN ARR_DELAY < 15 THEN "ON TIME"
       ELSE "LATE"
     END
     ```
   - Click **Save**

2. **Alternative: Handle NULL values**
   - For more robust handling of cancelled/diverted flights:
     ```
     CASE
       WHEN CANCELLED = true THEN "CANCELLED"
       WHEN DIVERTED = true THEN "DIVERTED"
       WHEN ARR_DELAY < 15 THEN "ON TIME"
       WHEN ARR_DELAY >= 15 THEN "LATE"
       ELSE "UNKNOWN"
     END
     ```

### Build Dashboard Visualizations

**Recommended charts and metrics:**

1. **Scorecard: On-Time Performance Rate**
   - Metric: `Record Count` (with filter: `Flight_Status = "ON TIME"`)
   - Comparison: Total flights (percentage)
   - Shows overall on-time percentage

2. **Pie Chart: Flight Status Distribution**
   - Dimension: `Flight_Status`
   - Metric: `Record Count`
   - Shows proportion of ON TIME vs LATE flights

3. **Time Series: Daily On-Time Performance**
   - Date dimension: `FL_DATE`
   - Metric: Custom field with formula:
     ```
     SUM(CASE WHEN Flight_Status = "ON TIME" THEN 1 ELSE 0 END) / COUNT(*)
     ```
   - Shows trends over time

4. **Bar Chart: On-Time Performance by Airline**
   - Dimension: `UNIQUE_CARRIER`
   - Metric: On-time rate (calculated field)
   - Sort: Descending by on-time percentage
   - Shows which airlines perform best

5. **Table: Route Performance**
   - Dimensions: `ORIGIN`, `DEST`
   - Metrics:
     - Total flights: `Record Count`
     - Average delay: `AVG(ARR_DELAY)`
     - On-time rate: `Flight_Status` percentage
   - Shows best/worst performing routes

6. **Heatmap: Delays by Day of Week and Hour**
   - Dimensions: `EXTRACT(DAYOFWEEK FROM FL_DATE)`, `EXTRACT(HOUR FROM DEP_TIME)`
   - Metric: `AVG(ARR_DELAY)`
   - Shows when delays are most common

### Add Filters and Controls

1. **Date Range Control**
   - Add a **Date Range Control** widget
   - Set to `FL_DATE` field
   - Allows users to filter by date range

2. **Airline Dropdown Filter**
   - Add a **Drop-down list** control
   - Set to `UNIQUE_CARRIER` field
   - Enables filtering by specific airlines

3. **Origin/Destination Filters**
   - Add controls for `ORIGIN` and `DEST`
   - Allows analysis of specific airports or routes

### Dashboard Best Practices

- **Add titles and descriptions** to each chart
- **Use consistent color schemes**: Green for "ON TIME", Red for "LATE"
- **Enable drill-down** on charts where useful (e.g., from airline to specific routes)
- **Set up email delivery** for stakeholders (Schedule report delivery)
- **Optimize performance**:
  - Use date range filters to limit data scanned
  - Consider creating a BigQuery materialized view for frequently accessed aggregations
  - Enable query caching in BigQuery

---

## Summary

This workflow accomplishes:
1. **Data ingestion**: Copies ~6M rows of flight data from public GCP bucket to Cloud Storage
2. **BigQuery loading**: Loads CSV data with explicit schema and time partitioning for optimized queries
3. **Data cleaning**: Creates a standardized view with proper types and naming conventions
4. **Flight classification**: Implements business logic to categorize flights as ON TIME or LATE
5. **Dashboard creation**: Builds interactive Looker Studio dashboard with:
   - On-time performance metrics and KPIs
   - Visual analysis of delays by airline, route, and time
   - Interactive filters for deep-dive analysis
   - Computed field for flight status classification

**Data Pipeline:**
```
Public GCS Bucket → Your GCS Bucket → BigQuery Raw Table → BigQuery View → Looker Studio Dashboard
```

**Next steps:**
- **Machine Learning**: Predict flight delays using BigQuery ML or Vertex AI
- **Advanced Analytics**: Analyze delay patterns by weather, time of day, seasonality
- **Real-time Processing**: Set up streaming data ingestion with Pub/Sub and Dataflow
- **Automation**: Schedule monthly data updates using Cloud Scheduler and Cloud Run
- **Cost Optimization**: Create materialized views for frequently accessed aggregations