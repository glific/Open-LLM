import os
import secrets
import string

import django
from django.db import connection
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from pypdf import PdfReader
import openai

from .chains.embeddings import get_pgvector_idx

from .chains.functions import detect_languages_chain
from .chains.chat import run_chat_chain
from .models import Organization


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm.settings")

django.setup()


@api_view(["POST"])
def create_chat(request):
    try:
        organization = current_organization(request)
        if not organization:
            return Response(
                f"Invalid API key",
                status=status.HTTP_404_NOT_FOUND,
            )

        prompt = request.data.get("prompt").strip()
        gpt_model = request.data.get("gpt_model", "gpt-3.5-turbo").strip()
        session_id = (request.data.get("session_id") or generate_short_id()).strip()

        language_detector = detect_languages_chain(gpt_model)
        languages = language_detector.run(prompt)

        print(f"Language detector chain result: {languages}")

        primary_language = languages["primary_detected_language"]
        english_translation_prompt = languages["translation_to_english"]

        response = run_chat_chain(
            prompt=prompt,
            session_id=session_id,
            primary_language=primary_language,
            english_translation_prompt=english_translation_prompt,
            organization_id=organization.id,
            gpt_model=gpt_model,
        )

        print(f"Chat chain result: {response}")

        del response["source_documents"]

        return Response(
            {
                "answer": response["result"],
                "chat_history": response["chat_history"],
                "session_id": session_id,
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as error:
        print(f"Error: {error}")
        return Response(
            f"Something went wrong",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class FileUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, format=None):
        try:
            org = current_organization(request)
            if not org:
                return Response(
                    f"Invalid API key",
                    status=status.HTTP_404_NOT_FOUND,
                )

            if "file" not in request.data:
                raise ValueError("Empty content")

            file = request.data["file"]

            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text().replace("\n", " ")

                response = openai.Embedding.create(
                    model="text-embedding-ada-002", input=page_text
                )

                embeddings = response["data"][0]["embedding"]
                if len(embeddings) != 1536:
                    raise ValueError(f"Invalid embedding length: #{len(embeddings)}")

                # TODO: uncomment after possible move away from langchain to simplify code
                # Embedding.objects.create(
                #     source_name=file.name,
                #     original_text=page_text,
                #     text_vectors=embeddings,
                #     organization=org,
                # )

                pgvector_idx = get_pgvector_idx()
                pgvector_idx.add_texts(
                    texts=[page_text], metadatas=[{"organization_id": org.id}]
                )

            return JsonResponse({"status": "file upload successful"})
        except ValueError as error:
            return Response(
                f"Invalid file: {error}",
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as error:
            print(f"Error: {error}")
            return Response(
                f"Something went wrong",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["DELETE"])
def delete_embeddings(request):
    try:
        org = current_organization(request)
        if not org:
            return Response(
                f"Invalid API key",
                status=status.HTTP_404_NOT_FOUND,
            )

        # TODO: uncomment after possible move away from langchain to simplify code
        # Embedding.objects.filter(organization_id=org.id).delete()

        # Langchain pgvector connector doesn't have affordance for deleting all vectors by metadata filter so we use raw SQL to do this
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM langchain_pg_embedding WHERE cmetadata->>'organization_id' = %s",
                [str(org.id)],
            )

        return Response(
            f"Deleted all embeddings",
            status=status.HTTP_201_CREATED,
        )
    except Exception as error:
        print(f"Error: {error}")
        return Response(
            f"Something went wrong",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def set_system_prompt(request):
    try:
        system_prompt = request.data.get("system_prompt").strip()
        org = current_organization(request)
        if not org:
            return Response(
                f"Invalid API key",
                status=status.HTTP_404_NOT_FOUND,
            )

        Organization.objects.filter(id=org.id).update(system_prompt=system_prompt)

        return Response(
            f"Updated System Prompt",
            status=status.HTTP_201_CREATED,
        )
    except Exception as error:
        print(f"Error: {error}")
        return Response(
            f"Something went wrong",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def current_organization(request):
    api_key = request.headers.get("Authorization")
    if not api_key:
        return None

    try:
        return Organization.objects.get(api_key=api_key)
    except Organization.DoesNotExist:
        return None


def generate_short_id(length=6):
    alphanumeric = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphanumeric) for _ in range(length))
