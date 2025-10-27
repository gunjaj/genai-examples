from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    Tags,
    BundlingOptions,
    BundlingOutput,
    CfnOutput,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_s3_deployment as s3_deploy,
)
import aws_cdk as cdk
import os
from constructs import Construct
from pathlib import Path
from aws_cdk import triggers as triggers

# Create infrastructure to create a vector store, injest data and store in Pinecone


class PineconeIndexStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, pinecone_api_key: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create secret in AWS Secrets Manager
        self.pinecone_secret = secretsmanager.Secret(
            self,
            "PineconeApiKeySecret",
            secret_name="rag/pinecone/api-key",
            description="API key for Pinecone access",
            secret_string_value=cdk.SecretValue.unsafe_plain_text(pinecone_api_key),
        )
        Tags.of(self.pinecone_secret).add("example", "rag")

        data_bucket = s3.Bucket(
            self,
            "PineconeDataBucket",
            bucket_name=f"{self.account}-rag-demo-data",
            versioned=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        Tags.of(data_bucket).add("example", "rag")

        project_root = Path(__file__).resolve().parents[2]

        upload = s3_deploy.BucketDeployment(
            self,
            "DeployDemoData",
            sources=[s3_deploy.Source.asset(str(project_root / "data"))],
            destination_bucket=data_bucket,
        )

        # Define IAM role for Lambda function.
        lambda_role = iam.Role(
            self,
            "PineconeLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
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
                )
            }
        )
        Tags.of(lambda_role).add("example", "rag")

        # Lambda layer for third-party dependencies
        self.layer = _lambda.LayerVersion(
            self,
            "PineconeDepsLayer",
            code=_lambda.Code.from_asset(
                "./src/lambda/deps_layer",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-lc",
                        "pip install -r requirements.txt -t /asset-output/python && cp -au . /asset-output/python",
                    ],
                    output_type=BundlingOutput.NOT_ARCHIVED,
                ),
            ),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            compatible_architectures=[_lambda.Architecture.X86_64],
            description="Dependencies for Pinecone Ingest Lambda",
        )

        Tags.of(self.layer).add("example", "rag")

        # Lambda function to interact with Pinecone
        lambda_function = _lambda.Function(
            self,
            "IngestIntoPineCone",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            role=lambda_role,
            code=_lambda.Code.from_asset("./src/lambda/pinecone_ingest"),
            memory_size=256,
            timeout=Duration.seconds(60),
            environment={
                # Pass identifiers, not the raw secret;
                "PINECONE_SECRET_NAME": self.pinecone_secret.secret_name,
                "PINECONE_SECRET_ARN": self.pinecone_secret.secret_arn,
                "DATA_BUCKET_NAME": data_bucket.bucket_name,
                "MOVIES_DATA_FILE": "movies.jsonl",
                "REVIEWS_DATA_FILE": "reviews.jsonl",
                "BEDROCK_REGION": self.region,
                "EMBED_DIM": "1024",
            },
            layers=[self.layer],
        )
        Tags.of(lambda_function).add("example", "rag")

        self.pinecone_secret.grant_read(lambda_function)
        s3.Bucket.grant_read(data_bucket, lambda_function)

        # Output the Lambda function name
        CfnOutput(
            self,
            "IngestIntoPineConFunctionName",
            value=lambda_function.function_name,
            description="The name of the Pinecone Lambda function",
        )

        triggers.Trigger(
            self,
            "PineconeIngestTrigger",
            handler=lambda_function,
            timeout = Duration.minutes(1),
            execute_after=[upload],
        )
