#!/bin/sh
set -e

echo "Configuring SeaweedFS buckets..."

weed shell -master="${SEAWEEDFS_MASTER}" <<EOF
s3.bucket.create -name=${S3_BUCKET_NAME}
s3.bucket.create -name=${CONNECTOR_SPEC_BUCKET_NAME}
s3.bucket.create -name=test.${S3_BUCKET_NAME}
EOF

echo "Listing the created bucket(s)..."

weed shell -master="${SEAWEEDFS_MASTER}" <<EOF
s3.bucket.list
EOF

echo "Configuring S3 credentials for ${S3_SAM_USER}..."

weed shell -master="${SEAWEEDFS_MASTER}" <<EOF
s3.configure -apply \
  -access_key=${S3_ACCESS_KEY_ID} \
  -secret_key=${S3_SECRET_ACCESS_KEY} \
  -user=${S3_SAM_USER} \
  -actions=Read,Write,List \
  -buckets=${S3_BUCKET_NAME}
s3.configure -apply \
  -access_key=${S3_ACCESS_KEY_ID} \
  -secret_key=${S3_SECRET_ACCESS_KEY} \
  -user=${S3_SAM_USER} \
  -actions=Read,Write,List,Tagging,Admin \
  -buckets=${CONNECTOR_SPEC_BUCKET_NAME}
s3.configure -apply \
  -user=anonymous \
  -actions=Read,List \
  -buckets=${CONNECTOR_SPEC_BUCKET_NAME}
s3.configure -apply \
  -access_key=${S3_ACCESS_KEY_ID} \
  -secret_key=${S3_SECRET_ACCESS_KEY} \
  -user=${S3_SAM_USER} \
  -actions=Read,Write,List \
  -buckets=test.${S3_BUCKET_NAME}
EOF

echo "Verifying S3 configuration..."

weed shell -master="${SEAWEEDFS_MASTER}" <<EOF
s3.configure
EOF

echo "SeaweedFS initialization complete."

