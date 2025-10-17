#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infrastructure.infrastructure_stack import InfrastructureStack
from infrastructure.guardrails import GuardrailsStack


app = cdk.App()
guardrails = GuardrailsStack(app, "ChatGuardrailStack",)

InfrastructureStack(app, 
                    "InfrastructureStack",
                    guardrail_id=guardrails.guardrail_id, 
                    guardrail_version=guardrails.guardrail_version)

app.synth()
