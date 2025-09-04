import shutil
from .tts_processor import is_tesseract_installed

def check_dependencies():
    """
    Checks for non-Python dependencies (Tesseract, espeak) and returns an error message if any are missing.

    Returns:
        A string containing an informative error message if dependencies are missing, otherwise None.
    """
    missing = []
    error_message = ""

    # 1. Check for Tesseract
    if not is_tesseract_installed():
        missing.append("Tesseract OCR")
        error_message += "Tesseract is required for reading text from memes.\n"
        error_message += "Please install it from: https://github.com/tesseract-ocr/tesseract\n\n"

    # 2. Check for espeak (for pyttsx3 on Linux)
    if shutil.which('espeak') is None and shutil.which('espeak-ng') is None:
        # This check is primarily for Linux. Windows and macOS have their own TTS engines.
        # A more robust check would be platform-specific.
        import platform
        if platform.system() == "Linux":
            missing.append("eSpeak / eSpeak-NG")
            error_message += "eSpeak is required for the Text-to-Speech engine on Linux.\n"
            error_message += "Please install it using your system's package manager (e.g., 'sudo apt-get install espeak').\n\n"

    if not missing:
        return None

    full_message = f"Missing Dependencies: {', '.join(missing)}\n\n" + error_message
    full_message += "The application cannot start until these are installed."

    return full_message

# This file is intended to be used as a module.
