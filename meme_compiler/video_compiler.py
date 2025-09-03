import requests
import os
from moviepy.editor import *
from urllib.parse import urlparse
import shutil
from .tts_processor import extract_text_from_image, generate_tts_audio, is_tesseract_installed

def download_file(url, folder="temp_media"):
    """Downloads a file from a URL to a local folder."""
    if not os.path.exists(folder):
        os.makedirs(folder)

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        filename = os.path.join(folder, os.path.basename(urlparse(url).path))

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filename
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None

def create_video(selected_memes, intro_path, outro_path, background_path, output_path="final_video.mp4", enable_tts=False, voice_id=None):
    """
    Compiles a video from memes, an intro, an outro, and a background video.

    Args:
        selected_memes (list): A list of dictionaries with meme URLs.
        intro_path (str): Filepath for the intro video.
        outro_path (str): Filepath for the outro video.
        background_path (str): Filepath for the background gameplay video.
        output_path (str): Where to save the final compiled video.
        enable_tts (bool): Whether to enable Text-to-Speech for image memes.
        voice_id (str, optional): The ID of the voice to use for TTS.
    """
    print("Starting video compilation...")
    temp_folder = "temp_media"
    tts_audio_files = []

    # --- 1. Get all media paths (downloading if necessary) ---
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    downloaded_meme_paths = []
    for meme in selected_memes:
        url = meme['url']
        # If the "url" is actually a local file path, just copy it to the temp folder
        if os.path.exists(url):
            filename = os.path.basename(url)
            dest_path = os.path.join(temp_folder, filename)
            shutil.copy(url, dest_path)
            path = dest_path
        else: # Otherwise, assume it's a URL and download it
            path = download_file(url, temp_folder)

        if path:
            downloaded_meme_paths.append(path)

    if not downloaded_meme_paths:
        print("No valid memes could be downloaded.")
        return

    # --- 2. Load all base video clips ---
    intro_clip = VideoFileClip(intro_path)
    outro_clip = VideoFileClip(outro_path)
    background_clip = VideoFileClip(background_path)

    # --- 3. Create clips for each meme ---
    meme_clip_duration = 40 / len(downloaded_meme_paths)
    meme_clips = []

    try:
        for i, path in enumerate(downloaded_meme_paths):
            clip = None
            if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                clip = ImageClip(path).set_duration(meme_clip_duration)

                if enable_tts:
                    text = extract_text_from_image(path)
                    if text:
                        audio_path = os.path.join(temp_folder, f"tts_{i}.mp3")
                        if generate_tts_audio(text, audio_path, voice_id=voice_id):
                            audio_clip = AudioFileClip(audio_path)
                            # If audio is longer than the clip, cut the audio.
                            if audio_clip.duration > clip.duration:
                                audio_clip = audio_clip.subclip(0, clip.duration)
                            clip = clip.set_audio(audio_clip)
                            tts_audio_files.append(audio_path)

            elif path.lower().endswith(('.gif', '.mp4')):
                clip = VideoFileClip(path).set_duration(meme_clip_duration)
                if clip.duration < meme_clip_duration and path.lower().endswith('.gif'):
                    clip = clip.fx(vfx.loop, duration=meme_clip_duration)

            if clip:
                clip_resized = clip.resize(width=background_clip.w * 0.9)
                meme_clips.append(clip_resized)

        if not meme_clips:
            print("Could not create any meme clips.")
            return

        # --- 4. Composite memes over the background ---
        total_meme_duration = sum(c.duration for c in meme_clips)
        if background_clip.duration < total_meme_duration:
            print("Warning: Background video is shorter than total meme duration. Looping background.")
            background_clip = background_clip.fx(vfx.loop, duration=total_meme_duration)

        background_segment = background_clip.subclip(0, total_meme_duration)

        final_meme_segment = concatenate_videoclips(meme_clips, method="compose")
        composited_segment = CompositeVideoClip([background_segment, final_meme_segment.set_position(("center", "center"))])

        # --- 5. Concatenate all parts ---
        final_video = concatenate_videoclips([intro_clip, composited_segment, outro_clip])

        # --- 6. Write the final video file ---
        print(f"Writing final video to {output_path}...")
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        print("Video compilation successful!")

    except Exception as e:
        print(f"An error occurred during video creation: {e}")
    finally:
        # --- 7. Cleanup ---
        print("Cleaning up temporary files...")
        # Close all moviepy clips to release file handles
        intro_clip.close()
        outro_clip.close()
        background_clip.close()
        if 'final_video' in locals():
            final_video.close()
        for clip in meme_clips:
            # This is tricky because some clips might have audio clips that need closing
            if clip.audio:
                clip.audio.close()
            clip.close()

        # Delete the temporary media folder
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
            print(f"Removed temporary folder: {temp_folder}")

# This file is intended to be used as a module.
# The test harness has been moved to tests/test_video_compiler.py
