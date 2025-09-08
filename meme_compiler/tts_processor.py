import easyocr
import os
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from playsound import playsound

# --- OCR Model Initialization ---
print("Initializing OCR engine (easyocr)... This may take a moment.")
try:
    reader = easyocr.Reader(['en'])
    print("OCR engine initialized successfully.")
except Exception as e:
    print(f"CRITICAL: Could not initialize OCR engine. Text extraction will not work. Error: {e}")
    reader = None

def extract_text_from_image(image_path):
    """Extracts text from an image file using EasyOCR."""
    if not reader:
        print("OCR reader not available.")
        return ""
    try:
        result = reader.readtext(image_path, detail=0, paragraph=True)
        text = " ".join(result)
        print(f"Extracted text: '{text.strip()}'")
        return text.strip()
    except Exception as e:
        print(f"An error occurred during OCR with easyocr: {e}")
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
