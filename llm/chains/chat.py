import psycopg2, os
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings.openai import OpenAIEmbeddings

from llm.chains import memory
from llm.chains.embeddings import get_pgvector_idx
from llm.models import Organization


def run_chat_chain(
    prompt: str,
    session_id: str,
    primary_language: str,
    english_translation_prompt: str,
    organization_id: int,
    gpt_model: str,
):
    llm = ChatOpenAI(model_name=gpt_model, temperature=0.7)

    retriever = get_pgvector_idx().as_retriever(
        search_kwargs={
            "score_threshold": 0.7,
            "filter": {"organization_id": organization_id},
        }
    )

    relevant_english_context = "".join(
        doc.page_content
        for doc in retriever.get_relevant_documents(english_translation_prompt)
    )

    # Pull previous message in this conversation history based on session id
    chain_memory = memory.conversation_history(session_id=session_id)

    # 2. Retrieval QA
    chain_prompt = chat_chain_prompt(
        organization_id=organization_id,
        language=primary_language,
        english_context=relevant_english_context,
    )
    chain_type_kwargs = {"prompt": chain_prompt}
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
        memory=chain_memory,
        chain_type_kwargs=chain_type_kwargs,
    )
    result = chain({"query": prompt})

    return result


def context_prompt_messages(
    organization_id: int, language: str, english_context: str, question: str
) -> list[dict]:
    org_system_prompt = Organization.objects.get(id=organization_id).system_prompt
    system_message_prompt = {"role": "system", "content": org_system_prompt}
    human_message_prompt = {
        "role": "user",
        "content": f"""Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

        Context:

        {english_context}

        Examples:

        Question: Peshab ki jagah se kharash ho rahi hai
        Chatbot Answer in Hindi: aapakee samasya ke lie dhanyavaad. yah peshaab ke samay kharaash kee samasya ho sakatee hai. ise yoorinaree traikt inphekshan (uti) kaha jaata hai. yoorinaree traikt imphekshan utpann hone ka mukhy kaaran aantarik inphekshan ho sakata hai.

        User question: {question}

        """,
    }
    chat_prompt_messages = [system_message_prompt, human_message_prompt]
    return chat_prompt_messages
