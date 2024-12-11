# Cloud Computing - GCP

This document outlines commands executed across various Google Cloud Platform (GCP) services, along with explanations for each command.

## Commands Executed

### Compute Engine

This section covers commands related to managing virtual machines (VMs) in Compute Engine.  Compute Engine lets you create and run VMs on Google's infrastructure.

```bash
sudo su                      # Switch to root user
apt update                  # Update package lists
apt install apache2         # Install Apache web server
ls /var/www/html           # List files in Apache's default web directory
echo "Hello World!"         # Print "Hello World!" to the console
echo "Hello World!" > /var/www/html/index.html  # Create a simple index.html file
echo $(hostname)            # Print the hostname of the VM
echo $(hostname -i)         # Print the internal IP address of the VM
echo "Hello World from $(hostname)" # Print a greeting with hostname
echo "Hello World from $(hostname) $(hostname -i)" # Print greeting with hostname and IP
echo "Hello world from $(hostname) $(hostname -i)" > /var/www/html/index.html # Update index.html with hostname and IP
sudo service apache2 start # Start the Apache web server


#!/bin/bash
apt update 
apt -y install apache2
echo "Hello world from $(hostname) $(hostname -I)" > /var/www/html/index.html


#!/bin/bash
echo "Hello world from $(hostname) $(hostname -I)" > /var/www/html/index.html
service apache2 start


gcloud config list project
gcloud config configurations list
gcloud config configurations activate my-default-configuration
gcloud config list
gcloud config configurations describe my-second-configuration
gcloud compute instances list
gcloud compute instances create
gcloud compute instances create my-first-instance-from-gcloud
gcloud compute instances describe my-first-instance-from-gcloud
gcloud compute instances delete my-first-instance-from-gcloud
gcloud compute zones list
gcloud compute regions list
gcloud compute machine-types list

gcloud compute machine-types list --filter zone:asia-southeast2-b
gcloud compute machine-types list --filter "zone:(asia-southeast2-b asia-southeast2-c)"
gcloud compute zones list --filter=region:us-west2
gcloud compute zones list --sort-by=region
gcloud compute zones list --sort-by=~region
gcloud compute zones list --uri
gcloud compute regions describe us-west4

gcloud compute instance-templates list
gcloud compute instance-templates create instance-template-from-command-line
gcloud compute instance-templates delete instance-template-from-command-line
gcloud compute instance-templates describe my-instance-template-with-custom-image

gcloud compute instances create my-test-vm --source-instance-template=my-instance-template-with-custom-image
gcloud compute instance-groups managed list
gcloud compute instance-groups managed delete my-managed-instance-group
gcloud compute instance-groups managed create my-mig --zone us-central1-a --template my-instance-template-with-custom-image --size 1
gcloud compute instance-groups managed set-autoscaling my-mig --max-num-replicas=2 --zone us-central1-a
gcloud compute instance-groups managed stop-autoscaling my-mig --zone us-central1-a
gcloud compute instance-groups managed resize my-mig --size=1 --zone=us-central1-a
gcloud compute instance-groups managed recreate-instances my-mig --instances=my-mig-85fb --zone us-central1-a
gcloud compute instance-groups managed delete my-managed-instance-group --region=us-central1
```

### App Engine
This section focuses on deploying and managing applications on App Engine. App Engine is a Platform as a Service (PaaS) for building and deploying scalable web applications and APIs.

```bash
cd default-service                # Change directory to the default service
gcloud app deploy                # Deploy the application to App Engine
gcloud app services list         # List all services in the App Engine project
gcloud app versions list          # List all versions of the deployed application
gcloud app instances list         # List all running instances of the application
gcloud app deploy --version=v2    # Deploy a new version (v2) of the application
gcloud app versions list          # List versions after deploying v2
gcloud app browse                # Open the deployed application in a web browser (default version)
gcloud app browse --version 20210215t072907  # Open a specific version in browser
gcloud app deploy --version=v3 --no-promote  # Deploy v3 without making it the default serving version
gcloud app browse --version v3   # Open v3 in browser
gcloud app services set-traffic split=v3=.5,v2=.5 # Split traffic between v2 and v3 (50/50)
watch curl https://melodic-furnace-304906.uc.r.appspot.com/ # Continuously curl the app URL (to observe traffic splitting)
gcloud app services set-traffic --splits=v3=.5,v2=.5 --split-by=random # Split traffic randomly

cd ../my-first-service/          # Change to another service directory
gcloud app deploy                # Deploy the "my-first-service" application
gcloud app browse --service=my-first-service # Open "my-first-service" in browser

gcloud app services list         # List all services

gcloud app regions list #List available regions for App Engine


gcloud app browse --service=my-first-service --version=20210215t075851 # Open specific version of "my-first-service"
gcloud app browse --version=v2   # Open v2 of the default service
gcloud app open-console --version=v2  # Open App Engine console for v2
gcloud app versions list --hide-no-traffic # List versions, hiding those not receiving traffic
```

