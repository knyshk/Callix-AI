import json
import time
import numpy as np
from app.intent.embedding_model import encode_text
from app.core.errors_catalog import UNKNOWN_INTENT

# load intent examples
with open("app/intent/intents.json", "r") as f:
    INTENTS = json.load(f)

intent_examples = []
intent_labels = []

# flatten dataset
for intent, phrases in INTENTS.items():
    for phrase in phrases:
        intent_examples.append(phrase)
        intent_labels.append(intent)

# compute embeddings once
intent_vectors = encode_text(intent_examples)


def detect_intent(text: str):

    start = time.perf_counter()

    # encode user sentence
    query_vector = encode_text([text])[0]

    # cosine similarity via dot product
    similarities = np.dot(intent_vectors, query_vector)

    best_index = similarities.argmax()
    best_score = similarities[best_index]

    latency = (time.perf_counter() - start) * 1000
    print("INTENT_LATENCY_MS:", round(latency, 2))

    if best_score < 0.35:
        return UNKNOWN_INTENT

    return {
        "intent": intent_labels[best_index],
        "score": float(best_score)
    }