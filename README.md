# Meme Video Compiler

A desktop application to automatically find memes on Reddit and compile them into a short video, complete with a user-provided intro, outro, background video, background music, and a high-quality Text-to-Speech (TTS) voiceover.

## Features

- **Keyword Search**: Finds memes on Reddit based on a keyword.
- **Meme Selection**: A simple UI with checkboxes to select your favorite memes and a preview pane to view them.
- **Fully Customizable Videos**: Use your own intro, outro, background video, and background music.
- **Cloud-Powered OCR & TTS**: Integrates with OCR.space and ElevenLabs APIs to provide high-quality text extraction and natural-sounding voiceovers.
- **Voice Previews**: Listen to a sample of each ElevenLabs voice before you compile the video.
- **Centralized API Management**: A dedicated settings tab to manage your API keys for all services.
- **Usage Tracking**: See your remaining ElevenLabs character count directly in the app.
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
2.  Scroll to the bottom and click **"are you a developer? create an app..."**.
3.  Fill out the form (e.g., name: `MemeCompiler`, type: `script`, redirect uri: `http://localhost:8080`).
4.  Click **"create app"**.
5.  You must make your client ID and client secret available to the application by setting them as **environment variables**:
    *   **On Linux/macOS**:
        ```bash
        export REDDIT_CLIENT_ID="YOUR_CLIENT_ID_HERE"
        export REDDIT_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
        ```
    *   **On Windows (PowerShell)**:
        ```powershell
        $env:REDDIT_CLIENT_ID="YOUR_CLIENT_ID_HERE"
        $env:REDDIT_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
        ```

#### ElevenLabs & OCR.space
1.  Go to the [ElevenLabs website](https://elevenlabs.io/), sign up, and get your API key from your profile.
2.  Go to the [OCR.space website](https://ocr.space/ocrapi) and register for a free API key.
3.  Launch the application, go to the **"Settings"** tab, paste both API keys into their respective fields.
4.  Click **"Save All Keys & Refresh Voices"**. The app will save your keys locally in a `config.json` file.

### Using the Application

1.  **Launch the application**:
    ```bash
    python3 -m meme_compiler.app
    ```
2.  **Find Memes**: In the "Compiler" tab, enter a keyword and click **"Search..."**.
3.  **Select Memes**: Use the checkboxes to select the memes you want. Click the text of a meme to see a preview in the right-hand pane.
4.  **Add Your Files**:
    *   Click **"Select Intro"**, **"Select Background"**, and **"Select Outro"** to choose your video files.
    *   Click **"Select BG Music"** to choose an audio file (`.mp3`, `.wav`) for the background music (optional).
5.  **Finish & Compile**:
    *   Check **"Add TTS Voiceover"** to enable it.
    *   Select a voice from the dropdown. Click **"Preview Voice"** to hear a sample.
    *   Check **"Create 9:16 Vertical Video"** for a Shorts/TikTok format (optional).
    *   Click **"Compile Video!"** and choose where to save the output file.
    *   Wait for the compilation to finish. This may take several minutes.
