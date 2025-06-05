import ollama

# Initialize the Ollama Client
client = ollama.Client()

# Define model and prompt
model = "llama3.2"
prompt = "What is Standard Meta Language?"

def generateResponse(prompt):
    # Generate model response
    response = client.generate(model=model, prompt=prompt)

    # Return generated response
    return (response.response)