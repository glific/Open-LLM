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

We use Python 3.9 pipenv for managing dependencies and create the virtual environment.

Start a virtualenv using pipenv:

```bash
pipenv shell
```

Install the dependencies, run:

```bash
pipenv install
```

### Start the server

```bash
python manage.py runserver
```

### Query

For testing the LLM, we are using [HTTPie](https://httpie.io) because of its succint syntax. You may alternatively use curl or Postman or your favorite HTTP client for this.

You can query the LLM using the following command:

```bash
http POST :8000/llm/ prompt='How can I help someone with anxiety'
```

This will return a JSON endpoint with the LLM response as well as a session id.

```json
{
  "answer": "If you know someone who is struggling with anxiety, there are several ways you can help:\n\n1. Express concern: Reach out to them and provide support by simply listening to what they have to say. Let them know they can come to you when they feel anxious and that you would like to be there for them.\n\n2. Know what is not helpful: It is important to understand that continuing to say \"don't worry about that because...\" is not actually helping, even if your friend or loved one thinks it is. Avoid forcing activities that you think might be helpful for them.\n\n3. Ask them: Don't assume things. Ask the person what they need and act accordingly. Make them feel that you are there for them and their needs.\n\n4. Listen non-judgmentally: If the person isn't in a crisis, ask how they're feeling and how long they've been feeling that way. Be patient and engaged while they speak. Ask clarifying questions and show that you care.\n\n5. Provide practical help: Offer your loved one practical assistance with tasks like getting groceries, cleaning, or household chores. Be careful not to take over or encourage dependency.\n\n6. Educate yourself: Understanding what helps anxiety takes time and effort. Make yourself aware of what anxiety is so that you don't provide any wrong information or invalid help.\n\nRemember, it's important to be supportive, patient, and understanding. Encourage them to seek professional help if needed.",
  "chat_history": [],
  "session_id": "e971aH"
}
```

To ask a fellow up question, you can use the session id returned in the previous response:

```bash
http POST :8000/api/chat prompt='Give me examples of practical help I can offer' session_id='e971aH'
```

```json
{
  "answer": "Here are some examples of practical help you can offer to someone:\n\n1. Offer to run errands or help with household tasks, like getting groceries, cleaning, or cooking.\n2. Provide transportation to appointments or offer to accompany them to medical or therapy appointments.\n3. Help with childcare or offer to babysit so they can have some time for themselves.\n4. Assist with paperwork or administrative tasks, such as filling out forms or organizing documents.\n5. Offer to help with technology-related issues, like setting up a new device or troubleshooting computer problems.\n6. Provide emotional support by being a good listener and offering a shoulder to lean on.\n7. Help them research and connect with local resources or support groups that may be beneficial to their situation.\n8. Offer to help with financial matters, such as budgeting or finding ways to save money.\n9. Assist in finding educational opportunities or job training programs to enhance their skills and improve their employment prospects.\n10. Help them explore and engage in activities that promote self-care and well-being, such as exercising together, practicing mindfulness, or participating in a hobby they enjoy.\n\nRemember, it's important to ask the person what they specifically need and respect their boundaries. Everyone's situation is unique, so offering tailored support can make a meaningful difference.",
  "chat_history": [
    [
      ["content", "How can I help someone with anxiety"],
      ["additional_kwargs", {}],
      ["example", false]
    ],
    [
      [
        "content",
        "If you know someone who is struggling with anxiety, there are several ways you can help:\n\n1. Express concern: Reach out to them and provide support by simply listening to what they have to say. Let them know they can come to you when they feel anxious and that you would like to be there for them.\n\n2. Know what is not helpful: It is important to understand that continuing to say \"don't worry about that because...\" is not actually helping, even if your friend or loved one thinks it is. Avoid forcing activities that you think might be helpful for them.\n\n3. Ask them: Don't assume things. Ask the person what they need and act accordingly. Make them feel that you are there for them and their needs.\n\n4. Listen non-judgmentally: If the person isn't in a crisis, ask how they're feeling and how long they've been feeling that way. Be patient and engaged while they speak. Ask clarifying questions and show that you care.\n\n5. Provide practical help: Offer your loved one practical assistance with tasks like getting groceries, cleaning, or household chores. Be careful not to take over or encourage dependency.\n\n6. Educate yourself: Understanding what helps anxiety takes time and effort. Make yourself aware of what anxiety is so that you don't provide any wrong information or invalid help.\n\nRemember, it's important to be supportive, patient, and understanding. Encourage them to seek professional help if needed."
      ],
      ["additional_kwargs", {}],
      ["example", false]
    ]
  ],
  "session_id": "e971aH"
}
```

### Embeddings

The source documents for the embeddings are stored locally in the `llm/data/sources` folder. To re-generate the embeddings, run:

```bash
http POST :8000/api/embeddings
```
