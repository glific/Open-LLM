import uuid
import os
import django
import json
import openai
from logging import basicConfig, INFO, getLogger

from pypdf import PdfReader
from pgvector.django import L2Distance
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView

from llm.utils.prompt import (
    context_prompt_messages,
    evaluate_criteria_score,
    count_tokens_for_text,
)
from llm.utils.general import generate_session_id
from llm.models import Organization, Embedding, Message, File, KnowledgeCategory


basicConfig(level=INFO)
logger = getLogger()

TOKEN_LIMIT = 7000

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "llm.settings")

django.setup()

openai.api_key = os.getenv("OPENAI_API_KEY")


@api_view(["POST"])
def create_chat(request):
    try:
        organization: Organization = request.org
        logger.info(f"processing chat prompt request for org {organization.name}")

        if not organization.openai_key:
            return JsonResponse(
                {"error": "Please add your openai key"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        openai.api_key = organization.openai_key

        knowledge_cat = None
        if "category_uuid" in request.data:
            knowledge_cat = KnowledgeCategory.objects.filter(
                uuid=request.data["category_uuid"]
            ).first()

        question = request.data.get("question").strip()
        system_prompt = (
            request.data.get("system_prompt", None) or organization.system_prompt
        )
        system_prompt = system_prompt.strip() if system_prompt else None
        logger.info(f"Using the system prompt : {system_prompt}")

        gpt_model = request.data.get("gpt_model", "gpt-3.5-turbo").strip()
        session_id = (request.data.get("session_id") or generate_session_id()).strip()

        # 1. Function calling to do language detection of the user's question (1st call to OpenAI)
        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=[
                {
                    "role": "user",
                    "content": f"Detect the languages in this text: {question}",
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
        logger.info(f"Language detected: {language_results['language']}")

        # 2. Pull relevant chunks from vector database
        prompt_embeddings = openai.Embedding.create(
            model="text-embedding-ada-002", input=question
        )["data"][0]["embedding"]

        embedding_results_query = Embedding.objects

        if knowledge_cat:
            embedding_results_query = embedding_results_query.filter(
                file__knowledge_category=knowledge_cat
            )

        embedding_results = (
            embedding_results_query.alias(
                distance=L2Distance("text_vectors", prompt_embeddings),
            )
            # .filter(distance__gt=0.7)
            .order_by("-distance")
        )
        logger.info(
            f"retrieved {len(embedding_results)} relevant document context from db"
        )

        # Filter embedding to make sure token limit is under 7000
        final_embeddings: list[Embedding] = []
        token_count = 0
        for embedding in embedding_results:
            token_count += embedding.num_tokens
            if token_count < TOKEN_LIMIT:
                final_embeddings.append(embedding)
            else:
                break

        logger.info(
            f"Using {len(final_embeddings)}/{len(embedding_results)} relevant docs to make sure token limit is under {TOKEN_LIMIT}. Token count: {token_count}"
        )

        relevant_english_context = "".join(
            result.original_text for result in final_embeddings
        )

        # 3. Fetch the chat history from our message store to send to openai and back in the response
        historical_chats = Message.objects.filter(session_id=session_id).all()

        # 4. Retrieval question and answer (2nd call to OpenAI, use language from 1. to help LLM respond in same language as user question)
        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=context_prompt_messages(
                system_prompt,
                organization.id,
                language_results["language"],
                relevant_english_context,
                language_results["english_translation"],
                historical_chats,
            ),
        )
        logger.info("received response from the ai bot for the current prompt")

        prompt_response = response.choices[0].message

        # 5. Evaluate if the request asks for it
        evaluation_scores = {}
        if request.data.get("evaluate"):
            logger.info("Evaluting the response")
            evaluator_prompts = organization.evaluator_prompts  # { 'coherence': ... }
            for criteria, evaluator_prompt in evaluator_prompts.items():
                score = evaluate_criteria_score(
                    evaluator_prompt, question, prompt_response, gpt_model
                )
                evaluation_scores[criteria] = score
                logger.info(f"Evaluated criteria: {criteria} with score: {score}")

            logger.info("Completed evaluating the llm response", evaluator_prompts)

        else:
            logger.info("Evaluator prompt for the org has not been set")

        # 6. Store the current question and ans to the message store
        Message.objects.create(
            session_id=session_id,
            role="user",
            message=question,
            evaluation_score=evaluation_scores,
        )
        Message.objects.create(
            session_id=session_id,
            role=prompt_response.role,
            message=prompt_response.content,
            evaluation_score=evaluation_scores,
        )
        logger.info("Stored messages in django db")

        return JsonResponse(
            {
                "question": question,
                "answer": prompt_response.content,
                "language_results": language_results,
                "embedding_results_count": len(embedding_results),
                "chat_history": [
                    {"role": chat.role, "message": chat.message}
                    for chat in historical_chats
                ],
                "session_id": session_id,
                "evaluation_scores": evaluation_scores,
            },
            status=status.HTTP_201_CREATED,
        )
    except Exception as error:
        logger.error(f"Error: {error}")
        return JsonResponse(
            {"error": f"Something went wrong {error}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class FileUploadView(APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, format=None):
        try:
            org: Organization = request.org
            logger.info(f"processing file upload for org {org.name}")

            if "file" not in request.data:
                raise ValueError("Empty content")

            openai.api_key = org.openai_key

            request_file = request.data["file"]

            knowledge_cat = None
            if "category_uuid" in request.data:
                knowledge_cat = KnowledgeCategory.objects.filter(
                    uuid=request.data["category_uuid"]
                ).first()

            logger.info("Using Knowledge Category : %s", knowledge_cat)

            logger.info("Uploading file %s", request_file.name)

            # Create the file object
            file = File.objects.create(
                knowledge_category=knowledge_cat,
                name=request_file.name,
            )

            pdf_reader = PdfReader(request_file)
            for page in pdf_reader.pages:
                page_text = page.extract_text().replace("\n", " ")

                if len(page_text) > 0:
                    response = openai.Embedding.create(
                        model="text-embedding-ada-002", input=page_text
                    )

                    embeddings = response["data"][0]["embedding"]
                    if len(embeddings) != 1536:
                        raise ValueError(
                            f"Invalid embedding length: #{len(embeddings)}"
                        )

                    Embedding.objects.create(
                        source_name=file.name,
                        original_text=page_text,
                        text_vectors=embeddings,
                        organization=org,
                        num_tokens=count_tokens_for_text(page_text),
                        file=file,
                    )

            return JsonResponse({"msg": f"Uploaded file {file.name} successfully"})
        except ValueError as error:
            logger.error(f"Error: {error}")
            return JsonResponse(
                {"error": f"Invalid file"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as error:
            logger.error(f"Error: {error}")
            return JsonResponse(
                {"error": f"Something went wrong"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["POST"])
def set_system_prompt(request):
    try:
        org: Organization = request.org
        logger.info(f"processing set system prompt for org {org.name}")

        system_prompt = request.data.get("system_prompt").strip()

        Organization.objects.filter(id=org.id).update(system_prompt=system_prompt)

        return JsonResponse(
            {"msg": f"Updated System Prompt"},
            status=status.HTTP_201_CREATED,
        )
    except Exception as error:
        logger.error(f"Error: {error}")
        return JsonResponse(
            {"error": f"Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def set_evaluator_prompt(request):
    try:
        org: Organization = request.org
        logger.info(f"processing set evaluator prompt request for org {org.name}")

        evaluator_prompts = request.data.get("evaluator_prompts")

        Organization.objects.filter(id=org.id).update(
            evaluator_prompts=evaluator_prompts
        )

        return JsonResponse(
            {"msg": f"Updated Evaluator Prompt"},
            status=status.HTTP_201_CREATED,
        )
    except Exception as error:
        logger.info(f"Error: {error}")
        return JsonResponse(
            {"error": f"Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def set_examples_text(request):
    """
    Example request body:

    '
    Question: Peshab ki jagah se kharash ho rahi hai
    Chatbot Answer in Hindi: aapakee samasya ke lie dhanyavaad. yah peshaab ke samay kharaash kee samasya ho sakatee hai. ise yoorinaree traikt inphekshan (uti) kaha jaata hai. yoorinaree traikt imphekshan utpann hone ka mukhy kaaran aantarik inphekshan ho sakata hai.
    '
    """
    try:

        org: Organization = request.org
        logger.info(f"processing set examples text request for org {org.name}")

        examples_text = request.data.get("examples_text")

        Organization.objects.filter(id=org.id).update(examples_text=examples_text)

        return JsonResponse(
            {"msg": f"Updated Examples Text"},
            status=status.HTTP_201_CREATED,
        )

    except Exception as error:
        logger.error(f"Error: {error}")
        return JsonResponse(
            {"error": f"Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def set_openai_key(request):
    """
    Example request body:

    '
    Question: Peshab ki jagah se kharash ho rahi hai
    Chatbot Answer in Hindi: aapakee samasya ke lie dhanyavaad. yah peshaab ke samay kharaash kee samasya ho sakatee hai. ise yoorinaree traikt inphekshan (uti) kaha jaata hai. yoorinaree traikt imphekshan utpann hone ka mukhy kaaran aantarik inphekshan ho sakata hai.
    '
    """
    try:
        org: Organization = request.org
        logger.info(f"processing set openai key request for org {org.name}")

        openai_key = request.data.get("key")

        Organization.objects.filter(id=org.id).update(openai_key=openai_key)

        return JsonResponse(
            {"msg": f"Updated openai key"},
            status=status.HTTP_200_OK,
        )

    except Exception as error:
        logger.error(f"Error: {error}")
        return JsonResponse(
            {"error": f"Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def create_knowledge_category(request):
    """
    Create a new category for an org
    """
    try:
        org: Organization = request.org

        name = request.data.get("name")

        if KnowledgeCategory.objects.filter(name=name, org=org).exists():
            return JsonResponse(
                {"error": f"Knowledge Category with name {name} already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        knowledge_cat = KnowledgeCategory.objects.create(name=name.strip(), org=org)

        return JsonResponse(
            {"name": knowledge_cat.name, "uuid": knowledge_cat.uuid},
            status=status.HTTP_200_OK,
        )

    except Exception as error:
        logger.error(f"Error: {error}")
        return JsonResponse(
            {"error": f"Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_knowledge_categories(request):
    """
    Fetches all categories for an org
    """
    try:
        org: Organization = request.org

        return JsonResponse(
            {
                "data": [
                    {"name": knowledge_cat.name, "uuid": knowledge_cat.uuid}
                    for knowledge_cat in KnowledgeCategory.objects.filter(org=org).all()
                ]
            },
            status=status.HTTP_200_OK,
        )

    except Exception as error:
        logger.error(f"Error: {error}")
        return JsonResponse(
            {"error": f"Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["DELETE"])
def delete_knowledge_category(request, category_uuid):
    """
    Example request body:

    '
    Question: Peshab ki jagah se kharash ho rahi hai
    Chatbot Answer in Hindi: aapakee samasya ke lie dhanyavaad. yah peshaab ke samay kharaash kee samasya ho sakatee hai. ise yoorinaree traikt inphekshan (uti) kaha jaata hai. yoorinaree traikt imphekshan utpann hone ka mukhy kaaran aantarik inphekshan ho sakata hai.
    '
    """
    try:
        org: Organization = request.org

        try:
            uuid.UUID(
                category_uuid
            )  # This will raise a ValueError if uuid_str is not a valid UUID
        except ValueError:
            return JsonResponse(
                {"error": "Invalid UUID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        knowledge_cat = KnowledgeCategory.objects.filter(
            uuid=category_uuid, org=org
        ).first()

        if not knowledge_cat:
            return JsonResponse(
                {"error": f"Knowledge Category does not exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        knowledge_cat.delete()

        return JsonResponse(
            {"msg": f"Category deleted successfully"},
            status=status.HTTP_200_OK,
        )

    except Exception as error:
        logger.error(f"Error: {error}")
        return JsonResponse(
            {"error": f"Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_documents(request):
    """
    Fetches all documents uploaded by the org
    """
    try:
        org: Organization = request.org

        return JsonResponse(
            {
                "data": [
                    {
                        "name": file.name,
                        "uuid": file.uuid,
                        "category": {
                            "name": file.knowledge_category.name,
                            "uuid": file.knowledge_category.uuid,
                        },
                    }
                    for file in File.objects.filter(knowledge_category__org=org).all()
                ]
            },
            status=status.HTTP_200_OK,
        )

    except Exception as error:
        logger.error(f"Error: {error}")
        return JsonResponse(
            {"error": f"Something went wrong"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
