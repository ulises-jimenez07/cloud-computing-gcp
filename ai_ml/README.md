# GCP AI/ML Exercises Guide

This guide covers different approaches to machine learning on Google Cloud Platform, from using prebuilt AI models to creating custom models and AutoML solutions.

---

## Table of Contents
1. [Prebuilt AI Models (Vision & Language APIs)](#1-prebuilt-ai-models-vision--language-apis)
2. [Creating Custom Models and Model Registry](#2-creating-custom-models-and-model-registry)
3. [BigQuery ML (BQML)](#3-bigquery-ml-bqml)
4. [AutoML on Vertex AI](#4-automl-on-vertex-ai)
5. [Cleanup: Avoid Unexpected Charges](#cleanup-avoid-unexpected-charges)

---

## 1. Prebuilt AI Models (Vision & Language APIs)

Google Cloud provides ready-to-use AI services that require no machine learning expertise.

### 1.1 Vision API

#### Setup
```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Authenticate with your Google account
gcloud auth application-default login

# Install Python client library
pip3 install --upgrade google-cloud-vision
```

#### Available Detection Types

**Logo Detection**
```bash
gcloud ml vision detect-logos Logo-Vodafone.png
```

**Object Detection**
```bash
gcloud ml vision detect-objects rose.jpg
```

**Text Detection (OCR)**
```bash
gcloud ml vision detect-text cloud-computing.png
```

#### Python Example: Logo Detection
```python
import io
import os
import json
from google.cloud import vision

# Instantiate a client
client = vision.ImageAnnotatorClient()

# Load the image
file_name = os.path.abspath('vodafone.jpg')
with io.open(file_name, 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)

# Perform logo detection
response = client.logo_detection(image=image)
logos = response.logo_annotations

# Display results
for logo in logos:
    print(f"{logo.description}: {logo.score}")

# Save full response to JSON file for detailed analysis
# View at https://jsoneditoronline.org for better formatting
with open('response.json', 'w') as f:
    json.dump(json.loads(response.__class__.to_json(response)), f, indent=2)
```

---

### 1.2 Natural Language API

#### Setup
```bash
# Install Python client library
pip3 install google-cloud-language

# Ensure authentication is configured
gcloud auth application-default login
```

#### Text Classification
Categorizes content into predefined categories (e.g., Politics, Technology, Sports).

**Example: Politics News**
```bash
gcloud ml language classify-text --content='House Intelligence Committee Chairman Adam Schiff, who also sits on the House committee investigating the Jan. 6, 2021, insurrection, said Sunday that he doesnt believe the committees upcoming report would focus almost entirely on Donald Trump.'
```

**Example: Technology News**
```bash
gcloud ml language classify-text --content='Facebooks parent company, Meta, has released an AI model called Galactica that is designed to write essays or scientific papers summarising the state of the art on a given topic, complete with citations, as well as detailed Wikipedia articles.'
```

#### Sentiment Analysis
Analyzes the emotional tone of text (positive, negative, neutral).

**Example: Product Review**
```bash
gcloud ml language analyze-sentiment --content='In description it says newest model, not true. BUT, for the price and quality itll do the job. The first thing that popped up is that there is no more updates for this laptop...'
```

**Example: Short Text**
```bash
gcloud ml language analyze-sentiment --content='I hate apple'
```

#### Entity Analysis
Extracts entities (people, organizations, locations) from text.

**Example: Wikipedia Text**
```bash
gcloud ml language analyze-entities --content='Google was founded on September 4, 1998, by Larry Page and Sergey Brin while they were PhD students at Stanford University in California.'
```

---

## 2. Creating Custom Models and Model Registry

Build your own ML model using scikit-learn and save it to Google Cloud Storage.

### 2.1 Create a Vertex AI Workbench Instance

Before training custom models, set up a Jupyter notebook environment on Vertex AI Workbench.

#### Prerequisites
```bash
# Enable required APIs
gcloud services enable notebooks.googleapis.com

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

#### Console Steps

1. **Navigate to Vertex AI Workbench**
   - Go to: https://console.cloud.google.com/vertex-ai/workbench/instances
   - Or search for "Vertex AI Workbench" in the Cloud Console

2. **Create New Instance**
   - Click **Create New** or **New Instance**
   - Select **Python 3** (or your preferred environment)

3. **Configure Instance Settings**
   - **Name**: Enter a name (e.g., `ml-workbench-instance`)
   - **Region**: Select closest region (e.g., `us-central1`)
   - **Zone**: Choose a zone in your region

4. **Machine Configuration**
   - **Machine type**: Select based on your needs
     - For basic tasks: `n1-standard-4` (4 vCPUs, 15 GB RAM)
     - For intensive training: `n1-highmem-8` or higher
   - View monthly cost estimate for each machine type

5. **Optional: Add GPU**
   - **GPU type**: NVIDIA Tesla T4, V100, or A100
   - **Number of GPUs**: 1 or more
   - Check **Install NVIDIA GPU driver automatically for me**

6. **Environment Settings**
   - **JupyterLab version**: Select JupyterLab 4.x (or 3.x)
   - **Idle shutdown**: Set minutes before auto-shutdown (10-1440)
     - Recommended: 60 minutes to save costs

7. **Create Instance**
   - Click **Create**
   - Wait 3-5 minutes for instance provisioning

8. **Access JupyterLab**
   - Once ready, click **Open JupyterLab**
   - Your notebook environment will open in a new tab

#### Alternative: Create via gcloud CLI
```bash
gcloud notebooks instances create ml-workbench-instance \
  --location=us-central1-a \
  --machine-type=n1-standard-4 \
  --vm-image-project=deeplearning-platform-release \
  --vm-image-family=common-cpu-notebooks
```

---

### 2.2 Training a Custom Model

**Python Code: Iris Classification Model**
```python
from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn import tree
from sklearn.metrics import accuracy_score
import pickle
import sklearn

# Load dataset
iris = datasets.load_iris()
x = iris.data
y = iris.target

# Split data
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.8)

# Train model
classifier = tree.DecisionTreeClassifier()
classifier.fit(x_train, y_train)

# Evaluate
predictions = classifier.predict(x_test)
print(f"Accuracy: {accuracy_score(y_test, predictions)}")

# Check sklearn version (important for deployment)
print(f"Scikit-learn version: {sklearn.__version__}")
```

### 2.3 Saving Model to Model Registry

#### Step 1: Serialize the model
```python
import pickle

pkl_filename = "model.pkl"
with open(pkl_filename, 'wb') as file:
    pickle.dump(classifier, file)
```

#### Step 2: Create a Cloud Storage bucket and upload model
```bash
# Create a bucket (if you don't have one)
gsutil mb -l us-central1 gs://YOUR-BUCKET-NAME

# Create a models directory structure
gsutil mkdir gs://YOUR-BUCKET-NAME/iris_model/1/

# Upload the model
gsutil cp model.pkl gs://YOUR-BUCKET-NAME/iris_model/1/model.pkl
```

#### Step 3: Import Model to Vertex AI Model Registry (Console)

1. **Navigate to Model Registry**
   - Go to: https://console.cloud.google.com/vertex-ai/models
   - Click **Import** (top of page)

2. **Choose Import Type**
   - Select **Import as new model**
   - Click **Continue**

3. **Model Settings**
   - **Model name**: `iris_classifier`
   - **Region**: Select same region as your bucket (e.g., `us-central1`)
   - **Version name**: `v1` (optional)
   - **Description**: "Iris classification model using Decision Tree"

4. **Model Framework**
   - **Framework**: Select **Scikit-learn**
   - **Framework version**: Match your sklearn version (check with `sklearn.__version__`)
   - **Python version**: 3.8 or 3.9

5. **Model Location**
   - **Model artifacts location**:
     - Click **Browse**
     - Navigate to: `gs://YOUR-BUCKET-NAME/iris_model/1/`
     - Select the folder (not the file)
   - The path should be the directory containing `model.pkl`

6. **Container Settings**
   - **Prediction container**: Use pre-built container
   - **Pre-built container**: `sklearn` (auto-selected based on framework)

7. **Import Model**
   - Click **Import**
   - Wait 2-5 minutes for import to complete
   - Model will appear on Models page when ready

#### Alternative: Import via gcloud CLI
```bash
gcloud ai models upload \
  --region=us-central1 \
  --display-name=iris_classifier \
  --container-image-uri=us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest \
  --artifact-uri=gs://YOUR-BUCKET-NAME/iris_model/1/
```

---

### 2.4 Deploy and Make Predictions

#### Deploy to Endpoint (Console)

1. **Create Endpoint**
   - Go to: https://console.cloud.google.com/vertex-ai/endpoints
   - Click **Create Endpoint**
   - Name: `iris_endpoint`
   - Region: Same as model
   - Click **Create**

2. **Deploy Model to Endpoint**
   - In Models page, click your model name
   - Click **Deploy to Endpoint**
   - Select your endpoint
   - **Machine type**: `n1-standard-2`
   - **Min replicas**: 1
   - **Max replicas**: 1
   - Click **Deploy**

3. **Test Predictions**
   - Go to endpoint page
   - Click **Sample Request** tab
   - Use this input format:

```json
{
  "instances": [
    [5.1, 7.1, 3, 2.5],
    [4.9, 3, 1.4, 0.2]
  ]
}
```

#### Python Prediction Example
```python
from google.cloud import aiplatform

aiplatform.init(project='YOUR_PROJECT_ID', location='us-central1')

# Get endpoint
endpoint = aiplatform.Endpoint('projects/PROJECT_NUMBER/locations/us-central1/endpoints/ENDPOINT_ID')

# Make prediction
prediction = endpoint.predict(
    instances=[
        [5.1, 7.1, 3.0, 2.5],
        [4.9, 3.0, 1.4, 0.2]
    ]
)

print(prediction.predictions)
```

---

## 3. BigQuery ML (BQML)

Train and deploy ML models directly in BigQuery using SQL.

### 3.1 Explore the Dataset

```sql
SELECT *
FROM `bigquery-public-data.ml_datasets.iris`
```

### 3.2 Create and Train a Model

```sql
CREATE OR REPLACE MODEL
  `ds_bqml_tutorial.irisdata_model`
OPTIONS
  (
    model_type='LOGISTIC_REG',
    auto_class_weights=TRUE,
    data_split_method='NO_SPLIT',
    input_label_cols=['species'],
    max_iterations=10
  ) AS
SELECT *
FROM `bigquery-public-data.ml_datasets.iris`
```

**Model Options Explained:**
- `model_type='LOGISTIC_REG'`: Logistic regression for classification
- `auto_class_weights=TRUE`: Automatically balance classes
- `input_label_cols=['species']`: The column to predict
- `max_iterations=10`: Number of training iterations

### 3.3 Evaluate the Model

```sql
SELECT *
FROM ML.EVALUATE(
  MODEL ds_bqml_tutorial.irisdata_model,
  (SELECT * FROM `bigquery-public-data.ml_datasets.iris`)
)
```

### 3.4 Make Predictions

```sql
SELECT *
FROM ML.PREDICT(
  MODEL ds_bqml_tutorial.irisdata_model,
  (
    SELECT
      5.1 as sepal_length,
      2.5 as petal_length,
      3.0 as petal_width,
      1.1 as sepal_width
  )
)
```

**Benefits of BQML:**
- No need to export data from BigQuery
- Use familiar SQL syntax
- Automatic scaling
- Integrated with BigQuery ecosystem

---

## 4. AutoML on Vertex AI

AutoML allows you to train high-quality custom models with minimal machine learning expertise.

### 4.1 AutoML Vision: Image Classification

**Use Case**: Classify flower images (daisy, dandelion, rose, sunflower, tulip)

#### Dataset
```
gs://cloud-samples-data/ai-platform/flowers/flowers.csv
```
or for newer Vertex AI:
```
gs://cloud-samples-data/vision/automl_classification/flowers/all_data_v2.csv
```

#### Steps via Console

1. **Navigate to Vertex AI**
   ```bash
   # Open in browser
   https://console.cloud.google.com/vertex-ai
   ```

2. **Create Dataset**
   - Go to Datasets → Create Dataset
   - Select "Image classification (Single-label)"
   - Name: `flowers_dataset`
   - Region: Choose your preferred region
   - Upload method: Import files from Cloud Storage
   - Enter the CSV path above

3. **Explore Data**
   - Review images and labels
   - Check class distribution
   - Ensure minimum 100 images per label

4. **Train Model**
   - Click "Train New Model"
   - Select AutoML
   - Training budget: Start with 1-8 node hours
   - Click "Start Training"

5. **Evaluate Model**
   - View precision, recall, F1-score
   - Check confusion matrix
   - Analyze per-label performance

6. **Deploy Model**
   - Deploy to endpoint for online predictions
   - Or use batch predictions for large datasets

#### Steps via Python SDK

```python
from google.cloud import aiplatform

aiplatform.init(project='YOUR_PROJECT_ID', location='us-central1')

# Create dataset
dataset = aiplatform.ImageDataset.create(
    display_name='flowers_dataset',
    gcs_source='gs://cloud-samples-data/vision/automl_classification/flowers/all_data_v2.csv'
)

# Train AutoML model
job = aiplatform.AutoMLImageTrainingJob(
    display_name='flowers_automl_training',
    prediction_type='classification',
    multi_label=False
)

model = job.run(
    dataset=dataset,
    model_display_name='flowers_automl_model',
    training_fraction_split=0.8,
    validation_fraction_split=0.1,
    test_fraction_split=0.1,
    budget_milli_node_hours=8000,
)
```

---

### 4.2 AutoML Natural Language: Text Classification

**Use Case**: Classify happy moments into categories

#### Dataset
```
gs://cloud-ml-data/NL-classification/happiness.csv
```

#### Dataset Format
AutoML Natural Language expects CSV with:
- Column 1: Text content or URL
- Column 2: Label/category

**Recommendations:**
- Minimum 1000 training documents per label
- Balanced class distribution
- Clear, distinct categories

#### Steps via Console

1. **Navigate to Vertex AI**
   ```bash
   https://console.cloud.google.com/vertex-ai
   ```

2. **Create Dataset**
   - Datasets → Create Dataset
   - Select "Text classification (Single-label)"
   - Name: `happiness_classification`
   - Region: us-central1
   - Import from Cloud Storage: `gs://cloud-ml-data/NL-classification/happiness.csv`

3. **Review Data**
   - Check text samples
   - Verify label distribution
   - Remove duplicates or errors

4. **Train Model**
   - Click "Train New Model"
   - Select AutoML
   - Training budget: 1-3 node hours for testing
   - Click "Start Training"

5. **Evaluate**
   - Review metrics: Precision, Recall, F1
   - Test with sample predictions
   - Check classification report

6. **Deploy or Export**
   - Deploy to endpoint for real-time predictions
   - Or export model for edge deployment

#### Steps via Python SDK

```python
from google.cloud import aiplatform

aiplatform.init(project='YOUR_PROJECT_ID', location='us-central1')

# Create dataset
dataset = aiplatform.TextDataset.create(
    display_name='happiness_classification',
    gcs_source='gs://cloud-ml-data/NL-classification/happiness.csv'
)

# Train AutoML model
job = aiplatform.AutoMLTextTrainingJob(
    display_name='happiness_automl_training',
    prediction_type='classification',
)

model = job.run(
    dataset=dataset,
    model_display_name='happiness_automl_model',
    training_fraction_split=0.8,
    validation_fraction_split=0.1,
    test_fraction_split=0.1,
)

# Deploy model
endpoint = model.deploy(
    machine_type='n1-standard-2',
    min_replica_count=1,
    max_replica_count=1,
)

# Make predictions
prediction = endpoint.predict(
    instances=[
        {"content": "I got a promotion at work today!"}
    ]
)
print(prediction)
```

---

## Comparison: When to Use Each Approach

| Approach | Best For | Pros | Cons |
|----------|----------|------|------|
| **Prebuilt APIs** | Common tasks (OCR, sentiment, etc.) | No training needed, instant results | Limited customization |
| **Custom Models** | Specific use cases, full control | Complete flexibility | Requires ML expertise |
| **BigQuery ML** | Data already in BigQuery | SQL-based, no data movement | Limited to BigQuery ecosystem |
| **AutoML** | Custom models without ML expertise | High quality, minimal coding | Can be expensive, less control |

---

## Resources

### Official Documentation
- [Vertex AI Workbench Instance Creation](https://cloud.google.com/vertex-ai/docs/workbench/instances/create-console-quickstart)
- [Vertex AI Image Classification Tutorial](https://cloud.google.com/vertex-ai/docs/tutorials/image-classification-automl/dataset)
- [AutoML Natural Language Beginner's Guide](https://cloud.google.com/natural-language/automl/docs/beginners-guide)
- [Vertex AI Model Registry Introduction](https://docs.cloud.google.com/vertex-ai/docs/model-registry/introduction)
- [Import Models to Vertex AI](https://cloud.google.com/vertex-ai/docs/model-registry/import-model)
- [Vertex AI Samples Repository](https://github.com/GoogleCloudPlatform/vertex-ai-samples)
- [Vertex AI Cleanup Guide](https://cloud.google.com/vertex-ai/docs/tutorials/image-recognition-automl/cleanup)

### Hands-on Labs
- [Using an Image Dataset to Train an AutoML Model](https://www.cloudskillsboost.google/focuses/33568?parent=catalog)
- [Vertex AI: Training and Serving a Custom Model](https://www.cloudskillsboost.google/focuses/73258?parent=catalog)

### Blog Posts
- [Build a text classification model with AutoML Natural Language](https://cloud.google.com/blog/products/ai-machine-learning/no-deep-learning-experience-needed-build-a-text-classification-model-with-google-cloud-automl-natural-language)

---

## Cleanup: Avoid Unexpected Charges

**IMPORTANT**: Delete resources when you're done to avoid ongoing charges.

### Cleanup Order

Resources must be deleted in a specific order to avoid dependency errors.

#### 1. Undeploy Models from Endpoints

**Console:**
1. Go to: https://console.cloud.google.com/vertex-ai/endpoints
2. Click on your endpoint
3. Find the deployed model
4. Click **⋮** (three dots) → **Undeploy model from endpoint**
5. Click **Undeploy** in the confirmation dialog
6. Wait for undeployment to complete

**gcloud CLI:**
```bash
gcloud ai endpoints undeploy-model ENDPOINT_ID \
  --region=us-central1 \
  --deployed-model-id=DEPLOYED_MODEL_ID
```

#### 2. Delete Endpoints

**Console:**
1. Go to: https://console.cloud.google.com/vertex-ai/endpoints
2. Click **☑** checkbox next to endpoint
3. Click **Delete**
4. Confirm deletion

**gcloud CLI:**
```bash
gcloud ai endpoints delete ENDPOINT_ID --region=us-central1
```

#### 3. Delete Models

**Console:**
1. Go to: https://console.cloud.google.com/vertex-ai/models
2. Click **⋮** (three dots) on model row
3. Click **Delete model**
4. Click **Delete** in confirmation dialog

**gcloud CLI:**
```bash
gcloud ai models delete MODEL_ID --region=us-central1
```

#### 4. Delete Datasets

**Console:**
1. Go to: https://console.cloud.google.com/vertex-ai/datasets
2. Click **⋮** (three dots) on dataset row
3. Click **Delete dataset**
4. Click **Delete** in confirmation dialog

**gcloud CLI:**
```bash
gcloud ai datasets delete DATASET_ID --region=us-central1
```

#### 5. Delete Vertex AI Workbench Instances

**Console:**
1. Go to: https://console.cloud.google.com/vertex-ai/workbench/instances
2. Click **☑** checkbox next to instance
3. Click **Delete**
4. Confirm deletion

**gcloud CLI:**
```bash
gcloud notebooks instances delete ml-workbench-instance \
  --location=us-central1-a
```

#### 6. Delete BigQuery ML Models

**BigQuery Console:**
```sql
DROP MODEL IF EXISTS `ds_bqml_tutorial.irisdata_model`;
```

**gcloud CLI:**
```bash
bq rm -m ds_bqml_tutorial.irisdata_model
```

#### 7. Delete Cloud Storage Buckets

**Console:**
1. Go to: https://console.cloud.google.com/storage/browser
2. Click **☑** checkbox next to bucket
3. Click **Delete**
4. Type bucket name to confirm
5. Click **Delete**

**gcloud CLI:**
```bash
# Delete all objects first
gsutil -m rm -r gs://YOUR-BUCKET-NAME/**

# Delete the bucket
gsutil rb gs://YOUR-BUCKET-NAME
```

### Quick Cleanup Script

```bash
#!/bin/bash
# Save as cleanup.sh and run: bash cleanup.sh

PROJECT_ID="YOUR_PROJECT_ID"
REGION="us-central1"

echo "Starting cleanup..."

# Undeploy and delete endpoints
gcloud ai endpoints list --region=$REGION --format="value(name)" | while read endpoint; do
  echo "Deleting endpoint: $endpoint"
  gcloud ai endpoints delete $endpoint --region=$REGION --quiet
done

# Delete models
gcloud ai models list --region=$REGION --format="value(name)" | while read model; do
  echo "Deleting model: $model"
  gcloud ai models delete $model --region=$REGION --quiet
done

# Delete datasets
gcloud ai datasets list --region=$REGION --format="value(name)" | while read dataset; do
  echo "Deleting dataset: $dataset"
  gcloud ai datasets delete $dataset --region=$REGION --quiet
done

# Delete Workbench instances
gcloud notebooks instances list --location=${REGION}-a --format="value(name)" | while read instance; do
  echo "Deleting instance: $instance"
  gcloud notebooks instances delete $instance --location=${REGION}-a --quiet
done

echo "Cleanup complete!"
echo "Remember to manually delete Cloud Storage buckets if needed."
```

### Cost-Saving Tips

- **Set idle timeouts** on Workbench instances (60 minutes recommended)
- **Use preemptible instances** for training jobs (up to 80% cheaper)
- **Delete endpoints** when not actively serving predictions
- **Use batch predictions** instead of online endpoints for large jobs
- **Monitor billing** regularly at: https://console.cloud.google.com/billing

---

## Next Steps

1. **Start Simple**: Begin with prebuilt APIs to understand GCP AI services
2. **Experiment with BQML**: If you have data in BigQuery, try creating a simple model
3. **Try AutoML**: Use the flowers or happiness datasets to train your first AutoML model
4. **Advanced**: Build custom models when you need specific functionality
5. **Always Clean Up**: Delete resources when done to avoid unexpected charges

Remember to enable the required APIs and set up billing before starting!
