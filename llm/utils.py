from llm.models import Message, Organization
import openai
from typing import Union


def context_prompt_messages(
    organization_id: int,
    language: str,
    english_context: str,
    question: str,
    historical_chats: list[Message],
) -> list[dict]:
    org = Organization.objects.filter(id=organization_id).first()
    
    org_system_prompt = org.system_prompt
    examples_text = org.examples_text
    
    system_message_prompt = {"role": "system", "content": org_system_prompt}
    human_message_prompt = {
        "role": "user",
        "content": f"""Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

        Context:

        {english_context}

        Examples:

        {examples_text}

        Question: {question}
        Chatbot Answer in {language}: """,
    }
    chat_prompt_messages = (
        [system_message_prompt]
        + [{"role": chat.role, "content": chat.message} for chat in historical_chats]
        + [human_message_prompt]
    )
    return chat_prompt_messages


def evaluate_criteria_score(
    evaluator_prompt: str, prompt: str, response: str, gpt_model: str
) -> Union[int, None]:
    evaluation_score: Union[int, None] = None
    if evaluator_prompt is not None:
        # replace the place holders for question and response in the evaluator prompt
        evaluator_prompt = evaluator_prompt.replace("[[QUESTION]]", prompt).replace(
            "[[RESPONSE]]", response.content
        )

        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=[{"role": "system", "content": evaluator_prompt}],
        )
        response_text = response.choices[0].message.content

        print(f"response_text: {response_text}")
        evaluation_score = int(response_text)

    return evaluation_score
