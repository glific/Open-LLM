import os
from typing import List

from django.conf import settings
from langchain.document_loaders import PyPDFLoader
from langchain.schema import Document


def load_pdf(file_name: str) -> List[Document]:
    path = os.path.join(settings.BASE_DIR, "llm", "data", f"{file_name}")
    loader = PyPDFLoader(path)
    chunks = loader.load_and_split()

    return chunks
