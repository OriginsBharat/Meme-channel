# Meme Video Compiler

A desktop application to automatically find and compile image and video memes from Reddit into a short video, complete with a user-provided intro, outro, background video, background music, and a high-quality Text-to-Speech (TTS) voiceover for image-based memes.

## Features

- **Keyword Search**: Finds image and video memes on Reddit based on a keyword.
- **Content Filtering**:
    - Automatically skips image memes larger than 1MB to work with the OCR.space API.
    - Automatically skips memes you have already used in a previous video.
- **Meme Selection & Preview**:
    - A simple UI with checkboxes to select your favorite memes.
    - A preview pane that can display images and play video/GIF memes.
- **Fully Customizable Videos**: Use your own intro, outro, background video, and background music.
- **Cloud-Powered OCR & TTS**:
    - Integrates with the **OCR.space API** for accurate text extraction from images.
    - Integrates with the **ElevenLabs API** for natural-sounding voiceovers.
- **Voice Previews**: Listen to a sample of each ElevenLabs voice before you compile the video.
- **Centralized API Management**: A dedicated settings tab to manage your API keys.
- **Vertical Video Format**: An option to create videos in a 9:16 aspect ratio for platforms like YouTube Shorts and TikTok.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
2.  **Create a virtual environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```
3.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set Environment Variables** for the Reddit API (see Usage section below).

## Usage Guide

### Step 0: API Credentials

You need API keys for Reddit, ElevenLabs, and OCR.space.

#### Reddit
1.  Go to [Reddit's app preferences](https://www.reddit.com/prefs/apps).
2.  Create a new 'script' app.
3.  Set your Client ID and Client Secret as **environment variables**.

#### ElevenLabs & OCR.space
1.  Go to the [ElevenLabs website](https://elevenlabs.io/) and get an API key.
2.  Go to the [OCR.space website](https://ocr.space/ocrapi) and register for a free API key.

### Using the Application

1.  **Launch the application**:
    ```bash
    python3 -m meme_compiler.app
    ```
2.  **Configure Settings (First Run)**:
    *   Go to the **"Settings"** tab.
    *   Paste your **ElevenLabs API Key** and **OCR.space API Key** into their respective fields.
    *   Click **"Save All Keys & Refresh Voices"**. The app will save your keys locally in a `config.json` file.

3.  **Find & Select Memes**:
    *   In the "Compiler" tab, enter a keyword and click **"Search..."**.
    *   Click the **"Refresh"** button to run the same search again, which will show new memes if available (and hide ones you've already used).
    *   Use the checkboxes to select the memes you want. Click the text of a meme to see a preview.
4.  **Add Your Files**: Select your intro, outro, background video, and optional background music.
5.  **Finish & Compile**: Choose your TTS voice (for images), video format, and click **"Compile Video!"**.
6.  After a video is created, the app will save the URLs of the used memes to `used_memes.txt` to prevent them from showing up in future searches.
