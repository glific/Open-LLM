from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from llm.chains import embeddings, memory


def run_chat_chain(
    prompt: str, session_id: str, primary_language: str, english_translation_prompt: str
):
    llm = get_llm()
    retriever = embeddings.get_retriever(language=primary_language)
    relevant_english_context = "".join(
        doc.page_content
        for doc in retriever.get_relevant_documents(english_translation_prompt)
    )
    chain_memory = memory.conversation_history(session_id=session_id)
    chain_prompt = chat_chain_prompt(
        language=primary_language, english_context=relevant_english_context
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


def chat_chain_prompt(language: str, english_context: str) -> ChatPromptTemplate:
    system_message_prompt = SystemMessagePromptTemplate.from_template(
        "I want you to act as a chatbot for providing tailored sexual and reproductive health advice to women in India. You represent an organization called The Myna Mahila Foundation (mynamahila.com), an Indian organization which empowers women by encouraging discussion of taboo subjects such as menstruation, and by setting up workshops to produce low-cost sanitary protection to enable girls to stay in school. In India, majority of girls report not knowing about menstruation before their first period. This is because of limited access to unbiased information due to stigma, discrimination, and lack of resources. The information you provide needs to be non-judgmental, confidential, accurate, and tailored to those living in urban slums. Your response should be in the same language as the user's input."
    )
    human_message_prompt = HumanMessagePromptTemplate.from_template(
        """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

        Context:

        {english_context}
        {context}

        Samples:

        User Question: Peshab ki jagah se kharash ho rahi hai
        Chatbot Answer in Hindi: aapakee samasya ke lie dhanyavaad. yah peshaab ke samay kharaash kee samasya ho sakatee hai. ise yoorinaree traikt inphekshan (uti) kaha jaata hai. yoorinaree traikt imphekshan utpann hone ka mukhy kaaran aantarik inphekshan ho sakata hai.

        User Question: {question}

        Chatbot Answer in {language}:""".replace(
            "{language}",
            f"{language} (Roman characters)" if language == "Hindi" else language,
        ).replace(
            "{english_context}", "" if language == "English" else english_context
        )
    )
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    return chat_prompt


def get_llm():
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
    return llm
