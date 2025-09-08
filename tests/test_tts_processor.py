import os
import sys
import shutil
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to allow importing the main modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meme_compiler.tts_processor import (
    extract_text_from_image,
    get_elevenlabs_subscription_info,
    get_elevenlabs_voices,
    generate_elevenlabs_tts,
    play_voice_preview
)

class TestOcrProcessor(unittest.TestCase):

    @patch('meme_compiler.tts_processor.requests.post')
    def test_extract_text_from_image_success(self, mock_post):
        # --- Mock Configuration ---
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ParsedResults": [
                {
                    "ParsedText": "This is a test\r\n"
                }
            ],
            "IsErroredOnProcessing": False
        }
        mock_post.return_value = mock_response

        # Create a dummy file to pass to the function
        dummy_path = "dummy_image.png"
        with open(dummy_path, "w") as f:
            f.write("dummy")

        # --- Function Call ---
        text = extract_text_from_image("dummy_ocr_key", dummy_path)

        # --- Assertions ---
        self.assertEqual(text, "This is a test") # Check if it strips whitespace and replaces \r\n
        mock_post.assert_called_once()
        # Clean up dummy file
        os.remove(dummy_path)

    @patch('meme_compiler.tts_processor.requests.post')
    def test_extract_text_from_image_api_error(self, mock_post):
        # --- Mock Configuration ---
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "IsErroredOnProcessing": True,
            "ErrorMessage": ["Test API Error"]
        }
        mock_post.return_value = mock_response

        dummy_path = "dummy_image.png"
        with open(dummy_path, "w") as f:
            f.write("dummy")

        # --- Function Call ---
        text = extract_text_from_image("dummy_ocr_key", dummy_path)

        # --- Assertions ---
        self.assertEqual(text, "") # Should return empty string on error
        os.remove(dummy_path)


# New test class for the ElevenLabs TTS functions
class TestElevenLabsProcessor(unittest.TestCase):
    def setUp(self):
        self.assets_dir = 'test_assets_tts'
        if not os.path.exists(self.assets_dir):
            os.makedirs(self.assets_dir)
        self.dummy_api_key = "dummy_key"

    def tearDown(self):
        if os.path.exists(self.assets_dir):
            shutil.rmtree(self.assets_dir)

    @patch('meme_compiler.tts_processor.ElevenLabs')
    def test_get_subscription_info_success(self, MockElevenLabs):
        mock_client = MockElevenLabs.return_value
        mock_sub = MagicMock()
        mock_sub.character_count = 500
        mock_sub.character_limit = 10000
        mock_client.user.get_subscription.return_value = mock_sub

        info = get_elevenlabs_subscription_info(self.dummy_api_key)
        self.assertIsNotNone(info)
        self.assertEqual(info.character_count, 500)
        MockElevenLabs.assert_called_with(api_key=self.dummy_api_key)

    @patch('meme_compiler.tts_processor.ElevenLabs')
    def test_get_subscription_info_failure(self, MockElevenLabs):
        mock_client = MockElevenLabs.return_value
        mock_client.user.get_subscription.side_effect = Exception("API Error")
        info = get_elevenlabs_subscription_info(self.dummy_api_key)
        self.assertIsNone(info)

    @patch('meme_compiler.tts_processor.ElevenLabs')
    def test_get_voices_success(self, MockElevenLabs):
        mock_client = MockElevenLabs.return_value
        # Configure the mock objects correctly
        mock_voice1 = MagicMock()
        mock_voice1.name = "Rachel"
        mock_voice1.voice_id = "v1"

        mock_voice2 = MagicMock()
        mock_voice2.name = "Josh"
        mock_voice2.voice_id = "v2"

        mock_voices_response = MagicMock()
        mock_voices_response.voices = [mock_voice1, mock_voice2]
        mock_client.voices.get_all.return_value = mock_voices_response

        voices = get_elevenlabs_voices(self.dummy_api_key)
        self.assertEqual(len(voices), 2)
        self.assertIn("Rachel", voices)
        self.assertEqual(voices["Rachel"], "v1")

    @patch('meme_compiler.tts_processor.ElevenLabs')
    def test_generate_tts_success(self, MockElevenLabs):
        mock_client = MockElevenLabs.return_value
        # The convert method returns a generator/iterable of chunks
        mock_client.text_to_speech.convert.return_value = [b'fake_audio_data']
        output_path = os.path.join(self.assets_dir, "test.mp3")

        success, message = generate_elevenlabs_tts(self.dummy_api_key, "v1", "hello", output_path)

        self.assertTrue(success)
        self.assertIsNone(message)
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'rb') as f:
            self.assertEqual(f.read(), b'fake_audio_data')
        mock_client.text_to_speech.convert.assert_called_with(voice_id="v1", text="hello")

    @patch('meme_compiler.tts_processor.playsound')
    @patch('meme_compiler.tts_processor.ElevenLabs')
    def test_play_voice_preview_success(self, MockElevenLabs, mock_playsound):
        mock_client = MockElevenLabs.return_value
        mock_client.text_to_speech.convert.return_value = [b'fake_preview_audio']

        play_voice_preview(self.dummy_api_key, "v1")

        mock_client.text_to_speech.convert.assert_called_with(voice_id="v1", text="Hello, this is a preview of my voice.")
        # Check that playsound was called with the temporary file
        mock_playsound.assert_called_once_with("temp_preview.mp3")
        # Verify the temp file was created and then removed
        self.assertFalse(os.path.exists("temp_preview.mp3"))

if __name__ == '__main__':
    unittest.main()
