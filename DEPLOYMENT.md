# ☁️ AeroQuant AWS Cloud Deployment Guide

AeroQuant is architected natively around Amazon Web Services (AWS) across storage, training, serverless inference, and web hosting.

---

## 🏗️ Complete AWS Cloud Architecture

`	ext
                  +----------------------------------------------+
                  |            End User Web Browser              |
                  +----------------------------------------------+
                                         |
                                         | HTTPS (Port 443 / 8080)
                                         v
+-----------------------------------------------------------------------------------+
|                            AWS APP RUNNER / ECS FARGATE                           |
|  +-----------------------------------------------------------------------------+  |
|  | Containerized Bloomberg Terminal Web Service (FastAPI + Uvicorn ASGI)       |  |
|  | Serves frontend UI, runs Portfolio Optimizer, Watchlist & Backtester        |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
                                         |
               +-------------------------+-------------------------+
               |                                                   |
               v                                                   v
+-----------------------------+                     +-----------------------------+
|    AMAZON SAGEMAKER CLOUD   |                     |      AMAZON S3 DATA LAKE    |
|                             |                     |                             |
| - Scikit-learn Estimator    |                     | - Historical OHLCV Parquet  |
|   (train_sagemaker.py)      | <------------------ |   & CSV Cache Data          |
|                             |    Dataset Staging  | - Model Artifacts Tarball   |
| - Serverless Inference      |                     |   (model.tar.gz)            |
|   Endpoint                  |                     +-----------------------------+
|   (stock-rf-trend-endpoint) |
+-----------------------------+
               ^
               | (Alternative Serverless API)
+-----------------------------+
|     AWS LAMBDA HANDLER      |
|  (lambda_function.py)       |
|  Exposed via API Gateway    |
+-----------------------------+
`

---

## 🚀 Deployment Option 1: AWS App Runner (Recommended for Web Terminal)

AWS App Runner is the modern, fully-managed container service by AWS that builds and runs web applications directly from a GitHub repository or Amazon ECR.

### Step 1: Push Repository to GitHub or AWS CodeCommit
`ash
cd C:\Users\anshu\Documents\stock_intelligence_system
git add .
git commit -m feat: complete aws bloomberg terminal
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/stock-intelligence-terminal.git
git push -u origin main
`

### Step 2: Launch on AWS App Runner
1. Open the [AWS Management Console](https://console.aws.amazon.com/apprunner).
2. Click **Create service**.
3. Select **Source code repository** -> choose **GitHub** -> select your repository and main branch.
4. Under **Deployment settings**, select **Automatic**.
5. Under **Build settings**, select **Use a configuration file** (App Runner will automatically detect pprunner.yaml).
6. Under **Service configuration**, set:
   - **Service name**: eroquant-terminal
   - **CPU & Memory**: 1 vCPU, 2 GB Memory
7. Click **Create & deploy**.
8. In ~3 minutes, AWS provides a secured live HTTPS URL (e.g. https://xxxxxx.us-east-1.awsapprunner.com).

---

## 🧠 Deployment Option 2: AWS SageMaker + Lambda (Serverless ML Core)

This pipeline deploys the machine learning inference model to AWS SageMaker Serverless.

### Step 1: Configure AWS CLI Credentials
`ash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and Default Region (e.g., us-east-1)
`

### Step 2: Run the SageMaker Training & Deployment Script
`ash
python train_sagemaker.py
`
What this does automatically:
1. Creates an Amazon S3 bucket for training data staging (s3://<bucket>/stock-intelligence/data).
2. Configures a SageMaker SKLearn estimator and submits a distributed cloud training job.
3. Deploys the model to a **SageMaker Serverless Inference Endpoint** (stock-rf-trend-endpoint) with auto-scaling down to zero cost when idle.

### Step 3: Deploy AWS Lambda Serverless Handler
1. Open the **AWS Lambda Console** -> **Create function** -> Author from scratch (Python 3.11).
2. Copy the code from lambda_function.py into the Lambda editor.
3. Under **Configuration** -> **Environment variables**, add:
   - SAGEMAKER_ENDPOINT_NAME: stock-rf-trend-endpoint
4. Attach IAM Policy: Ensure the Lambda execution role has AmazonSageMakerFullAccess.
5. Under **Function overview**, click **Add trigger** -> select **API Gateway** (HTTP API) -> Create.
6. You now have a serverless API endpoint URL for instant real-time predictions!

---

## 🐳 Deployment Option 3: AWS Elastic Container Service (ECS Fargate)

If deploying via Docker container directly to AWS:

`ash
# 1. Authenticate Docker with Amazon ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# 2. Create ECR Repository
aws ecr create-repository --repository-name aeroquant-terminal

# 3. Build & Tag Docker Image
docker build -t aeroquant-terminal .
docker tag aeroquant-terminal:latest <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/aeroquant-terminal:latest

# 4. Push Image to ECR
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/aeroquant-terminal:latest

# 5. Launch ECS Task on AWS Fargate with Port 5000 mapped
`

---

## 📋 Required AWS IAM Policies

To run the full AWS pipeline, ensure your IAM user or role has:
- AmazonSageMakerFullAccess
- AmazonS3FullAccess
- AWSAppRunnerFullAccess (or AWSLambdaFullAccess for serverless)
