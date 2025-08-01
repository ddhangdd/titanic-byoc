#!/usr/bin/env python3
"""
Test script for SageMaker endpoint
"""
import json

import boto3


def test_sagemaker_endpoint():
    # Initialize SageMaker runtime client
    client = boto3.client('sagemaker-runtime', region_name='us-east-1')
    
    # Load test data
    with open('tests/test_json/test_json.json', 'r') as f:
        test_data = f.read()
    
    # Invoke the endpoint
    response = client.invoke_endpoint(
        EndpointName='sagemaker-titanic-byoc-endpoint',
        ContentType='application/json',
        Body=test_data
    )
    
    # Parse and print the result
    result = json.loads(response['Body'].read().decode())
    print("SageMaker Endpoint Response:", result)
    return result

if __name__ == "__main__":
    try:
        result = test_sagemaker_endpoint()
        print("✅ Endpoint test successful!")
    except Exception as e:
        print(f"❌ Endpoint test failed: {e}")
