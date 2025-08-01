# Titanic Survival Prediction: From Jupyter Notebook to AWS SageMaker

## 📋 Project Overview

This project demonstrates a complete machine learning deployment pipeline, taking a Titanic survival prediction model from a Jupyter notebook to a production-ready AWS SageMaker endpoint.

### 🎯 What We Built

- **ML Model**: Random Forest Classifier for Titanic survival prediction (83.4% accuracy)
- **API**: FastAPI application with health check and prediction endpoints
- **Container**: Docker image for consistent deployment
- **Cloud Deployment**: AWS SageMaker real-time inference endpoint
- **Testing**: Lambda function proxy for easy API testing

---

## 🛤️ Deployment Roadmap

```
Step 1: Jupyter Notebooks → Step 2: Model Training → Step 3: FastAPI → Step 4: Docker → Step 5: SageMaker → Step 6: Lambda Testing
```

---

## 🚀 Step-by-Step Implementation

### Step 1: Environment Setup & Data Exploration ✅

**Goal**: Set up Python 3.8.8 environment and explore the data

**Key Actions**:

- Created virtual environment: `python -m venv venv_py38`
- Installed exact package versions for compatibility
- Resolved NumPy compatibility issue with category-encoders

**Key Learning**:

> **Package Version Compatibility Matters!** We had to downgrade NumPy to `<1.20` to resolve compatibility issues with `category-encoders==2.2.2`.

**Files Modified**:

- `requirements.txt` - Exact version specifications
- Environment activated with specific Python 3.8.8

---

### Step 2: Model Development & Training ✅

**Goal**: Build and train the machine learning pipeline

**Key Components**:

```python
# Custom age binning function
def create_age_bins(df):
    df['Age_Binned'] = pd.cut(df['Age'], bins=[0, 18, 35, 60, 100],
                              labels=['Child', 'Young Adult', 'Adult', 'Senior'])
    return df

# ML Pipeline
pipeline = Pipeline([
    ('age_binner', FunctionTransformer(create_age_bins)),
    ('data_preprocessor', data_preprocessor),
    ('classifier', RandomForestClassifier(random_state=42))
])
```

**Results**:

- **Model Accuracy**: 83.4%
- **Model Artifacts**: `rfc_pipeline.pkl`, `rfc_model.pkl`

**Key Learning**:

> **Feature Engineering is Critical!** Age binning and proper preprocessing significantly improved model performance.

---

### Step 3: FastAPI Application ✅

**Goal**: Create REST API for model serving

**API Endpoints**:

- `GET /ping` - Health check endpoint
- `POST /invocations` - Prediction endpoint (SageMaker standard)

**Key Code** (`container/api.py`):

```python
@api.get("/ping")
def ping():
    return {"status": "healthy!"}

@api.post("/invocations")
def invocations(passenger_data: List[dict]):
    # Load model and make predictions
    predictions = pipeline.predict(df)
    return {"survival_prediction": int(predictions[0])}
```

**Testing**:

```bash
# Local testing
uvicorn --host 0.0.0.0 --port 8000 api:api
curl http://localhost:8000/ping
curl -X POST http://localhost:8000/invocations -H "Content-Type: application/json" -d @tests/test_json/test_json.json
```

**Key Learning**:

> **SageMaker has specific endpoint conventions!** Using `/invocations` and `/ping` ensures compatibility with AWS SageMaker.

---

### Step 4: Containerization ✅

**Goal**: Package application in Docker for consistent deployment

**Dockerfile**:

```dockerfile
FROM python:3.8-slim-bullseye

# Install system dependencies
RUN apt-get --yes update
RUN apt-get --yes install gcc libxml2

# Install Python dependencies
COPY dependencies/requirements.txt /
RUN pip install -r /requirements.txt

# Copy application files
COPY models/ /opt/models
COPY container/ /opt/program

# Set working directory and permissions
WORKDIR /opt/program
RUN chmod +x serve

# Define startup command
CMD ["./serve"]
```

**Serve Script** (`container/serve`):

```bash
#!/bin/sh
uvicorn --host 0.0.0.0 --port 8080 api:api
```

**Build & Test**:

```bash
docker build -t titanic-api .
docker run -p 8080:8080 titanic-api
curl http://localhost:8080/ping
```

**Key Learning**:

> **Always specify CMD in Dockerfile!** Without it, Docker falls back to the base image's default command (python3), which doesn't start your application.

---

### Step 5: AWS SageMaker Deployment ✅

**Goal**: Deploy containerized model to AWS SageMaker

**Process**:

1. **Create ECR Repository**:

```bash
aws ecr create-repository --repository-name titanic-model --region us-east-1
```

2. **Push Docker Image**:

```bash
# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 676206917956.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag titanic-api:latest 676206917956.dkr.ecr.us-east-1.amazonaws.com/titanic-model:latest
docker push 676206917956.dkr.ecr.us-east-1.amazonaws.com/titanic-model:latest
```

3. **Create SageMaker Model & Endpoint**:

```bash
# Create IAM role for SageMaker
aws iam create-role --role-name SageMakerExecutionRole --assume-role-policy-document '{...}'
aws iam attach-role-policy --role-name SageMakerExecutionRole --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

# Create model, endpoint config, and endpoint
aws sagemaker create-model --model-name titanic-model-xxx --primary-container Image=676206917956.dkr.ecr.us-east-1.amazonaws.com/titanic-model:latest --execution-role-arn arn:aws:iam::676206917956:role/SageMakerExecutionRole
```

**Result**:

