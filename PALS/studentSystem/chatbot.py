# unfinished chatbot

"""import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "meta-llama/Llama-3.2-1B"
# Load tokenizer and model directly from Hugging Face
tokenizer = AutoTokenizer.from_pretrained(model_id, use_auth_token=True, use_fast=False)

# Defines transformer pipeline (our model)
pipeline = transformers.pipeline(
    "question-answering",
    model=model_id,
    torch_dtype=torch.float16,
    device_map="auto",
)
# Chat

def nextResponse(request):

    # Chat
    sequences = pipeline(
        'What is StandardML?\n',
        truncation=False,
        max_length=400,
    )

    print(sequences[0]['generated_text'])"""