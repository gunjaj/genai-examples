# ChatStack: FAQ Chatbot with AWS Bedrock

## Overview
This project demonstrates how to build a secure FAQ chatbot using AWS Bedrock with built-in guardrails. The solution includes a Streamlit web client, API Gateway endpoint, Lambda function, and Bedrock Guardrails to ensure safe and appropriate responses.

## Architecture
- **Streamlit Client**: Web interface for user interactions
- **API Gateway**: Exposes the `/chat` endpoint with CORS support
- **AWS Lambda**: Handles chat requests and invokes Bedrock with guardrails
- **Bedrock Guardrails**: Content filtering and topic restrictions
- **Bedrock Model**: `amazon.nova-micro-v1:0` for response generation

## Prerequisites
- AWS account with access to Bedrock and Lambda
- AWS CLI and [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) installed
- Node.js and Python 3.10+
- Bedrock model access enabled for `amazon.nova-micro-v1:0`

## Getting Started

### 1. Enable Bedrock Model
Request access to the Bedrock model `amazon.nova-micro-v1:0` in the AWS Console if not already enabled.

### 2. Deploy Infrastructure
1. Navigate to infrastructure directory and install dependencies:
   ```sh
   cd infrastructure
   pip install -r requirements.txt
   npm install -g aws-cdk
   ```
2. Deploy both stacks (Guardrails first, then Infrastructure):
   ```sh
   cdk deploy ChatGuardrailStack --profile $AWS_PROFILE
   cdk deploy InfrastructureStack --profile $AWS_PROFILE
   ```
   Replace `$AWS_PROFILE` with your AWS CLI profile name.

### 3. Setup and Run Streamlit Client
1. Navigate to client directory and install dependencies:
   ```sh
   cd ../client
   pip install -r requirements.txt
   ```
2. Get your API Gateway URL from the CDK output:
   ```sh
   # Find your API Gateway URL
   aws cloudformation describe-stacks \
     --stack-name InfrastructureStack \
     --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
     --output text --profile $AWS_PROFILE
   ```
3. Update `client/app.py` with your API Gateway URL:
   ```python
   API_URL = "https://your-api-id.execute-api.us-east-1.amazonaws.com"  # Replace with your URL
   ```
4. Run the Streamlit app:
   ```sh
   streamlit run app.py
   ```
5. Open your browser to `http://localhost:8501` and test the chatbot

## Testing Examples

### Positive Use Case
**Prompt:** "How far is the earth from the sun?"
- **Expected:** ✅ Response provided
- **Rationale:** General science question that doesn't violate any topic policies or content filters

### Blocked Use Cases
**Prompt:** "Which stocks should I buy?"
- **Expected:** ❌ Blocked by guardrails
- **Rationale:** Matches the "InvestmentTopics" policy that denies financial investment advice

**Prompt:** "How do I treat high fever?"
- **Expected:** ❌ Blocked by guardrails  
- **Rationale:** Matches the "MedicalTopics" policy that blocks health and medical recommendations

## Bedrock Guardrails
This project implements comprehensive content safety through AWS Bedrock Guardrails:

### Content Filtering
- **Hate Speech**: Blocks hateful content with HIGH sensitivity
- **Insults**: Prevents insulting language with HIGH sensitivity
- **PII Protection**: Blocks US Social Security Numbers

### Topic Restrictions
- **Investment Advice**: Denies financial investment guidance
- **Medical Advice**: Blocks health and medical recommendations  
- **Legal Advice**: Prevents legal counsel and guidance

### Custom Messages
- **Blocked Input**: "Input blocked due to topic policy or detected PII or toxic content."
- **Blocked Output**: "Output response blocked due to topic policy or detected PII or toxic content."

## Cleanup
To remove all resources:
```sh
cd infrastructure
cdk destroy InfrastructureStack --profile $AWS_PROFILE
cdk destroy ChatGuardrailStack --profile $AWS_PROFILE
```

## Project Structure
```
chatstack/
├── client/                  # Streamlit web client
│   ├── app.py              # Streamlit application
│   └── requirements.txt    # Client dependencies
├── infrastructure/          # CDK app and infrastructure code
│   ├── infrastructure/      # CDK stack definitions
│   │   ├── guardrails.py   # Bedrock Guardrails stack
│   │   └── infrastructure_stack.py # Main infrastructure
│   ├── app.py              # CDK app entry point
│   ├── cdk.json            # CDK configuration
│   ├── requirements.txt    # CDK dependencies
│   └── requirements-dev.txt # CDK dev dependencies
├── src/
│   └── lambda/
│       ├── handler.py      # Lambda function code
│       └── requirements.txt # Lambda dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Customization
- Swap out the Bedrock model or prompt for your use case
- Extend the Lambda to support additional request/response formats
- Integrate with your web/app frontend

## License
See the root `LICENSE` file for license information.

## Support
For questions or issues, please refer to the main repository or open an issue.
