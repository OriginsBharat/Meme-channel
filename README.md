# Meme Video Compiler

A desktop application to automatically find and compile image and video memes from Reddit into a short video, complete with a user-provided intro, outro, background video, background music, and a high-quality Text-to-Speech (TTS) voiceover for image-based memes.

## Features

- **Keyword Search**: Finds image and video memes on Reddit based on a keyword.
- **Content Filtering**: Automatically skips memes you have already used in a previous video.
- **Meme Selection & Preview**:
    - A simple UI with checkboxes to select your favorite memes.
    - A preview pane that can display images and play video/GIF memes.
- **Fully Customizable Videos**: Use your own intro, outro, background video, and background music.
- **High-Quality TTS**: Integrates with the **ElevenLabs API** for natural-sounding voiceovers.
- **Tesseract OCR**: Uses the Tesseract engine for local, high-quality text extraction from memes.
- **Centralized Settings**: A dedicated settings tab to manage all your API keys and the Tesseract executable path.
- **Vertical Video Format**: An option to create videos in a 9:16 aspect ratio for platforms like YouTube Shorts and TikTok.

## Installation

### Step 1: Install Tesseract OCR

This application requires the Tesseract OCR engine to be installed on your system.

1.  Go to the official repository for Windows installers: **[Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)**.
2.  On that page, find and download the latest available installer (e.g., `tesseract-ocr-w64-setup-v5.x.x.exe`).
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

### Step 3: Configure the Application

1.  **Launch the application**:
    ```bash
    python -m meme_compiler.app
    ```
2.  **Enter All Credentials in Settings**:
    *   Go to the **"Settings"** tab.
    *   Paste your **Reddit Client ID** and **Client Secret**.
    *   Paste your **ElevenLabs API Key**.
    *   Paste the full path to your **`tesseract.exe`** file from Step 1.
    *   Click **"Save All Settings & Refresh Voices"**. The app will save your settings locally in a `config.json` file.

## Usage

1.  **Find & Select Memes**: In the "Compiler" tab, enter a keyword, search, and use the checkboxes to select memes.
2.  **Add Your Files**: Select your intro, outro, background video, and optional background music.
3.  **Finish & Compile**: Choose your TTS voice, video format, and click **"Compile Video!"**.
4.  After a video is created, the app will save the URLs of the used memes to `used_memes.txt` to prevent them from showing up in future searches.
