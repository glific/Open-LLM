import os
from typing import List

from django.conf import settings

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document

EMBEDDINGS_PATH = os.path.join(
    settings.BASE_DIR,
    "llm",
    "data",
)


def create_embeddings(chunks: List[Document], index_name: str) -> FAISS:
    store = OpenAIEmbeddings()
    db = FAISS.from_documents(chunks, store)

    db.save_local(EMBEDDINGS_PATH, index_name)

    return db


def load_embeddings(index_name: str) -> FAISS:
    return FAISS.load_local(EMBEDDINGS_PATH, OpenAIEmbeddings(), index_name)


def get_retriever(language: str):
    return load_embeddings("embeddings").as_retriever()
