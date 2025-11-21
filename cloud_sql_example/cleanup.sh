#!/bin/bash
# Cleanup Script - Delete all resources created by this example
# WARNING: This will delete all resources and data!

set -e

PROJECT_ID=$(gcloud config get-value project)
ZONE="us-central1-a"
REGION="us-central1"
VM_NAME="mariadb-vm"
INSTANCE_NAME="employees-mysql-instance"
BUCKET_NAME="${PROJECT_ID}-employees-db-backup"

echo "==========================================================="
echo "   Cloud SQL Migration - Cleanup Script"
echo "   WARNING: This will delete all resources!"
echo "==========================================================="
echo ""
echo "Project: $PROJECT_ID"
echo ""
echo "Resources that will be deleted:"
echo "  - VM Instance: $VM_NAME"
echo "  - Cloud SQL Instance: $INSTANCE_NAME"
echo "  - GCS Bucket: gs://$BUCKET_NAME"
echo "  - Local export files"
echo ""
echo "WARNING: This action cannot be undone!"
echo ""
read -p "Are you sure you want to delete all resources? (type 'DELETE' to confirm): " -r
echo ""

if [[ ! $REPLY == "DELETE" ]]; then
    echo "Aborted. No resources were deleted."
    exit 0
fi

echo "Starting cleanup..."
echo ""

# Delete Cloud SQL Instance
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Deleting Cloud SQL Instance: $INSTANCE_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if gcloud sql instances describe $INSTANCE_NAME &>/dev/null; then
    echo "Deleting Cloud SQL instance (this may take a few minutes)..."
    gcloud sql instances delete $INSTANCE_NAME --quiet
    echo "[OK] Cloud SQL instance deleted"
else
    echo "[SKIP] Cloud SQL instance not found (already deleted or never created)"
fi
echo ""

# Delete VM
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Deleting VM Instance: $VM_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
    gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
    echo "[OK] VM instance deleted"
else
    echo "[SKIP] VM instance not found (already deleted or never created)"
fi
echo ""

# Delete GCS Bucket
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Deleting GCS Bucket: gs://$BUCKET_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if gsutil ls -b gs://$BUCKET_NAME &>/dev/null; then
    echo "Deleting bucket contents..."
    gsutil -m rm -r gs://$BUCKET_NAME/** 2>/dev/null || true
    echo "Deleting bucket..."
    gsutil rb gs://$BUCKET_NAME
    echo "[OK] GCS bucket deleted"
else
    echo "[SKIP] GCS bucket not found (already deleted or never created)"
fi
echo ""

# Delete local files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Deleting Local Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
LOCAL_FILES=("employees_db_export.sql" "connection_info.txt" "downloaded_backup.sql")
for file in "${LOCAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "[OK] Deleted: $file"
    fi
done
echo ""

# Optional: Delete service accounts (commented out for safety)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Service Accounts"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "The following service accounts may have been created:"
echo "  - cloudsql-client@${PROJECT_ID}.iam.gserviceaccount.com"
echo ""
echo "To delete service accounts manually:"
echo "  gcloud iam service-accounts delete SERVICE_ACCOUNT_EMAIL"
echo ""

# List any remaining resources
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Checking for any remaining resources..."
echo ""

# Check VMs
VM_COUNT=$(gcloud compute instances list --filter="name:mariadb*" --format="value(name)" | wc -l)
if [ $VM_COUNT -gt 0 ]; then
    echo "[WARNING] Found $VM_COUNT remaining VM(s):"
    gcloud compute instances list --filter="name:mariadb*"
else
    echo "[OK] No VMs found"
fi

# Check Cloud SQL
SQL_COUNT=$(gcloud sql instances list --filter="name:employees*" --format="value(name)" | wc -l)
if [ $SQL_COUNT -gt 0 ]; then
    echo "[WARNING] Found $SQL_COUNT remaining Cloud SQL instance(s):"
    gcloud sql instances list --filter="name:employees*"
else
    echo "[OK] No Cloud SQL instances found"
fi

# Check buckets
BUCKET_COUNT=$(gsutil ls | grep -c "employees-db-backup" || true)
if [ $BUCKET_COUNT -gt 0 ]; then
    echo "[WARNING] Found $BUCKET_COUNT remaining bucket(s):"
    gsutil ls | grep "employees-db-backup"
else
    echo "[OK] No buckets found"
fi

echo ""
echo "==========================================================="
echo "   Cleanup Complete!"
echo "==========================================================="
echo ""
echo "All resources have been deleted."
echo "Your GCP project should no longer incur charges from this example."
echo ""
echo "To verify, check the GCP Console:"
echo "  - Compute Engine: https://console.cloud.google.com/compute"
echo "  - Cloud SQL: https://console.cloud.google.com/sql"
echo "  - Cloud Storage: https://console.cloud.google.com/storage"
echo ""
