from typing import List
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from analysis.knowledge_gpt.core.debug import FakeChatModel
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI


def pop_docs_upto_limit(
    query: str, chain: StuffDocumentsChain, docs: List[Document], max_len: int
) -> List[Document]:
    """Pops documents from a list until the final prompt length is less
    than the max length."""

    token_count: int = chain.prompt_length(docs, question=query)  # type: ignore

    while token_count > max_len and len(docs) > 0:
        docs.pop()
        token_count = chain.prompt_length(docs, question=query)  # type: ignore

    return docs


def get_llm(model: str, **kwargs) -> BaseChatModel:
    if model == "debug":
        return FakeChatModel()

    if "gpt" in model:
        return ChatOpenAI(model=model, **kwargs)  # type: ignore

    raise NotImplementedError(f"Model {model} not supported!")
