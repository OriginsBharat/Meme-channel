import praw
import os
import logging
import tempfile
from .utils import download_file


def get_reddit_instance(client_id, client_secret, user_agent):
    """
    Initializes and returns a PRAW Reddit instance.

    Args:
        client_id (str): Your Reddit app's client ID.
        client_secret (str): Your Reddit app's client secret.
        user_agent (str): A unique user agent string.

    Returns:
        An authenticated PRAW Reddit instance or None if credentials are not provided.
    """
    if not all([client_id, client_secret, user_agent]):
        raise ValueError("Reddit API credentials are not fully provided.")

    logging.info("Initializing PRAW Reddit instance.")
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )

def find_memes(reddit, keyword, limit=25, min_upvotes=500):
    """
    Finds memes on Reddit based on a keyword.

    Args:
        reddit: An authenticated PRAW Reddit instance.
        keyword (str): The keyword to search for.
        limit (int): The number of posts to fetch from each subreddit.
        min_upvotes (int): The minimum number of upvotes a post must have.

    Returns:
        A list of dictionaries, where each dictionary contains post title and url.
    """
    memes = []
    logging.info(f"Starting meme search for keyword: '{keyword}' with limit={limit}, min_upvotes={min_upvotes}")

    # Create a single temporary directory for all thumbnails for this search
    temp_dir = tempfile.mkdtemp(prefix="meme-compiler-")
    logging.info(f"Created temporary directory for thumbnails: {temp_dir}")

    try:
        subreddits = [subreddit.display_name for subreddit in reddit.subreddits.search(keyword, limit=5)]
        if not subreddits:
            logging.warning(f"No subreddits found for keyword: {keyword}")
            return [], temp_dir

        logging.info(f"Found subreddits: {', '.join(subreddits)}")

        for sub_name in subreddits:
            subreddit = reddit.subreddit(sub_name)
            hot_posts = subreddit.hot(limit=limit)

            for post in hot_posts:
                if post.score >= min_upvotes and not post.is_self and not post.stickied:
                    is_image = post.url.endswith(('.jpg', '.jpeg', '.png'))
                    is_gif = post.url.endswith('.gif')

                    if is_image or is_gif:
                        thumbnail_path = download_file(post.url, temp_dir)
                        if thumbnail_path:
                            memes.append({
                                "title": post.title,
                                "url": post.url,
                                "subreddit": sub_name,
                                "upvotes": post.score,
                                "thumbnail_path": thumbnail_path,
                                "is_video": is_gif # Treat gifs as videos
                            })
                            logging.info(f"Found and downloaded meme: '{post.title}'")
                        else:
                            logging.warning(f"Failed to download meme: {post.title} from {post.url}")

    except praw.exceptions.PRAWException as e:
        logging.error(f"A PRAW-related error occurred during Reddit search for keyword '{keyword}'", exc_info=True)

    logging.info(f"Found a total of {len(memes)} memes.")
    # Return the temp directory path so it can be cleaned up later
    return memes, temp_dir

if __name__ == '__main__':
    # This is for testing the scraper directly.
    # It requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT env vars.
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT")

    if not all([client_id, client_secret, user_agent]):
        print("Please set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and REDDIT_USER_AGENT env vars to test.")
    else:
        try:
            reddit = get_reddit_instance(client_id, client_secret, user_agent)
            keyword_to_search = "memes"
            found_memes, temp_dir = find_memes(reddit, keyword_to_search)

            if found_memes:
                print(f"\nFound {len(found_memes)} memes for '{keyword_to_search}':")
                for meme in found_memes:
                    print(f"- {meme['title']} ({meme['url']}) -> {meme['thumbnail_path']}")
            else:
                print(f"No memes found for '{keyword_to_search}'.")
        except Exception as e:
            print(f"An error occurred during testing: {e}")
        finally:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                print(f"Cleaning up temporary directory: {temp_dir}")
                shutil.rmtree(temp_dir)
