# Meme Video Compiler

A desktop application to automatically find memes on Reddit and compile them into a short video, complete with an intro, outro, background video, and Text-to-Speech (TTS) voiceover.

## Features

- **Keyword Search**: Finds memes on Reddit based on a keyword (e.g., "dankmemes").
- **Upvote Filtering**: Gathers posts with 500+ upvotes.
- **Meme Selection**: Displays the found memes for you to select your favorites.
- **Custom Videos**: Allows you to use your own intro, outro, and background gameplay videos.
- **Offline TTS**: Generates a voiceover for image-based memes using a selection of offline voices.
- **Step-by-Step UI**: A simple, wizard-style user interface guides you through the process.
- **Standalone**: Can be built into a single executable file.

## Installation

There are two ways to use this application: by running the pre-built executable (easiest) or by running the source code directly (for developers).

### Method 1: Running the Executable (Recommended)

1.  Navigate to the **"Releases"** page on this GitHub repository.
2.  Download the `MemeCompiler` executable for your operating system (e.g., `MemeCompiler.exe` for Windows).
3.  **Install Dependencies**: Before running the app, you may need to install two system-level dependencies if you don't already have them:
    *   **Tesseract OCR**: Required for reading text from images. [Installation Guide](https://github.com/tesseract-ocr/tesseract)
    *   **eSpeak / eSpeak-NG** (for Linux users): Required for the TTS engine. You can usually install it with `sudo apt-get install espeak`.
4.  Run the `MemeCompiler` executable.

### Method 2: Running from Source (For Developers)

1.  **Clone the repository**:
    ```bash
    git clone <repository_url>
    cd meme-compiler-app
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
4.  **Install system dependencies** as described in Method 1 (Tesseract and/or eSpeak).
5.  **Set Environment Variables** for the Reddit API (see Usage section below).
6.  **Run the application**:
    ```bash
    python3 meme_compiler/app.py
    ```

## Usage Guide

### Step 0: Reddit API Credentials

Before you start, you need to get API credentials from Reddit.
1.  Go to [Reddit's app preferences](https://www.reddit.com/prefs/apps).
2.  Scroll to the bottom and click **"are you a developer? create an app..."**.
3.  Fill out the form:
    *   **name**: MemeCompiler
    *   **type**: select `script`
    *   **redirect uri**: `http://localhost:8080`
4.  Click **"create app"**. You will see your client ID and client secret.
5.  You must make these credentials available to the application by setting them as **environment variables**:
    *   **On Linux/macOS**:
        ```bash
        export REDDIT_CLIENT_ID="YOUR_CLIENT_ID_HERE"
        export REDDIT_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
        ```
    *   **On Windows**:
        ```powershell
        $env:REDDIT_CLIENT_ID="YOUR_CLIENT_ID_HERE"
        $env:REDDIT_CLIENT_SECRET="YOUR_CLIENT_SECRET_HERE"
        ```

### Step 1: Find Memes

-   Launch the application.
-   Enter a keyword for the type of memes you want (e.g., `historymemes`, `wholesomememes`).
-   Click **"Search..."**. The app will search Reddit for matching posts.

### Step 2: Select Memes

-   Once the search is complete, a list of found memes will appear.
-   Click on the memes you want to include in your video. You can select multiple by holding `Ctrl` (or `Cmd` on Mac) and clicking.

### Step 3: Add Your Video Files

-   Buttons will appear for you to select your video files.
-   Click **"Select Intro"**, **"Select Background"**, and **"Select Outro"** and choose the appropriate `.mp4` or `.gif` files from your computer.

### Step 4: Finish & Compile

-   Once you have selected at least one meme and all three video files, the final compilation step will appear.
-   **TTS Options**:
    *   Check the "Add TTS Voiceover" box to enable the feature.
    *   Select a voice from the dropdown menu.
-   Click the **"Compile Video!"** button.
-   A dialog box will ask you where you want to save the final video file.
-   The compilation will start. This may take several minutes depending on the number of memes. The app will notify you when it's complete.

## Building From Source

If you want to build the executable yourself, you can use the included `PyInstaller` configuration.
1.  Follow the "Running from Source" instructions to set up the environment.
2.  Run the build command:
    ```bash
    pyinstaller --name MemeCompiler --onefile --noconfirm --clean --hidden-import="tkinter.filedialog" --hidden-import="PIL.Image" --hidden-import="pyttsx3.drivers" --hidden-import="pyttsx3.drivers.espeak" meme_compiler/app.py
    ```
3.  The final executable will be located in the `dist/` directory.
