# CI/CD Pipeline for API

This repository uses GitHub Actions for continuous integration and deployment of the API.

## Workflow Overview

### 1. API Tests & Linting (`backend-tests`)
- **Black** - Python code formatting check
- **Ruff** - Fast Python linter
- **MyPy** - Static type checking
- **Pytest** - Unit tests with coverage reporting
- **Codecov** - Upload test coverage

### 2. Integration Tests (`integration-tests`)
- **Qdrant Service** - Vector database container
- **API Health Checks** - Verify API is running
- **End-to-End Tests** - Full query flow validation

### 3. Deploy API (`deploy`)
- Triggered on push to main branch
- Manual trigger available
- Production environment gate
- Docker image build and push

## Running Tests Locally

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run linters
black --check .
ruff check .

# Run type checking
mypy --ignore-missing-imports .

# Run tests
pytest tests/ -v --cov=.
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | CI pipeline for API |
| `.github/workflows/deploy.yml` | Deploy API to production |
| `backend/requirements.txt` | Python dependencies |
| `backend/pyproject.toml` | Black & pytest config |
| `backend/ruff.toml` | Ruff linter config |
| `backend/mypy.ini` | MyPy type checker config |

## Test Coverage

Tests cover:
- ✅ API endpoint validation
- ✅ Request/response formats
- ✅ Error handling
- ✅ Integration with vector DB
- ✅ Full query flow

## Adding New Tests

1. **API tests**: Add to `backend/tests/`
2. **Integration tests**: Add to `scripts/test_integration.py`

## Secrets Required

For deployment, configure these in GitHub Secrets:
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password/token
- `GROQ_API_KEY` - Groq API key
- `LANGCHAIN_API_KEY` - LangSmith API key

## Status Badges

Add to README.md:
```markdown
[![CI Pipeline](https://github.com/your-username/repo/actions/workflows/ci.yml/badge.svg)]
[![codecov](https://codecov.io/gh/your-username/repo/branch/main/graph/badge.svg)]
```
