import praw
import os

# It's recommended to use environment variables for credentials
# For now, we will use placeholders. The final app will have input fields for these.
# IMPORTANT: The user will need to get their own Reddit API credentials.
# You can get them by creating an app on Reddit: https://www.reddit.com/prefs/apps
CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID")
CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "MemeCompilerApp/0.1 by YourUsername")

def get_reddit_instance():
    """Initializes and returns a PRAW Reddit instance."""
    return praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
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

    # Search for subreddits related to the keyword
    try:
        subreddits = [subreddit.display_name for subreddit in reddit.subreddits.search(keyword, limit=5)]
        if not subreddits:
            print(f"No subreddits found for keyword: {keyword}")
            return []

        print(f"Found subreddits: {', '.join(subreddits)}")

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
                        print(f"Found meme: {post.title} ({post.score} upvotes)")

    except Exception as e:
        print(f"An error occurred: {e}")
        # In a real app, this would be logged and shown to the user

    return memes

if __name__ == '__main__':
    # This is for testing the scraper directly
    reddit = get_reddit_instance()
    # A sample keyword
    keyword_to_search = "memes"
    found_memes = find_memes(reddit, keyword_to_search)

    if found_memes:
        print(f"\nFound {len(found_memes)} memes for '{keyword_to_search}':")
        for meme in found_memes:
            print(f"- {meme['title']} ({meme['url']})")
    else:
        print(f"No memes found for '{keyword_to_search}'. "
              f"Try checking your Reddit API credentials or using a different keyword.")