### Kubernetes
This section demonstrates commands for interacting with Kubernetes clusters. Kubernetes is a container orchestration system for automating deployment, scaling, and management of containerized applications.

```bash
gcloud config set project my-kubernetes-project-304910 # Set the project for Kubernetes operations.
gcloud container clusters get-credentials my-cluster --zone us-central1-c --project my-kubernetes-project-304910 # Get credentials for a cluster.
kubectl create deployment hello-world-rest-api --image=in28min/hello-world-rest-api:0.0.1.RELEASE # Create a deployment.
kubectl get deployment # List deployments.
kubectl expose deployment hello-world-rest-api --type=LoadBalancer --port=8080  # Expose deployment using a LoadBalancer.
kubectl get services # List services.
kubectl get services --watch # Watch for changes in services.
curl 35.184.204.214:8080/hello-world #  Curl the exposed service.
kubectl scale deployment hello-world-rest-api --replicas=3  # Scale the deployment to 3 replicas.
gcloud container clusters resize my-cluster --node-pool default-pool --num-nodes=2 --zone=us-central1-c # Resize the cluster's node pool.
kubectl autoscale deployment hello-world-rest-api --max=4 --cpu-percent=70 # Configure autoscaling based on CPU usage.
kubectl get hpa  # List HorizontalPodAutoscalers.
kubectl create configmap hello-world-config --from-literal=RDS_DB_NAME=todos # Create a ConfigMap.
kubectl get configmap # List ConfigMaps.
kubectl describe configmap hello-world-config # Describe a ConfigMap.
kubectl create secret generic hello-world-secrets-1 --from-literal=RDS_PASSWORD=dummytodos  # Create a secret.
kubectl get secret # List secrets.
kubectl describe secret hello-world-secrets-1 # Describe a secret.
kubectl apply -f deployment.yaml # Apply a deployment configuration from a file.
gcloud container node-pools list --zone=us-central1-c --cluster=my-cluster # List node pools in a cluster.
kubectl get pods -o wide  # List pods with more details.

kubectl set image deployment hello-world-rest-api hello-world-rest-api=in28min/hello-world-rest-api:0.0.2.RELEASE  # Update the image used in a deployment.
kubectl get services  # List services.
kubectl get replicasets # List ReplicaSets.
kubectl get pods # List pods.
kubectl delete pod hello-world-rest-api-58dc9d7fcc-8pv7r  # Delete a specific pod.

kubectl scale deployment hello-world-rest-api --replicas=1 # Scale deployment down to 1 replica.
kubectl get replicasets # List ReplicaSets.
gcloud projects list  # List projects.

kubectl delete service hello-world-rest-api # Delete a service.
kubectl delete deployment hello-world-rest-api # Delete a deployment.
gcloud container clusters delete my-cluster --zone us-central1-c # Delete a cluster.
```

### Block Storage - Persistent Disks

```bash
gcloud config set project glowing-furnace-304608 # Set the active project.
gcloud compute disks list # List persistent disks.
gcloud compute disk-types list # List available disk types.
gcloud compute disks resize instance-1 --size=20GB --zone=us-central1-a  # Resize a persistent disk.
gcloud compute snapshots list # List snapshots of disks.
gcloud compute images list  # List custom images.
```

### Cloud Storage
```bash
gcloud --version # Display the gcloud SDK version.
gsutil mb gs://my_bucket_in28minutes_shell  # Create a new Cloud Storage bucket using gsutil.  Note: bucket names must be globally unique.
gcloud config set project glowing-furnace-304608 # Set the active project.
gsutil mb gs://my_bucket_in28minutes_shell  # Create a new Cloud Storage bucket.
gsutil ls gs://my_bucket_in28minutes_shell # List the contents of a Cloud Storage bucket.
```

