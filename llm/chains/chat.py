from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import psycopg2, os
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


def get_organization_data(column_name):
    database_url = os.getenv('DATABASE_URL')
    try:
        # Connect to the PostgreSQL database using the DATABASE_URL
        connection = psycopg2.connect(database_url)
        cursor = connection.cursor()

        # Define the SQL query to fetch data
        query = f"SELECT {column_name} FROM organization WHERE id = 1;"

        # Execute the query
        cursor.execute(query)

        # Fetch the result
        result = cursor.fetchone()

        if result:
            value = result[0]
            print(f"{column_name.capitalize()} for ID 1: {value}")
        else:
            print(f"No data found for ID 1 in the 'organization' table.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error: {error}")

    finally:
        # Close the cursor and connection
        if connection:
            cursor.close()
            connection.close()

def chat_chain_prompt(language: str, english_context: str) -> ChatPromptTemplate:
    system_message_prompt = SystemMessagePromptTemplate.from_template(str(get_organization_data("system_prompt")))
    system_human_message_prompt = str(get_organization_data("message_prompt"))
    human_message_prompt = HumanMessagePromptTemplate.from_template(
        """Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

        Context:

        {english_context}
        {context}

        Samples:

        {system_human_message_prompt}

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
