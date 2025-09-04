import os
import sys

# Add the parent directory to the path to allow importing the main modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meme_compiler.tts_processor import get_available_voices, generate_tts_audio

if __name__ == '__main__':
    print("--- Running TTS Processor Tests (pyttsx3) ---")

    print("\n--- Testing Voice Discovery ---")
    voices = get_available_voices()
    if voices:
        print("Found available voices:")
        for name, voice_id in voices.items():
            print(f"- {name}")

        print("\n--- Testing TTS Generation ---")
        # Don't run generation if the default is the only one, as it indicates a missing engine
        if len(voices) > 1:
            first_voice_id = list(voices.values())[0]
            test_text = "Hello, this is a test of the new pyttsx3 engine."
            output_audio_path = "test_pyttsx3_output.mp3"

            if generate_tts_audio(test_text, output_audio_path, first_voice_id):
                if os.path.exists(output_audio_path):
                    print(f"Test audio file created successfully at '{output_audio_path}'.")
                    os.remove(output_audio_path)
                else:
                    print("TTS function returned success, but file was not created.")
            else:
                print("TTS function failed.")
        else:
            print("Skipping TTS generation test as no real voices were found (espeak likely missing).")
    else:
        print("No voices found, cannot test TTS generation.")

    print("\n--- TTS Processor Tests Finished ---")
