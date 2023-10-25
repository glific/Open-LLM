import os
import django
import secrets
import string
import json

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from llm.chains.chat import context_prompt_messages
from pgvector.django import L2Distance
from .models import Organization

from django.http import JsonResponse
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from pypdf import PdfReader
from llm.models import Embedding, Message

import openai
from logging import basicConfig, INFO, getLogger


basicConfig(level=INFO)
logger = getLogger()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm.settings")

django.setup()

openai.api_key = os.getenv("OPENAI_API_KEY")


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

        # 1. Function calling to do language detection of the user's question (1st call to OpenAI)
        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=[
                {
                    "role": "user",
                    "content": f"Detect the languages in this text: {prompt}",
                }
            ],
            functions=[
                {
                    "name": "detect_languages",
                    "description": "Detecting language and other insights on a piece of user input text.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "language": {
                                "title": "Language",
                                "description": "The primary detected language e.g English, French, Hindi, etc",
                                "type": "string",
                            },
                            "confidence": {
                                "title": "Confidence",
                                "description": "Confidence level of the language detection from scale of 0 to 1",
                                "type": "number",
                            },
                            "english_translation": {
                                "title": "English translation",
                                "description": "English translation of the user input text if not in English",
                                "type": "string",
                            },
                            "translation_confidence": {
                                "title": "Confidence",
                                "description": "Confidence level of the language translation to English from scale of 0 to 1",
                                "type": "number",
                            },
                        },
                        "required": [
                            "language",
                            "confidence",
                            "english_translation",
                            "translation_confidence",
                        ],
                    },
                }
            ],
            function_call={"name": "detect_languages"},
            temperature=0,
        )

        language_results = json.loads(
            response["choices"][0]["message"]["function_call"]["arguments"]
        )
        logger.info("Fetched language results via function calls")
        logger.info("language detected")

        # 2. Pull relevant chunks from vector database
        prompt_embeddings = openai.Embedding.create(
            model="text-embedding-ada-002", input=prompt
        )["data"][0]["embedding"]

        results = Embedding.objects.alias(
            distance=L2Distance("text_vectors", prompt_embeddings)
        ).filter(distance__gt=0.7)

        relevant_english_context = "".join(result.original_text for result in results)
        logger.info("retrieved the relevant document context from db")

        # 3. Fetch the chat history from our message store to send to openai and back in the response
        historical_chats = Message.objects.filter(session_id=session_id).all()

        # 4. Retrievial question and answer (2nd call to OpenAI, use language from 1. to help LLM respond in same language as user question)
        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=context_prompt_messages(
                organization.id,
                language_results["language"],
                relevant_english_context,
                language_results["english_translation"],
                historical_chats,
            ),
        )
        logger.info("received response from the ai bot for the current prompt")

        prompt_response = response.choices[0].message

        # 5. Store the current question and ans to the message store
        Message.objects.create(session_id=session_id, role="user", message=prompt)
        Message.objects.create(
            session_id=session_id,
            role=prompt_response.role,
            message=prompt_response.content,
        )

        return Response(
            {
                "answer": prompt_response.content,
                "chat_history": [
                    {"role": chat.role, "message": chat.message}
                    for chat in historical_chats
                ],
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

                Embedding.objects.create(
                    source_name=file.name,
                    original_text=page_text,
                    text_vectors=embeddings,
                    organization=org,
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


@api_view(["POST"])
def set_evaluator_prompt(request):
    try:
        print(request.data)
        evaluator_prompt = request.data.get("evaluator_prompt").strip()
        org = current_organization(request)
        logger.debug("ORG", org)
        if not org:
            return Response(
                f"Invalid API key",
                status=status.HTTP_404_NOT_FOUND,
            )

        Organization.objects.filter(id=org.id).update(evaluator_prompt=evaluator_prompt)

        return Response(
            f"Updated Evaluator Prompt",
            status=status.HTTP_201_CREATED,
        )
    except Exception as error:
        print(f"Error: {error}")
        return Response(
            f"Something went wrong",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
