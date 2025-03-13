from gtts import gTTS
import os
import tempfile
import base64

def generate_audio(input_text):
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