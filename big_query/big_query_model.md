# BigQuery ML: Flight Delay Prediction Model

## Overview
This guide demonstrates how to build a machine learning model in BigQuery to predict whether a flight will arrive on time or late using logistic regression.

**Business Goal**: Predict if a flight will be "on time" (arrival delay < 15 minutes) or "late" (arrival delay ≥ 15 minutes)

## Prerequisites
- Completed the [flights view setup](flights_view.md)
- Dataset `dsongcp` with the `flights` view created

---

## Step 1: Create the Prediction Model (Test Run)

First, create a test model with limited data to verify the setup:

```sql
CREATE OR REPLACE MODEL dsongcp.arr_delay_lm
OPTIONS(
  input_label_cols=['ontime'],
  model_type='logistic_reg'
)
AS
SELECT
  IF(ARR_DELAY < 15, 'ontime', 'late') AS ontime,
  DEP_DELAY,
  TAXI_OUT,
  DISTANCE
FROM dsongcp.flights
WHERE
  CANCELLED = False AND
  DIVERTED = False
LIMIT 5
```

**Model Configuration:**
- **`input_label_cols=['ontime']`**: Target variable (what we're predicting)
- **`model_type='logistic_reg'`**: Logistic regression for binary classification

**Features:**
- **`DEP_DELAY`**: Departure delay in minutes (from `flights` view)
- **`TAXI_OUT`**: Taxi-out time in minutes (from `flights` view)
- **`DISTANCE`**: Flight distance in miles (from `flights` view)

**Label:**
- **`ontime`**: 'ontime' if `ARR_DELAY` < 15 minutes, otherwise 'late'

**Note:** The `LIMIT 5` is just for testing. Remove it for the full model (see Step 5).

---

## Step 2: Examine Model Weights

After the model is trained, inspect the learned coefficients:

```sql
SELECT * FROM ML.WEIGHTS(MODEL dsongcp.arr_delay_lm)
```

**What this shows:**
- **Positive weights**: Features that increase probability of being "late"
- **Negative weights**: Features that increase probability of being "ontime"
- **Magnitude**: Strength of the feature's influence

**Expected insights:**
- `DEP_DELAY` should have a strong positive weight (higher delay → more likely to be late)
- `DISTANCE` might have a negative weight (longer flights can recover time)
- `TAXI_OUT` likely has a positive weight (longer taxi → congestion → delays)

---

## Step 3: Make a Prediction

Test the model with a single flight prediction:

```sql
SELECT * FROM ML.PREDICT(MODEL dsongcp.arr_delay_lm,
  (
    SELECT 12.0 AS DEP_DELAY, 14.0 AS TAXI_OUT, 1231 AS DISTANCE
  )
)
```

**Scenario:**
- Flight departed 12 minutes late (`DEP_DELAY = 12.0`)
- Took 14 minutes to taxi and take off (`TAXI_OUT = 14.0`)
- Flying 1,231 miles (`DISTANCE = 1231`)

**Output includes:**
- `predicted_ontime`: Either 'ontime' or 'late'
- `predicted_ontime_probs`: Array of probabilities for each class
  - Example: `[{label: "ontime", prob: 0.65}, {label: "late", prob: 0.35}]`

---

## Step 4: Evaluate Model Performance

Check how well the model performs:

```sql
SELECT *
FROM ML.EVALUATE(MODEL dsongcp.arr_delay_lm)
```

**Key metrics:**
- **`accuracy`**: Overall percentage of correct predictions (target: > 0.80)
- **`precision`**: Of flights predicted as "late", what % were actually late?
- **`recall`**: Of flights that were actually late, what % did we catch?
- **`f1_score`**: Harmonic mean of precision and recall
- **`roc_auc`**: Area under ROC curve (0.5 = random, 1.0 = perfect; target: > 0.75)
- **`log_loss`**: Lower is better

---

## Step 5: Train Full Model (Remove LIMIT)

Once you've verified everything works, train the model on the full dataset:

```sql
CREATE OR REPLACE MODEL dsongcp.arr_delay_lm
OPTIONS(
  input_label_cols=['ontime'],
  model_type='logistic_reg'
)
AS
SELECT
  IF(ARR_DELAY < 15, 'ontime', 'late') AS ontime,
  DEP_DELAY,
  TAXI_OUT,
  DISTANCE
FROM dsongcp.flights
WHERE
  CANCELLED = False AND
  DIVERTED = False
```

**Note:** Removed the `LIMIT 5` to train on all available data from the `flights` view.

---

## Step 6: Batch Predictions

Make predictions on multiple flights for a specific date:

```sql
SELECT
  FL_DATE,
  UNIQUE_CARRIER,
  ORIGIN,
  DEST,
  DEP_DELAY,
  TAXI_OUT,
  DISTANCE,
  ARR_DELAY AS actual_arr_delay,
  predicted_ontime,
  predicted_ontime_probs
FROM ML.PREDICT(MODEL dsongcp.arr_delay_lm,
  (
    SELECT *
    FROM dsongcp.flights
    WHERE
      FL_DATE = '2016-01-15' AND
      CANCELLED = False AND
      DIVERTED = False
  )
)
ORDER BY actual_arr_delay DESC
```

This predicts all flights for January 15, 2016 and compares predictions to actual outcomes.

---

## Summary

**Complete Workflow:**
1. Train model with test data (`LIMIT 5`)
2. Examine model weights (`ML.WEIGHTS`)
3. Make single prediction (`ML.PREDICT`)
4. Evaluate model performance (`ML.EVALUATE`)
5. Train full model (remove `LIMIT`)
6. Make batch predictions on new data

**Required Columns from `flights` view:**
- `ARR_DELAY`: For creating the label (ontime vs late)
- `DEP_DELAY`: Feature - Departure delay
- `TAXI_OUT`: Feature - Taxi-out time
- `DISTANCE`: Feature - Flight distance
- `CANCELLED`: Filter out cancelled flights
- `DIVERTED`: Filter out diverted flights
- `FL_DATE`, `UNIQUE_CARRIER`, `ORIGIN`, `DEST`: For batch predictions

**Prediction Target:**
- `ontime`: Flights with arrival delay < 15 minutes
- `late`: Flights with arrival delay ≥ 15 minutes
