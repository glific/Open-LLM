from django.db import models

from pgvector.django import VectorField


class Message(models.Model):
    """
    Stores the chat history
    """

    id = models.AutoField(primary_key=True)
    session_id = models.TextField()
    role = models.CharField(
        max_length=50,
        default="user",
        choices=(("system", "system"), ("user", "user"), ("assistant", "assistant")),
    )
    message = models.TextField()
    evaluation_score = models.JSONField(null=True)

    class Meta:
        db_table = "messages"


class Organization(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, unique=True)
    system_prompt = models.TextField()
    evaluator_prompts = models.JSONField(
        null=True
    )  # { "confidence": "Your task is to...", "friendliness": "Your task is to..." }
    examples_text = models.TextField(null=True)
    openai_key = models.CharField(max_length=255, unique=True, null=True)

    class Meta:
        db_table = "organization"


class Embedding(models.Model):
    id = models.AutoField(primary_key=True)
    source_name = models.TextField()
    original_text = models.TextField()
    text_vectors = VectorField(dimensions=1536, null=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        db_table = "embedding"
