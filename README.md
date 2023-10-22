# Open-LLM

This project aims to take Glific interactions to the next level by seamlessly integrating OpenAI's Language Model to generate contextually accurate responses from the custom knowledge base. This will be a standalone repository within the Glific ecosystem and will be hosted separately. Through the use of Glific webhooks, this will be connected to the Glific instance for better contextual response through the chatbot

## Architecture

![Diagram of overall chain](diagram-of-overall-chain.png)

## Development

### Prerequisites

#### Python & pip

Make sure you have Python and pip installed. You can check this by running:

```bash
python --version
pip --version
```

#### Pipenv

This project uses [pipenv](https://pipenv.pypa.io/en/latest/) for dependency management. To install pipenv, run:

```bash
pip install pipenv --user
```

## Getting Started

### .env

Run `cp .env.example .env` file and add your OpenAI key.

### Start database

We are using Postgres to store conversation history. You can start the database using docker-compose:

```bash
docker-compose up
```

### Project dependencies

This project uses Python 3.9 and virtual environments:

Create a virtualenv using pipenv:

```bash
python -m venv venv
```

Activate the virtualenv:

```bash
source venv/bin/activate
```

Install the dependencies, run:

```bash
pip install -r requirements.txt
```

Run migration

```bash
python manage.py migrate
```

### Start the server

```bash
python manage.py runserver
```

### Seeding

To seed the database with a sample organization, open a python shell (`python manage.py shell`) and run the following command:

```python
from llm.models import Organization
Organization.objects.create(
  name="Myna Mahila",
  system_prompt="I want you to act as a chatbot for providing tailored sexual and reproductive health advice to women in India. You represent an organization called The Myna Mahila Foundation (mynamahila.com), an Indian organization which empowers women by encouraging discussion of taboo subjects such as menstruation, and by setting up workshops to produce low-cost sanitary protection to enable girls to stay in school. In India, majority of girls report not knowing about menstruation before their first period. This is because of limited access to unbiased information due to stigma, discrimination, and lack of resources. The information you provide needs to be non-judgmental, confidential, accurate, and tailored to those living in urban slums. Your response should be in the same language as the user's input.",
  api_key="sk_EXAMPLE_SECRET_KEY",
)
```

To make requests to the API with the organization's API key, use the following command:

```bash
curl -X POST -H "Authorization: sk_EXAMPLE_SECRET_KEY" -H "Content-Type: application/json" -d '{"system_prompt":"You are a chatbot that formats your responses as poetry."}' http://localhost:8000/api/system_prompt
```

To upload a file from `llm/data/sources/*` and ultimately create embeddings out of it, use the following command:

```bash
curl -X POST -H "Authorization: sk_EXAMPLE_SECRET_KEY" -H "Content-Type: multipart/form-data" -F "file=@llm/data/sources/ANXIETY.docx.pdf" http://localhost:8000/api/upload
```

For testing and convenience, running the `upload_docs.sh` script will upload all the files in `llm/data/sources/*` for embeddings to be created out of them.

```bash
./upload_docs.sh
```

### Query

For testing the LLM, we are using [HTTPie](https://httpie.io) because of its succint syntax. You may alternatively use curl or Postman or your favorite HTTP client for this.

You can query the LLM using the following command:

```bash
curl -X POST -H "Authorization: sk_EXAMPLE_SECRET_KEY" -H "Content-Type: application/json" -d '{"prompt": "Peshab ki jagah se kharash ho rahi hai"}' http://localhost:8000/api/chat
```

This will return a JSON endpoint with the LLM response as well as a session id.

```json
{
  "answer": "Aapki samasya ke liye dhanyavaad. Yah peshab ke samay kharash ki samasya ho sakti hai. Isko urinary tract infection (UTI) kaha jata hai. Urinary tract infection utpann hone ka mukhya karan antarik infection ho sakta hai.",
  "chat_history": [],
  "session_id": "uhh0pq"
}
```

To ask a fellow up question, you can use the session id returned in the previous response:

```bash
curl -X POST -H "Authorization: sk_EXAMPLE_SECRET_KEY" -H "Content-Type: application/json" -d '{"prompt":"Peshab ki jagah kharash hai","session_id":"uhh0pq"}' http://127.0.0.1:8000/api/chat
```

```json
{
  "answer": "aapki samasya ke liye dhanyavad. Yah peshaab ki jagah me kharash ho sakti hai. Isko urinary tract infection (UTI) kaha jata hai. UTI utpann hone ka mukhya karan aantarik infection ho sakta hai.",
  "chat_history": [
    [
      ["content", "Peshab ki jagah se kharash ho rahi hai"],
      ["additional_kwargs", {}],
      ["type", "human"],
      ["example", false]
    ],
    [
      [
        "content",
        "Aapki samasya ke liye dhanyavaad. Yah peshab ke samay kharash ki samasya ho sakti hai. Isko urinary tract infection (UTI) kaha jata hai. Urinary tract infection utpann hone ka mukhya karan antarik infection ho sakta hai."
      ],
      ["additional_kwargs", {}],
      ["type", "ai"],
      ["example", false]
    ]
  ],
  "session_id": "uhh0pq"
}
```


The default model used is [`gpt-3.5-turbo`](https://platform.openai.com/docs/models/gpt-3-5) but you can specify a different GPT model by passing a `gpt_model` parameter in the request body.

```bash
curl -X POST -H "Authorization: sk_EXAMPLE_SECRET_KEY" -H "Content-Type: application/json" -d '{"prompt":"Mujhe peshab ki jagah pe kharash ho rahi hai","gpt_model":"gpt-3.5-turbo-16k"}' http://127.0.0.1:8000/api/chat
```

```json
{
  "answer": "Aapki samasya ke liye dhanyavaad. Yah peshaab karne ke samay kharash ki samasya ho sakti hai. Isko urinary tract infection (UTI) kaha jata hai. UTI utpann hone ka mukhya karan aantrik infection ho sakta hai.",
  "chat_history": [],
  "session_id": "cfbQXg"
}
```
