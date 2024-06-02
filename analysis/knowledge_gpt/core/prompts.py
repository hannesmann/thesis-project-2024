# flake8: noqa
from langchain_core.prompts import PromptTemplate

## Use a shorter template to reduce the number of tokens in the prompt
template = """Use only the provided document and do not attempt to fabricate an answer.

QUESTION: {question}
=========
{summaries}
=========
FINAL ANSWER:"""

STUFF_PROMPT = PromptTemplate(
    template=template, input_variables=["summaries", "question"]
)
