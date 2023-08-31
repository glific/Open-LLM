import os
import django
import secrets
import string

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .chains.functions import detect_languages_chain
from .chains.chat import run_chat_chain
from .chains import embeddings
from .data import loader


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm.settings")

django.setup()


@api_view(["POST"])
def create_chat(request):
    prompt = request.data.get("prompt").strip()
    session_id = (request.data.get("session_id") or generate_short_id()).strip()

    language_detector = detect_languages_chain()
    languages = language_detector.run(prompt)

    print(f"Language detector chain result: {languages}")

    primary_language = languages["primary_detected_language"]
    english_translation_prompt = languages["translation_to_english"]

    response = run_chat_chain(
        prompt=prompt,
        session_id=session_id,
        primary_language=primary_language,
        english_translation_prompt=english_translation_prompt,
    )

    print(f"Chat chain result: {response}")

    # Remove source documents from response since we have verbose logging setup
    del response["source_documents"]

    return Response(
        {
            "answer": response["result"],
            "chat_history": response["chat_history"],
            "session_id": session_id,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def create_embeddings(_):
    chunks = loader.load_pdfs()
    embeddings.create_embeddings(chunks=chunks, index_name="embeddings")

    return Response(
        f"Created embeddings index",
        status=status.HTTP_201_CREATED,
    )


def generate_short_id(length=6):
    alphanumeric = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphanumeric) for _ in range(length))
