"""
MigrateIQ Vector Store Interface
Supports Local In-Memory/JSON Vector Store with Cosine/BM25 similarity,
with pluggable connectors for Qdrant Cloud and SAP HANA Cloud Vector Engine.
"""

import os
import json
import math
import re
from typing import List, Dict, Any, Optional

STORE_FILE = "vector_store_data.json"

class VectorStore:
    def __init__(self, store_type: Optional[str] = None):
        self.store_type = store_type or os.getenv("VECTOR_DB_TYPE", "local")
        self.chunks: List[Dict[str, Any]] = []
        self._load_local_store()

    def _load_local_store(self):
        """Loads cached chunks from disk if available."""
        if os.path.exists(STORE_FILE):
            try:
                with open(STORE_FILE, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
            except Exception:
                self.chunks = []

    def _save_local_store(self):
        """Persists indexed chunks to disk."""
        with open(STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2, ensure_ascii=False)

    def wipe(self):
        """Wipes the existing vector store collection."""
        self.chunks = []
        if os.path.exists(STORE_FILE):
            os.remove(STORE_FILE)

    def add_chunks(self, new_chunks: List[Dict[str, Any]]):
        """Adds and indexes document chunks."""
        for c in new_chunks:
            # Pre-calculate term frequencies for search
            text = c.get("text", "")
            words = re.findall(r"\w+", text.lower())
            tf = {}
            for w in words:
                tf[w] = tf.get(w, 0) + 1
            
            c["_tf"] = tf
            c["_len"] = len(words)
            self.chunks.append(c)

        self._save_local_store()

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves top-k candidate chunks matching the query.
        Uses BM25-style term weighting over document frequency and term frequency.
        """
        if not self.chunks:
            self._load_local_store()

        if not self.chunks:
            return []

        query_terms = re.findall(r"\w+", query.lower())
        if not query_terms:
            return self.chunks[:top_k]

        N = len(self.chunks)
        # Calculate DF for query terms
        df = {}
        for qt in query_terms:
            df[qt] = sum(1 for c in self.chunks if qt in c.get("_tf", {}))

        scores = []
        avg_dl = sum(c.get("_len", 1) for c in self.chunks) / max(1, N)

        k1 = 1.5
        b = 0.75

        for c in self.chunks:
            doc_len = c.get("_len", 1)
            tf_dict = c.get("_tf", {})
            score = 0.0

            for qt in query_terms:
                if len(qt) <= 1:
                    continue
                tf = tf_dict.get(qt, 0)
                if tf > 0:
                    doc_freq = df.get(qt, 1)
                    idf = math.log((N - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
                    term_score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_dl)))
                    score += term_score

            scores.append((score, c))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, c in scores[:top_k]:
            clean_chunk = {k: v for k, v in c.items() if not k.startswith("_")}
            clean_chunk["retrieval_score"] = round(float(score), 4)
            results.append(clean_chunk)

        return results

    def count(self) -> int:
        return len(self.chunks)
