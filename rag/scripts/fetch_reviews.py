from datasets import load_dataset, concatenate_datasets
import json, os, random

os.makedirs("data", exist_ok=True)

# Load all splits and merge
splits = [load_dataset("rotten_tomatoes", split=s) for s in ["train", "validation", "test"]]
ds = concatenate_datasets(splits)

# Shuffle for randomness
ds = ds.shuffle(seed=42)

# Optional: small subset (keeps cost low)
ds = ds.select(range(10))  # adjust as needed

label_map = {0: "negative", 1: "positive", 2: "neutral"}

with open("data/reviews.jsonl", "w", encoding="utf-8") as f:
    for i, r in enumerate(ds):
        text = (r.get("text") or "").strip()
        label = label_map.get(r.get("label"), "unknown")
        if not text:
            continue
        f.write(json.dumps({
            "repo": "reviews",
            "id": i,
            "title": label,
            "text": text[:8000]
        }) + "\n")

print("✅ wrote data/reviews.jsonl with mixed sentiment")
