import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

client = boto3.client('bedrock-runtime')
model_id = os.environ.get('MODEL_ID', 'amazon.nova-micro-v1:0')
region = os.environ.get('REGION', 'us-east-1')


def lambda_handler(event, context):
    try:
        #event_raw = event['body']
        logger.info("Received event: ")
        logger.info(event)

        message = event.get('message')
        if not message:
            return {
                'statusCode': 400,
                'body': 'Message is required'
            }
        
        # Defaults
        max_tokens = 256
        temperature = 0.3
        top_p = 0.9

# Converse API provides a simple interface to interact with the model
# InvokeModel API provides more control over the request and response structure
# Here we are using Converse API for simplicity 
        response = client.converse(
            modelId=model_id,
            messages=[
                {
                    'role': 'user',
                    'content': [{'text': message}]
                }
            ],
            inferenceConfig={
                'maxTokens': max_tokens,
                'temperature': temperature,
                'topP': top_p
            }
        )
        logger.info("Response from model: ")
        logger.info(response)

# Expect a truncated message as we have set max tokens to 256

        return {
            'statusCode': 200,
            'body': response['output']['message']['content']
        }
    
    except Exception as e:
        logger.error("Error processing request: ", exc_info=True)
        return {
            'statusCode': 500,
            'body': str(e)
        }