- **SageMaker Endpoint**: `https://runtime.sagemaker.us-east-1.amazonaws.com/endpoints/sagemaker-titanic-byoc-endpoint/invocations`

**Key Learning**:

> **Docker tagging is essential for registry push!** You must tag your local image with the ECR repository URI format before pushing.

---

### Step 6: Lambda Proxy for Easy Testing ✅

**Goal**: Create simple HTTP endpoint for testing via Postman

**Lambda Function** (`aws/lambdas/invoke_endpoint.py`):

```python
def lambda_handler(event, context):
    # Parse request body
    data = json.dumps(json.loads(event['body']))

    # Invoke SageMaker endpoint
    response = sagemaker_client.invoke_endpoint(
        EndpointName='sagemaker-titanic-byoc-endpoint',
        ContentType='application/json',
        Body=data
    )

    return {
        'statusCode': 200,
        'body': json.dumps(json.loads(response['Body'].read().decode()))
    }
```

**Why Lambda Proxy?**
| Method | Complexity | Postman Setup | Security |
|--------|------------|---------------|----------|
| **Direct SageMaker** | High | AWS Signature V4 auth | Credentials in Postman |
| **Lambda Proxy** | Low | Simple HTTP POST | Credentials stay in AWS |

**Key Learning**:

> **Lambda functions make excellent API proxies!** They handle AWS authentication automatically and expose simple HTTP endpoints.

---

## 🔧 Technical Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Jupyter       │───▶│   FastAPI       │───▶│   Docker        │───▶│   AWS ECR       │
│   Notebook      │    │   Application   │    │   Container     │    │   Registry      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ML Pipeline   │    │   REST API      │    │   Port 8080     │    │   SageMaker     │
│   83.4% Acc     │    │   /ping         │    │   Uvicorn       │    │   Endpoint      │
│                 │    │   /invocations  │    │   Server        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 📦 Project Structure

```
titanic-byoc-v2/
├── notebooks/                  # Jupyter notebooks for development
│   ├── data-exploration.ipynb
│   ├── feature-engineering.ipynb
│   └── predictive-modeling.ipynb
├── container/                  # FastAPI application
│   ├── api.py                 # Main FastAPI app
│   ├── serve                  # Startup script
│   └── start_api.sh
├── models/                    # Trained model artifacts
│   ├── rfc_model.pkl
│   └── rfc_pipeline.pkl
├── data/                      # Training and test data
│   ├── raw/
│   └── clean/
├── aws/lambdas/              # Lambda functions
│   └── invoke_endpoint.py    # SageMaker proxy
├── tests/                    # Test data and scripts
│   ├── test_json/
│   └── curl_scripts/
├── dependencies/
│   └── requirements.txt      # Exact package versions
└── Dockerfile               # Container definition
```

---

## 🧪 Testing Guide

### Local Testing

```bash
# Test FastAPI locally
uvicorn --host 0.0.0.0 --port 8000 api:api
curl http://localhost:8000/ping

# Test Docker container
docker run -p 8080:8080 titanic-api
curl http://localhost:8080/ping
```

### SageMaker Testing

```bash
# AWS CLI
aws sagemaker-runtime invoke-endpoint \
    --endpoint-name sagemaker-titanic-byoc-endpoint \
    --content-type application/json \
    --body file://tests/test_json/test_json.json \
    --region us-east-1 \
    output.json && cat output.json
```

### Postman Testing (via Lambda)

- **Method**: POST
- **URL**: `https://your-lambda-url.lambda-url.us-east-1.on.aws/`
- **Body**: JSON test data
- **No authentication required!**

---

## 🎓 Key Lessons Learned

### 1. Environment Compatibility

- **Issue**: NumPy version conflicts with category-encoders
- **Solution**: Pin exact package versions in requirements.txt
- **Learning**: Always test with exact production package versions

### 2. Docker CMD Specification

- **Issue**: Container exited immediately after starting
- **Solution**: Added `CMD ["./serve"]` to Dockerfile
- **Learning**: Base images have default commands that may not match your needs

### 3. SageMaker Endpoint Conventions

- **Issue**: Non-standard endpoint names
- **Solution**: Use `/ping` and `/invocations` endpoints
- **Learning**: Follow AWS conventions for seamless integration

### 4. Docker Registry Tagging

- **Issue**: Cannot push to ECR without proper tagging
- **Solution**: Tag image with full ECR URI before pushing
- **Learning**: Registry naming conventions are strict

### 5. Authentication Complexity

- **Issue**: SageMaker endpoints require AWS Signature V4
- **Solution**: Lambda proxy function for simple HTTP access
- **Learning**: Proxies can simplify complex authentication requirements

---

## 🔮 Next Steps

1. **Auto-scaling**: Configure SageMaker endpoint auto-scaling
2. **Monitoring**: Add CloudWatch metrics and alarms
3. **CI/CD**: Automate deployment pipeline with GitHub Actions
4. **Model Versioning**: Implement model registry for version control
5. **A/B Testing**: Deploy multiple model versions for comparison

---

## 📊 Performance Metrics

- **Model Accuracy**: 83.4%
- **API Response Time**: ~200ms (local)
- **Container Size**: ~1.2GB
- **SageMaker Instance**: ml.t2.medium
- **Cold Start Time**: ~30 seconds (SageMaker)

---

## 🛠️ Prerequisites for Replication

1. **AWS Account** with SageMaker permissions
2. **Docker** installed locally
3. **AWS CLI** configured with credentials
4. **Python 3.8.8** environment
5. **VS Code** with terminal access

---

_This documentation represents a complete end-to-end ML deployment journey, showcasing best practices for containerization, cloud deployment, and API design._
