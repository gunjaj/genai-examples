from aws_cdk import (
    Stack,
    CfnOutput,
    Tags,
    aws_bedrock as guardrails
)

from constructs import Construct

# https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_bedrock.CfnGuardrail.html

class GuardrailsStack(Stack):
    """Stack to create Bedrock Guardrails resources."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a Bedrock Guardrail
        guardrail = guardrails.CfnGuardrail(
            self, "DefaultGuardrails",
            name="ChatstackGuardrail",
            description="Bedrock Guardrails for Chatstack application. Block PII and Toxic content.",
            blocked_input_messaging="Input blocked due to topic policy or detected PII or toxic content.",
            blocked_outputs_messaging="Output response blocked due to topic policy or detected PII or toxic content.",
            content_policy_config=guardrails.CfnGuardrail.ContentPolicyConfigProperty(
                filters_config=[
                    guardrails.CfnGuardrail.ContentFilterConfigProperty(
                        type="INSULTS",
                        input_strength="HIGH",
                        output_strength="HIGH"
                    ),
                    guardrails.CfnGuardrail.ContentFilterConfigProperty(
                        type="HATE",
                        input_strength="HIGH",
                        output_strength="HIGH"
                    ),
                ]
            ),
            topic_policy_config=guardrails.CfnGuardrail.TopicPolicyConfigProperty(
                topics_config=[
                    guardrails.CfnGuardrail.TopicConfigProperty(
                        name="InvestmentTopics",
                        definition="Investment advice",
                        examples=["What is the best stock to buy?", "Should I invest in real estate?","How can I save for retirement?"],
                        type="DENY"
                    ),
                    guardrails.CfnGuardrail.TopicConfigProperty(
                        name="MedicalTopics",
                        definition="Medical advice",
                        examples=["What are the symptoms of diabetes?", "How can I treat a headache?","What is the best diet for weight loss?"],
                        type="DENY"
                    ),
                    guardrails.CfnGuardrail.TopicConfigProperty(
                        name="LegalTopics",
                        definition="Legal advice",
                        examples=["What are my rights if I'm arrested?", "How can I file for divorce?","What is the process for creating a will?"],
                        type="DENY"
                    ),
                ]
            ),
            sensitive_information_policy_config = guardrails.CfnGuardrail.SensitiveInformationPolicyConfigProperty(
                pii_entities_config=[
                    guardrails.CfnGuardrail.PiiEntityConfigProperty(
                        type="US_SOCIAL_SECURITY_NUMBER",
                        action="BLOCK"
                    )
                ],
            )
        )

        gr_id = guardrail.attr_guardrail_id
        gr_ver = guardrails.CfnGuardrailVersion(
            self, "GuardrailVersion",
            guardrail_identifier=gr_id,
            description="Initial version of the Chatstack Guardrail",
        )
        gr_ver.add_dependency(guardrail)

        self.guardrail_id = gr_id
        self.guardrail_version = gr_ver.attr_version

        Tags.of(guardrail).add("example", "chatstack")
        CfnOutput(self, "GuardrailIdOutput", value=self.guardrail_id)
        CfnOutput(self, "GuardrailVersionOutput", value=self.guardrail_version)