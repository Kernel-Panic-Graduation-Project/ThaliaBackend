import os
import re
import requests

LLM_CONTAINER_URL = os.getenv("LLM_CONTAINER_URL", "http://localhost:8080")

def generate_text(description, theme, characters, max_seq_length=5000, temperature=1.0, top_k=50):
    character_name = f"{characters[0]['name']} ({characters[0]['source']})"
    system_prompt = "You are an exceptional story teller that writes stories in transcript format for children."

    input_message = f"""Create me a kids story in a narrator speech format. It should be like:
<Story>
The story ends.

Don't generate any text other than the story. Only give the story in the response. The story shouldn't be inside quotation marks.
Give the output in plain text, so no bold and italic like outputs.
Use the exact given character names and only use the provided main character and no one else. You can use generic names for other characters like witch, bear, fox and etc...
Ensure that the story ends properly without cutting off. The story should be approximately between 1250 and 1500 words, and MUST NOT EXCEED 1500 WORDS. End the story with "The story ends."
The theme should be: {theme}.
The main character should be: {character_name}
The story description is: {description}
Each character's source is given in parentheses. Use only the provided names in the transcript. Don't use the source names in the story."""
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
