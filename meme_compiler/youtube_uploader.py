import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# The scopes define the level of access the application is requesting.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
TOKEN_PICKLE_FILE = "token.pickle"

def get_authenticated_service(client_secrets_file):
    """
    Authenticates with the YouTube API.
    Handles the OAuth 2.0 flow and token management.
    Returns an authenticated YouTube service object.
    """
    credentials = None

    # Load credentials from the token file if it exists.
    if os.path.exists(TOKEN_PICKLE_FILE):
        with open(TOKEN_PICKLE_FILE, "rb") as token:
            credentials = pickle.load(token)

    # If there are no valid credentials available, ask the user to log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(client_secrets_file):
                print(f"Error: Client secrets file not found at '{client_secrets_file}'")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            # This will run a local server to handle the OAuth flow and open a browser window.
            credentials = flow.run_local_server(port=0)
        
        # Save the credentials for the next run.
        with open(TOKEN_PICKLE_FILE, "wb") as token:
            pickle.dump(credentials, token)
    
    try:
        service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
        return service
    except HttpError as e:
        print(f"An error occurred while building the service: {e}")
        return None

def upload_video(youtube_service, file_path, title, description, privacy_status, tags=None):
    """
    Uploads a video to YouTube.

    Args:
        youtube_service: The authenticated YouTube service object.
        file_path: Path to the video file.
        title: The title of the video.
        description: The description of the video.
        privacy_status: 'public', 'private', or 'unlisted'.
        tags: A list of tags for the video.

    Returns:
        The ID of the uploaded video, or None if the upload fails.
    """
    if not os.path.exists(file_path):
        print(f"Video file not found: {file_path}")
        return None
        
    try:
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags or [],
                "categoryId": "20" # 20 is for Gaming, a reasonable default for this app
            },
            "status": {
                "privacyStatus": privacy_status
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

        request = youtube_service.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )

        # This loop will print the upload progress.
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%.")
        
        print(f"Upload successful! Video ID: {response.get('id')}")
        return response.get('id')

    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during upload: {e}")
        return None
