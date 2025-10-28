import json
from process import search_tfidf_weighted

def precision_at_k(results, relevant, k=10):
    hits = sum(1 for doc_id, _ in results[:k] if doc_id in relevant)
    return hits / k

def average_precision(results, relevant):
    hits, sum_prec = 0, 0
    for i, (doc_id, _) in enumerate(results):
        if doc_id in relevant:
            hits += 1
            sum_prec += hits / (i + 1)
    return sum_prec / len(relevant) if relevant else 0

def evaluate():
    with open("evaluation_queries.json", "r", encoding="utf-8") as f:
        queries = json.load(f)

    precisions, maps = [], []

    for q in queries:
        df = search_tfidf_weighted(q["query"], min_score=0.0)
        results = [(idx, row["similarity_score"]) for idx, row in df.iterrows()]

        p10 = precision_at_k(results, q["relevant"], 10)
        ap = average_precision(results, q["relevant"])
        precisions.append(p10)
        maps.append(ap)

        print(f"{q['query']}: P@10 = {p10:.2f}, AP = {ap:.2f}")

    print("\n📊 Mean Precision@10:", sum(precisions) / len(precisions))
    print("📊 MAP:", sum(maps) / len(maps))


if __name__ == "__main__":
    evaluate()
