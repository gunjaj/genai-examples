import boto3
import json
import os
import logging
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

client = boto3.client('bedrock-runtime')
model_id = os.environ.get('MODEL_ID', 'amazon.nova-micro-v1:0')
region = os.environ.get('REGION', 'us-east-1')

# Standard response structure for API Gateway
def _response(status: int, message=None):
    return {
        'statusCode': status,
        'body': json.dumps({'message': message}),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    }
def _parse_event(event):
    body = event.get('body')
    if body:
        try:
            if event.get('isBase64Encoded'):
                body = base64.b64decode(body).decode('utf-8')
            return json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return None
    return None

def lambda_handler(event, context):
    try:
        #event_raw = event['body']
        logger.info("Received event: ")
        logger.info(event)

        body = _parse_event(event)

        message = body.get('message')
        if not message:
            return _response(400, "Missing 'message' in request body")
        
        # Defaults
        max_tokens = 1024
        temperature = 0.3
        top_p = 0.9

        kwargs = {
            'modelId':model_id,
            'messages':[
                {
                    'role': 'user',
                    'content': [{'text': message}]
                }
            ],
            'inferenceConfig':{
                'maxTokens': max_tokens,
                'temperature': temperature,
                'topP': top_p
            },
            'guardrailConfig':{
                "guardrailIdentifier": os.environ["GUARDRAIL_ID"],
                "guardrailVersion": os.environ["GUARDRAIL_VERSION"]
            }
        }

# Converse API provides a simple interface to interact with the model
# InvokeModel API provides more control over the request and response structure
# Here we are using Converse API for simplicity 
        response = client.converse(**kwargs)
        logger.info("Response from model: ")
        logger.info(response)

# Expect a truncated message as we have set max tokens to 1024

        return _response(200, response['output']['message']['content'][0]['text'])
    
    except Exception as e:
        logger.error("Error processing request: ", exc_info=True)
        return {
            'statusCode': 500,
            'body': str(e)
        }