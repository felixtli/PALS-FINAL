from ollama import Client
from dotenv import load_dotenv
import os

load_dotenv() 

def generateCloudResponse(messages):
    client = Client(
        host="https://ollama.com",
        headers={'Authorization': 'Bearer ' + os.getenv("OLLAMA_API_KEY")}
    )

    # System instruction
    concise_instruction = {
        "role": "system",
        "content": "Respond concisely. Use short, direct explanations unless more detail is explicitly requested. Keep your answers in plaintext. Do not attempt to use code formatting, table formatting, bullet points, bold text, or anything of that nature." +
        ""
    }

    messages = [concise_instruction] + messages

    response = client.chat(
        model = 'gpt-oss:120b',
        messages = messages,
        stream = False
    )

    return response["message"]["content"]
