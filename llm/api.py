import os
import django
import secrets
import string

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
    prompt = request.data.get("prompt").strip()
    session_id = (request.data.get("session_id") or generate_short_id()).strip()

    answer = run_chat_chain(prompt=prompt, session_id=session_id)

    return Response(
        {
            "answer": answer,
            "session_id": session_id,
        },
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


def generate_short_id(length=6):
    alphanumeric = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphanumeric) for _ in range(length))
