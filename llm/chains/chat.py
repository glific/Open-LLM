from llm.chains import config, embeddings

from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA


def run_chat_chain(prompt: str):
    llm = get_llm()
    retriever = embeddings.get_retriever()
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, retriever=retriever, chain_type="stuff", return_source_documents=True
    )
    result = qa_chain({"query": prompt})

    print(result)

    return result


def get_llm():
    llm = ChatOpenAI(model_name="gpt-3.5-turbo-16k", temperature=config.BOT_TEMPATURE)
    return llm