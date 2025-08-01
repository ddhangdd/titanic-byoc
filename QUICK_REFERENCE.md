# Quick Reference: Titanic ML Deployment

## 🚀 TL;DR - What We Built

**From**: Jupyter Notebook with ML model  
**To**: Production AWS SageMaker endpoint with Lambda proxy

**Result**: 83.4% accurate Titanic survival prediction API accessible via simple HTTP POST

---

## 📋 Commands Cheat Sheet

### Local Development

```bash
# Setup environment
python -m venv venv_py38
source venv_py38/Scripts/activate  # Windows Git Bash
pip install -r dependencies/requirements.txt

# Run FastAPI locally
cd container
uvicorn --host 0.0.0.0 --port 8000 api:api

# Test locally
curl http://localhost:8000/ping
curl -X POST http://localhost:8000/invocations -H "Content-Type: application/json" -d @../tests/test_json/test_json.json
```

### Docker

```bash
# Build and run container
docker build -t titanic-api .
docker run -p 8080:8080 titanic-api

# Test container
curl http://localhost:8080/ping
```

### AWS Deployment

```bash
# Create ECR repository
aws ecr create-repository --repository-name titanic-model --region us-east-1

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [ACCOUNT-ID].dkr.ecr.us-east-1.amazonaws.com

# Tag and push to ECR
docker tag titanic-api:latest [ACCOUNT-ID].dkr.ecr.us-east-1.amazonaws.com/titanic-model:latest
docker push [ACCOUNT-ID].dkr.ecr.us-east-1.amazonaws.com/titanic-model:latest

# Test SageMaker endpoint
aws sagemaker-runtime invoke-endpoint \
    --endpoint-name sagemaker-titanic-byoc-endpoint \
    --content-type application/json \
    --body file://tests/test_json/test_json.json \
    --region us-east-1 \
    output.json && cat output.json
```

---

## 🎯 Key Files

| File                                  | Purpose                                             |
| ------------------------------------- | --------------------------------------------------- |
| `notebooks/predictive-modeling.ipynb` | ML model training (83.4% accuracy)                  |
| `container/api.py`                    | FastAPI application with `/ping` and `/invocations` |
| `container/serve`                     | Uvicorn startup script                              |
| `Dockerfile`                          | Container definition with `CMD ["./serve"]`         |
| `dependencies/requirements.txt`       | Exact package versions (NumPy <1.20)                |
| `aws/lambdas/invoke_endpoint.py`      | Lambda proxy for easy testing                       |
| `models/rfc_pipeline.pkl`             | Trained ML pipeline                                 |

---

## 🔧 Architecture Flow

```
Postman → Lambda Function → SageMaker Endpoint → Docker Container → FastAPI → ML Model → Prediction
```

---

## 💡 Critical Learnings

1. **Package Versions Matter**: NumPy <1.20 for category-encoders compatibility
2. **Docker CMD Required**: Specify startup command or container exits immediately
3. **SageMaker Conventions**: Use `/ping` and `/invocations` endpoints
4. **ECR Tagging**: Must tag with full registry URI before pushing
5. **Lambda Simplifies Testing**: Avoids complex AWS Signature V4 in Postman

---

## 🧪 Test Data Format

```json
[
  {
    "PassengerId": 891,
    "Pclass": 3,
    "Name": "Kelly, Mr. James",
    "Sex": "male",
    "Age": 34.5,
    "SibSp": 0,
    "Parch": 0,
    "Ticket": "330911",
    "Fare": 7.8292,
    "Cabin": "",
    "Embarked": "Q"
  }
]
```

**Expected Response**: `{"survival_prediction": 0}`

---

## 🌐 Endpoints

- **Local FastAPI**: `http://localhost:8000/invocations`
- **Local Docker**: `http://localhost:8080/invocations`
- **SageMaker**: `https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/sagemaker-titanic-byoc-endpoint/invocations`
- **Lambda Proxy**: `https://[lambda-url].lambda-url.us-east-1.on.aws/`

---

_Perfect for sharing with teammates or as a deployment reference!_
