from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    Tags,
    CfnOutput,
    aws_s3 as s3,
)
from constructs import Construct
from aws_cdk.aws_apigatewayv2 import HttpApi, HttpMethod, CorsHttpMethod
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration

class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define IAM role for Lambda function. Add Bedrock permissions.
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
                                "bedrock:Converse",
                                "bedrock:InvokeModelWithResponseStream",
                                "bedrock:ConverseWithResponseStream",
                            ],
                            resources=["arn:aws:bedrock:*:*:foundation-model/*"]
                        )
                    ]
                )
            }
        )

        # Lambda function
        lambda_function = _lambda.Function(self, "ChatFunction",
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
        Tags.of(lambda_function).add("example", "chatstack")
        CfnOutput(self, "LambdaFunctionName", value=lambda_function.function_name)

        # API Gateway
        api = HttpApi(self, "ChatAPI", 
            api_name="ChatAPI",
            cors_preflight={
                "allow_origins": ["*"], # Adjust as needed for security
                "allow_methods": [CorsHttpMethod.POST, CorsHttpMethod.OPTIONS],
                "allow_headers": ["*"],
            }
        )
        lambda_integration = HttpLambdaIntegration("LambdaIntegration", lambda_function)
        api.add_routes(
            path="/chat",
            methods=[HttpMethod.POST],
            integration=lambda_integration,
        )
        Tags.of(api).add("example", "chatstack")
        CfnOutput(self, "ApiEndpoint", value=api.api_endpoint)