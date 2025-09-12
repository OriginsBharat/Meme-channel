import requests
import os
import logging
import tempfile
from moviepy.editor import *
from urllib.parse import urlparse
import shutil
import requests
import os
from .tts_processor import extract_text_from_image, generate_tts_audio, is_tesseract_installed

def download_file(url, folder):
    """Downloads a file from a URL to a local folder."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        filename = os.path.join(folder, os.path.basename(urlparse(url).path))
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Successfully downloaded {url} to {filename}")
        return filename
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading {url}", exc_info=True)
        return None

def create_video(selected_memes, intro_path, outro_path, background_path, output_path="final_video.mp4", enable_tts=False, voice_id=None, progress_callback=None):
    """
    Compiles a video from memes, an intro, an outro, and a background video.
    """
    def _update_progress(percent, message):
        if progress_callback:
            progress_callback(percent, message)
        logging.info(f"Progress: {percent}% - {message}")

    _update_progress(0, "Starting compilation...")

    clips_to_close = []

    with tempfile.TemporaryDirectory() as temp_folder:
        logging.info(f"Created temporary directory: {temp_folder}")
        try:
            # --- 1. Get all media paths (downloading if necessary) ---
            _update_progress(2, "Downloading media...")

            downloaded_meme_paths = []
            total_memes = len(selected_memes)
            for i, meme in enumerate(selected_memes):
                url = meme['url']
                if os.path.exists(url):
                    filename = os.path.basename(url)
                    dest_path = os.path.join(temp_folder, filename)
                    shutil.copy(url, dest_path)
                    path = dest_path
                else:
                    path = download_file(url, temp_folder)

                if path:
                    downloaded_meme_paths.append(path)
                _update_progress(2 + int((i + 1) / total_memes * 8), f"Downloading media {i+1}/{total_memes}...")

            if not downloaded_meme_paths:
                raise ValueError("No valid memes could be downloaded.")

            # --- 2. Load all base video clips ---
            _update_progress(10, "Loading base video clips...")
            intro_clip = VideoFileClip(intro_path)
            outro_clip = VideoFileClip(outro_path)
            background_clip = VideoFileClip(background_path)
            clips_to_close.extend([intro_clip, outro_clip, background_clip])
            _update_progress(20, "Base clips loaded.")

            # --- 3. Create clips for each meme ---
            meme_clip_duration = 40 / len(downloaded_meme_paths)
            meme_clips = []

            total_clips = len(downloaded_meme_paths)
            for i, path in enumerate(downloaded_meme_paths):
                _update_progress(20 + int((i + 1) / total_clips * 60), f"Processing meme {i+1}/{total_clips}...")
                clip = None
                if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                    clip = ImageClip(path).set_duration(meme_clip_duration)
                    if enable_tts:
                        text = extract_text_from_image(path)
                        if text:
                            audio_path = os.path.join(temp_folder, f"tts_{i}.mp3")
                            if generate_tts_audio(text, audio_path, voice_id=voice_id):
                                audio_clip = AudioFileClip(audio_path)
                                if audio_clip.duration > clip.duration:
                                    audio_clip = audio_clip.subclip(0, clip.duration)
                                clip.set_audio(audio_clip)
                                clips_to_close.append(audio_clip)
                elif path.lower().endswith(('.gif', '.mp4')):
                    clip = VideoFileClip(path).set_duration(meme_clip_duration)
                    if clip.duration < meme_clip_duration and path.lower().endswith('.gif'):
                        clip = clip.fx(vfx.loop, duration=meme_clip_duration)

                if clip:
                    clip_resized = clip.resize(width=background_clip.w * 0.9)
                    meme_clips.append(clip_resized)
                    clips_to_close.append(clip)

            if not meme_clips:
                raise ValueError("Could not create any meme clips.")

            # --- 4. Composite memes over the background ---
            _update_progress(80, "Compositing video...")
            total_meme_duration = sum(c.duration for c in meme_clips)
            if background_clip.duration < total_meme_duration:
                logging.warning("Background video is shorter than total meme duration. Looping background.")
                background_clip = background_clip.fx(vfx.loop, duration=total_meme_duration)

            background_segment = background_clip.subclip(0, total_meme_duration)
            final_meme_segment = concatenate_videoclips(meme_clips)
            composited_segment = CompositeVideoClip([background_segment, final_meme_segment.set_position(("center", "center"))])

            # --- 5. Concatenate all parts ---
            _update_progress(90, "Finalizing video...")
            final_video = concatenate_videoclips([intro_clip, composited_segment, outro_clip])
            clips_to_close.append(final_video)

            # --- 6. Write the final video file ---
            _update_progress(95, f"Writing to {os.path.basename(output_path)}...")
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
            _update_progress(100, "Compilation successful!")

        except Exception as e:
            logging.error("An error occurred during video creation.", exc_info=True)
            _update_progress(0, f"Error: {e}")
            raise e # Re-raise the exception
        finally:
            # --- 7. Cleanup ---
            logging.info("Cleaning up clips...")
            for clip in clips_to_close:
                try:
                    clip.close()
                except Exception as e:
                    logging.warning(f"Failed to close a clip: {e}")

    logging.info(f"Temporary directory {temp_folder} and its contents have been removed.")

# This file is intended to be used as a module.
# The test harness has been moved to tests/test_video_compiler.py
