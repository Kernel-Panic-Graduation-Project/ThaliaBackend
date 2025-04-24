import os
import re
import requests

LLM_CONTAINER_URL = os.getenv("LLM_CONTAINER_URL", "http://localhost:8080")

def generate_text(description, theme, characters, max_seq_length=5000, temperature=1.0, top_k=50):
    character_names = ', '.join([f"{name} ({source})" for name, source in characters])
    system_prompt = "You are an exceptional story teller that writes stories in transcript format for children."
    input_message = f"""Create me a kids story in a transcript format. It should be like:
Person1: blablabla
Person2: blablabla
[Explain the scene]
Person3: blablabla
Person2: blablabla
The story ends.

Don't generate any text other than the story. Only give the story transcript in the response. Replace Person1, Person2 names with the actual names of the characters.
Explain the scene sometimes in "[" and "]". Scene explanations should always be between the character speeches. Character speeches shouldn't be inside quotation marks.
There should only be what the character is saying and nothing else on where blablabla is. Give the output in plain text, so no bold and italic like outputs.
Use the exact given character names and only use the provided names and no one else. Ensure that the story ends properly without cutting off.
The story should be approximately between 1250 and 1500 words, and MUST NOT EXCEED 1500 WORDS. End the story with "The story ends."
The theme should be: {theme}.
The characters should be: {character_names}.
The story description is: {description}
Each character's source is given in parentheses. Use only the provided names in the transcript."""
    try:
        payload = {
            "model": "model",
            "max_completion_tokens": max_seq_length,
            "temperature": temperature,
            "top_k": top_k,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": input_message
                }
            ]
        }
        
        response = requests.post(
            f"{LLM_CONTAINER_URL}/v1/chat/completions",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json().get("choices")[0].get("message").get("content")
        else:
            raise ValueError(f"LLM request failed with status code {response.status_code}")
    except Exception as e:
        raise ValueError(f"Error generating text: {str(e)}")
