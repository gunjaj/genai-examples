from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    Duration,
    Tags,
    CfnOutput,
    aws_s3 as s3,
)
from constructs import Construct
from aws_cdk.aws_apigatewayv2 import HttpApi, HttpMethod, CorsHttpMethod
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration

class ClientStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, pinecone_secret_val: secretsmanager.ISecret, lambda_layer: _lambda.ILayerVersion, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        lambda_role = iam.Role(self, "StreamlitClientLambdaExecutionRole",
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
                            ],
                            resources=["arn:aws:bedrock:*:*:foundation-model/*"]
                        ),
                    ]
                ),
                "SecretAccess":  iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "secretsmanager:GetSecretValue",
                            ],
                            resources=[pinecone_secret_val.secret_arn]
                        ),
                    ]
                ),
            }
        )
        Tags.of(lambda_role).add("example", "rag")

        lambda_function = _lambda.Function(self, "RAGFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            role=lambda_role,
            code=_lambda.Code.from_asset("./src/lambda/search_client"),
            memory_size=128,
            timeout=Duration.seconds(30),
            environment={
                "MODEL_ID": "amazon.nova-micro-v1:0",
                "REGION": self.region,
                "PINECONE_SECRET_NAME": pinecone_secret_val.secret_name,
                "PINECONE_SECRET_ARN": pinecone_secret_val.secret_arn,
                "EMBED_DIM": "1024",
                "TOP_K" : "5"
            }, 
            layers=[lambda_layer],
        )
        Tags.of(lambda_function).add("example", "rag")


        # Create HTTP API Gateway
        http_api = HttpApi(self, "RAGHttpApi",
            api_name="RAGHttpApi",
            cors_preflight={
                "allow_origins": ["*"],
                "allow_methods": [CorsHttpMethod.GET, CorsHttpMethod.POST, CorsHttpMethod.OPTIONS],
            }
        )

        # Integrate Lambda function with API Gateway
        lambda_integration = HttpLambdaIntegration(
            "RAGLambdaIntegration",
            lambda_function,
        )

        # Add routes to the API Gateway
        http_api.add_routes(
            path="/rag",
            methods=[HttpMethod.POST],
            integration=lambda_integration,
        )

        Tags.of(http_api).add("example", "rag")

        # Output the API endpoint URL
        CfnOutput(self, "ApiEndpoint",
            value=http_api.api_endpoint,
            description="The endpoint URL of the RAG HTTP API",
        )