"""RAGAS eval over data/eval_dataset.jsonl.

Runs faithfulness, context_recall, and answer_relevancy on the
knowledge/application questions. Calculation questions are skipped —
they're tool-use, not RAG.

Requires: ChromaDB + TEI running, GROQ_API_KEY set.
"""

import argparse
import json
import sys
from pathlib import Path

from datasets import Dataset
from langchain_groq import ChatGroq
from langchain_openai import OpenAIEmbeddings
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, context_recall, faithfulness

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import prompts  # noqa: E402
from agent.config import Settings as AgentSettings  # noqa: E402
from mcp_server.config import Settings as KBSettings  # noqa: E402
from mcp_server.knowledge_base import init_knowledge_base  # noqa: E402

EVAL_PATH = ROOT / "data" / "eval_dataset.jsonl"
RESULTS_DIR = ROOT / "data"

LLM_MODEL = "llama-3.3-70b-versatile"
TOP_K = 5


def load_eval_set(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_rag_samples(kb, llm, rows: list[dict], rag_prompt: str) -> dict:
    questions, contexts, answers, ground_truths, ids = [], [], [], [], []
    for i, row in enumerate(rows, 1):
        print(f"[{i}/{len(rows)}] {row['id']}  {row['question'][:70]}")
        retrieved = kb.retrieve(row["question"], top_k=TOP_K)
        ctx_texts = [r["text"] for r in retrieved]
        prompt = rag_prompt.format(context="\n\n---\n\n".join(ctx_texts), question=row["question"])
        answer = llm.invoke(prompt).content
        questions.append(row["question"])
        contexts.append(ctx_texts)
        answers.append(answer)
        ground_truths.append(row["ground_truth"])
        ids.append(row["id"])
    return {
        "question": questions,
        "contexts": contexts,
        "answer": answers,
        "ground_truth": ground_truths,
        "id": ids,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run RAGAS eval against the project KB.")
    p.add_argument(
        "--prompt-version",
        default=None,
        help="Prompt version key (e.g. 'v1'). Defaults to Settings.prompt_version.",
    )
    p.add_argument(
        "--results",
        default=None,
        help="Output path. Defaults to data/eval_results_<version>.json.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    agent_s = AgentSettings()
    kb_s = KBSettings()
    if not agent_s.groq_api_key:
        sys.exit("GROQ_API_KEY is required")

    version = args.prompt_version or agent_s.prompt_version
    rag_prompt = prompts.eval_rag(version)
    results_path = Path(args.results) if args.results else RESULTS_DIR / f"eval_results_{version}.json"
    print(f"Prompt version: {version}\nResults will be written to: {results_path.relative_to(ROOT)}\n")

    kb = init_knowledge_base(kb_s)
    llm = ChatGroq(model=LLM_MODEL, temperature=0.1, groq_api_key=agent_s.groq_api_key)

    eval_set = load_eval_set(EVAL_PATH)
    rag_rows = [r for r in eval_set if r["category"] in ("knowledge", "application")]
    print(f"RAG eval on {len(rag_rows)}/{len(eval_set)} questions (skipping calculation)\n")

    samples = build_rag_samples(kb, llm, rag_rows, rag_prompt)
    ids = samples.pop("id")
    dataset = Dataset.from_dict(samples)

    embeddings = OpenAIEmbeddings(
        model=kb_s.tei_model,
        openai_api_base=f"{kb_s.tei_base_url}/v1",
        openai_api_key="not-needed",
        check_embedding_ctx_length=False,
    )
    ragas_llm = LangchainLLMWrapper(llm)
    ragas_emb = LangchainEmbeddingsWrapper(embeddings)

    print("\nScoring with RAGAS (faithfulness, context_recall, answer_relevancy)...\n")
    result = evaluate(
        dataset,
        metrics=[faithfulness, context_recall, answer_relevancy],
        llm=ragas_llm,
        embeddings=ragas_emb,
    )

    df = result.to_pandas()
    df.insert(0, "id", ids)
    df.insert(1, "prompt_version", version)

    print("\n=== Per-question scores ===")
    print(df[["id", "faithfulness", "context_recall", "answer_relevancy"]].to_string(index=False))

    print("\n=== Aggregate ===")
    agg = df[["faithfulness", "context_recall", "answer_relevancy"]].mean()
    for metric, score in agg.items():
        print(f"  {metric:20s} {score:.3f}")

    results_path.write_text(df.to_json(orient="records", indent=2), encoding="utf-8")
    print(f"\nSaved to {results_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()