#!/bin/bash
set -e

# Initialize MinIO bucket for Lingooru
# Run this after docker compose up -d

cd /opt/lingooru

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

BUCKET_NAME=${S3_BUCKET_NAME:-lingooru-audio}
MINIO_USER=${MINIO_ROOT_USER:-minioadmin}
MINIO_PASS=${MINIO_ROOT_PASSWORD:-minioadmin}

echo "=== Initializing MinIO Bucket ==="

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
until curl -sf http://localhost:9000/minio/health/live > /dev/null 2>&1; do
    echo "  MinIO not ready yet, waiting..."
    sleep 2
done
echo "MinIO is ready!"

# Configure mc client inside the container
echo "Configuring MinIO client..."
docker exec lingooru-minio mc alias set local http://localhost:9000 "$MINIO_USER" "$MINIO_PASS"

# Create bucket if not exists
echo "Creating bucket: $BUCKET_NAME"
docker exec lingooru-minio mc mb --ignore-existing "local/$BUCKET_NAME"

# Set bucket policy for public read (audio files need to be accessible via URL)
echo "Setting public download policy..."
docker exec lingooru-minio mc anonymous set download "local/$BUCKET_NAME"

echo ""
echo "=== MinIO Initialized ==="
echo "Bucket: $BUCKET_NAME"
echo "Console: http://localhost:9001"
echo ""
