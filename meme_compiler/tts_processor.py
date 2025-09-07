import easyocr
import pyttsx3
import os

# --- OCR Model Initialization ---
# This is done once when the module is imported. It can take a moment
# as it loads the deep learning model into memory.
print("Initializing OCR engine (easyocr)... This may take a moment.")
try:
    reader = easyocr.Reader(['en'])
    print("OCR engine initialized successfully.")
except Exception as e:
    print(f"CRITICAL: Could not initialize OCR engine. Text extraction will not work. Error: {e}")
    reader = None

def extract_text_from_image(image_path):
    """
    Extracts text from an image file using EasyOCR.

    Args:
        image_path (str): The path to the image file.

    Returns:
        A string containing the extracted text, or an empty string if no text is found or an error occurs.
    """
    if not reader:
        print("OCR reader not available.")
        return ""

    try:
        # The 'detail=0' parameter returns a list of strings directly.
        result = reader.readtext(image_path, detail=0, paragraph=True)
        text = " ".join(result)
        print(f"Extracted text: '{text.strip()}'")
        return text.strip()
    except Exception as e:
        print(f"An error occurred during OCR with easyocr: {e}")
        return ""

def get_available_voices():
    """
    Gets a list of available TTS voices from pyttsx3.

    Returns:
        A dictionary mapping a display name (e.g., "Voice 0 - Male") to the voice ID.
    """
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.stop()
        voice_dict = {}
        for i, voice in enumerate(voices):
            gender = "Female" if hasattr(voice, 'gender') and voice.gender and "female" in voice.gender.lower() else "Male"
            name = f"Voice {i} ({voice.name}, {gender})"
            voice_dict[name] = voice.id
        return voice_dict
    except Exception as e:
        print(f"Could not get pyttsx3 voices. TTS might not work. Error: {e}")
        return {"Default": "default"}


def generate_tts_audio(text, output_path, voice_id=None):
    """
    Generates an audio file from text using pyttsx3.

    Args:
        text (str): The text to convert to speech.
        output_path (str): The path to save the output audio file (e.g., .mp3, .wav).
        voice_id (str, optional): The ID of the voice to use. Defaults to None (pyttsx3 default).

    Returns:
        True if successful, False otherwise.
    """
    if not text:
        print("No text provided for TTS.")
        return False

    try:
        engine = pyttsx3.init()
        if voice_id and voice_id != "default":
            engine.setProperty('voice', voice_id)

        engine.save_to_file(text, output_path)
        engine.runAndWait()
        engine.stop()
        print(f"TTS audio saved to {output_path}")
        return True
    except Exception as e:
        print(f"An error occurred during pyttsx3 TTS generation: {e}")
        return False

# This file is intended to be used as a module.
# The test harness has been moved to tests/test_tts_processor.py
