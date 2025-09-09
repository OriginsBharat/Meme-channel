# Meme Video Compiler

A desktop application to automatically find memes on Reddit and compile them into a short video, complete with a user-provided intro, outro, background video, background music, and a high-quality Text-to-Speech (TTS) voiceover.

## Features

- **Keyword Search**: Finds memes on Reddit based on a keyword.
- **Meme Selection**: A simple UI with checkboxes to select your favorite memes and a preview pane to view them.
- **Fully Customizable Videos**: Use your own intro, outro, background video, and background music.
- **High-Quality TTS**: Integrates with the ElevenLabs API for natural-sounding voiceovers.
- **Tesseract OCR**: Uses the Tesseract engine for local, high-quality text extraction from memes.
- **Voice Previews**: Listen to a sample of each ElevenLabs voice before you compile the video.
- **Centralized Settings**: A dedicated settings tab to manage your ElevenLabs API key and Tesseract executable path.
- **Vertical Video Format**: An option to create videos in a 9:16 aspect ratio for platforms like YouTube Shorts and TikTok.

## Installation

### Step 1: Install Tesseract OCR

This application requires the Tesseract OCR engine to be installed on your system.

1.  Go to the official repository for Windows installers: [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
2.  Download the latest available installer (e.g., `tesseract-ocr-w64-setup-v5.x.x.exe`).
3.  Run the installer. **It is highly recommended to install it in the default location** (e.g., `C:\Program Files\Tesseract-OCR`).
4.  After installation, find the `tesseract.exe` file. Note this full path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`). You will need it inside the app.

### Step 2: Set up the Python Environment

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

### Step 3: Set up API Credentials

You need API keys for Reddit and ElevenLabs.

#### Reddit
1.  Go to [Reddit's app preferences](https://www.reddit.com/prefs/apps).
2.  Create a new 'script' app.
3.  Set your Client ID and Client Secret as **environment variables**:
    *   **On Windows (PowerShell)**:
        ```powershell
        $env:REDDIT_CLIENT_ID="YOUR_CLIENT_ID_HERE"
        $env:REDDIT_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
        ```
    *   **On macOS/Linux**:
        ```bash
        export REDDIT_CLIENT_ID="YOUR_CLIENT_ID_HERE"
        export REDDIT_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
        ```

#### ElevenLabs
1.  Go to the [ElevenLabs website](https://elevenlabs.io/), sign up, and get your API key from your profile.

## Usage Guide

1.  **Launch the application**:
    ```bash
    python3 -m meme_compiler.app
    ```
2.  **Configure Settings (First Run)**:
    *   Go to the **"Settings"** tab.
    *   Paste your **ElevenLabs API Key** into the first field.
    *   Paste the full path to your **`tesseract.exe`** file into the second field (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`).
    *   Click **"Save Settings & Refresh Voices"**. The app will save your settings locally in a `config.json` file.

3.  **Find & Select Memes**: In the "Compiler" tab, enter a keyword, search, and use the checkboxes to select memes.
4.  **Add Your Files**: Select your intro, outro, background video, and optional background music.
5.  **Finish & Compile**: Choose your TTS voice, video format, and click **"Compile Video!"**.
