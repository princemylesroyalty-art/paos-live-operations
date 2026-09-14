# PAOS Live Operations - Manual Build Options

This document outlines the manual build options for extending PAOS Live Operations with advanced features.

## 1. LangGraph Agent Integration

### Purpose
Integrate LangGraph for sophisticated multi-step agent reasoning and tool orchestration.

### Files to Create
- `paos/agents/base_agent.py` - Base agent class with LangGraph support
- `paos/agents/ceo_agent.py` - CEO agent (task router)
- `paos/agents/research_agent.py` - Research agent (market analysis)
- `paos/agents/opportunity_agent.py` - Opportunity agent (filtering)
- `paos/agents/sales_agent.py` - Sales agent (offer generation)
- `paos/agents/lead_agent.py` - Lead agent (prospect identification)
- `paos/agents/risk_agent.py` - Risk agent (validation)
- `paos/agents/automation_agent.py` - Automation agent (execution)

### Implementation Steps

1. **Install LangGraph**
   ```bash
   pip install langgraph langchain langchain-openai
   ```

2. **Create Base Agent Class**
   ```python
   # paos/agents/base_agent.py
   from langgraph.graph import StateGraph, END
   from langchain_openai import ChatOpenAI
   from pydantic import BaseModel
   from typing import Any, Dict, List
   
   class AgentState(BaseModel):
       input: Dict[str, Any]
       thoughts: List[str] = []
       tools_used: List[Dict[str, Any]] = []
       output: Dict[str, Any] = None
       error: str = None
   
   class BaseAgent:
       def __init__(self, name: str, model: str = "gpt-4"):
           self.name = name
           self.llm = ChatOpenAI(model_name=model)
           self.graph = StateGraph(AgentState)
       
       async def think(self, state: AgentState) -> AgentState:
           # Agent thinking/reasoning step
           response = await self.llm.agenerate(...)
           state.thoughts.append(response.content)
           return state
       
       async def execute(self, state: AgentState) -> AgentState:
           # Execute tools and collect results
           return state
   ```

3. **Build Agent Pipeline**
   - Connect agents in sequence: CEO → Research → Opportunity → Sales → Lead → Risk → Automation
   - Pass output from one agent as input to next
   - Implement error handling and fallbacks

4. **Update Orchestrator**
   Replace the simulation in `paos/orchestrator.py` with real LangGraph execution:
   ```python
   async def _run_agent_simulation(self, db, task, run):
       agent = self.get_agent(task.assigned_agent)
       state = AgentState(input=task.input_data)
       result = await agent.execute(state)
       run.output_data = result.output
       run.tools_used = result.tools_used
   ```

### Configuration
Add to `.env`:
```env
LANGGRAPH_DEBUG=false
AGENT_MODEL=gpt-4
AGENT_TEMPERATURE=0.7
```

---

## 2. Multi-Agent Coordination

### Purpose
Enable multiple agents to work in parallel, share context, and coordinate actions.

### Files to Create
- `paos/coordination/coordinator.py` - Central coordinator
- `paos/coordination/context_manager.py` - Shared execution context
- `paos/coordination/message_broker.py` - Inter-agent messaging

### Implementation Steps

1. **Create Coordinator**
   ```python
   # paos/coordination/coordinator.py
   class AgentCoordinator:
       def __init__(self):
           self.agents = {}
           self.context = SharedContext()
           self.message_queue = asyncio.Queue()
       
       async def coordinate(self, task: Task) -> Dict:
           # Spawn multiple agents in parallel
           tasks = [
               self.run_agent("research"),
               self.run_agent("opportunity"),
               self.run_agent("compliance"),
           ]
           results = await asyncio.gather(*tasks)
           return self.merge_results(results)
       
       async def run_agent(self, agent_name: str):
           agent = self.agents[agent_name]
           return await agent.execute(self.context)
   ```

2. **Implement Shared Context**
   ```python
   # paos/coordination/context_manager.py
   class SharedContext:
       def __init__(self):
           self.data = {}
           self.lock = asyncio.Lock()
       
       async def get(self, key: str):
           async with self.lock:
               return self.data.get(key)
       
       async def set(self, key: str, value: Any):
           async with self.lock:
               self.data[key] = value
       
       async def update(self, key: str, fn):
           async with self.lock:
               self.data[key] = fn(self.data.get(key))
   ```

3. **Add Message Broker**
   ```python
   # paos/coordination/message_broker.py
   class MessageBroker:
       async def publish(self, topic: str, message: Dict):
           # Publish message to topic
           pass
       
       async def subscribe(self, topic: str, handler: Callable):
           # Subscribe to topic updates
           pass
   ```

