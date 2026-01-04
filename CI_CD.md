# CI/CD Pipeline

This repository uses GitHub Actions for continuous integration and deployment.

## Workflow Overview

### 1. Backend Tests & Linting (`backend-tests`)
- **Black** - Python code formatting check
- **Ruff** - Fast Python linter
- **MyPy** - Static type checking
- **Pytest** - Unit tests with coverage reporting
- **Codecov** - Upload test coverage

### 2. Frontend Tests & Build (`frontend-tests`)
- **ESLint** - JavaScript/TypeScript linting
- **TypeScript** - Type checking
- **Next.js Build** - Production build verification
- **Artifact Upload** - Store build artifacts

### 3. Integration Tests (`integration-tests`)
- **Qdrant Service** - Vector database container
- **API Health Checks** - Verify backend is running
- **End-to-End Tests** - Full query flow validation

### 4. Deploy (`deploy`)
- Manual deployment trigger
- Only runs on `main` branch
- Production environment gate

## Running Tests Locally

### Backend
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

### Frontend
```bash
cd frontend

# Install dependencies
npm ci

# Run linter
npm run lint

# Type check
npx tsc --noEmit

# Build
npm run build
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Main CI/CD pipeline |
| `backend/requirements.txt` | Python dependencies |
| `backend/pyproject.toml` | Black & pytest config |
| `backend/ruff.toml` | Ruff linter config |
| `backend/mypy.ini` | MyPy type checker config |
| `frontend/package.json` | Node dependencies & scripts |

## Test Coverage

Tests cover:
- ✅ API endpoint validation
- ✅ Request/response formats
- ✅ Error handling
- ✅ Integration with vector DB
- ✅ Full query flow

## Adding New Tests

1. **Backend tests**: Add to `backend/tests/`
2. **Integration tests**: Add to `scripts/test_integration.py`
3. **Frontend tests**: Add to `frontend/tests/` (if needed)

## Secrets Required

For deployment, configure these in GitHub Secrets:
- `GROQ_API_KEY` - Groq API key
- `LANGCHAIN_API_KEY` - LangSmith API key
- `DEPLOY_HOST` - Deployment server (if applicable)
- `DEPLOY_TOKEN` - Auth token for deployment

## Status Badges

Add to README.md:
```markdown
[![CI/CD Pipeline](https://github.com/your-username/repo/actions/workflows/ci.yml/badge.svg)]
[![codecov](https://codecov.io/gh/your-username/repo/branch/main/graph/badge.svg)]
```
