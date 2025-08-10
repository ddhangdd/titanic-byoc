# Titanic BYOC Project - AI Coding Assistant Instructions

## 🎯 Project Overview

This is a complete ML deployment pipeline project that takes a Titanic survival prediction model from Jupyter notebooks to production deployments across multiple platforms (AWS SageMaker, Kubernetes, local). The project demonstrates "Bring Your Own Container" (BYOC) patterns for ML model deployment.

## 🏗️ Architecture & Key Components

### Core Service Boundary

- **Training Pipeline**: `container/train.py` + Jupyter notebooks in `notebooks/`
- **Inference API**: `container/api.py` (FastAPI with 2 endpoints: `/invocations` for predictions, `/ping` for health)
- **Container**: Dockerfile creates AWS SageMaker-compatible container with executable scripts `serve` and `train`
- **Deployment Targets**: Local (uvicorn), Kubernetes (`k8s/`), AWS SageMaker + Lambda proxy (`aws/`)

### Data Flow Pattern

```
Raw CSV → Jupyter notebooks → Cleaned features (data/clean/) → Model training → Serialized pipeline (models/rfc_pipeline.pkl) → FastAPI → Container → Deployment
```

### AWS SageMaker Integration Pattern

The container follows SageMaker conventions:

- Uses `/opt/ml/` directory structure for models and data
- `serve` script starts uvicorn on port 8080 with host 0.0.0.0
- `api.py` loads model from `../models/rfc_pipeline.pkl` using cloudpickle
- Lambda function `aws/lambdas/invoke_endpoint.py` provides API Gateway proxy to SageMaker endpoint

## 🛠️ Developer Workflows

### Local Development

```bash
# Start API locally
cd container && uvicorn api:api --reload

# Test endpoints
curl --request POST --data @../tests/test_json/test_json.json localhost:8080/invocations
curl localhost:8080/ping
```

### Testing

```bash
# Run unit tests from tests/ directory
cd tests && bash test_scripts/run_unit_tests.sh
# Creates test_reports/unit_test_report.txt
```

### Container Build & Test

```bash
# Build container (uses Python 3.8-slim-bullseye base)
docker build -t titanic-byoc:dev .

# Test container locally
docker run -p 8080:8080 titanic-byoc:dev
```

## 📋 Project-Specific Conventions

### Model Pipeline Pattern

- Uses `cloudpickle` for serialization (not standard pickle) for better sklearn compatibility
- Model is a complete sklearn Pipeline with preprocessing (`rfc_pipeline.pkl`)
- Input: JSON object with Titanic features → Output: `{'survival_prediction': 0|1}`

### API Response Format

```python
# Always return JSONResponse with specific keys:
return JSONResponse({'survival_prediction': pred})  # for predictions
return JSONResponse({'status': 'healthy!'})         # for health check
```

### Environment Dependencies

- **Critical**: Requires exact versions in `dependencies/requirements.txt`
- Known issue: `category-encoders==2.2.2` requires `numpy<1.20` (compatibility constraint)
- Python 3.8 required (specified in Dockerfile and venv setup)

### File Structure Patterns

- **Executable scripts**: `container/serve` and `container/train` (no .sh extension, made executable in Dockerfile)
- **Test data**: JSON files in `tests/test_json/` directory
- **Models**: Serialized in `models/` directory, loaded relative to container working directory
- **Configuration**: `k8s/api-deployment.yaml` uses `imagePullPolicy: IfNotPresent` for local development

### Kubernetes Deployment Pattern

- Uses `titanic-byoc:dev` image tag for local development
- Container runs `serve` command (not direct uvicorn)
- Exposes port 8080 with resource requests of 500m CPU

## 🔧 Integration Points

### AWS SageMaker Integration

- Container must expose port 8080 with uvicorn ASGI server
- Model path: `/opt/models` mounted in container, accessed as `../models/` from `/opt/program/`
- Environment variables: `PYTHONUNBUFFERED=TRUE`, `PYTHONDONTWRITEBYTECODE=TRUE`

### Lambda Proxy Pattern

- `aws/lambdas/invoke_endpoint.py` handles both API Gateway events and direct test events
- Converts single objects to arrays for SageMaker compatibility
- Returns CORS-enabled responses with `Access-Control-Allow-Origin: '*'`

## 🎓 Key Learning Patterns

### Testing Strategy

- Uses FastAPI TestClient for API endpoint testing
- Validates exact response format and status codes
- Separates test data into reusable JSON files

### Deployment Verification

- Always test `/ping` endpoint first to verify container health
- Use curl scripts in `tests/curl_scripts/` for different deployment targets
- Each deployment (local, minikube, aws) has its own test script

When working on this codebase, prioritize understanding the complete pipeline flow and test each component individually before integration.
