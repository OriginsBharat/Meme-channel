import os
import sys
import shutil

# Add the parent directory to the path to allow importing the main modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from meme_compiler.video_compiler import create_video

if __name__ == '__main__':
    print("--- Running Video Compiler Test ---")
    # This test is designed to check the pre-processing and dependency checks,
    # it is expected to fail during the actual video processing with dummy files.

    # This import is here because Pillow is a dependency of the main app, not the test itself
    from PIL import Image, ImageDraw, ImageFont

    # --- Setup Test Assets ---
    assets_dir = 'test_assets'
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)

    # 1. Create a test image with text
    try:
        img = Image.new('RGB', (500, 150), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 40)
        except IOError:
            print("Default font not found. Using basic font.")
            font = ImageFont.load_default()
        draw.text((10, 10), "This is a test meme\nwith two lines of text.", fill=(0, 0, 0), font=font)
        test_image_path = os.path.join(assets_dir, "test_meme_image.png")
        img.save(test_image_path)
        print(f"Created test image at: {test_image_path}")
    except Exception as e:
        print(f"Failed to create test image. Cannot run test. Error: {e}")
        exit()

    # 2. Create dummy video files
    intro_path = os.path.join(assets_dir, "intro.mp4")
    outro_path = os.path.join(assets_dir, "outro.mp4")
    bg_path = os.path.join(assets_dir, "background.mp4")
    with open(intro_path, 'w') as f: f.write('dummy')
    with open(outro_path, 'w') as f: f.write('dummy')
    with open(bg_path, 'w') as f: f.write('dummy')
    print("Created dummy video files.")

    # 3. Define test data
    sample_memes = [{'url': test_image_path}] # Using the local file path
    output_video_path = "test_output_video.mp4"

    # --- Run the Test ---
    print("\n--- Calling create_video with TTS enabled ---")
    try:
        # We need to check for dependencies first, like the main app does
        from meme_compiler.dependency_handler import check_dependencies
        deps_error = check_dependencies()
        if deps_error:
            print("Dependency check failed. The app would normally exit.")
            print(deps_error)
            # We will continue the test to check video logic, but TTS should be skipped.

        create_video(sample_memes, intro_path, outro_path, bg_path, output_video_path, enable_tts=True)
    except Exception as e:
        print(f"\nCaught expected exception during moviepy processing: {type(e).__name__}: {e}")

    # --- Cleanup ---
    finally:
        print("\n--- Cleaning up test assets ---")
        if os.path.exists(assets_dir):
            shutil.rmtree(assets_dir)
            print(f"Removed test assets directory: {assets_dir}")
        if os.path.exists(output_video_path):
            os.remove(output_video_path)
            print(f"Removed test output video: {output_video_path}")
        # The create_video function should clean its own temp_media folder

    print("\n--- Video Compiler Test Finished ---")
