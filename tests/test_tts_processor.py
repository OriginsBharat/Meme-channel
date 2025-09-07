import os
import sys
import shutil

# Add the parent directory to the path to allow importing the main modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meme_compiler.tts_processor import get_available_voices, generate_tts_audio, extract_text_from_image

if __name__ == '__main__':
    print("--- Running TTS & OCR Processor Tests ---")

    # This import is here because Pillow is a dependency of the main app, not the test itself
    from PIL import Image, ImageDraw, ImageFont

    assets_dir = 'test_assets'

    try:
        # --- Setup Test Assets ---
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)

        test_image_path = os.path.join(assets_dir, "test_ocr_image.png")

        try:
            img = Image.new('RGB', (600, 150), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 40)
            except IOError:
                print("Default font not found for test image. Using basic font.")
                font = ImageFont.load_default()
            test_string = "This is a test for easyocr"
            draw.text((10, 10), test_string, fill=(0, 0, 0), font=font)
            img.save(test_image_path)
            print(f"Created test image at: {test_image_path}")
        except Exception as e:
            print(f"Failed to create test image. Cannot run OCR test. Error: {e}")
            test_image_path = None # Ensure test doesn't run if image fails

        # --- Run OCR Test ---
        if test_image_path:
            print("\n--- Testing OCR (easyocr) ---")
            extracted_text = extract_text_from_image(test_image_path)
            if extracted_text:
                print(f"SUCCESS: Extracted text: '{extracted_text}'")
                if test_string.lower() in extracted_text.lower():
                    print("SUCCESS: Found original string in extracted text.")
                else:
                    print("WARNING: Original string not found in extracted text.")
            else:
                print("FAILURE: OCR did not extract any text.")

        # --- Run TTS Tests ---
        print("\n--- Testing Voice Discovery ---")
        voices = get_available_voices()
        if voices:
            print("Found available voices:")
            for name, voice_id in voices.items():
                print(f"- {name}")

            print("\n--- Testing TTS Generation ---")
            if len(voices) > 1 or (len(voices) == 1 and "default" not in list(voices.keys())[0].lower()):
                first_voice_id = list(voices.values())[0]
                test_text = "Hello, this is a test of the new pyttsx3 engine."
                output_audio_path = os.path.join(assets_dir, "test_pyttsx3_output.mp3")

                if generate_tts_audio(test_text, output_audio_path, first_voice_id):
                    if os.path.exists(output_audio_path):
                        print(f"SUCCESS: Test audio file created successfully.")
                    else:
                        print("FAILURE: TTS function returned success, but file was not created.")
                else:
                    print("FAILURE: TTS function failed.")
            else:
                print("Skipping TTS generation test as no real voices were found (espeak likely missing).")
        else:
            print("No voices found, cannot test TTS generation.")

    finally:
        # --- Cleanup ---
        print("\n--- Cleaning up test assets ---")
        if os.path.exists(assets_dir):
            shutil.rmtree(assets_dir)
            print(f"Removed test assets directory: {assets_dir}")

    print("\n--- TTS & OCR Processor Tests Finished ---")
