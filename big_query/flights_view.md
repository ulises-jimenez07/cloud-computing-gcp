git clone    https://github.com/GoogleCloudPlatform/data-science-on-gcp/
cd data-science-on-gcp/02_ingest/
./ingest_from_crsbucket.sh my-bucket-ulises-up2


bq mk dsongcp
bq load --autodetect --source_format=CSV \
   dsongcp.flights_auto \
   gs://my-bucket-ulises-up2/flights/raw/201501.csv
   
./bqload.sh my-bucket-ulises-up 2015 



 
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


CASE WHEN
(ARR_DELAY < 15)
THEN
"ON TIME"
ELSE
"LATE"
END