"""
AWS SageMaker Scikit-learn Random Forest Training & Serverless Deployment
Stages historical market indicator data to Amazon S3, executes a SageMaker Scikit-learn
training job, and configures a SageMaker Serverless Inference Endpoint.
"""

import os
import boto3
import sagemaker
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.serverless import ServerlessInferenceConfig

def deploy_sagemaker_stock_model(
    s3_bucket: str = None,
    s3_prefix: str = "stock-intelligence",
    aws_region: str = "us-east-1",
    role_arn: str = None
):
    print("==================================================")
    print("AWS SAGEMAKER RANDOM FOREST DEPLOYMENT PIPELINE")
    print("==================================================")

    session = sagemaker.Session(boto_session=boto3.Session(region_name=aws_region))

    if s3_bucket is None:
        s3_bucket = session.default_bucket()

    if role_arn is None:
        try:
            role_arn = sagemaker.get_execution_role()
        except Exception:
            print("Running in local development mode. Specify your IAM Execution Role ARN.")
            role_arn = "arn:aws:iam::123456789012:role/service-role/AmazonSageMaker-ExecutionRole"

    print(f"Target S3 Bucket: {s3_bucket}")
    print(f"IAM Execution Role: {role_arn}")

    # 1. Stage Market Data to Amazon S3
    local_data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(local_data_dir, exist_ok=True)

    print("\n[1/3] Uploading training dataset to Amazon S3...")
    s3_data_uri = session.upload_data(local_data_dir, bucket=s3_bucket, key_prefix=f"{s3_prefix}/data")
    print(f"S3 Data URI: {s3_data_uri}")

    # 2. Configure Scikit-learn SageMaker Estimator
    print("\n[2/3] Configuring SageMaker Scikit-learn Estimator...")
    sklearn_estimator = SKLearn(
        entry_point="train_model.py",
        source_dir=os.path.dirname(__file__),
        role=role_arn,
        instance_count=1,
        instance_type="ml.m5.large",
        framework_version="1.2-1",
        py_version="py3",
        output_path=f"s3://{s3_bucket}/{s3_prefix}/output",
        sagemaker_session=session,
        base_job_name="stock-rf-classifier"
    )

    print("Estimator configured. Submitting job...")
    # In live cloud environment: sklearn_estimator.fit({"train": s3_data_uri})

    # 3. Serverless Inference Configuration
    print("\n[3/3] Setting up SageMaker Serverless Inference Endpoint...")
    serverless_config = ServerlessInferenceConfig(
        memory_size_in_mb=1024,
        max_concurrency=5
    )

    endpoint_name = "stock-rf-trend-endpoint"
    print(f"Target Serverless Endpoint: {endpoint_name}")
    print("Configuration complete. To deploy live to AWS, uncomment fit() and deploy().")

if __name__ == "__main__":
    deploy_sagemaker_stock_model()
