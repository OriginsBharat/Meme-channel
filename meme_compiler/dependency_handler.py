import shutil
import platform

def check_dependencies():
    """
    Checks for non-Python dependencies (espeak on Linux) and returns an error message if any are missing.

    Returns:
        A string containing an informative error message if dependencies are missing, otherwise None.
    """
    missing = []
    error_message = ""

    # Check for espeak (for pyttsx3 on Linux)
    if platform.system() == "Linux":
        if shutil.which('espeak') is None and shutil.which('espeak-ng') is None:
            missing.append("eSpeak / eSpeak-NG")
            error_message += "eSpeak is required for the Text-to-Speech engine on Linux.\n"
            error_message += "Please install it using your system's package manager (e.g., 'sudo apt-get install espeak').\n\n"

    if not missing:
        return None

    full_message = f"Missing Dependencies: {', '.join(missing)}\n\n" + error_message
    full_message += "The application cannot start until these are installed."

    return full_message

# This file is intended to be used as a module.
