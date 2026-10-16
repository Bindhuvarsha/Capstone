"""
MigrateIQ Ingestion Processor CLI
Usage: python -m app.ingestion.processor DATA --wipe
"""

import sys
import argparse
from app.ingestion.loader import DocumentLoader
from app.ingestion.vector_store import VectorStore

def run_ingestion(data_dir: str = "DATA", wipe: bool = False):
    print(f"[*] Starting MigrateIQ Knowledge Base Ingestion from: {data_dir}")
    store = VectorStore()

    if wipe:
        print("[!] --wipe flag detected. Resetting existing vector store collection...")
        store.wipe()

    loader = DocumentLoader(data_dir=data_dir)
    documents = loader.load_documents()

    if not documents:
        print(f"[!] No valid documents found in directory: {data_dir}")
        return

    total_chunks = []
    for doc in documents:
        chunks = doc.get("chunks", [])
        total_chunks.extend(chunks)
        print(f" -> Processed '{doc['filename']}': {len(chunks)} chunks with metadata: topic='{doc['metadata'].get('topic')}', source='{doc['metadata'].get('source')}'")

    store.add_chunks(total_chunks)
    print(f"[+] Ingestion complete! Successfully indexed {len(total_chunks)} chunks across {len(documents)} documents.")
    print(f"[+] Total indexed store size: {store.count()} chunks.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MigrateIQ Document Ingestion Pipeline")
    parser.add_argument("data_dir", nargs="?", default="DATA", help="Path to documents directory (default: DATA)")
    parser.add_argument("--wipe", action="store_true", help="Wipe and recreate collection before ingesting")

    args = parser.parse_args()
    run_ingestion(data_dir=args.data_dir, wipe=args.wipe)
