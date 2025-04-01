SELECT
   ORIGIN,
   AVG(DEP_DELAY) AS dep_delay,
   AVG(ARR_DELAY) AS arr_delay,
   COUNT(ARR_DELAY) AS num_flights
 FROM
   ds_flights.flights_tzcorr
 GROUP BY
   ORIGIN

SELECT
ORIGIN,
AVG(DEP_DELAY) AS dep_delay,
AVG(ARR_DELAY) AS arr_delay,
COUNT(ARR_DELAY) AS num_flights
FROM
ds_flights.flights_tzcorr
WHERE EXTRACT(MONTH FROM FL_DATE) = 1
GROUP BY
ORIGIN
HAVING num_flights > 310
ORDER BY dep_delay DESC



CREATE OR REPLACE VIEW ds_flights.airport_delays AS
WITH delays AS (
    SELECT d.*, a.LATITUDE, a.LONGITUDE
    FROM ds_flights.streaming_delays d
    JOIN ds_flights.airports a USING(AIRPORT) 
    WHERE a.AIRPORT_IS_LATEST = 1
)
 
SELECT 
    AIRPORT,
    CONCAT(LATITUDE, ',', LONGITUDE) AS LOCATION,
    ARRAY_AGG(
        STRUCT(AVG_ARR_DELAY, AVG_DEP_DELAY, NUM_FLIGHTS, END_TIME)
        ORDER BY END_TIME DESC LIMIT 1) AS a
FROM delays
GROUP BY AIRPORT, LONGITUDE, LATITUDE

--Notebook for Workbench



%%bigquery
SELECT
  COUNTIF(arr_delay >= 15)/COUNT(arr_delay) AS frac_delayed
FROM ds_flights.flights_tzcorr


%%bigquery df
SELECT ARR_DELAY, DEP_DELAY
FROM ds_flights.flights_tzcorr
WHERE DEP_DELAY >= 10

df.describe()

sns.set_style("whitegrid")
ax = sns.violinplot(data=df, x='ARR_DELAY', inner='box', orient='h')
ax.axes.set_xlim(-50, 300);


import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


%%bigquery df
SELECT ARR_DELAY, DEP_DELAY
FROM ds_flights.flights_tzcorr


df['ontime'] = df['DEP_DELAY'] < 10

ax = sns.violinplot(data=df, x='ARR_DELAY', y='ontime',
                    inner='box', orient='h')
ax.set_xlim(-50, 200)



CREATE OR REPLACE TABLE ds_flights.trainday AS
SELECT
  FL_DATE,
  IF(ABS(MOD(FARM_FINGERPRINT(CAST(FL_DATE AS STRING)), 100)) < 70,
     'True', 'False') AS is_train_day
FROM (
  SELECT
    DISTINCT(FL_DATE) AS FL_DATE
  FROM
    ds_flights.flights_tzcorr)
ORDER BY
  FL_DATE
  
  
  
#model on BQ

CREATE OR REPLACE MODEL ds_flights.arr_delay_lm
OPTIONS(input_label_cols=['ontime'], 
        model_type='logistic_reg', 
        data_split_method='custom',
        data_split_col='is_eval_day')
AS
SELECT
  IF(arr_delay < 15, 'ontime', 'late') AS ontime,
  dep_delay,
  taxi_out,
  distance,
  IF(is_train_day = 'True', False, True) AS is_eval_day
FROM ds_flights.flights_tzcorr f
JOIN ds_flights.trainday t
ON f.FL_DATE = t.FL_DATE
WHERE
  f.CANCELLED = False AND
  f.DIVERTED = False
LIMIT 5
  
SELECT * FROM ML.WEIGHTS(MODEL ds_flights.arr_delay_lm) 


SELECT * FROM ML.PREDICT(MODEL ds_flights.arr_delay_lm,
                        (
SELECT 12.0 AS dep_delay, 14.0 AS taxi_out, 1231 AS distance
                        ))
						


SELECT * 
FROM ML.EVALUATE(MODEL ds_flights.arr_delay_lm)


CREATE OR REPLACE MODEL ds_flights.arr_delay_lm
OPTIONS(input_label_cols=['ontime'], 
        model_type='logistic_reg', 
        data_split_method='custom',
        data_split_col='is_eval_day')
AS
SELECT
  IF(arr_delay < 15, 'ontime', 'late') AS ontime,
  dep_delay,
  taxi_out,
  distance
FROM `cc-2023-q1.dsongcp.flights`
WHERE  CANCELLED = False AND
  DIVERTED = False
LIMIT 5