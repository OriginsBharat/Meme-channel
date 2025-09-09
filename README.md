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
- **Centralized Settings**: A dedicated settings tab to manage all your API keys.
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

## Usage Guide

### Step 1: Get API Credentials

You need credentials for three services. The app will save them all securely in a local `config.json` file, so you only need to enter them once.

1.  **Reddit**:
    *   Go to [Reddit's app preferences](https://www.reddit.com/prefs/apps).
    *   Create a new 'script' app. You will get a **Client ID** and a **Client Secret**.
2.  **ElevenLabs**:
    *   Go to the [ElevenLabs website](https://elevenlabs.io/), sign up, and get your **API Key**.
3.  **OCR.space**:
    *   Go to the [OCR.space website](https://ocr.space/ocrapi) and register for a free **API Key**.

### Step 2: Configure and Run the App

1.  **Launch the application**:
    ```bash
    python3 -m meme_compiler.app
    ```
2.  **Enter All Credentials**:
    *   Go to the **"Settings"** tab.
    *   Carefully paste your Reddit, ElevenLabs, and OCR.space credentials into the correct fields.
    *   Click **"Save All Settings & Refresh Voices"**.
3.  **Start Compiling!**
    *   Go to the "Compiler" tab and start making videos. All your settings are saved for future use.
