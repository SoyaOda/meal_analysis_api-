#!/bin/bash

# Check Cloud Run logs for revision meal-analysis-api-00006-5l4
export PATH="$HOME/google-cloud-sdk/bin:$PATH"

gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=meal-analysis-api AND resource.labels.revision_name=meal-analysis-api-00006-5l4" --limit=20 --format="value(textPayload)" > logs/log.txt

echo "Logs have been saved to logs/log.txt"
cat logs/log.txt