from gtts import gTTS
import os
import tempfile
import base64
import requests

TTS_BACKEND_URL = os.getenv("TTS_BACKEND_URL", "http://localhost:9000")

def generate_audio_gtts(input_text):
	"""
	Convert text to speech using Google Text-to-Speech API and return base64 encoded audio data.
	
	Args:
		input_text: The text to convert to speech
			
	Returns:
		A dictionary containing the base64 encoded audio data
	"""
	if not input_text:
		return {"audio_data": None, "text": input_text}
	
	try:
		# Create a temporary file to store the audio
		with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
			temp_filename = temp_file.name
		
		# Generate the speech
		tts = gTTS(text=input_text, lang='en')
		tts.save(temp_filename)
		
		# Read the audio file and encode it to base64
		with open(temp_filename, 'rb') as audio_file:
			audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
		
		# Clean up the temporary file
		os.remove(temp_filename)
		
		return audio_data
	except Exception as e:
		print(f"Error generating audio: {str(e)}")
		return {"audio_data": None, "error": str(e)}

def generate_audio(input_text, audio_file_id):
    """
    Convert text to speech using the specified TTS backend and return base64 encoded audio data.

    Args:
        input_text: The text to convert to speech
        audio_file_id: The ID of the voice to use for TTS

    Returns:
        The base64 encoded audio data or an error message if the request fails.
    """
    if not input_text:
        return {"audio_data": None, "text": input_text}

    response = requests.post(
        f"{TTS_BACKEND_URL}/api/text-to-audio/generate/",
        json={"input_text": input_text, "audio_file_id": audio_file_id}
    )

    if response.status_code == 200:
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        return audio_base64
    else:
        return generate_audio_gtts(input_text)
