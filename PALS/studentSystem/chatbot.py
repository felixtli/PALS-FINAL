import ollama
from ollama import Client
import requests, json
import os
import subprocess

url = "http://localhost:11434"

speed_options = {
  "gpu_layers": 100000,  # offload as many layers to GPU as will fit
  "num_ctx": 4096,       # keep context modest for speed
  "num_batch": 1024,     # faster prompt ingestion; reduce if OOM
  "num_predict": 768,    # cap length = faster responses
  "num_thread": 8,       # near your physical core count
  "temperature": 0.2,    # concise/deterministic
}

model = "gemma3:4b"

def generateResponse (messages):

    payload = {
        "model": model,
        "messages": messages,
        "keep_alive": -1,  # keep model hot
        "stream": True,
        "options": speed_options
    }

    url = "http://localhost:11434/api/chat"
    with requests.post(url, json=payload, stream=True, timeout=None) as r:
        r.raise_for_status()
        full_message = ""
        for line in r.iter_lines():
            if not line: 
                continue
            data = json.loads(line.decode("utf-8"))
            if "message" in data and "content" in data["message"]:
                full_message += data["message"]["content"]
            if data.get("done"):
                messages.append({"role": "assistant", "content": full_message})
                return full_message

def generateCloudResponse(messages):
    client = Client(
        host="https://ollama.com",
        headers={'Authorization': 'Bearer ' + 'd70bb7b59f934982bb2f5a31fe589f5c.QTMkwMi-QS3FDBJ3r3M1PEmu'}
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