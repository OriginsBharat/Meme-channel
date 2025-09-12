import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to allow importing the main modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meme_compiler.reddit_scraper import find_memes

class TestRedditScraper(unittest.TestCase):

    def setUp(self):
        self.used_memes_log = "test_used_memes.txt"
        # Ensure the log file is clean before each test
        if os.path.exists(self.used_memes_log):
            os.remove(self.used_memes_log)

    def tearDown(self):
        # Clean up the log file after each test
        if os.path.exists(self.used_memes_log):
            os.remove(self.used_memes_log)

    @patch('meme_compiler.reddit_scraper.requests.head')
    @patch('meme_compiler.reddit_scraper.praw.Reddit')
    def test_find_memes_filtering(self, MockReddit, mock_head):
        # --- Mock Configuration ---
        # Mock the PRAW search results
        mock_post1 = MagicMock(url="http://i.redd.it/large_meme.jpg", is_video=False, score=600, is_self=False, stickied=False, title="Large Meme")
        mock_post2 = MagicMock(url="http://i.redd.it/good_meme.jpg", is_video=False, score=600, is_self=False, stickied=False, title="Good Meme")
        mock_post3 = MagicMock(url="http://i.redd.it/used_meme.jpg", is_video=False, score=600, is_self=False, stickied=False, title="Used Meme")
        mock_post4 = MagicMock(url="http://v.redd.it/video_meme.mp4", is_video=True, score=600, is_self=False, stickied=False, title="Video Meme", media={'reddit_video': {'fallback_url': 'http://v.redd.it/video_meme.mp4'}})

        mock_subreddit = MagicMock()
        mock_subreddit.search.return_value = [mock_post1, mock_post2, mock_post3, mock_post4]
        
        mock_reddit_instance = MockReddit.return_value
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        # Mock the subreddits search to return at least one subreddit
        mock_reddit_instance.subreddits.search.return_value = [MagicMock(display_name="memes")]

        # Mock the HEAD request for file sizes
        def head_side_effect(url, timeout):
            mock_resp = MagicMock()
            if "large_meme" in url:
                mock_resp.headers = {'Content-Length': '2000000'} # 2MB
            else:
                mock_resp.headers = {'Content-Length': '500000'} # 0.5MB
            return mock_resp
        mock_head.side_effect = head_side_effect
        
        # Create a dummy used_memes file
        with open(self.used_memes_log, "w") as f:
            f.write("http://i.redd.it/used_meme.jpg\n")

        # --- Function Call ---
        memes = find_memes(mock_reddit_instance, "test", self.used_memes_log)

        # --- Assertions ---
        self.assertEqual(len(memes), 2) # Should find the good image and the video
        
        found_titles = [m['title'] for m in memes]
        self.assertIn("Good Meme", found_titles)
        self.assertIn("Video Meme", found_titles)
        
        self.assertNotIn("Large Meme", found_titles) # Should be filtered by size
        self.assertNotIn("Used Meme", found_titles) # Should be filtered by log file

if __name__ == '__main__':
    unittest.main()
