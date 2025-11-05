import ollama
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

model = "phi4:14b"

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
