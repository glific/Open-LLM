from django.db import models

class MessageStore(models.Model):
    """
    See Langchain source code for the table schema we match here: https://github.com/langchain-ai/langchain/blob/7fa82900cb15d9c41099ad7dbb8aaa66941f6905/libs/langchain/langchain/memory/chat_message_histories/postgres.py#L39-L42
    """
    id = models.AutoField(primary_key=True)
    session_id = models.TextField()
    message = models.JSONField()

    class Meta:
        db_table = "message_store"

class Embeddings(models.Model):
    id = models.AutoField(primary_key=True)
    raw_text = models.TextField()
    text_source = models.TextField()
    doc_vectors = models.BinaryField(max_length=1536)

    class Meta:
        db_table = "embeddings"
