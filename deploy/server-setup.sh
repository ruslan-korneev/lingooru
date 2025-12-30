#!/bin/bash
set -e

# Lingooru Server Setup Script
# Run as root or with sudo on a fresh Ubuntu/Debian server

echo "=== Lingooru Server Setup ==="

# Update system
echo "Updating system packages..."
apt-get update && apt-get upgrade -y

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
else
    echo "Docker already installed"
fi

# Install Docker Compose plugin
if ! docker compose version &> /dev/null; then
    echo "Installing Docker Compose plugin..."
    apt-get install -y docker-compose-plugin
else
    echo "Docker Compose already installed"
fi

# Create deployment directory
echo "Creating deployment directory..."
mkdir -p /opt/lingooru
cd /opt/lingooru

# Create .env template
cat > .env.example << 'EOF'
# === Required ===

# Database
DB_NAME=lingooru
DB_USERNAME=lingooru
DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD

# MinIO (S3)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=CHANGE_ME_STRONG_PASSWORD
S3_BUCKET_NAME=lingooru-audio

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
TELEGRAM_WEBHOOK_URL=https://your-domain.com
TELEGRAM_WEBHOOK_SECRET=CHANGE_ME_RANDOM_STRING

# === Optional ===

# GitHub (for image pulling)
GITHUB_REPOSITORY=your-username/lingooru
IMAGE_TAG=latest

# OpenAI (for voice features)
OPENAI_API_KEY=

# Sentry (for error tracking)
SENTRY_DSN=

# Public URL for audio files
S3_PUBLIC_URL_BASE=https://your-domain.com/s3

# Logging
ENVIRONMENT=production
LOGGING_LEVEL=INFO
EOF

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Copy docker-compose.yml to /opt/lingooru/"
echo "2. Create .env file: cp .env.example .env && nano .env"
echo "3. Login to GHCR: docker login ghcr.io -u YOUR_USERNAME"
echo "4. Start services: docker compose up -d"
echo "5. Initialize MinIO bucket: ./deploy/init-minio.sh"
echo "6. Configure nginx on host to proxy to localhost:8000"
echo ""
