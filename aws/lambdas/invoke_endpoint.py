import json

import boto3

# Defining the name of the endpoint
ENDPOINT_NAME = 'SERVERLESS-sagemaker-titanic-byoc-endpoint'

# Establishing the SageMaker runtime client
sagemaker_client = boto3.Session().client('sagemaker-runtime')


def lambda_handler(event, context):
    try:
        # Getting the JSON data from the body of the request
        if 'body' in event:
            # If called via API Gateway
            request_data = json.loads(event['body'])
        else:
            # If called directly with test data
            request_data = event
        
        # Ensure data is in list format (SageMaker expects array)
        if not isinstance(request_data, list):
            request_data = [request_data]
        
        # Convert to JSON string for SageMaker
        data_json = json.dumps(request_data)
        
        # Getting a response from the SageMaker endpoint
        response = sagemaker_client.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='application/json',
            Body=data_json
        )
        
        # Returning the response back to the end user
        result = json.loads(response['Body'].read().decode())
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to invoke SageMaker endpoint'
            })
        }
