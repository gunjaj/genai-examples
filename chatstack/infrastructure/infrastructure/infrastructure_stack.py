from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    Tags
)
from constructs import Construct

class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define IAM role for Lambda function
        lambda_role = iam.Role(self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            inline_policies={
                "BedrockAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "bedrock:InvokeModel",
                                "bedrock:Converse"
                            ],
                            resources=["arn:aws:bedrock:*:*:foundation-model/*"]
                        )
                    ]
                )
            }
        )

        # Lambda function
        lambda_function = _lambda.Function(self, "ChatStack",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="handler.lambda_handler",
            role=lambda_role,
            code=_lambda.Code.from_asset("../src/lambda"),
            memory_size=128,
            timeout=Duration.seconds(30),
            environment={
                "MODEL_ID": "amazon.nova-micro-v1:0",
                "REGION": self.region
            }, 
        )
        Tags.of(lambda_function).add("example", "ChatStack")
 