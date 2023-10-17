from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.chains.openai_functions import (
    create_structured_output_chain,
)

detect_languages_schema = {
    "title": "Detect Languages",
    "description": "Detecting language and other insights on a piece of user input text.",
    "type": "object",
    "properties": {
        "primary_detected_language": {
            "title": "Primary language",
            "description": "The primary detected language",
            "type": "string",
        },
        "detection_confidence": {
            "title": "Confidence",
            "description": "Confidence level of the language detection from scale of 0 to 1",
            "type": "number",
        },
        "secondary_detected_languages": {
            "title": "Secondary languages",
            "description": "Command separated list of secondary languages detected if any",
            "type": "string",
        },
        "translation_to_english": {
            "title": "English translation",
            "description": "English translation of the user input text if not in English",
            "type": "string",
        },
        "translation_confidence": {
            "title": "Confidence",
            "description": "Confidence level of the language translation to English from scale of 0 to 1",
            "type": "number",
        },
        "has_english_words": {
            "title": "If the user input text has any English words",
            "description": "Whether the input text has English words",
            "type": "boolean",
        },
    },
    "required": [
        "primary_detected_language",
        "detection_confidence",
        "translation_to_english",
        "translation_confidence",
        "has_english_words",
    ],
}


def detect_languages_chain():
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a language detection bot specialized in detecting standard and niche local India languages.",
            ),
            ("human", "Detect the languages in this text: {input}"),
        ]
    )
    return create_structured_output_chain(
        detect_languages_schema, llm=llm, prompt=prompt
    )
