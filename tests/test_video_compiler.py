import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call

# Add the parent directory to the path to allow importing the main modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meme_compiler.video_compiler import create_video

class TestVideoCompiler(unittest.TestCase):

    # This is a complex mock setup. We need to patch all moviepy and other external functions
    # to test the logic of 'create_video' without actually creating a video.
    @patch('meme_compiler.video_compiler.download_file')
    @patch('meme_compiler.video_compiler.ImageClip')
    @patch('meme_compiler.video_compiler.VideoFileClip')
    @patch('meme_compiler.video_compiler.AudioFileClip')
    @patch('meme_compiler.video_compiler.concatenate_videoclips')
    @patch('meme_compiler.video_compiler.CompositeVideoClip')
    @patch('shutil.rmtree') # Mock filesystem cleanup
    def test_create_video_logic_horizontal(self, mock_rmtree, mock_composite, mock_concatenate, mock_audio, mock_video, mock_image, mock_download_file):
        """
        Tests the video creation logic for the default horizontal format by checking
        if moviepy functions are called with the correct parameters.
        """
        # --- Mock Configuration ---
        # Mock the clip objects to have necessary attributes (w, h, duration, audio)
        mock_clip = MagicMock()
        mock_clip.w = 1920
        mock_clip.h = 1080
        mock_clip.duration = 10
        mock_clip.audio = None
        # The 'resize' and other methods should also return a mock
        mock_clip.resize.return_value = mock_clip
        mock_clip.set_duration.return_value = mock_clip
        mock_clip.set_audio.return_value = mock_clip
        mock_clip.subclip.return_value = mock_clip

        # Assign the configured mock to the patched classes
        mock_image.return_value = mock_clip
        mock_video.return_value = mock_clip
        mock_audio.return_value = mock_clip
        mock_concatenate.return_value = mock_clip
        mock_composite.return_value = mock_clip

        # Mock download_file to return a dummy path
        mock_download_file.return_value = "/tmp/dummy_meme.jpg"

        # --- Test Data ---
        sample_memes = [{'url': 'http://i.redd.it/meme.jpg'}]

        # --- Function Call ---
        create_video(
            selected_memes=sample_memes,
            intro_path="/tmp/intro.mp4",
            outro_path="/tmp/outro.mp4",
            background_path="/tmp/bg.mp4",
            vertical_format=False # Test horizontal format
        )

        # --- Assertions ---
        # Assert that the meme was "downloaded"
        mock_download_file.assert_called_with('http://i.redd.it/meme.jpg', 'temp_media')

        # Assert that the clips were loaded
        mock_video.assert_any_call("/tmp/intro.mp4")
        mock_video.assert_any_call("/tmp/outro.mp4")
        mock_video.assert_any_call("/tmp/bg.mp4")
        mock_image.assert_called_with("/tmp/dummy_meme.jpg")

        # Assert resize logic for horizontal format (90% of background width)
        expected_width = 1920 * 0.9
        mock_clip.resize.assert_any_call(width=expected_width)

        # Assert that the final video was written
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
        """
        Tests the video creation logic for the 9:16 vertical format.
        """
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

        # Mock the crop function specifically
        mock_vfx.crop.return_value = mock_clip

        mock_image.return_value = mock_clip
        mock_video.return_value = mock_clip
        mock_audio.return_value = mock_clip
        mock_concatenate.return_value = mock_clip
        mock_composite.return_value = mock_clip
        mock_download_file.return_value = "/tmp/dummy_meme.jpg"

        # --- Test Data ---
        sample_memes = [{'url': 'http://i.redd.it/meme.jpg'}]

        # --- Function Call ---
        create_video(
            selected_memes=sample_memes,
            intro_path="/tmp/intro.mp4",
            outro_path="/tmp/outro.mp4",
            background_path="/tmp/bg.mp4",
            vertical_format=True # Test vertical format
        )

        # --- Assertions ---
        # Assert resize logic for vertical format (width of 1080)
        mock_clip.resize.assert_any_call(width=1080)

        # Assert that the crop function was called for the background videos
        self.assertGreaterEqual(mock_vfx.crop.call_count, 3)
        # Check that it was called with the correct target dimensions
        mock_vfx.crop.assert_any_call(mock_clip, width=1080, height=1920, x_center=mock_clip.w / 2, y_center=mock_clip.h / 2)

        # Assert that the final video was written
        mock_clip.write_videofile.assert_called_once()


if __name__ == '__main__':
    unittest.main()
