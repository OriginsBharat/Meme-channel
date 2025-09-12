import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meme_compiler.video_compiler import create_video

class TestVideoCompiler(unittest.TestCase):

    def setUp(self):
        self.temp_dir = "temp_media_test"
        # Ensure the test temp directory is clean before each test
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
        os.makedirs(self.temp_dir)

        # Create dummy files that need to exist for paths
        self.dummy_intro_path = os.path.join(self.temp_dir, "intro.mp4")
        self.dummy_outro_path = os.path.join(self.temp_dir, "outro.mp4")
        self.dummy_bg_path = os.path.join(self.temp_dir, "bg.mp4")
        for path in [self.dummy_intro_path, self.dummy_outro_path, self.dummy_bg_path]:
            with open(path, "w") as f:
                f.write("dummy")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    @patch('meme_compiler.video_compiler.download_file')
    def test_create_video_returns_none_if_download_fails(self, mock_download):
        """Test that video creation returns None if all memes fail to download."""
        mock_download.return_value = None
        selected_memes = [{'url': 'http://example.com/meme.jpg', 'title': 'Test'}]

        result = create_video(selected_memes, self.dummy_intro_path, self.dummy_outro_path, self.dummy_bg_path)
        
        self.assertIsNone(result, "Should return None when no memes are downloaded")

    # @patch('meme_compiler.video_compiler.CompositeVideoClip')
    # @patch('meme_compiler.video_compiler.concatenate_videoclips')
    # @patch('meme_compiler.video_compiler.AudioFileClip')
    # @patch('meme_compiler.video_compiler.ImageClip')
    # @patch('meme_compiler.video_compiler.VideoFileClip')
    # @patch('meme_compiler.video_compiler.download_file')
    # @patch('meme_compiler.video_compiler.extract_text_from_image')
    # @patch('meme_compiler.video_compiler.generate_elevenlabs_tts')
    # def test_tts_failure_is_handled_gracefully(self, mock_generate_tts, mock_extract_text, mock_download, mock_video_clip, mock_image_clip, mock_audio_clip, mock_concat, mock_composite):
    #     """Test that if TTS fails, the video is still created and the failure is reported."""
    #     # --- MOCK SETUP ---
    #     # Mock file downloads
    #     meme_path = os.path.join(self.temp_dir, "meme1.jpg")
    #     with open(meme_path, "w") as f: f.write("dummy")
    #     mock_download.return_value = meme_path

    #     # Mock OCR
    #     mock_extract_text.return_value = "This is some text from the meme"

    #     # Mock TTS to simulate a failure
    #     mock_generate_tts.return_value = (False, "Credit limit reached")

    #     # Mock moviepy objects to prevent actual video processing
    #     mock_clip = MagicMock()
    #     mock_clip.duration = 5
    #     mock_clip.audio = None
    #     mock_clip.set_duration.return_value = mock_clip
    #     mock_clip.set_audio.return_value = mock_clip
    #     mock_clip.resize.return_value = mock_clip
    #     mock_clip.subclip.return_value = mock_clip
    #     mock_clip.fx.return_value = mock_clip
        
    #     mock_image_clip.return_value = mock_clip
    #     mock_video_clip.return_value = mock_clip
    #     mock_audio_clip.return_value = mock_clip
    #     mock_concat.return_value = mock_clip
    #     mock_composite.return_value = mock_clip

    #     # --- TEST CALL ---
    #     selected_memes = [{'url': 'http://example.com/meme1.jpg', 'title': 'Test Meme 1'}]
    #     result = create_video(
    #         selected_memes=selected_memes,
    #         intro_path=self.dummy_intro_path,
    #         outro_path=self.dummy_outro_path,
    #         background_path=self.dummy_bg_path,
    #         enable_tts=True,
    #         elevenlabs_api_key="dummy_key",
    #         tesseract_cmd_path="dummy_path",
    #         voice_id="dummy_voice"
    #     )

    #     # --- ASSERTIONS ---
    #     # The function should return a list of failures, not None
    #     self.assertIsInstance(result, list)
    #     # The list should contain our one failed meme
    #     self.assertEqual(len(result), 1)
    #     # The failure tuple should contain the correct title and reason
    #     self.assertEqual(result[0], ('Test Meme 1', 'Credit limit reached'))
    #     # Crucially, the video should still be "written"
    #     mock_clip.write_videofile.assert_called_once()


if __name__ == '__main__':
    unittest.main()
