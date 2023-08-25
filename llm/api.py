import os
import django
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .chains.chat import run_chat_chain
from .chains import embeddings
from .data import loader


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm.settings")

django.setup()


@api_view(["POST"])
def create_chat(request):
    question = request.data.get("question").strip()

    answer = run_chat_chain(question)

    return Response(
        {"answer": answer},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def create_embeddings(request):
    document_file_name = request.data.get("file_name").strip()

    chunks = loader.load_pdf(document_file_name)
    embeddings.create_embeddings(chunks, document_file_name)

    return Response(
        f"Created {document_file_name} index",
        status=status.HTTP_201_CREATED,
    )