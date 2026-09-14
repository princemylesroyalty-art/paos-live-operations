# PAOS 4.0 Live Operations Backend

Real-time AI agent orchestration, workflows, approvals, and integrations for the PAOS operating system.

## Overview

PAOS Live Operations is a FastAPI-based backend that orchestrates AI agents, manages task workflows, handles approval gates, and integrates with external services.

**Key Features:**
- 🤖 Agent orchestration (CEO → Research → Opportunity → Sales → Lead → Risk → Automation)
- ✅ Approval workflow system (READ → ANALYZE → CREATE → COMMUNICATE/PURCHASE/FINANCIAL → EXECUTE)
- 🔌 Encrypted connection manager for external services (OpenAI, Gmail, Stripe, etc.)
- 📊 Real-time WebSocket streaming for live dashboard updates
- 📝 Complete audit trail and event logging
- 💰 Cost tracking per agent run
- 🛡️ Security-first design with encrypted credentials

## Architecture

```
┌─────────────────────────────────────┐
│   PAOS Dashboard (Frontend)          │
│   - Live Operations Lobby            │
│   - Task Queue                       │
│   - Approval Manager                 │
└──────────────┬──────────────────────┘
               │ WebSocket (Real-time)
               ▼
┌─────────────────────────────────────┐
│   FastAPI Backend                   │
│   - REST API Routes                 │
│   - WebSocket Manager               │
│   - Agent Orchestrator              │
└──────────┬────────────────┬─────────┘
           │                │
           ▼                ▼
    ┌─────────────┐  ┌──────────────┐
    │ PostgreSQL  │  │ Redis        │
    │ (Tasks,     │  │ (Caching,    │
    │  Runs,      │  │  Events,     │
    │  Approvals) │  │  Sessions)   │
    └─────────────┘  └──────────────┘
           │                │
           └────────┬───────┘
                    ▼
        ┌──────────────────────┐
        │ External Services    │
        │ - OpenAI / Claude    │
        │ - Gmail              │
        │ - Stripe             │
        │ - Shopify            │
        │ - etc.               │
        └──────────────────────┘
```

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis 6+

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/princemylesroyalty-art/paos-live-operations.git
cd paos-live-operations
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -e .[dev]
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
python -c "from paos.database import init_db; init_db()"
```

6. **Run the server**
```bash
python -m paos.main
```

Server will be available at `http://localhost:8000`

## API Documentation

Once running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Core Endpoints

### Tasks
- `POST /api/tasks` - Create a new task
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/{task_id}` - Get task details
- `POST /api/tasks/{task_id}/run` - Execute a task

### Runs
- `GET /api/runs/{run_id}` - Get run details
- `GET /api/tasks/{task_id}/runs` - Get task's runs

### Approvals
- `POST /api/approvals` - Create approval request
- `GET /api/approvals/{approval_id}` - Get approval
- `POST /api/approvals/{approval_id}/decide` - Approve/reject

### Connections
- `POST /api/connections` - Create connection
- `GET /api/connections` - List connections
- `GET /api/connections/{connection_id}` - Get connection
- `POST /api/connections/{connection_id}/verify` - Test connection

### Events/Activity
- `GET /api/events` - Get activity log
- `WS /ws/operations` - WebSocket for real-time updates

## Database Schema

### Tables
- **tasks** - Top-level operations
- **runs** - Individual agent executions
- **approvals** - Approval requests and decisions
- **connections** - External service integrations
- **events** - Real-time event log

## Approval Workflow

Actions are gated by approval levels:

```
READ              → Automatic (data retrieval)
ANALYZE           → Automatic (data processing)
CREATE            → Automatic (generating content)
COMMUNICATE       → ✅ Requires Approval (emails, messages)
PURCHASE          → ✅ Requires Approval (buying items)
FINANCIAL         → ✅ Requires Approval (payments, transfers)
IRREVERSIBLE      → ✅ Requires Approval (permanent changes)
```

When an agent reaches an approval gate, the task pauses and waits for your decision.

## Connection Types

Supported external services:

| Service | Type | Status |
|---------|------|--------|
| OpenAI | `openai` | ✅ Implemented |
| Anthropic Claude | `anthropic` | ✅ Implemented |
| Gmail | `gmail` | 🔧 In Progress |
| Stripe | `stripe` | 🔧 In Progress |
| Shopify | `shopify` | 📋 Planned |
| Zapier | `zapier` | 📋 Planned |

## Security

- All credentials encrypted with Fernet (symmetric encryption)
- Connection status validation before use
- Approval gates for sensitive operations
- Complete audit trail of all actions
- JWT token authentication (coming soon)

## Development

### Run tests
```bash
pytest
```

### Format code
```bash
black .
ruff check . --fix
```

### Type checking
```bash
mypy paos/
```

## Roadmap

- [x] Core database models
- [x] REST API foundation
- [x] WebSocket real-time updates
- [x] Approval workflow system
- [x] Encrypted connections manager
- [ ] LangGraph agent integration
- [ ] Multi-agent coordination
- [ ] Advanced approval rules
- [ ] Billing/cost analytics
- [ ] Email notifications
- [ ] Mobile app integration
- [ ] Advanced monitoring dashboard

## License

MIT

## Support

For issues or questions, open an issue on GitHub.
