# Cloud SQL Migration Guide

A practical guide to migrating a MariaDB database to Google Cloud SQL.

## Prerequisites

- GCP account with appropriate permissions
- gcloud CLI installed and configured
- Active GCP project

```bash
# Verify gcloud installation
gcloud --version

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Verify current project
gcloud config get-value project
```

## Step 1: Create VM and Install MariaDB

Create a Compute Engine VM with MariaDB and load the employees sample database.

```bash
# Set variables
PROJECT_ID=$(gcloud config get-value project)
ZONE="us-central1-a"
VM_NAME="mariadb-vm"

# Create VM with MariaDB installation script
gcloud compute instances create $VM_NAME \
    --zone=$ZONE \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --tags=mariadb-server \
    --metadata=startup-script='#!/bin/bash
    apt-get update
    apt-get install -y mariadb-server git
    systemctl start mariadb
    systemctl enable mariadb
    '

# Wait for VM to be ready
sleep 60

# Import employees database
gcloud compute ssh $VM_NAME --zone=$ZONE --command='
    sleep 10
    cd ~
    git clone https://github.com/datacharmer/test_db.git
    cd test_db
    sudo mysql -u root < employees.sql
    sudo mysql -u root -e "USE employees; SHOW TABLES;"
    sudo mysql -u root -e "USE employees; SELECT COUNT(*) FROM employees;"
'
```

## Step 2: Export and Upload to GCS

Export the database and upload to Google Cloud Storage.

```bash
# Set variables
BUCKET_NAME="${PROJECT_ID}-employees-db-backup"
EXPORT_FILE="employees_db_export.sql"
EXPORT_PATH="/tmp/${EXPORT_FILE}"

# Create GCS bucket
gsutil mb -p ${PROJECT_ID} -l us-central1 gs://${BUCKET_NAME}/

# Export database from VM
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
    sudo mysqldump -u root employees > ${EXPORT_PATH}
    ls -lh ${EXPORT_PATH}
"

# Copy export file to local machine
gcloud compute scp ${VM_NAME}:${EXPORT_PATH} ./${EXPORT_FILE} --zone=$ZONE

# Upload to GCS
gsutil cp ./${EXPORT_FILE} gs://${BUCKET_NAME}/

# Verify upload
gsutil ls -lh gs://${BUCKET_NAME}/
```

## Step 3: Create Cloud SQL and Import Data

Create a Cloud SQL MySQL instance and import the data.

Note: MySQL 8.0 is the appropriate choice because MariaDB is a MySQL fork that maintains compatibility. Cloud SQL MySQL can directly import MySQL/MariaDB dumps with the same SQL syntax.

```bash
# Set variables
INSTANCE_NAME="employees-mysql-instance"
REGION="us-central1"
DATABASE_VERSION="MYSQL_8_0"
TIER="db-f1-micro"
ROOT_PASSWORD="TempPassword123#"

# Create Cloud SQL instance
gcloud sql instances create $INSTANCE_NAME \
    --database-version=$DATABASE_VERSION \
    --tier=$TIER \
    --region=$REGION \
    --root-password=$ROOT_PASSWORD \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase

# Create database
gcloud sql databases create employees --instance=$INSTANCE_NAME

# Authorize your IP
MY_IP=$(curl -s ifconfig.me)
gcloud sql instances patch $INSTANCE_NAME \
    --authorized-networks=$MY_IP \
    --quiet

# Grant bucket access to Cloud SQL service account
SERVICE_ACCOUNT=$(gcloud sql instances describe $INSTANCE_NAME \
    --format="value(serviceAccountEmailAddress)")
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:objectViewer gs://${BUCKET_NAME}

# Import database
gcloud sql import sql $INSTANCE_NAME \
    gs://${BUCKET_NAME}/${EXPORT_FILE} \
    --database=employees

# Create test user
gcloud sql users create test-user \
    --instance=$INSTANCE_NAME \
    --password=TestPass123#

# Get connection information
gcloud sql instances describe $INSTANCE_NAME \
    --format='value(ipAddresses[0].ipAddress,connectionName)'
```

## Step 4: Connect from Colab

Use Google Colab to connect and query the database. Import [Notebook](cloud_sql_example/cloud_sql_colab.ipynb)


## Cleanup Resources

Remove all created resources to avoid charges.

```bash
# Delete Cloud SQL instance
gcloud sql instances delete employees-mysql-instance --quiet

# Delete GCS bucket
gsutil rm -r gs://${PROJECT_ID}-employees-db-backup/

# Delete VM
gcloud compute instances delete mariadb-vm --zone=us-central1-a --quiet

# Delete local files
rm employees_db_export.sql
```

## Security Best Practices

### Production Authentication

Use service accounts for production workloads:

```bash
# Create service account
gcloud iam service-accounts create cloudsql-client \
    --display-name="Cloud SQL Client"

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:cloudsql-client@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

# Create key
gcloud iam service-accounts keys create ~/key.json \
    --iam-account=cloudsql-client@PROJECT_ID.iam.gserviceaccount.com
```

### Use Secret Manager

Store passwords securely:

```bash
# Create secret
echo -n "PASSWORD" | gcloud secrets create db-password --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding db-password \
    --member="serviceAccount:SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
```


## Troubleshooting

### Connection Issues

```bash
# Check instance status
gcloud sql instances describe INSTANCE_NAME

# Verify authorized networks
gcloud sql instances describe INSTANCE_NAME \
    --format='value(settings.ipConfiguration.authorizedNetworks)'

# Add your IP
gcloud sql instances patch INSTANCE_NAME --authorized-networks=YOUR_IP
```

### Import Errors

```bash
# Verify service account permissions
SERVICE_ACCOUNT=$(gcloud sql instances describe INSTANCE_NAME \
    --format='value(serviceAccountEmailAddress)')
gsutil iam ch serviceAccount:${SERVICE_ACCOUNT}:objectViewer gs://YOUR-BUCKET/
```

## Using Cloud SQL Proxy

Alternative connection method using Cloud SQL Proxy:

```bash
# Download Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy

# Start proxy
./cloud-sql-proxy PROJECT:REGION:INSTANCE

# Connect via localhost
mysql -h 127.0.0.1 -u USERNAME -p
```

## Best Practices

### Security
- Use service accounts for production workloads
- Store passwords in Secret Manager
- Use Cloud SQL Proxy or Private IP for connections
- Enable SSL/TLS connections
- Never commit credentials to version control
- Avoid using public IP in production

### Performance
- Use appropriate instance tier for workload
- Enable query cache
- Create indexes for frequent queries
- Use connection pooling
- Monitor with Cloud Monitoring

### Cost Optimization
- Use shared-core instances for development/testing
- Enable auto-scaling storage
- Set up automatic backups with retention policy
- Delete test resources when done

## Resources

- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Employees Database](https://github.com/datacharmer/test_db)
- [Cloud SQL Python Connector](https://github.com/GoogleCloudPlatform/cloud-sql-python-connector)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org)
- [gsutil Documentation](https://cloud.google.com/storage/docs/gsutil)
