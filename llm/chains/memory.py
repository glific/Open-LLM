import os

from langchain.memory import PostgresChatMessageHistory, ConversationBufferMemory


def conversation_history(session_id: str):
    history = PostgresChatMessageHistory(
      connection_string=os.getenv("DATABASE_URL"),
      session_id=session_id,
    )
    memory = ConversationBufferMemory(
      memory_key="chat_history",
      return_messages=True,
      input_key="query",
      output_key="result",
      chat_memory=history
    )
    return memory

