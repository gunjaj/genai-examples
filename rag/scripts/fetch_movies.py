from datasets import load_dataset
import json, os

os.makedirs("data", exist_ok=True)
ds = load_dataset("vishnupriyavr/wiki-movie-plots-with-summaries", split="train").select(range(10))

with open("data/movies.jsonl","w") as f:
    for r in ds:
        title = r.get("Title") or r.get("title")
        text  = r.get("Plot") or r.get("plot")
        if text:
            f.write(json.dumps({
                "repo": "movies",
                "id": title,
                "title": title,
                "text": text[:8000]
            }) + "\n")

print("✅ wrote data/movies.jsonl")