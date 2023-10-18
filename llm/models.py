from django.db import models

from pgvector.django import VectorField


class MessageStore(models.Model):
    """
    See Langchain source code for the table schema we match here: https://github.com/langchain-ai/langchain/blob/7fa82900cb15d9c41099ad7dbb8aaa66941f6905/libs/langchain/langchain/memory/chat_message_histories/postgres.py#L39-L42
    """

    id = models.AutoField(primary_key=True)
    session_id = models.TextField()
    message = models.JSONField()

    class Meta:
        db_table = "message_store"


class Organization(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)
    system_prompt = models.TextField()

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
