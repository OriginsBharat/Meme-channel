import praw
import os
import logging


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

    # Search for subreddits related to the keyword
    try:
        subreddits = [subreddit.display_name for subreddit in reddit.subreddits.search(keyword, limit=5)]
        if not subreddits:
            logging.warning(f"No subreddits found for keyword: {keyword}")
            return []

        logging.info(f"Found subreddits: {', '.join(subreddits)}")

        for sub_name in subreddits:
            subreddit = reddit.subreddit(sub_name)
            # Get top posts from the last week
            hot_posts = subreddit.hot(limit=limit)

            for post in hot_posts:
                if post.score >= min_upvotes and not post.is_self and not post.stickied:
                    # Check if it's an image or a reddit-hosted video
                    if post.url.endswith(('.jpg', '.jpeg', '.png', '.gif')) or 'v.redd.it' in post.url:
                        memes.append({
                            "title": post.title,
                            "url": post.url,
                            "subreddit": sub_name,
                            "upvotes": post.score
                        })
                        logging.info(f"Found meme: '{post.title}' ({post.score} upvotes) in r/{sub_name}")

    except praw.exceptions.PRAWException as e:
        logging.error(f"A PRAW-related error occurred during Reddit search for keyword '{keyword}'", exc_info=True)

    logging.info(f"Found a total of {len(memes)} memes.")
    return memes

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
            found_memes = find_memes(reddit, keyword_to_search)

            if found_memes:
                print(f"\nFound {len(found_memes)} memes for '{keyword_to_search}':")
                for meme in found_memes:
                    print(f"- {meme['title']} ({meme['url']})")
            else:
                print(f"No memes found for '{keyword_to_search}'.")
        except Exception as e:
            print(f"An error occurred during testing: {e}")
