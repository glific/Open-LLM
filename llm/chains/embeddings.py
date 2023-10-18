import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores.pgvector import PGVector


def get_pgvector_idx():
    CONNECTION_STRING = PGVector.connection_string_from_db_params(
        driver=os.environ.get("PGVECTOR_DRIVER", "psycopg2"),
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", "5432")),
        database=os.environ.get("DB_NAME", "llm_db"),
        user=os.environ.get("DB_USER", "llm_agent"),
        password=os.environ.get("DB_PASSWORD", "llm_password"),
    )
    return PGVector.from_existing_index(
        embedding=OpenAIEmbeddings(),
        connection_string=CONNECTION_STRING,
    )
