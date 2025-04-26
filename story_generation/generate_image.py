import json
import os
from google.api_core.exceptions import ResourceExhausted
from itertools import cycle
import time
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.errors import ClientError
import base64
import requests
from story_generation.image_config import *

GEMINI_API_KEYS = [
    os.getenv("GENAI_API_KEY_5"),
    os.getenv("GENAI_API_KEY_4"),
    os.getenv("GENAI_API_KEY_3"),
    os.getenv("GENAI_API_KEY_2"),
    os.getenv("GENAI_API_KEY_1"),
]

API_KEY_CYCLE = cycle(key for key in GEMINI_API_KEYS if key)

class Section(BaseModel):
    text: str
    image_prompt: str

def generate_sections_and_image_prompts(generated_story, theme):
    """
    Generate image prompts and sections for the story using the Gemini API.
    """
    while True:
        try:
            client = genai.Client(api_key=next(API_KEY_CYCLE))

            input_message = f"""
I will provide you a story, theme and character name and you will seperate this story into meaningful segments and provide me an image prompt for each segment to use in SDXL model.,

Here are the rules:
1 - do not describe character appearance, directly use its name as reference for its appearance.
2 - create prompts as concrete as possible, do not use abstract words, just describe the scene in detail.
3 - just answer the output, do not say hello or anything.
4 - if more than one prompts share the same environment, explain the environment in detail in all of these prompts.
5 - create approximately 10 segments for the story.
6 - be sure to include the whole story in the text fields combined. Try to make the text segments lengths to be as equal as possible.

Here is an example image_prompt:
1- Alice, solo, cat, cute, sleeping, light_particles, nature, mountain, depth of field, the best quality, amazing quality, high quality, masterpiece,

Here is the output format:
SEGMENT 1: \text: ${"story in segment 1"} \image_prompt: ${"image prompt for segment 1"}
SEGMENT 2: \text: ${"story in segment 2"} \image_prompt: ${"image prompt for segment 2"}
\n
Theme: {theme}
Story:
{generated_story}"""

            model = "gemini-2.5-flash-preview-04-17"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=input_message),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig(
                thinking_config = types.ThinkingConfig(
                    thinking_budget=0,
                ),
                response_mime_type="application/json",
                max_output_tokens=16000,
                response_schema=list[Section],
            )

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=generate_content_config,
            )

            response_json = json.loads(response.text)

            return response_json
        except ResourceExhausted:
            sleep_time = 20
            print(f"Rate limit exceeded for story: Waiting for {sleep_time} seconds before retrying...")
            time.sleep(sleep_time)
        except ClientError as e:
            if e.code == 429:
                print("Rate limit exceeded for images.")
                sleep_time = 20
                print(f"Rate limit exceeded for images: Waiting for {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
            else:
                raise e
            
def split_and_generate_image_prompts(generated_story, line_count=10):
    """
    Split the generated story into sections and generate image prompts for each section.
    """
    sections = []
    lines = generated_story.splitlines()
    for i in range(0, len(lines), line_count):
        segment = "\n".join(lines[i:i + line_count])
        sections.append({
            'text': segment,
            'image_prompt': ''
        })
    
    # Fill the image prompts using the Gemini API
    for section in sections:
        while True:
            try:
                model = "gemini-2.5-flash-preview-04-17"
                client = genai.Client(api_key=next(API_KEY_CYCLE))
                input_message = f"""
I will provide you a story and that story's segment and you will generate an image prompt for only the given segment to use in SDXL model.
Here are the rules:
1 - do not describe character appearance, directly use its name as reference.
2 - try not to use more than one character name in the same prompt. Make prompts with only one character name.
3 - ABSOLUTELY DO NOT USE MORE THAN ONE CHARACTER NAME IN THE SAME PROMPT.
4 - create prompts as concrete as possible, do not use abstract words, just describe the scene in detail.
5 - just answer the output, do not say hello or anything.
6 - if more than one prompts share the same environment, explain the environment in detail in all of these prompts.
7 - Explain the environment in detail in all of these prompts.

Here is an example image prompt:

Alice, realistic, solo, cat, cute, sleeping, light_particles, nature, mountain, depth of field, the best quality, amazing quality, high quality, masterpiece,

Story:
{generated_story}

Segment:
{section['text']}
"""
                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=input_message),
                        ],
                    ),
                ]
                generate_content_config = types.GenerateContentConfig(
                    thinking_config = types.ThinkingConfig(
                        thinking_budget=0,
                    ),
                    response_mime_type="text/plain",
                    max_output_tokens=16000,
                )
                

                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=generate_content_config,
                )
                section['image_prompt'] = response.text
                break
            except ResourceExhausted:
                sleep_time = 20
                print(f"Rate limit exceeded for prompts: Waiting for {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
            except ClientError as e:
                if e.code == 429:
                    print("Rate limit exceeded for prompts.")
                    sleep_time = 20
                    print(f"Rate limit exceeded for prompts: Waiting for {sleep_time} seconds before retrying...")
                    time.sleep(sleep_time)
                else:
                    raise e

    return sections

def generate_images_gemini(sections):
    """
    Generate images for the given sections using the Gemini API.
    """
    for section in sections:
        while True:
            try:
                # Initialize the client with API key
                client = genai.Client(api_key=next(API_KEY_CYCLE))
                model_name = "gemini-2.0-flash-exp-image-generation"

                # Check if image_prompt exists and is not empty, otherwise use a default prompt
                image_prompt = section.get('image_prompt', '')
                if not image_prompt or image_prompt.strip() == '':
                    # Create a basic prompt from the first couple sentences of the section text
                    text_preview = section.get('text', '')[:100] + '...' if section.get('text') else ''
                    image_prompt = f"Create an illustration for a children's story showing: {text_preview}"
                    # Save the generated prompt back to the section
                    section['image_prompt'] = image_prompt

                # Create proper request structure with Content and Part objects
                contents = [
                    genai.types.Content(
                        role="user",
                        parts=[
                            genai.types.Part.from_text(
                                text=f"Generate a horizontal 16:9 cartoon style image for the following prompt: {image_prompt}"
                            ),
                        ],
                    ),
                ]
                
                # Configure generation with proper response modalities
                generate_content_config = genai.types.GenerateContentConfig(
                    response_modalities=["image", "text"],
                    response_mime_type="text/plain",
                )
                
                # Stream the response to handle binary data
                response_stream = client.models.generate_content_stream(
                    model=model_name,
                    contents=contents,
                    config=generate_content_config,
                )
                
                # Process the stream chunks
                for chunk in response_stream:
                    if (
                        chunk.candidates is None
                        or chunk.candidates[0].content is None
                        or chunk.candidates[0].content.parts is None
                    ):
                        continue
                    
                    # If we have inline data (binary image data)
                    if chunk.candidates[0].content.parts[0].inline_data:
                        inline_data = chunk.candidates[0].content.parts[0].inline_data
                        # Store the binary data directly in the section
                        section['image'] = inline_data.data
                        section['image_mime_type'] = inline_data.mime_type
                break

            except ResourceExhausted:
                sleep_time = 20
                print(f"Rate limit exceeded for images: Waiting for {sleep_time} seconds before retrying...")
                time.sleep(sleep_time)
            except ClientError as e:
                print(e.code)
                if e.code == 429:
                    print("Rate limit exceeded for images.")
                    sleep_time = 20
                    print(f"Rate limit exceeded for images: Waiting for {sleep_time} seconds before retrying...")
                    time.sleep(sleep_time)
                else:
                    raise e

    return sections

def generate_images(sections, model_category):
    IMAGE_GENERATOR_URL = os.getenv('IMAGE_GENERATOR_URL')
    
    MODEL_CATEGORY = model_category
    
    for section in sections:
        PROMPT = section['image_prompt']
        NEGATIVE_PROMPT = ""
        
        model_payload = {
            'sd_model_checkpoint': CONFIG_CHECKPOINT[MODEL_CATEGORY]
        }

        config_payload = {
            'prompt'              : f'{CONFIG_PROMPT[MODEL_CATEGORY]}, {CONFIG_LORA[MODEL_CATEGORY]}, {PROMPT}',
            'negative_prompt'     : f'{CONFIG_NEGATIVE_PROMPT[MODEL_CATEGORY]}, {NEGATIVE_PROMPT}',


            'sampler_name'        : f'{CONFIG_SAMPLER[MODEL_CATEGORY]}',
            'scheduler'           : 'Automatic',
            'steps'               : f'{CONFIG_STEPS[MODEL_CATEGORY]}',
            'width'               : f'{CONFIG_WIDTH[MODEL_CATEGORY]}',
            'height'              : f'{CONFIG_HEIGHT[MODEL_CATEGORY]}',
            'cfg_scale'           : f'{CONFIG_GUIDANCE_SCALE[MODEL_CATEGORY]}',
            'seed'                : f'{CONFIG_SEED[MODEL_CATEGORY]}',

            'enable_hr'           : False,
            'hr_upscaler'         : f'{CONFIG_UPSCALER[MODEL_CATEGORY]}',
            'hr_scale'            : f'{CONFIG_UPSCALE_FACTOR[MODEL_CATEGORY]}',
            'denoising_strength'  : f'{CONFIG_DENOISING_STRENGTH[MODEL_CATEGORY]}',

            'override_settings' : {
                'CLIP_stop_at_last_layers' : 2,
            }
        }

        requests.post(url=f'{IMAGE_GENERATOR_URL}/sdapi/v1/options', json=model_payload, verify=False)
        response = requests.post(url=f'{IMAGE_GENERATOR_URL}/sdapi/v1/txt2img', json=config_payload, verify=False).json()

        section['image'] = base64.b64decode(response['images'][0])
        section['image_mime_type'] = 'image/png'
        
    return sections