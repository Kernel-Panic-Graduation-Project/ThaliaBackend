import os
import re
import requests

LLM_CONTAINER_URL = os.getenv("LLM_CONTAINER_URL", "http://localhost:8080")

def generate_text(input, max_seq_length=50, repetition_penalty=1.2, temperature=0.7, top_k=50):
    system_prompt = "You are an exceptional story teller that writes stories in transcript format for children."
    try:
        payload = {
            "model": "model",
            "max_completion_tokens": max_seq_length,
            "repeat_penalty": repetition_penalty,
            "temperature": temperature,
            "top_k": top_k,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Generate an episode of The Amazing World Of Gumball with the given keywords and size:\nkeywords: {input}; size: short"
                }
            ]
        }
        
        response = requests.post(
            f"{LLM_CONTAINER_URL}/v1/chat/completions",
            json=payload
        )
        
        if response.status_code == 200:
            return parse_response(response)
        else:
            raise ValueError(f"LLM request failed with status code {response.status_code}")
    except Exception as e:
        raise ValueError(f"Error generating text: {str(e)}")


def parse_response(response):
    try:
        assistant_message = response.json().get("choices")[0].get("message").get("content")
        
        # Extract title
        title_match = re.search(r"Title:\s*(.*?)(?:\n|$)", assistant_message)
        title = title_match.group(1).strip() if title_match else "Untitled Story"
        
        # Extract all image prompts
        image_prompts = []
        for match in re.finditer(r"<imagePrompt>(.*?)</imagePrompt>", assistant_message, re.DOTALL):
            image_prompts.append(match.group(1).strip())
        
        # Extract all text sections
        text_sections = []
        for match in re.finditer(r"<text>(.*?)</text>", assistant_message, re.DOTALL):
            text_sections.append(match.group(1).strip())
        
        # If no structured content was found, use the entire message as a single text section
        if not text_sections:
            text_sections = [assistant_message]
        
        return {
            "title": title,
            "image_prompts": image_prompts,
            "text_sections": text_sections
        }
    except Exception as e:
        print(f"Error parsing LLM response: {str(e)}")
        return {"title": "Error", "image_prompts": [], "text_sections": [assistant_message]}