4. **Update Orchestrator**
   ```python
   async def execute_task(self, db, task):
       coordinator = AgentCoordinator()
       result = await coordinator.coordinate(task)
       # Save results to database
   ```

### Configuration
Add to `.env`:
```env
MAX_PARALLEL_AGENTS=5
CONTEXT_TIMEOUT_SECONDS=600
MESSAGE_BROKER_TYPE=memory  # or 'redis'
```

---

## 3. Advanced Approval Rules

### Purpose
Define complex, context-aware approval workflows.

### Files to Create
- `paos/approvals/rule_engine.py` - Rule evaluation engine
- `paos/approvals/rules.py` - Predefined rule templates
- `paos/approvals/notification.py` - Approval notifications

### Implementation Steps

1. **Create Rule Engine**
   ```python
   # paos/approvals/rule_engine.py
   class ApprovalRuleEngine:
       def __init__(self):
           self.rules = {}
       
       def register_rule(self, name: str, rule: ApprovalRule):
           self.rules[name] = rule
       
       async def evaluate(self, task: Task, action: str) -> ApprovalDecision:
           # Evaluate all applicable rules
           decisions = []
           for rule in self.rules.values():
               if rule.applies_to(action):
                   decision = await rule.evaluate(task)
                   decisions.append(decision)
           
           # Combine decisions (unanimous approval, majority, etc.)
           return self.combine_decisions(decisions)
   ```

2. **Define Rule Templates**
   ```python
   # paos/approvals/rules.py
   class AmountThresholdRule(ApprovalRule):
       def __init__(self, threshold: float, requires_approval: bool = True):
           self.threshold = threshold
           self.requires_approval = requires_approval
       
       async def evaluate(self, task: Task) -> ApprovalDecision:
           amount = task.input_data.get("amount", 0)
           if amount > self.threshold:
               return ApprovalDecision(
                   requires_approval=True,
                   reason=f"Amount ${amount} exceeds threshold ${self.threshold}"
               )
           return ApprovalDecision(requires_approval=False)
   
   class TimeWindowRule(ApprovalRule):
       # Only allow certain actions during business hours
       pass
   
   class RiskScoreRule(ApprovalRule):
       # Require approval if risk score is above threshold
       pass
   ```

3. **Add Notification System**
   ```python
   # paos/approvals/notification.py
   class ApprovalNotifier:
       async def notify_approval_required(self, approval: Approval):
           # Send email/SMS/webhook notification
           await self.send_email(
               to="user@example.com",
               subject=f"Approval Required: {approval.action_type}",
               body=approval.required_reason
           )
   ```

4. **Update API Routes**
   ```python
   # In paos/api/routes.py
   @router.post("/approval-rules")
   async def create_rule(rule: ApprovalRuleCreate, db: Session = Depends(get_db)):
       # Create custom approval rule
       pass
   ```

### Configuration
Add to `.env`:
```env
APPROVAL_RULE_ENGINE=default
NOTIFICATION_METHOD=email  # or 'sms', 'webhook'
APPROVAL_TIMEOUT_MINUTES=30
```

---

## 4. Billing/Cost Analytics

### Purpose
Track, analyze, and report on costs across all agent runs and integrations.

### Files to Create
- `paos/billing/cost_calculator.py` - Calculate costs per operation
- `paos/billing/models.py` - Billing database models
- `paos/billing/analytics.py` - Cost analysis and reporting
- `paos/api/billing_routes.py` - Billing API endpoints

### Implementation Steps

1. **Create Cost Calculator**
   ```python
   # paos/billing/cost_calculator.py
   class CostCalculator:
       # Pricing per API call
       PRICES = {
           "openai": {"gpt-4": 0.03, "gpt-3.5": 0.001},
           "anthropic": {"claude-3": 0.015},
           "gmail": {"send": 0.01, "search": 0.001},
           "stripe": {"api_call": 0.01},
       }
       
       def calculate_run_cost(self, run: Run) -> float:
           cost = 0
           for tool_call in run.tools_used:
               service = tool_call.get("service")
               tool = tool_call.get("tool")
               price = self.PRICES.get(service, {}).get(tool, 0)
               cost += price
           return cost
       
       def calculate_token_cost(self, model: str, tokens: int) -> float:
           # Calculate cost based on token usage
           pass
   ```

2. **Add Billing Models**
   ```python
   # paos/billing/models.py
   class CostEntry(Base):
       __tablename__ = "cost_entries"
       
       id = Column(String(36), primary_key=True)
       run_id = Column(String(36), ForeignKey("runs.id"))
       service_type = Column(String(100))
       operation = Column(String(255))
       cost_cents = Column(Integer)
       created_at = Column(DateTime, default=datetime.utcnow)
   
   class BillingCycle(Base):
       __tablename__ = "billing_cycles"
       
       id = Column(String(36), primary_key=True)
       start_date = Column(DateTime)
       end_date = Column(DateTime)
       total_cost_cents = Column(Integer)
       entries = relationship("CostEntry")
   ```

