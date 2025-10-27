import os 
import json
import boto3
import math
from pinecone import Pinecone as pinecone
from pinecone import ServerlessSpec
from typing import List


bedrock = boto3.client("bedrock-runtime", region_name=os.getenv("BEDROCK_REGION", "us-east-1"))
TITAN_V2_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBED_DIM = int(os.getenv("EMBED_DIM", "1024"))
MAX_BATCH = 2000  # Max texts per batch for embedding. Titan supports 2048 texts per request.

def _get_API_key(PINECONE_SECRET_NAME):
    sm = boto3.client("secretsmanager")
    resp = sm.get_secret_value(SecretId=PINECONE_SECRET_NAME)
    secret = resp.get("SecretString") or resp["SecretBinary"]
    if isinstance(secret, (bytes, bytearray)):
        secret = secret.decode()
    pinecone_api_key = json.loads(secret) if secret.startswith("{") else secret
    return pinecone_api_key

def _get_records(bucket_name, file_name):
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    records = response["Body"].read().decode("utf-8").split("\n")
    records = [json.loads(record) for record in records if record]
    return records

def build_text(record):
    #Combining title and text into one string for embedding."""
    title = (record.get("title") or "").strip()
    text = (record.get("text") or "").strip()
    if title or text:
        return f"{title}\n\n{text}"
    return ""


def titan_v2_embed(texts, dims=EMBED_DIM, normalize=True) -> List[List[float]]:
    #Call Amazon Titan v2 model for each text to get embedding vector (list of floats).
    embeddings = []
    for t in texts:
        if not t:         # skip empties
            out.append([])
            continue
        body = {"inputText": t, "dimensions": dims, "normalize": normalize}
        response = bedrock.invoke_model(
            modelId=TITAN_V2_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        payload = json.loads(response["body"].read())
        record = payload.get("embedding", [])
        if record and isinstance(record, list) and isinstance(record[0], dict):
            record = record[0].get("embedding", [])
        embeddings.append(record)
    return embeddings


def prepare_records_for_embeddings(records):
    vectorized_records = []
    texts = [build_text(r) for r in records]
    # Filter out empty texts and keep track of their indices
    non_empty = [(i, t) for i, t in enumerate(texts) if t]
    if not non_empty:
        return []

    input_texts = [t for _, t in non_empty]
    print(input_texts)
    embeddings = titan_v2_embed(input_texts, dims=EMBED_DIM, normalize=True)
    print(embeddings)
    
    for (idx, _), vec in zip(non_empty, embeddings):
        record = records[idx]
        metadata = {
            k: str(v)
            for k, v in record.items()
            if k not in ("repo")  # skip large fields
        }
        vectorized_records.append({
            "id": str(record.get("id")),
            "values": vec,
            "metadata": metadata
        })

    return vectorized_records

def _upsert_records_by_namespace(index, records):
    _namespace = list({item["repo"] for item in records})   
    for namespace in _namespace:
        ns_records = [r for r in records if r["repo"] == namespace]
        records = prepare_records_for_embeddings(ns_records)
        index.upsert(namespace=namespace, vectors=records)

def lambda_handler(event, context):
    PINECONE_SECRET_NAME = os.getenv("PINECONE_SECRET_NAME")
    DATA_BUCKET_NAME = os.getenv("DATA_BUCKET_NAME")
    MOVIES_DATA_FILE = os.getenv("MOVIES_DATA_FILE")
    REVIEWS_DATA_FILE = os.getenv("REVIEWS_DATA_FILE")
    pinecone_api_key = _get_API_key(PINECONE_SECRET_NAME)
    movie_records = _get_records(DATA_BUCKET_NAME, MOVIES_DATA_FILE)
    review_records = _get_records(DATA_BUCKET_NAME, REVIEWS_DATA_FILE)

    #Create Index in Pinecone
    pc = pinecone(api_key=pinecone_api_key)
    index_name = "rag-index"
    if not pc.has_index(index_name):
        pc.create_index(
            name=index_name,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            dimension=1024,
            metric="cosine",
        )
    index = pc.Index(index_name)

    # --- ingest (per-namespace) ---
    _upsert_records_by_namespace(index, movie_records)
    _upsert_records_by_namespace(index, review_records)

    return {"statusCode": 200, "body": json.dumps({"message": "Records Uploaded to Pinecone"})}
