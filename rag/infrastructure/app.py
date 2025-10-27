#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infrastructure.stacks.pinecone_index_stack import PineconeIndexStack
from infrastructure.stacks.client_stack import ClientStack
from dotenv import load_dotenv
from pathlib import Path


app = cdk.App()
        # Load local .env file
root_dotenv = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=root_dotenv)

# Get the key
pinecone_api_key = os.getenv("PINECONE_API_KEY")

if not pinecone_api_key:
    raise ValueError("Missing PINECONE_API_KEY in .env")

pineconestack = PineconeIndexStack(app, "PineconeIndexStack", pinecone_api_key=pinecone_api_key)
ClientStack(app, "ClientStack", pinecone_secret_val = pineconestack.pinecone_secret, lambda_layer = pineconestack.layer)

app.synth()