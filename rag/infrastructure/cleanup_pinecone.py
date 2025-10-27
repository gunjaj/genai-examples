import os
import boto3
from pinecone import Pinecone

# --- CONFIG ---
index_name = "rag-index"      # Pinecone index name
NAMESPACES = ["movies", "reviews"]  # namespaces used

def main():
    secret_name="rag/pinecone/api-key"
    client = boto3.client("secretsmanager", region_name="us-east-1")
    API_KEY = client.get_secret_value(SecretId=secret_name).get("SecretString")
    print("API_KEY", API_KEY)
    pc = Pinecone(api_key=API_KEY)
    print("Deleting index", index_name)
    index = pc.Index(index_name)
    # Delete all demo namespaces
    for ns in NAMESPACES:
        try:
            print(f"Deleting namespace: {ns}")
            index.delete(namespace=ns, delete_all=True)
        except Exception as e:
            print(f"⚠️ Failed to delete namespace {ns}: {e}")
    pc.delete_index(index_name)
    print("✅ Cleanup complete!")

if __name__ == "__main__":
    main()