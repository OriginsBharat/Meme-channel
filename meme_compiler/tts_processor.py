import pytesseract
import pyttsx3
import os
import logging
from PIL import Image

def is_tesseract_installed():
    """Checks if the Tesseract command is available."""
    try:
        pytesseract.get_tesseract_version()
        logging.info("Tesseract is installed and accessible.")
        return True
    except pytesseract.TesseractNotFoundError:
        logging.warning("Tesseract Not Found: OCR functionality will not work.")
        return False

def extract_text_from_image(image_path):
    """Extracts text from an image file using Tesseract OCR."""
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        logging.info(f"Extracted text: '{text.strip()}' from {image_path}")
        return text.strip()
    except (pytesseract.TesseractError, FileNotFoundError) as e:
        logging.error(f"An error occurred during OCR on {image_path}", exc_info=True)
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
        engine.stop() # Stop engine after getting properties
        voice_dict = {}
        for i, voice in enumerate(voices):
            gender = "Female" if "female" in voice.gender.lower() else "Male"
            name = f"Voice {i} ({voice.name}, {gender})"
            voice_dict[name] = voice.id
        logging.info(f"Discovered {len(voice_dict)} TTS voices.")
        return voice_dict
    except RuntimeError as e:
        logging.error("Could not get pyttsx3 voices. TTS engine likely failed to initialize.", exc_info=True)
        return {}


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
        logging.warning("No text provided for TTS generation.")
        return False

    try:
        engine = pyttsx3.init()
        if voice_id and voice_id != "default":
            engine.setProperty('voice', voice_id)

        engine.save_to_file(text, output_path)
        engine.runAndWait() # Process the command queue
        engine.stop()
        logging.info(f"TTS audio saved to {output_path}")
        return True
    except RuntimeError as e:
        logging.error(f"An error occurred during pyttsx3 TTS generation for {output_path}", exc_info=True)
        return False

# This file is intended to be used as a module.
# The test harness has been moved to tests/test_tts_processor.py
