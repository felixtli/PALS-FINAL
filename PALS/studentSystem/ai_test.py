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

model = "gemma3:4b" # Change model name as needed

def chat_once (messages):
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
            if data.get("done"):
                break

if __name__ == "__main__":

    url = "http://localhost:11434/api/chat" 

    payload = {
        "model": model,
        "messages": [
                {"role": "user", "content": "Output the following text exactly as is: Hello, I am a helpful programming assistant specialized in Standard ML! Let me know if you have any questions about the language, and I'm here to help!"}
            ],
        "keep_alive": -1,  # keep model hot
        "stream": True,
        "options": speed_options
    }
    with requests.post(url, json=payload, stream=True, timeout=None) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line: 
                continue
            data = json.loads(line.decode("utf-8"))
            if "message" in data and "content" in data["message"]:
                pass
            if data.get("done"):
                break
    messages = [{"role": "system", "content": "You are a helpful programming assistant that has expertise in Standard ML."}]

    try:
        while True:
            user_message = input("You: ")
            messages.append({"role": "user", "content": user_message})
            chat_once(messages)
            print("\n")
    except KeyboardInterrupt:
        print ("Bye!")

    