

mysqldump -ucc_user -p employees > employees_backup.sql
gsutil cp employees_backup.sql gs://mariadb-sqlcloud-up


gcloud sql instances create my-instance --database-version=MYSQL_8_0 \
--cpu=2 --memory=4GB --region=us-central1 --root-password=example123 \
--no-deletion-protection


gcloud sql databases create employees --instance=my-instance

gcloud sql import sql my-instance gs://doc-ai-extractor-temp/employees_backup.sql --database=employees

gcloud sql instances delete my-instance