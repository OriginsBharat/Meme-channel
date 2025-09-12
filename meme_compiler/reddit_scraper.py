import praw
import os
import requests

USER_AGENT = "MemeCompilerApp/0.1 by Jules"

def get_reddit_instance(client_id, client_secret):
    """Initializes and returns a PRAW Reddit instance."""
    if not all([client_id, client_secret]):
        print("Reddit credentials are not configured.")
        return None
    return praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=USER_AGENT)

def _get_image_size(url):
    try:
        response = requests.head(url, timeout=5)
        response.raise_for_status()
        size = int(response.headers.get('Content-Length', 0))
        return size
    except Exception as e:
        print(f"Could not get size for {url}: {e}")
        return -1

def find_memes(reddit, keyword, used_memes_log, limit=25, min_upvotes=500):
    memes = []
    session_urls = set() # To track URLs found in the current session

    # Load used memes from the persistent log file
    if os.path.exists(used_memes_log):
        with open(used_memes_log, 'r') as f:
            used_urls = set(line.strip() for line in f)
    else:
        used_urls = set()

    try:
        subreddits = [subreddit.display_name for subreddit in reddit.subreddits.search(keyword, limit=5)]
        if not subreddits:
            print(f"No subreddits found for keyword: {keyword}")
            return []
        print(f"Found subreddits: {', '.join(subreddits)}")

        for sub_name in subreddits:
            subreddit = reddit.subreddit(sub_name)
            print(f"Searching for '{keyword}' in r/{sub_name}...")
            # Increased search limit to get more diverse results before filtering
            search_results = subreddit.search(keyword, sort="relevance", time_filter="year", limit=limit * 2)
            
            for post in search_results:
                if len(memes) >= limit:
                    break # Stop once we have enough memes

                is_image = post.url.endswith(('.jpg', '.jpeg', '.png'))
                is_gif = post.url.endswith('.gif')
                is_video = hasattr(post, 'is_video') and post.is_video

                if post.score >= min_upvotes and not post.is_self and not post.stickied and (is_image or is_gif or is_video):
                    url_to_use = post.url
                    if is_video:
                        url_to_use = post.media['reddit_video']['fallback_url']

                    # --- Filtering Logic ---
                    # Avoid duplicates from the log file and the current session
                    if url_to_use in used_urls or url_to_use in session_urls:
                        continue
                    
                    memes.append({
                        "title": post.title,
                        "url": url_to_use,
                        "subreddit": sub_name,
                        "upvotes": post.score
                    })
                    session_urls.add(url_to_use) # Add to session tracker
                    print(f"Found meme: {post.title} ({post.score} upvotes)")
            
            if len(memes) >= limit:
                break # Stop searching other subreddits if we have enough

    except Exception as e:
        print(f"An error occurred during Reddit search: {e}")
        
    return memes
