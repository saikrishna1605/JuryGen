#!/bin/bash

# Simple deployment script for Legal Companion
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-development}

echo "🚀 Deploying Legal Companion to $ENVIRONMENT environment..."

case $ENVIRONMENT in
  "development"|"dev")
    echo "📦 Starting development environment..."
    docker-compose up --build -d
    echo "✅ Development environment is running!"
    echo "Frontend: http://localhost:5173"
    echo "Backend: http://localhost:8000"
    ;;
    
  "production"|"prod")
    echo "📦 Starting production environment..."
    
    # Check if required environment variables are set
    if [ -z "$SECRET_KEY" ]; then
      echo "❌ ERROR: SECRET_KEY environment variable is required for production"
      exit 1
    fi
    
    if [ -z "$DATABASE_URL" ]; then
      echo "⚠️  WARNING: DATABASE_URL not set, using default SQLite"
    fi
    
    docker-compose -f docker-compose.prod.yml up --build -d
    echo "✅ Production environment is running!"
    echo "Frontend: http://localhost:80"
    echo "Backend: http://localhost:8000"
    ;;
    
  "stop")
    echo "🛑 Stopping all services..."
    docker-compose down
    docker-compose -f docker-compose.prod.yml down
    echo "✅ All services stopped!"
    ;;
    
  *)
    echo "❌ Unknown environment: $ENVIRONMENT"
    echo "Usage: $0 [development|production|stop]"
    exit 1
    ;;
esac

echo "🎉 Deployment complete!"