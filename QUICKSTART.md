# PAOS Live Operations - Quick Start Guide

Get PAOS Live Operations up and running in minutes.

## Prerequisites

- **Docker & Docker Compose** (recommended)
  - [Install Docker](https://docs.docker.com/get-docker/)
  - [Install Docker Compose](https://docs.docker.com/compose/install/)

- **OR** Local Setup:
  - Python 3.11+
  - PostgreSQL 12+
  - Redis 6+

## Option 1: Quick Start with Docker (Recommended)

### 1. Clone Repository
```bash
git clone https://github.com/princemylesroyalty-art/paos-live-operations.git
cd paos-live-operations
```

### 2. Create Environment File
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=your-key-here
```

### 3. Start Services
```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** on `localhost:5432`
- **Redis** on `localhost:6379`
- **PAOS API** on `http://localhost:8000`
- **Prometheus** on `http://localhost:9090`
- **Grafana** on `http://localhost:3000`

### 4. Verify Installation
```bash
curl http://localhost:8000/health
```

You should see:
```json
{"status": "healthy", "version": "0.1.0"}
```

### 5. Access the API

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboards**: http://localhost:3000 (admin/admin)

---

## Option 2: Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/princemylesroyalty-art/paos-live-operations.git
cd paos-live-operations
```

### 2. Create Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -e .[dev]
```

### 4. Setup Database

**Start PostgreSQL** (if not running):
```bash
# macOS (with Homebrew)
brew services start postgresql

# Linux
sudo systemctl start postgresql

# Or use Docker
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=paos \
  -e POSTGRES_PASSWORD=paospass \
  -e POSTGRES_DB=paos_operations \
  postgres:15
```

**Start Redis** (if not running):
```bash
# macOS (with Homebrew)
brew services start redis

# Linux
sudo systemctl start redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7
```

### 5. Initialize Database
```bash
python -c "from paos.database import init_db; init_db()"
```

### 6. Create Environment File
```bash
cp .env.example .env
```

### 7. Run Server
```bash
python -m paos.main
```

Server starts at `http://localhost:8000`

---

## First Steps

### 1. Create a Connection

```bash
curl -X POST http://localhost:8000/api/connections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-openai",
    "service_type": "openai",
    "credentials": {
      "api_key": "sk-your-key-here"
    }
  }'
```

### 2. Create a Task

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Research Market Opportunities",
    "description": "Find top 10 market opportunities",
    "assigned_agent": "research",
    "input_data": {
      "query": "best business opportunities 2024",
      "market": "technology"
    }
  }'
```

Response includes `task_id` - save this.

### 3. Run the Task

```bash
curl -X POST http://localhost:8000/api/tasks/{task_id}/run
```

### 4. Monitor Progress

```bash
# Check task status
curl http://localhost:8000/api/tasks/{task_id}

# Get activity log
curl http://localhost:8000/api/events?task_id={task_id}

# WebSocket for real-time updates
wscat -c ws://localhost:8000/ws/operations
```

### 5. Handle Approvals

```bash
# List pending approvals
curl http://localhost:8000/api/approvals

# Approve an action
curl -X POST http://localhost:8000/api/approvals/{approval_id}/decide \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "decision_comment": "Approved - looks good"
  }'
```

---

## Common Tasks

### View API Documentation

Open http://localhost:8000/docs in your browser.

### View Logs

```bash
# Docker
docker-compose logs -f api

# Local
# Logs appear in terminal where you ran `python -m paos.main`
```

### Stop Services

```bash
# Docker
docker-compose down

# Local
# Ctrl+C in the terminal
```

### Restart Services

```bash
# Docker
docker-compose restart

# Local
# Stop and run again
```

### Reset Database

```bash
# Docker
docker-compose down -v  # -v removes volumes
docker-compose up -d

# Local
python -c "from paos.database import drop_db; drop_db()"
python -c "from paos.database import init_db; init_db()"
```

### View Metrics

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

---

## Troubleshooting

### Port Already in Use

```bash
# Docker
docker-compose down

# Local - find and kill process
lsof -i :8000
kill -9 {PID}
```

### Database Connection Error

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Or check local installation
psql -U paos -d paos_operations -c "SELECT 1;"
```

### API Won't Start

```bash
# Check logs
docker-compose logs api

# Or run locally to see errors
python -m paos.main
```

### WebSocket Connection Failed

```bash
# Make sure you're using ws:// not http://
wscat -c ws://localhost:8000/ws/operations
```

---

## Next Steps

1. **Read the README**: [README.md](README.md)
2. **Explore Manual Build Options**: [MANUAL_BUILD_OPTIONS.md](MANUAL_BUILD_OPTIONS.md)
3. **Check API Endpoints**: http://localhost:8000/docs
4. **Connect Your Services**: See Connections section above
5. **Create Your First Workflow**: Use the API to define tasks and agents

---

## Development Workflow

### Make Changes to Code

```bash
# With Docker - changes auto-reload
vim paos/api/routes.py

# With local setup - restart the server
# Ctrl+C, then run again
python -m paos.main
```

### Run Tests

```bash
pytest
pytest -v  # Verbose
pytest --cov  # With coverage
```

### Format Code

```bash
black paos/
ruff check paos/ --fix
```

### Type Check

```bash
mypy paos/
```

---

## Production Deployment

For production, see:
1. Update `.env` with real values
2. Use PostgreSQL managed service (AWS RDS, etc.)
3. Use Redis managed service (AWS ElastiCache, etc.)
4. Deploy with Kubernetes or cloud run
5. Set up proper SSL certificates
6. Configure backups and monitoring

---

## Get Help

- **Documentation**: [README.md](README.md)
- **API Docs**: http://localhost:8000/docs
- **GitHub Issues**: [Open an issue](https://github.com/princemylesroyalty-art/paos-live-operations/issues)

Happy building! 🚀
