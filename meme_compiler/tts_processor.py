import os
import pytesseract
from PIL import Image
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from playsound import playsound

def extract_text_from_image(tesseract_cmd, image_path):
    """
    Extracts text from an image file using Tesseract OCR.
    """
    if not all([tesseract_cmd, image_path]):
        print("OCR Error: Missing Tesseract command path or image path.")
        return ""

    try:
        # Set the command path for pytesseract
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Open the image and extract text
        text = pytesseract.image_to_string(Image.open(image_path))

        print(f"Extracted text: '{text.strip()}'")
        return text.strip().replace('\n', ' ') # Replace newlines with spaces for TTS

    except pytesseract.TesseractNotFoundError:
        print("Tesseract Error: The Tesseract executable was not found.")
        print(f"Please ensure the path in your settings is correct: '{tesseract_cmd}'")
        # In a real app, we might want to pop up a more specific error message here.
        return ""
    except Exception as e:
        print(f"An unexpected error occurred during OCR processing: {e}")
        return ""

# --- ElevenLabs TTS Functions ---

def get_elevenlabs_subscription_info(api_key):
    """Fetches user subscription info from ElevenLabs."""
    if not api_key:
        return None
    try:
        client = ElevenLabs(api_key=api_key)
        response = client.user.get_subscription()
        return response
    except Exception as e:
        print(f"Error fetching ElevenLabs subscription info: {e}")
        return None

def get_elevenlabs_voices(api_key):
    """Fetches available voices from ElevenLabs."""
    if not api_key:
        return {}
    try:
        client = ElevenLabs(api_key=api_key)
        voices = client.voices.get_all()
        # Return a dictionary of voice_name: voice_id
        return {voice.name: voice.voice_id for voice in voices.voices}
    except Exception as e:
        print(f"Error fetching ElevenLabs voices: {e}")
        return {}

def generate_elevenlabs_tts(api_key, voice_id, text, output_path):
    """
    Generates an MP3 audio file from text using the ElevenLabs API.
    Returns a tuple: (success: bool, message: str)
    """
    if not all([api_key, voice_id, text]):
        message = "Missing API key, voice ID, or text for TTS generation."
        print(message)
        return (False, message)
    try:
        client = ElevenLabs(api_key=api_key)
        # The correct method is client.text_to_speech.convert() which returns a stream
        audio_stream = client.text_to_speech.convert(voice_id=voice_id, text=text)

        with open(output_path, 'wb') as f:
            for chunk in audio_stream:
                f.write(chunk)

        print(f"TTS audio saved to {output_path}")
        return (True, None)
    except Exception as e:
        error_message = f"An error occurred during ElevenLabs TTS generation: {e}"
        print(error_message)
        return (False, str(e))

def play_voice_preview(api_key, voice_id):
    """Generates and plays a short audio preview of a voice using the ElevenLabs API."""
    if not all([api_key, voice_id]):
        print("Missing API key or voice ID for voice preview.")
        return
    try:
        client = ElevenLabs(api_key=api_key)
        preview_text = "Hello, this is a preview of my voice."
        # Use the correct method and handle the stream
        audio_stream = client.text_to_speech.convert(voice_id=voice_id, text=preview_text)

        temp_preview_file = "temp_preview.mp3"
        with open(temp_preview_file, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        playsound(temp_preview_file)
        os.remove(temp_preview_file)

    except Exception as e:
        print(f"An error occurred during voice preview: {e}")
