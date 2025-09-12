import os
import pytesseract
from PIL import Image
from elevenlabs.client import ElevenLabs
from playsound import playsound
import tempfile

def extract_text_from_image(tesseract_cmd, image_path):
    """
    Extracts text from an image file using Tesseract OCR.
    """
    if not all([tesseract_cmd, image_path]):
        print("OCR Error: Missing Tesseract command path or image path.")
        return ""
        
    try:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        text = pytesseract.image_to_string(Image.open(image_path))
        print(f"Extracted text: '{text.strip()}'")
        return text.strip().replace('\n', ' ')

    except pytesseract.TesseractNotFoundError:
        print(f"Tesseract Error: The Tesseract executable was not found at '{tesseract_cmd}'")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred during OCR processing: {e}")
        return ""

def get_elevenlabs_subscription_info(api_key):
    if not api_key: return None
    try:
        client = ElevenLabs(api_key=api_key)
        return client.user.get_subscription()
    except Exception as e:
        print(f"Error fetching ElevenLabs subscription info: {e}")
        return None

def get_elevenlabs_voices(api_key):
    if not api_key: return {}
    try:
        client = ElevenLabs(api_key=api_key)
        return {voice.name: voice.voice_id for voice in client.voices.get_all().voices}
    except Exception as e:
        print(f"Error fetching ElevenLabs voices: {e}")
        return {}

def generate_elevenlabs_tts(api_key, voice_id, text, output_path):
    if not all([api_key, voice_id, text]):
        return (False, "Missing API key, voice ID, or text.")
    try:
        client = ElevenLabs(api_key=api_key)
        audio_stream = client.text_to_speech.convert(voice_id=voice_id, text=text)
        with open(output_path, 'wb') as f:
            for chunk in audio_stream:
                f.write(chunk)
        print(f"TTS audio saved to {output_path}")
        return (True, None)
    except Exception as e:
        return (False, str(e))

def play_voice_preview(api_key, voice_id):
    if not all([api_key, voice_id]): return
    
    # Use a temporary file to avoid conflicts
    temp_fd, temp_path = tempfile.mkstemp(suffix=".mp3")
    os.close(temp_fd) # Close the file descriptor

    try:
        client = ElevenLabs(api_key=api_key)
        # A shorter, more pleasant preview text
        preview_text = "The quick brown fox jumps over the lazy dog."
        audio_stream = client.text_to_speech.convert(voice_id=voice_id, text=preview_text)
        
        with open(temp_path, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
        
        playsound(temp_path)

    except Exception as e:
        print(f"An error occurred during voice preview: {e}")
    finally:
        # Ensure the temporary file is always deleted
        if os.path.exists(temp_path):
            os.remove(temp_path)
