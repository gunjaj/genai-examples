# ChatStack: FAQ Chatbot with AWS Bedrock

## Overview
This project demonstrates how to expose a `/chat` endpoint behind your web or app to answer FAQs using a generative AI model. The backend leverages AWS Lambda and the Bedrock foundation model (`amazon.nova-micro-v1:0`). The Lambda function receives requests from your application and returns model-generated responses.

## Architecture
- **API Gateway** (optional): Exposes the `/chat` endpoint to your web/app.
- **AWS Lambda**: Handles incoming chat requests and invokes the Bedrock model.
- **Bedrock Model**: Processes the input and generates a response.

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
2. Deploy the stack:
   ```sh
   cdk deploy InfrastructureStack --profile $AWS_PROFILE
   ```
   Replace `$AWS_PROFILE` with your AWS CLI profile name.

### 3. Find Lambda Function Name
After deployment, get the Lambda function name:
```sh
export AWS_REGION=us-east-1  # or your region
aws cloudformation list-stack-resources \
  --stack-name InfrastructureStack \
  --query "StackResourceSummaries[?ResourceType=='AWS::Lambda::Function'].PhysicalResourceId" \
  --output text \
  --region $AWS_REGION --profile $AWS_PROFILE
```

### 4. Test the Lambda Function
Invoke the Lambda function directly:
```sh
FN_NAME='Name returned by CloudFormation Stack'
aws lambda invoke \
  --function-name "$FN_NAME" \
  --payload '{"message":"How far is earth from Sun?"}' \
  --cli-binary-format raw-in-base64-out \
  response.json \
  --region $AWS_REGION --profile $AWS_PROFILE
cat response.json
```

### 5. (Optional) API Gateway Integration
To expose the Lambda as a REST endpoint, add an API Gateway resource in your CDK stack or via the AWS Console, and connect it to the Lambda function.

## Cleanup
To remove all resources:
```sh
cd infrastructure
cdk destroy InfrastructureStack --profile $AWS_PROFILE
```

## Project Structure
```
chatstack/
├── infrastructure/          # CDK app and infrastructure code
│   ├── infrastructure/      # CDK stack definitions
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
