"""
MigrateIQ Document Loader & Chunker
Parses SAP simplification items and migration documentation, extracting metadata and chunking.
"""

import os
import re
from typing import List, Dict, Any

class DocumentLoader:
    def __init__(self, data_dir: str = "DATA"):
        self.data_dir = data_dir

    def load_documents(self) -> List[Dict[str, Any]]:
        """
        Loads all markdown and text documents from data_dir.
        Extracts metadata: source, topic, release, title.
        """
        documents = []
        if not os.path.exists(self.data_dir):
            return documents

        for root, _, files in os.walk(self.data_dir):
            for file in files:
                if file.endswith((".md", ".txt")):
                    full_path = os.path.join(root, file)
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    metadata = self._extract_metadata(content, file)
                    chunks = self._chunk_document(content, metadata)
                    documents.append({
                        "filename": file,
                        "path": full_path,
                        "metadata": metadata,
                        "content": content,
                        "chunks": chunks
                    })
        return documents

    def _extract_metadata(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Extracts source, topic, release, and title metadata from header comments or lines.
        """
        metadata = {
            "source": "SAP Documentation",
            "topic": "General",
            "release": "S/4HANA",
            "title": filename.replace("_", " ").replace(".md", "").title()
        }

        # Check for YAML-like or markdown bullets: - **Source**: ...
        source_m = re.search(r"\*\*Source\*\*:\s*([^\n\r]+)", text, re.IGNORECASE)
        if source_m:
            metadata["source"] = source_m.group(1).strip()

        topic_m = re.search(r"\*\*Topic\*\*:\s*([^\n\r]+)", text, re.IGNORECASE)
        if topic_m:
            metadata["topic"] = topic_m.group(1).strip()

        release_m = re.search(r"\*\*S/4HANA Release\*\*:\s*([^\n\r]+)", text, re.IGNORECASE)
        if release_m:
            metadata["release"] = release_m.group(1).strip()

        # Check title from first H1 header
        h1_m = re.search(r"^#\s+([^\n\r]+)", text, re.MULTILINE)
        if h1_m:
            metadata["title"] = h1_m.group(1).strip()

        return metadata

    def _chunk_document(self, text: str, metadata: Dict[str, Any], chunk_size: int = 500) -> List[Dict[str, Any]]:
        """
        Splits document by Markdown headings (##) or paragraphs while preserving metadata.
        """
        sections = re.split(r"(?m)^(?=##\s+)", text)
        chunks = []

        chunk_id = 0
        for sec in sections:
            sec_clean = sec.strip()
            if not sec_clean:
                continue

            # Sub-split large sections if needed
            if len(sec_clean) > chunk_size * 2:
                paragraphs = sec_clean.split("\n\n")
                current_p = ""
                for p in paragraphs:
                    if len(current_p) + len(p) < chunk_size * 2:
                        current_p += "\n\n" + p
                    else:
                        if current_p.strip():
                            chunks.append({
                                "chunk_id": f"{metadata['title']}_{chunk_id}",
                                "text": current_p.strip(),
                                "metadata": {**metadata, "section": metadata["title"]}
                            })
                            chunk_id += 1
                        current_p = p
                if current_p.strip():
                    chunks.append({
                        "chunk_id": f"{metadata['title']}_{chunk_id}",
                        "text": current_p.strip(),
                        "metadata": {**metadata, "section": metadata["title"]}
                    })
                    chunk_id += 1
            else:
                chunks.append({
                    "chunk_id": f"{metadata['title']}_{chunk_id}",
                    "text": sec_clean,
                    "metadata": {**metadata, "section": metadata["title"]}
                })
                chunk_id += 1

        return chunks
