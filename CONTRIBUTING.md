# Contributing to PAOS Live Operations

Thanks for your interest in contributing to PAOS!

## Development Setup

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR-USERNAME/paos-live-operations.git
cd paos-live-operations
git remote add upstream https://github.com/princemylesroyalty-art/paos-live-operations.git
```

### 2. Create Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Setup Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

### 4. Make Changes
Edit files in `paos/` directory.

### 5. Write Tests
Create tests in `tests/` directory:
```python
# tests/test_features.py
import pytest
from paos.features import my_function

def test_my_function():
    result = my_function()
    assert result == expected_value
```

### 6. Run Tests
```bash
pytest
pytest tests/test_features.py -v
pytest --cov  # Coverage report
```

### 7. Format Code
```bash
black paos/
ruff check paos/ --fix
mypy paos/
```

### 8. Commit & Push
```bash
git add paos/ tests/
git commit -m "Add feature: description"
git push origin feature/your-feature-name
```

### 9. Create Pull Request
Go to GitHub and create a PR from your fork.

## Code Style

- **Black** for formatting (line length: 100)
- **Ruff** for linting
- **MyPy** for type checking
- **Pytest** for testing

## Commit Messages

Format:
```
type(scope): description

Optional body with more details.
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Example:
```
feat(approvals): add advanced approval rules

Implements context-aware approval workflows with
custom rule engine and notifications.
```

## Adding Features

### Option 1: Use Manual Build Options
See [MANUAL_BUILD_OPTIONS.md](MANUAL_BUILD_OPTIONS.md) for detailed guides on:
- LangGraph Agent Integration
- Multi-Agent Coordination
- Advanced Approval Rules
- Billing/Cost Analytics
- Email Notifications
- Mobile App Integration
- Advanced Monitoring Dashboard

### Option 2: Create New Feature

1. Create new module in `paos/`:
   ```
   paos/my_feature/
   ├── __init__.py
   ├── models.py
   ├── schemas.py
   └── routes.py
   ```

2. Add database models to `paos/models.py`
3. Add API schemas to `paos/schemas.py`
4. Add routes to `paos/api/routes.py`
5. Write tests in `tests/test_my_feature.py`
6. Document in README or MANUAL_BUILD_OPTIONS

## Database Migrations

Use Alembic for schema changes:

```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Review generated migration in alembic/versions/

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing Guidelines

### Unit Tests
```python
def test_function_returns_correct_value():
    result = function(input)
    assert result == expected
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_api_endpoint(client):
    response = await client.post("/api/endpoint", json={...})
    assert response.status_code == 200
```

### Fixtures
```python
@pytest.fixture
def sample_task(db):
    task = models.Task(...)
    db.add(task)
    db.commit()
    return task

def test_with_fixture(sample_task):
    assert sample_task.id is not None
```

## Documentation

### Code Comments
```python
def complex_function(param: str) -> Dict[str, Any]:
    """Short description.
    
    Longer description explaining what this does and why.
    
    Args:
        param: Description of parameter
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When this condition occurs
    """
    pass
```

### README Updates
If adding a major feature, update README.md roadmap section.

### New Guides
Create `.md` files in root directory for new major features.

## Performance

### Database Queries
- Use `db.query()` efficiently
- Add indexes for frequently queried columns
- Use pagination for large result sets

### Async/Await
- Use `async def` for I/O operations
- Avoid blocking operations in async functions
- Use `asyncio.gather()` for parallel execution

### Caching
- Use Redis for expensive computations
- Cache external API responses
- Set appropriate TTLs

## Security

- Never commit `.env` or credentials
- Encrypt sensitive data in database
- Validate all user inputs
- Use parameterized queries
- Implement rate limiting for APIs
- Add authentication/authorization

## CI/CD

(Setup in GitHub Actions)
- Runs tests on every PR
- Checks code formatting
- Performs type checking
- Generates coverage reports

## Review Process

1. PR submitted
2. Automated tests run
3. Code review (maintainers)
4. Revisions if needed
5. Approval and merge

## Questions?

- Check existing issues/discussions
- Ask in PR comments
- Open a discussion
- Email: team@paos.local

Thanks for contributing! 🎉
