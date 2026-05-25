from openai import OpenAI

from .config import Settings


class TEIEmbeddingFunction:
    """Calls the HuggingFace TEI OpenAI-compatible endpoint in batches of 8."""

    def __init__(self, settings: Settings) -> None:
        self._client = OpenAI(base_url=f"{settings.tei_base_url}/v1", api_key="not-needed")
        self._model = settings.tei_model

    def name(self) -> str:
        return "tei-embedding-function"

    def __call__(self, input: list[str]) -> list[list[float]]:
        result: list[list[float]] = []
        for i in range(0, len(input), 8):
            resp = self._client.embeddings.create(input=input[i : i + 8], model=self._model)
            result.extend(e.embedding for e in resp.data)
        return result