3. **Create Analytics**
   ```python
   # paos/billing/analytics.py
   class BillingAnalytics:
       def get_cost_by_service(self, period: DateRange) -> Dict[str, float]:
           # Breakdown by service
           pass
       
       def get_cost_by_agent(self, period: DateRange) -> Dict[str, float]:
           # Breakdown by agent
           pass
       
       def get_cost_trends(self, days: int = 30) -> List[Dict]:
           # Daily cost trends
           pass
       
       def estimate_monthly(self) -> float:
           # Project monthly costs
           pass
   ```

4. **Add API Routes**
   ```python
   # paos/api/billing_routes.py
   @router.get("/billing/costs")
   async def get_costs(start: date, end: date, db: Session = Depends(get_db)):
       analytics = BillingAnalytics(db)
       return {
           "by_service": analytics.get_cost_by_service((start, end)),
           "by_agent": analytics.get_cost_by_agent((start, end)),
       }
   ```

### Configuration
Add to `.env`:
```env
BILLING_ENABLED=true
COST_TRACKING_LEVEL=detailed  # or 'basic'
BILLING_CURRENCY=USD
COST_ALERT_THRESHOLD_CENTS=10000  # Alert if daily cost exceeds this
```

---

## 5. Email Notifications

### Purpose
Send real-time notifications for approvals, task completion, errors, and alerts.

### Files to Create
- `paos/notifications/email_service.py` - Email sending
- `paos/notifications/templates.py` - Email templates
- `paos/notifications/scheduler.py` - Scheduled notifications

### Implementation Steps

1. **Create Email Service**
   ```python
   # paos/notifications/email_service.py
   from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
   
   class EmailService:
       def __init__(self, config: ConnectionConfig):
           self.fm = FastMail(config)
       
       async def send_approval_notification(self, approval: Approval, recipient: str):
           message = MessageSchema(
               subject=f"Approval Required: {approval.action_type}",
               recipients=[recipient],
               template_body={
                   "action": approval.action_type,
                   "reason": approval.required_reason,
                   "approval_id": approval.id,
               },
               subtype="html"
           )
           await self.fm.send_message(message, template_name="approval_request.html")
       
       async def send_task_completed(self, task: Task, recipient: str):
           # Send task completion notification
           pass
       
       async def send_error_alert(self, run: Run, recipient: str):
           # Send error alert
           pass
   ```

2. **Create Email Templates**
   ```html
   <!-- templates/approval_request.html -->
   <h2>{{ action }} Approval Required</h2>
   <p>{{ reason }}</p>
   <p><a href="https://paos.local/approvals/{{ approval_id }}">Review Approval</a></p>
   ```

3. **Add Scheduler**
   ```python
   # paos/notifications/scheduler.py
   class NotificationScheduler:
       async def schedule_daily_summary(self, user_email: str):
           # Send daily summary of tasks and costs
           pass
       
       async def schedule_weekly_report(self, user_email: str):
           # Send weekly analytics report
           pass
   ```