### IAM
```bash
gcloud compute project-info describe # Get details about the current project.
gcloud auth list # List authenticated accounts.
gcloud projects get-iam-policy glowing-furnace-304608 # Get the IAM policy for a project.
gcloud projects add-iam-policy-binding glowing-furnace-304608 --member=user:in28minutes@gmail.com --role=roles/storage.objectAdmin # Grant a user the "Storage Object Admin" role.
gcloud projects remove-iam-policy-binding glowing-furnace-304608 --member=user:in28minutes@gmail.com --role=roles/storage.objectAdmin  # Revoke the "Storage Object Admin" role from a user.
gcloud iam roles describe roles/storage.objectAdmin  # Describe a specific IAM role.
gcloud iam roles copy --source=roles/storage.objectAdmin --destination=my.custom.role --dest-project=glowing-furnace-304608  # Copy an IAM role to create a custom role.
```

### Databases - Cloud SQL, Cloud Spanner and Cloud BigTable

```bash
# Cloud SQL
gcloud sql connect my-first-cloud-sql-instance --user=root --quiet # Connect to a Cloud SQL instance.
gcloud config set project glowing-furnace-304608 # Set the active project.
gcloud sql connect my-first-cloud-sql-instance --user=root --quiet # Connect to a Cloud SQL instance.
use todos;  -- Select the "todos" database.
create table user (id integer, username varchar(30) ); -- Create a table named "user".
describe user; -- Describe the structure of the "user" table.
insert into user values (1, 'Ranga'); -- Insert a row into the "user" table.
select * from user; -- Select all data from the "user" table.

mysqldump -ucc_user -p employees > employees_backup.sql  # Dump the "employees" database to a file (requires MySQL client).
gsutil cp employees_backup.sql gs://mariadb-sqlcloud-up  # Copy the backup file to Cloud Storage.


gcloud sql instances create my-instance --database-version=MYSQL_8_0 \
--cpu=2 --memory=4GB --region=us-central1 --root-password=example123 \
--no-deletion-protection # Create a new Cloud SQL instance.


gcloud sql databases create employees --instance=my-instance # Create a database within a Cloud SQL instance.

gcloud sql import sql my-instance gs://doc-ai-extractor-temp/employees_backup.sql --database=employees # Import data into a Cloud SQL database from a SQL dump file in Cloud Storage.


gcloud sql instances delete my-instance # Delete a Cloud SQL Instance.

# Cloud Spanner
CREATE TABLE Users (  -- Create a table in Cloud Spanner.
  UserId   INT64 NOT NULL,
  UserName  STRING(1024)
) PRIMARY KEY(UserId);



# Cloud BigTable
bq show bigquery-public-data:samples.shakespeare  # Show information about a BigQuery public dataset (example).

gcloud --version # Display the gcloud SDK version.
cbt listinstances -project=glowing-furnace-304608  # List Cloud Bigtable instances using the `cbt` tool.
echo project = glowing-furnace-304608 > ~/.cbtrc # Configure the project for the `cbt` tool in the configuration file.
cat ~/.cbtrc  # Display the contents of the `cbt` configuration file.
cbt listinstances # List Cloud Bigtable instances using the `cbt` tool (after configuration).
```

### Cloud Pub Sub

```bash
gcloud config set project glowing-furnace-304608 # Set the active project for gcloud commands.
gcloud pubsub topics create topic-from-gcloud # Create a new Pub/Sub topic.
gcloud pubsub subscriptions create subscription-gcloud-1 --topic=topic-from-gcloud # Create a subscription to the topic.
gcloud pubsub subscriptions create subscription-gcloud-2 --topic=topic-from-gcloud # Create another subscription to the topic.
gcloud pubsub subscriptions pull subscription-gcloud-2 # Pull messages from a subscription.
gcloud pubsub subscriptions pull subscription-gcloud-1 # Pull messages from another subscription.
gcloud pubsub topics publish topic-from-gcloud --message="My First Message" # Publish a message to the topic.
gcloud pubsub topics publish topic-from-gcloud --message="My Second Message" # Publish another message.
gcloud pubsub topics publish topic-from-gcloud --message="My Third Message" # Publish a third message.
gcloud pubsub subscriptions pull subscription-gcloud-1 --auto-ack # Pull messages and automatically acknowledge them.
gcloud pubsub subscriptions pull subscription-gcloud-2 --auto-ack # Pull messages and automatically acknowledge them.
gcloud pubsub topics list # List available Pub/Sub topics.
gcloud pubsub topics delete topic-from-gcloud # Delete a Pub/Sub topic.
gcloud pubsub topics list-subscriptions my-first-topic # List subscriptions for a specific topic.

```