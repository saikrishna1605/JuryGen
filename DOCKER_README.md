# 🐳 Docker Setup for Legal Companion

This project now uses a **simplified Docker setup** that's easy to understand and maintain.

## 🚀 Quick Start

### Development Environment
```bash
# Start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Environment
```bash
# Set required environment variables
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="your-database-url-here"

# Start production services
docker-compose -f docker-compose.prod.yml up --build -d

# Stop production services
docker-compose -f docker-compose.prod.yml down
```

### Using the Deploy Script
```bash
# Development
./scripts/deploy.sh development

# Production
./scripts/deploy.sh production

# Stop all services
./scripts/deploy.sh stop
```

## 📋 What's Included

### Services
- **Frontend**: React app with Vite (Port 5173 in dev, 80 in prod)
- **Backend**: FastAPI application (Port 8000)
- **Redis**: For caching and sessions (Port 6379)

### Features
- ✅ Hot reload in development
- ✅ Optimized production builds
- ✅ Simple configuration
- ✅ Easy to understand and modify
- ✅ Minimal resource usage

## 🔧 Configuration

### Environment Variables

#### Development (automatic)
- `NODE_ENV=development`
- `VITE_API_URL=http://localhost:8000`
- `ENVIRONMENT=development`
- `SECRET_KEY=dev-secret-key-change-in-production`

#### Production (required)
- `SECRET_KEY` - **Required** for production
- `DATABASE_URL` - Database connection string
- `CORS_ORIGINS` - Allowed CORS origins

### Example .env file for production:
```bash
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/legal_companion
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## 🛠️ Development

### Individual Services

#### Frontend only:
```bash
cd frontend
npm install
npm run dev
```

#### Backend only:
```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload
```

### Docker Commands

#### Rebuild specific service:
```bash
docker-compose build frontend
docker-compose build backend
```

#### View service logs:
```bash
docker-compose logs frontend
docker-compose logs backend
docker-compose logs redis
```

#### Execute commands in containers:
```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# Redis CLI
docker-compose exec redis redis-cli
```

## 🚀 Deployment

### Local Production Test
```bash
# Build and test production images
docker-compose -f docker-compose.prod.yml up --build

# Test the application
curl http://localhost:80        # Frontend
curl http://localhost:8000/health  # Backend health check
```

### CI/CD
The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:
- Runs tests for both frontend and backend
- Builds Docker images
- Tests the production setup

## 📁 File Structure

```
├── docker-compose.yml          # Development environment
├── docker-compose.prod.yml     # Production environment
├── frontend/
│   └── Dockerfile             # Simple frontend container
├── backend/
│   └── Dockerfile             # Simple backend container
├── scripts/
│   └── deploy.sh              # Deployment helper script
└── .github/workflows/
    └── ci.yml                 # CI/CD pipeline
```

## 🔄 What Changed

### ❌ Removed (Overly Complex)
- 15+ service docker-compose with Prometheus, Grafana, Elasticsearch, etc.
- Enterprise CI/CD pipeline with 17 steps
- Complex multi-stage Dockerfiles with security scanning
- Kubernetes deployment configs
- Terraform infrastructure (moved to separate branch if needed)

### ✅ Added (Simple & Practical)
- Clean 3-service setup (frontend, backend, redis)
- Simple Dockerfiles with dev/prod targets
- Basic CI/CD with GitHub Actions
- Easy deployment script
- Clear documentation

## 🆘 Troubleshooting

### Common Issues

#### Port conflicts:
```bash
# Check what's using the ports
netstat -tulpn | grep :5173
netstat -tulpn | grep :8000

# Stop conflicting services or change ports in docker-compose.yml
```

#### Permission issues (Linux/Mac):
```bash
# Make deploy script executable
chmod +x scripts/deploy.sh
```

#### Container won't start:
```bash
# Check logs
docker-compose logs [service-name]

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up
```

#### Database connection issues:
```bash
# Check if DATABASE_URL is set correctly
echo $DATABASE_URL

# For development, SQLite is used by default
# For production, set DATABASE_URL to your database
```

## 🎯 Next Steps

1. **Development**: Use `docker-compose up` and start coding
2. **Production**: Set environment variables and use `docker-compose.prod.yml`
3. **Scaling**: When you need more complexity, gradually add services
4. **Monitoring**: Add simple monitoring tools like Uptime Kuma or Grafana when needed

This setup grows with your project - start simple, add complexity only when needed! 🚀