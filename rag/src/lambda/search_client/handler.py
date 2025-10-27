import os 
import json
import boto3
import logging
import base64
from typing import Dict, List
from pinecone import Pinecone as pinecone

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

BEDROCK_REGION = os.getenv("BEDROCK_REGION", "us-east-1")
# Embedding Model
MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBED_DIM = int(os.getenv("EMBED_DIM", "1024"))
TOP_K = int(os.getenv("TOP_K", "5"))
MIN_SCORE = 0.30 # Minimum threshold score
KEEP_N = 2 # Client Side results

PINECONE_SECRET_NAME = os.getenv("PINECONE_SECRET_NAME")


# Foundation Model
NOVA_MODEL = "amazon.nova-micro-v1:0"
bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

NAMESPACE_DESCRIPTORS = {
  "movies":  "Contains names of movies and the plot of the movie",
  "reviews": "Contains user provided reviews for a movie"
}

# This section is for the demo to demostrate the namespace to search. This can be stored in a database
# 
def titan_embed_one(text: str, dims: int = EMBED_DIM, normalize: bool = True):
    body = {"inputText": text, "dimensions": dims, "normalize": normalize}
    resp = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )
    payload = json.loads(resp["body"].read())
    embs = payload.get("embedding", [])
    print("Embedding vector:", embs)
    return embs

def embed_descriptors(descs: Dict[str, str]) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = {}
    for ns, text in descs.items():
        text = (text or "").strip()
        if not text:
            continue
        out[ns] = titan_embed_one(text, dims=EMBED_DIM, normalize=True)
    return out

def dot(u: List[float], v: List[float]) -> float:
    return sum(a*b for a, b in zip(u, v))

# There are 2 namepsace. Determine which one to query
def pick_namespace_for_query(query_text: str) -> str:
    """Embed the query and choose the namespace with highest cosine similarity."""
    q_vec = titan_embed_one(query_text, dims=EMBED_DIM, normalize=True)
    best_ns, best_score = "", float("-inf")
    for ns, vec in NAMESPACE_EMBEDS.items():
        score = dot(q_vec, vec)  # cosine since normalized
        if score > best_score:
            best_ns, best_score = ns, score
    return best_ns

# Query the namespace in pinecone
def pinecone_query_by_namespace(query_text: str, namespace: str, top_k: int = TOP_K):
    """Embed the query once, then query Pinecone filtered to the chosen namespace."""
    q_vec = titan_embed_one(query_text, dims=EMBED_DIM, normalize=True)
    result = index.query(
        vector=q_vec,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace,
    )
    matches = (result.matches or [])
    matches = [m for m in matches if (m.score or 0) >= MIN_SCORE]
    matches.sort(key=calculate, reverse=True)
    return matches[:KEEP_N]

def build_context(matches) -> str:
    """Turn Pinecone matches into a readable context block for Nova."""
    lines = []
    for m in matches:
        md = getattr(m, "metadata", {}) or {}
        title = md.get("title") or md.get("name") or m.id
        text = md.get("text") or md.get("chunk") or ""
        lines.append(f"- {title}: {text}")
    return "\n".join(lines)

# Cached globally
print("Cold start: embedding namespace descriptors...")
NAMESPACE_EMBEDS = embed_descriptors(NAMESPACE_DESCRIPTORS)
print("Embedded:", {k: len(v) for k, v in NAMESPACE_EMBEDS.items()}) 


def _response(status: int, message=None):
    return {
        'statusCode': status,
        'body': json.dumps({'message': message}),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    }

def _parse_event(event):
    body = event.get('body')
    if body:
        try:
            if event.get('isBase64Encoded'):
                body = base64.b64decode(body).decode('utf-8')
            return json.loads(body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
            return None
    return None


def _get_API_key(PINECONE_SECRET_NAME):
    sm = boto3.client("secretsmanager")
    resp = sm.get_secret_value(SecretId=PINECONE_SECRET_NAME)
    secret = resp.get("SecretString") or resp["SecretBinary"]
    if isinstance(secret, (bytes, bytearray)):
        secret = secret.decode()
    pinecone_api_key = json.loads(secret) if secret.startswith("{") else secret
    return pinecone_api_key

# Fetch the api key during startup and get pine cone index
pinecone_api_key = _get_API_key(PINECONE_SECRET_NAME)
pc = pinecone(api_key=pinecone_api_key)
index = pc.Index('rag-index')


def calculate(m):
    return m.score

def lambda_handler(event, context):

    best = None
    context_text = ""

    body = _parse_event(event)

    query = body.get('message')
    if not query:
        return _response(400, "Missing 'query' in request body")

    namespace = pick_namespace_for_query(query.strip())
    result = pinecone_query_by_namespace(namespace=namespace, query_text=query.strip(), top_k=TOP_K)
    if not result:
        # Not invoking the model if no confident matches found
        return _response(200, f"No confident matches for movie {query} found.")
    else:
        try:
            best = max(result, key=calculate)
            context_text = build_context([best])  
        except Exception as e:
            print("calculate() failed, falling back to .score:", e)
            best = max(result, key=lambda m: (m.score or 0))
    # sort descending by score and pick the top one
        print("Best match ID:", best.id)
        print("Best score:", best.score)
        print("Metadata:", best.metadata)

    # Defaults
    max_tokens = 1024
    temperature = 0.3
    top_p = 0.9
    if namespace == "movies":
        system = f"""You are a good story teller and provide a helpful summary to a movie plot. 
        You provide you summary to the movie as covering the following details. 1/ Where the story takes place? 
        2/ Who are the main charatcters? 3/ What are the main challenges or conflicts the characters face? 
        4/ WWhat is the ultimate goal or quest the characters are on? 
        You will provide your response as a narrative with the movie being summarized 
        If you were not provided any data, say you dont have the movie in your database. 
        You are ONLY allowed to use the text inside the CONTEXT block.
        """
    else:
        system = f"""You are a helpful assistant and provide a rating to a movie review.
        Your rating for the movie are based on the feedback provided by the users
        If you were not provided any data, you cann provide a sentiment analysis.
        You are ONLY allowed to use the text inside the CONTEXT block.
        """

    prompt = f"Provide a summary for {context_text}"

    kwargs = {
        'modelId':NOVA_MODEL,
        'system' : [
            {
                'text': system
            }
        ],
        'messages':[
            {
                'role': 'user',
                'content': [{'text': prompt}]
            }
        ],
        'inferenceConfig':{
            'maxTokens': max_tokens,
            'temperature': temperature,
            'topP': top_p
        },
    }

    response = bedrock.converse(**kwargs)
    print("Response from model: ", response)

    return _response(200, response['output']['message']['content'][0]['text'])
