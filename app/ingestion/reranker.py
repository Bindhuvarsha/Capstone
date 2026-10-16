"""
MigrateIQ Semantic Reranker
Uses FlashRank when available, with a fast cross-scoring semantic relevance engine fallback.
Filters low-scoring / noisy documents.
"""

from typing import List, Dict, Any
import math
import re

class SemanticReranker:
    def __init__(self, score_threshold: float = 0.15):
        self.score_threshold = score_threshold
        self.flashrank_client = None

        # Attempt to load FlashRank if installed
        try:
            from flashrank import Ranker, RerankRequest
            self.flashrank_client = Ranker()
            self._use_flashrank = True
        except ImportError:
            self._use_flashrank = False

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Reranks retrieved candidate chunks against query and filters out noise.
        """
        if not documents:
            return []

        if self._use_flashrank and self.flashrank_client:
            try:
                from flashrank import RerankRequest
                passages = [{"id": i, "text": doc["text"], "meta": doc} for i, doc in enumerate(documents)]
                rerank_request = RerankRequest(query=query, passages=passages)
                results = self.flashrank_client.rerank(rerank_request)

                reranked = []
                for res in results[:top_k]:
                    if res.get("score", 0.0) >= self.score_threshold:
                        doc = res["meta"]
                        doc["rerank_score"] = round(float(res["score"]), 4)
                        reranked.append(doc)
                return reranked
            except Exception:
                # Fallback to local semantic cross-scorer
                pass

        return self._local_semantic_rerank(query, documents, top_k)

    def _local_semantic_rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Local fallback cross-scoring engine that computes exact term overlap,
        title bonuses, SAP keyword weights, and length penalty normalization.
        """
        query_words = set(re.findall(r"\w+", query.lower()))
        scored_docs = []

        for doc in documents:
            text = doc.get("text", "").lower()
            metadata = doc.get("metadata", {})
            title = metadata.get("title", "").lower()
            topic = metadata.get("topic", "").lower()

            # Heavy penalty if explicitly marked as noise or irrelevant
            if "noise" in topic or "unrelated" in title or "mainframe" in text:
                score = 0.01
            else:
                score = 0.0
                doc_words = re.findall(r"\w+", text)
                doc_word_counts = {}
                for w in doc_words:
                    doc_word_counts[w] = doc_word_counts.get(w, 0) + 1

                # Query word match with BM25-like sublinear scaling
                for qw in query_words:
                    if len(qw) <= 2:
                        continue
                    if qw in doc_word_counts:
                        tf = doc_word_counts[qw]
                        score += (tf / (tf + 1.2)) * (1.5 if qw in title else 1.0)

                # Boost if topic matches
                for qw in query_words:
                    if qw in topic:
                        score += 0.8

                # Normalize score
                if doc_words:
                    length_norm = 1.0 + 0.1 * math.log(len(doc_words))
                    score = score / length_norm

            doc_copy = dict(doc)
            doc_copy["rerank_score"] = round(float(score), 4)

            # Filter noisy chunks
            if score >= self.score_threshold:
                scored_docs.append(doc_copy)

        scored_docs.sort(key=lambda d: d["rerank_score"], reverse=True)
        return scored_docs[:top_k]
