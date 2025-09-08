import requests
import os
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from urllib.parse import urlparse
import shutil
from .tts_processor import extract_text_from_image, generate_elevenlabs_tts

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

def _resize_and_crop_to_fill(clip, target_size):
    """Resizes a clip to fill the target size, cropping as needed."""
    # Resize so that the smallest dimension matches the target dimension
    ratio = max(target_size[0] / clip.w, target_size[1] / clip.h)
    resized_clip = clip.resize(ratio)
    # Crop the excess from the center
    return vfx.crop(
        resized_clip,
        width=target_size[0],
        height=target_size[1],
        x_center=resized_clip.w / 2,
        y_center=resized_clip.h / 2
    )

def create_video(selected_memes, intro_path, outro_path, background_path, output_path="final_video.mp4", enable_tts=False, elevenlabs_api_key=None, ocr_api_key=None, voice_id=None, vertical_format=False, music_path=None):
    """
    Compiles a video from memes, an intro, an outro, and a background video.

    Args:
        ... (all previous args)
        elevenlabs_api_key (str, optional): The API key for ElevenLabs.
        ocr_api_key (str, optional): The API key for the OCR service.
        vertical_format (bool): If True, creates a 9:16 vertical video.
        music_path (str, optional): Path to the background music file.
    """
    print("Starting video compilation...")
    temp_folder = "temp_media"
    tts_failures = [] # To track which memes failed TTS

    # --- 1. Download memes ---
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    print("Downloading selected memes...")
    downloaded_memes = []
    for meme in selected_memes:
        path = download_file(meme['url'], temp_folder)
        if path:
            downloaded_memes.append({'path': path, 'title': meme['title']})

    if not downloaded_memes:
        print("No valid memes could be downloaded.")
        return None

    # --- 2. Define Target Size based on format ---
    TARGET_SIZE = (1080, 1920) if vertical_format else None

    # --- 3. Load and prepare all base video clips ---
    intro_clip = VideoFileClip(intro_path)
    outro_clip = VideoFileClip(outro_path)
    background_clip = VideoFileClip(background_path)

    if vertical_format:
        intro_clip = _resize_and_crop_to_fill(intro_clip, TARGET_SIZE)
        outro_clip = _resize_and_crop_to_fill(outro_clip, TARGET_SIZE)
        background_clip = _resize_and_crop_to_fill(background_clip, TARGET_SIZE)

    # --- 4. Create clips for each meme ---
    meme_clip_duration = 40 / len(downloaded_memes)
    meme_clips = []

    try:
        for i, meme_data in enumerate(downloaded_memes):
            path = meme_data['path']
            title = meme_data['title']
            clip = None

            if path.lower().endswith(('.jpg', '.jpeg', '.png')):
                clip = ImageClip(path).set_duration(meme_clip_duration)
                if enable_tts:
                    text = extract_text_from_image(ocr_api_key, path)
                    if text:
                        audio_path = os.path.join(temp_folder, f"tts_{i}.mp3")
                        success, message = generate_elevenlabs_tts(elevenlabs_api_key, voice_id, text, audio_path)
                        if not success:
                            print(f"Warning: TTS generation failed for '{title}' with error: {message}")
                            tts_failures.append((title, message))
                        else:
                            audio_clip = AudioFileClip(audio_path)
                            if audio_clip.duration > clip.duration:
                                audio_clip = audio_clip.subclip(0, clip.duration)
                            clip = clip.set_audio(audio_clip)
                    else:
                        print(f"Warning: OCR failed for '{title}', skipping TTS.")

            elif path.lower().endswith(('.gif', '.mp4')):
                clip = VideoFileClip(path).set_duration(meme_clip_duration)
                if clip.duration < meme_clip_duration and path.lower().endswith('.gif'):
                    clip = clip.fx(vfx.loop, duration=meme_clip_duration)

            if clip:
                if vertical_format:
                    clip_resized = clip.resize(width=TARGET_SIZE[0])
                else:
                    clip_resized = clip.resize(width=background_clip.w * 0.9)
                meme_clips.append(clip_resized)

        if not meme_clips:
            print("Could not create any meme clips.")
            return None

        # --- 5. Composite memes over the background ---
        total_meme_duration = sum(c.duration for c in meme_clips)
        if background_clip.duration < total_meme_duration:
            background_clip = background_clip.fx(vfx.loop, duration=total_meme_duration)

        background_segment = background_clip.subclip(0, total_meme_duration)

        final_meme_segment = concatenate_videoclips(meme_clips)
        composited_segment = CompositeVideoClip([background_segment, final_meme_segment.set_position(("center", "center"))])

        # --- 6. Add Background Music if provided ---
        if music_path:
            print(f"Adding background music from: {music_path}")
            background_music = AudioFileClip(music_path).volumex(0.1)

            # Ensure music loops if shorter than the video segment
            if background_music.duration < composited_segment.duration:
                background_music = background_music.fx(vfx.loop, duration=composited_segment.duration)
            else:
                background_music = background_music.subclip(0, composited_segment.duration)

            # Combine with existing audio (TTS)
            if composited_segment.audio:
                combined_audio = CompositeAudioClip([composited_segment.audio, background_music])
                composited_segment.audio = combined_audio
            else:
                composited_segment.audio = background_music

        # --- 7. Concatenate all parts ---
        final_video = concatenate_videoclips([intro_clip, composited_segment, outro_clip])

        # --- 8. Write the final video file ---
        print(f"Writing final video to {output_path}...")
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        print("Video compilation successful!")
        return tts_failures

    except Exception as e:
        print(f"An error occurred during video creation: {e}")
        return None # Return None on a hard crash
    finally:
        # --- 9. Cleanup ---
        print("Cleaning up temporary files...")
        intro_clip.close()
        outro_clip.close()
        background_clip.close()
        if 'final_video' in locals():
            final_video.close()
        for clip in meme_clips:
            if hasattr(clip, 'audio') and clip.audio:
                clip.audio.close()
            clip.close()

        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
            print(f"Removed temporary folder: {temp_folder}")
