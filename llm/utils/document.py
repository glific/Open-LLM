from typing import List
from langchain_community.document_loaders.base import BaseLoader
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
from langchain.schema import Document


class OpenLLMDocumentLoader(BaseLoader):
    def __init__(self, file_path: str, content_type: str):
        self.file_path = file_path
        self.file_type = content_type
        self.loader: BaseLoader = None

        if content_type == "text/plain":
            self.loader = TextLoader(file_path)
        elif content_type == "application/pdf":
            self.loader = PyPDFLoader(file_path)
        elif content_type == "text/markdown":
            self.loader = UnstructuredMarkdownLoader(file_path, mode="elements")
        elif (
            content_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            self.loader = Docx2txtLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {content_type}")

    def chunks(self) -> List[Document]:
        return self.loader.load_and_split()
