import json
import os
import time
from dataclasses import dataclass

import chromadb

from .config import Settings
from .embedding import TEIEmbeddingFunction


@dataclass
class KnowledgeBase:
    collection: chromadb.Collection
    emb: TEIEmbeddingFunction

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        embedding = self.emb([query])[0]
        results = self.collection.query(query_embeddings=[embedding], n_results=top_k)
        out = []
        for i in range(len(results["ids"][0])):
            item = results["metadatas"][0][i].copy()
            item["text"] = results["documents"][0][i]
            distances = results.get("distances")
            item["score"] = float(distances[0][i]) if distances else 0.0
            out.append(item)
        return out


def _load_jsonl(path: str) -> tuple[list[str], list[dict]]:
    texts: list[str] = []
    meta: list[dict] = []
    if not os.path.exists(path):
        return texts, meta
    with open(path, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            texts.append(item["text"])
            meta.append({k: v for k, v in item.items() if k != "text"})
    return texts, meta


def _connect_chroma(settings: Settings) -> chromadb.HttpClient:
    for attempt in range(1, 11):
        try:
            client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
            client.heartbeat()
            return client
        except Exception:
            print(f"Waiting for ChromaDB... ({attempt}/10)")
            time.sleep(2)
    raise ConnectionError(
        f"Could not connect to ChromaDB at {settings.chroma_host}:{settings.chroma_port}"
    )


def init_knowledge_base(settings: Settings) -> KnowledgeBase:
    emb = TEIEmbeddingFunction(settings)
    client = _connect_chroma(settings)
    collection = client.get_or_create_collection("cyber_knowledge", embedding_function=emb)
    texts, meta = _load_jsonl(settings.kb_path)
    if collection.count() == 0 and texts:
        collection.add(
            ids=[f"id_{i}" for i in range(len(texts))],
            documents=texts,
            metadatas=meta,
            embeddings=emb(texts),
        )
    return KnowledgeBase(collection=collection, emb=emb)