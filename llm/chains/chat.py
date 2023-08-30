from llm.chains import config, embeddings, memory

from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA


def run_chat_chain(prompt: str, session_id: str):
    llm = get_llm()
    retriever = embeddings.get_retriever()
    chain_memory = memory.conversation_history(session_id=session_id)
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
        memory=chain_memory,
    )
    result = chain({"query": prompt})

    return result


def get_llm():
    llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=config.BOT_TEMPATURE)
    return llm
