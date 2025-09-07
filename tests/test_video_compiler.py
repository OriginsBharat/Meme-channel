import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call

# Add the parent directory to the path to allow importing the main modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meme_compiler.video_compiler import create_video

class TestVideoCompiler(unittest.TestCase):

    @patch('meme_compiler.video_compiler.download_file')
    @patch('meme_compiler.video_compiler.ImageClip')
    @patch('meme_compiler.video_compiler.VideoFileClip')
    @patch('meme_compiler.video_compiler.AudioFileClip')
    @patch('meme_compiler.video_compiler.concatenate_videoclips')
    @patch('meme_compiler.video_compiler.CompositeVideoClip')
    @patch('shutil.rmtree')
    def test_create_video_logic_horizontal(self, mock_rmtree, mock_composite, mock_concatenate, mock_audio, mock_video, mock_image, mock_download_file):
        # --- Mock Configuration ---
        mock_clip = MagicMock()
        mock_clip.w = 1920
        mock_clip.h = 1080
        mock_clip.duration = 10
        mock_clip.audio = None
        mock_clip.resize.return_value = mock_clip
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.set_audio.return_value = mock_clip
        mock_clip.subclip.return_value = mock_clip
        mock_image.return_value = mock_clip
        mock_video.return_value = mock_clip
        mock_audio.return_value = mock_clip
        mock_concatenate.return_value = mock_clip
        mock_composite.return_value = mock_clip
        mock_download_file.return_value = "/tmp/dummy_meme.jpg"

        # --- Test Data ---
        sample_memes = [{'url': 'http://i.redd.it/meme.jpg', 'title': 'Horizontal Test'}]

        # --- Function Call ---
        create_video(
            selected_memes=sample_memes,
            intro_path="/tmp/intro.mp4",
            outro_path="/tmp/outro.mp4",
            background_path="/tmp/bg.mp4",
            vertical_format=False
        )

        # --- Assertions ---
        mock_download_file.assert_called_with('http://i.redd.it/meme.jpg', 'temp_media')
        mock_video.assert_any_call("/tmp/intro.mp4")
        expected_width = 1920 * 0.9
        mock_clip.resize.assert_any_call(width=expected_width)
        mock_clip.write_videofile.assert_called_once()


    @patch('meme_compiler.video_compiler.download_file')
    @patch('meme_compiler.video_compiler.ImageClip')
    @patch('meme_compiler.video_compiler.VideoFileClip')
    @patch('meme_compiler.video_compiler.AudioFileClip')
    @patch('meme_compiler.video_compiler.concatenate_videoclips')
    @patch('meme_compiler.video_compiler.CompositeVideoClip')
    @patch('meme_compiler.video_compiler.vfx')
    @patch('shutil.rmtree')
    def test_create_video_logic_vertical(self, mock_rmtree, mock_vfx, mock_composite, mock_concatenate, mock_audio, mock_video, mock_image, mock_download_file):
        # --- Mock Configuration ---
        mock_clip = MagicMock()
        mock_clip.w = 1920
        mock_clip.h = 1080
        mock_clip.duration = 10
        mock_clip.audio = None
        mock_clip.resize.return_value = mock_clip
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.set_audio.return_value = mock_clip
        mock_clip.subclip.return_value = mock_clip
        mock_vfx.crop.return_value = mock_clip
        mock_image.return_value = mock_clip
        mock_video.return_value = mock_clip
        mock_audio.return_value = mock_clip
        mock_concatenate.return_value = mock_clip
        mock_composite.return_value = mock_clip
        mock_download_file.return_value = "/tmp/dummy_meme.jpg"

        # --- Test Data ---
        sample_memes = [{'url': 'http://i.redd.it/meme.jpg', 'title': 'Vertical Test'}]

        # --- Function Call ---
        create_video(
            selected_memes=sample_memes,
            intro_path="/tmp/intro.mp4",
            outro_path="/tmp/outro.mp4",
            background_path="/tmp/bg.mp4",
            vertical_format=True
        )

        # --- Assertions ---
        mock_clip.resize.assert_any_call(width=1080)
        self.assertGreaterEqual(mock_vfx.crop.call_count, 3)
        mock_clip.write_videofile.assert_called_once()

    @patch('meme_compiler.video_compiler.download_file')
    @patch('meme_compiler.video_compiler.extract_text_from_image')
    @patch('meme_compiler.video_compiler.ImageClip')
    @patch('meme_compiler.video_compiler.VideoFileClip')
    @patch('meme_compiler.video_compiler.AudioFileClip')
    @patch('meme_compiler.video_compiler.concatenate_videoclips')
    @patch('meme_compiler.video_compiler.CompositeVideoClip')
    @patch('meme_compiler.video_compiler.generate_elevenlabs_tts')
    @patch('shutil.rmtree')
    def test_create_video_with_tts_failure(self, mock_rmtree, mock_generate_tts, mock_composite, mock_concatenate, mock_audio, mock_video, mock_image, mock_extract_text, mock_download_file):
        # --- Mock Configuration ---
        mock_generate_tts.return_value = False # Simulate TTS failure
        mock_download_file.return_value = "/tmp/dummy_meme.jpg"
        mock_extract_text.return_value = "some text"

        # Configure mocks with all necessary attributes to prevent comparison errors
        mock_image_clip = MagicMock(duration=10, audio=None)
        mock_image_clip.set_duration.return_value = mock_image_clip
        mock_image_clip.resize.return_value = mock_image_clip
        mock_image.return_value = mock_image_clip

        mock_video_clip = MagicMock(duration=10, audio=None, w=100, h=100)
        mock_video_clip.subclip.return_value = mock_video_clip
        mock_video_clip.fx.return_value = mock_video_clip
        mock_video.return_value = mock_video_clip

        mock_final_clip = MagicMock()
        mock_concatenate.return_value = mock_final_clip
        mock_composite.return_value = mock_final_clip

        # --- Test Data ---
        sample_memes = [{'url': 'http://i.redd.it/meme.jpg', 'title': 'Test Meme Title'}]

        # --- Function Call ---
        failed_memes = create_video(
            selected_memes=sample_memes,
            intro_path="/tmp/intro.mp4",
            outro_path="/tmp/outro.mp4",
            background_path="/tmp/bg.mp4",
            enable_tts=True
        )

        # --- Assertions ---
        self.assertIsNotNone(failed_memes, "Function should not return None on TTS failure")
        self.assertEqual(len(failed_memes), 1)
        self.assertEqual(failed_memes[0], 'Test Meme Title')


if __name__ == '__main__':
    unittest.main()