### Configuration
Add to `.env`:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@paos.local
NOTIFICATION_RECIPIENTS=you@example.com
SUMMARY_EMAIL_TIME=09:00  # Daily at 9 AM
```

---

## 6. Mobile App Integration

### Purpose
Enable mobile apps to connect to PAOS and receive notifications.

### Files to Create
- `paos/mobile/authentication.py` - Mobile auth (JWT/OAuth)
- `paos/mobile/api.py` - Mobile-optimized endpoints
- `paos/mobile/push_notifications.py` - Push notification service

### Implementation Steps

1. **Create Mobile Auth**
   ```python
   # paos/mobile/authentication.py
   from jose import JWTError, jwt
   from datetime import datetime, timedelta
   
   class MobileAuthService:
       async def create_mobile_token(self, user_id: str, device_id: str) -> str:
           payload = {
               "sub": user_id,
               "device_id": device_id,
               "exp": datetime.utcnow() + timedelta(days=30),
           }
           return jwt.encode(payload, settings.secret_key, algorithm="HS256")
       
       async def refresh_token(self, token: str) -> str:
           # Refresh expired token
           pass
   ```

2. **Create Mobile API**
   ```python
   # paos/mobile/api.py
   mobile_router = APIRouter(prefix="/api/mobile")
   
   @mobile_router.get("/dashboard")
   async def get_mobile_dashboard(token: str = Depends(verify_token)):
       # Return compact dashboard data for mobile
       return {
           "active_tasks": [...],
           "pending_approvals": [...],
           "cost_today": 42.50,
       }
   
   @mobile_router.post("/approvals/{approval_id}/approve")
   async def approve_via_mobile(approval_id: str, token: str = Depends(verify_token)):
       # Approve from mobile app
       pass
   ```

3. **Add Push Notifications**
   ```python
   # paos/mobile/push_notifications.py
   from firebase_admin import messaging
   
   class PushNotificationService:
       async def send_approval_push(self, device_tokens: List[str], approval: Approval):
           message = messaging.MulticastMessage(
               notification=messaging.Notification(
                   title="Approval Required",
                   body=approval.action_type,
               ),
               data={"approval_id": approval.id},
               tokens=device_tokens,
           )
           await messaging.send_multicast(message)
   ```

### Configuration
Add to `.env`:
```env
MOBILE_API_ENABLED=true
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-key.json
APP_DEEP_LINK_BASE=paos://app
```

---

## 7. Advanced Monitoring Dashboard

### Purpose
Real-time visualization of system performance, agent activity, and business metrics.

### Files to Create
- `paos/monitoring/metrics.py` - Metrics collection
- `paos/monitoring/prometheus.py` - Prometheus integration
- `paos/api/monitoring_routes.py` - Monitoring endpoints

### Implementation Steps

1. **Create Metrics Collector**
   ```python
   # paos/monitoring/metrics.py
   from prometheus_client import Counter, Histogram, Gauge
   
   class MetricsCollector:
       task_counter = Counter("paos_tasks_total", "Total tasks", ["status"])
       task_duration = Histogram("paos_task_duration_seconds", "Task duration")
       approval_pending = Gauge("paos_approvals_pending", "Pending approvals")
       agent_active = Gauge("paos_agents_active", "Active agents", ["agent_name"])
       cost_daily = Gauge("paos_cost_daily_cents", "Daily cost in cents")
       
       def record_task_completion(self, duration: float, status: str):
           self.task_counter.labels(status=status).inc()
           self.task_duration.observe(duration)
   ```

2. **Expose Prometheus Metrics**
   ```python
   # paos/monitoring/prometheus.py
   from prometheus_client import generate_latest
   from fastapi.responses import PlainTextResponse
   
   @app.get("/metrics")
   async def metrics():
       return PlainTextResponse(generate_latest())
   ```

3. **Create Monitoring Routes**
   ```python
   # paos/api/monitoring_routes.py
   @router.get("/monitoring/system-health")
   async def system_health(db: Session = Depends(get_db)):
       return {
           "status": "healthy",
           "database": check_db_health(db),
           "redis": await check_redis_health(),
           "api_response_time": get_avg_response_time(),
       }
   
   @router.get("/monitoring/agent-status")
   async def agent_status():
       return {
           "active_agents": get_active_agents(),
           "queued_tasks": get_queued_count(),
           "failed_runs": get_failed_count(),
       }
   ```

### Configuration
Add to `.env`:
```env
MONITORING_ENABLED=true
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
GRAFANA_URL=http://grafana:3000
```

---

## Implementation Guide

### Order of Implementation (Recommended)

1. **Start with LangGraph Agent Integration** (Foundation)
   - Enables real agent execution instead of simulation
   - Required for all other features

2. **Add Multi-Agent Coordination** (Core)
   - Builds on LangGraph foundation
   - Enables parallel agent execution

3. **Add Advanced Approval Rules** (Security)
   - Context-aware approval workflows
   - Works with existing API

4. **Add Billing/Cost Analytics** (Business)
   - Tracks system economics
   - Uses data from agent runs

5. **Add Email Notifications** (Usability)
   - Keeps users informed
   - Works with approvals and completions

6. **Add Mobile App Integration** (Expansion)
   - Remote access and control
   - Depends on notifications

7. **Add Advanced Monitoring Dashboard** (Operations)
   - System visibility
   - Last for optimization

### Testing Each Feature

For each feature, create tests in `tests/` directory:
```bash
tests/
├── test_agents/
├── test_coordination/
├── test_approvals/
├── test_billing/
├── test_notifications/
├── test_mobile/
└── test_monitoring/
```

### Database Migrations

Use Alembic for schema changes:
```bash
alembic init migrations
alembic revision --autogenerate -m "Add feature X"
alembic upgrade head
```

---

## Help & Support

Each feature has:
- Detailed implementation examples
- Configuration templates
- API endpoint specifications
- Database schema definitions
- Testing guidelines

Start with any feature by following its "Implementation Steps" section.
