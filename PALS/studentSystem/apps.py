from django.apps import AppConfig

class StudentsystemConfig(AppConfig): # Warms up AI model before server opens
    default_auto_field = "django.db.models.BigAutoField"
    name = "studentSystem"

    def ready(self): # Runs when the Django server starts
        import studentSystem.signals  # ensure signals are registered
        import requests, json
        import os
        import subprocess
        try:
            url = "http://localhost:11434/api/chat" 

            model = "gemma3:4b"

            speed_options = {
                "gpu_layers": 100000,  # offload as many layers to GPU as will fit
                "num_ctx": 4096,       # keep context modest for speed
                "num_batch": 1024,     # faster prompt ingestion; reduce if OOM
                "num_predict": 768,    # cap length = faster responses
                "num_thread": 8,       # near the physical core count
                "temperature": 0.2,    # concise/deterministic
            }


            payload = {
                "model": model,
                "messages": [
                        {"role": "user", "content": "Output the following text exactly as is: Hello, I am a helpful programming assistant specialized in Standard ML! Let me know if you have any questions about the language, and I'm here to help!"}
                    ],
                "keep_alive": -1,  # keep model hot
                "stream": True,
                "options": speed_options
            }

            with requests.post(url, json=payload, stream=True, timeout=None) as r: # Test connection to AI model
                r.raise_for_status()
                for line in r.iter_lines(): # Stream the response
                    if not line: 
                        continue
                    data = json.loads(line.decode("utf-8"))
                    if "message" in data and "content" in data["message"]:
                        print(data["message"]["content"], end="", flush=True)
                    if data.get("done"):
                        print("\n")
                        break

        except Exception as e:
            print ("Error connecting to AI Model: ", e)
