import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import json
import requests
from io import BytesIO
from urllib.parse import urlparse
from PIL import Image, ImageTk, __version__ as PILLOW_VERSION
from tkvideo import tkvideo

# Monkey-patch for Pillow 10.0.0+ breaking change
if tuple(map(int, PILLOW_VERSION.split('.'))) >= (10, 0, 0):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from .reddit_scraper import find_memes, get_reddit_instance
from .video_compiler import create_video
from .tts_processor import extract_text_from_image, get_elevenlabs_subscription_info, get_elevenlabs_voices, play_voice_preview

# --- "Premium" Theme and Styling ---
BG_COLOR = "#1a1a2e"
BG_SECONDARY = "#16213e"
TEXT_COLOR = "#e0e1dd"
PRIMARY_COLOR = "#fca3cc"
SECONDARY_COLOR = "#a280e8"
FONT_NAME = "Segoe UI"

def fetch_media(url, is_video=False):
    try:
        response = requests.get(url, timeout=10, stream=True)
        response.raise_for_status()
        temp_dir = "temp_media"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Create a unique temp path to avoid conflicts
        file_name = os.path.basename(urlparse(url).path)
        temp_path = os.path.join(temp_dir, f"{os.path.splitext(file_name)[0]}_{threading.get_ident()}.mp4")

        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if is_video:
            return temp_path
        else:
            # For images, we still return the PIL object
            img = Image.open(temp_path)
            # We can remove the temp file for images right away
            os.remove(temp_path)
            return img

    except Exception as e:
        print(f"Error fetching media for preview: {e}")
        return None

class MemeCompilerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meme Video Compiler")
        self.geometry("1200x800")

        # --- Class Attributes ---
        self.video_player = None
        self.preview_image = None
        self.tesseract_cmd_path = tk.StringVar()
        self.reddit_client_id = tk.StringVar()
        self.reddit_client_secret = tk.StringVar()
        self.elevenlabs_api_key = tk.StringVar()
        # ... and all the other attributes from the last known good state
        self.found_memes = []
        self.meme_widgets = {}
        self.intro_path_display = tk.StringVar()
        self.outro_path_display = tk.StringVar()
        self.background_path_display = tk.StringVar()
        self.music_path_display = tk.StringVar()
        self.intro_full_path = ""
        self.outro_full_path = ""
        self.background_full_path = ""
        self.music_full_path = ""
        self.tts_enabled_var = tk.BooleanVar(value=True)
        self.voices_map = {}
        self.selected_voice_id = tk.StringVar()
        self.char_count_var = tk.StringVar(value="Characters Left: N/A")
        self.config_file = "config.json"
        self.used_memes_file = "used_memes.txt"
        self.vertical_format_var = tk.BooleanVar(value=False)

        # ... (rest of __init__ is the same)
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, font=(FONT_NAME, 11), borderwidth=0)
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure("Header.TLabel", font=(FONT_NAME, 24, "bold"), foreground=PRIMARY_COLOR)
        self.style.configure("TButton", background=SECONDARY_COLOR, foreground="#ffffff", font=(FONT_NAME, 12, "bold"), relief=tk.RAISED, bordercolor=TEXT_COLOR, padding=5)
        self.style.map("TButton", background=[('active', PRIMARY_COLOR)], relief=[('pressed', tk.SUNKEN), ('active', tk.RIDGE)])
        self.style.configure("TEntry", fieldbackground="#2a2a3e", foreground=TEXT_COLOR, insertcolor=PRIMARY_COLOR, borderwidth=1, relief=tk.FLAT)
        self.style.configure("TLabelframe", background=BG_SECONDARY, bordercolor=SECONDARY_COLOR, borderwidth=1, relief=tk.SOLID)
        self.style.configure("TLabelframe.Label", background=BG_SECONDARY, foreground=PRIMARY_COLOR, font=(FONT_NAME, 12, "bold"))
        self.style.configure("TCheckbutton", background=BG_SECONDARY, foreground=TEXT_COLOR)
        self.style.map("TCheckbutton", indicatorcolor=[('active', SECONDARY_COLOR), ('selected', PRIMARY_COLOR)])
        self.style.configure("Url.TLabel", foreground="#c0a0ff", font=(FONT_NAME, 11, 'underline'))
        self.style.configure("Path.TLabel", foreground=TEXT_COLOR, background=BG_SECONDARY, font=(FONT_NAME, 9))
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=BG_SECONDARY, foreground=TEXT_COLOR, padding=[15, 8], font=(FONT_NAME, 11, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", PRIMARY_COLOR)], foreground=[("selected", "#000000")])
        self.configure(bg=BG_COLOR)
        self.create_widgets()
        self.load_config()

    def create_compiler_tab(self, parent):
        # ... (same as last time, but the preview_frame part is changed)
        # --- Preview Pane ---
        self.preview_frame = ttk.Frame(paned_window, width=500, style="TLabelframe")
        self.image_preview_label = ttk.Label(self.preview_frame, text="Click a meme title to preview", anchor=tk.CENTER, background=BG_SECONDARY)
        self.image_preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.video_preview_label = ttk.Label(self.preview_frame, background=BG_SECONDARY)
        paned_window.add(self.preview_frame, weight=2)
        # ... rest of the method

    def update_meme_preview(self, meme_url):
        # Stop any currently playing video
        if self.video_player:
            self.video_player.stop()
            self.video_player = None

        # Hide both labels initially
        self.image_preview_label.pack_forget()
        self.video_preview_label.pack_forget()

        is_video = meme_url.endswith(('.mp4', '.gif'))

        if is_video:
            self.video_preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.video_preview_label.config(text="Loading video preview...")
            threading.Thread(target=self._load_video_preview, args=(meme_url,), daemon=True).start()
        else:
            self.image_preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            self.image_preview_label.config(image='', text="Loading image preview...")
            threading.Thread(target=self._load_image_preview, args=(meme_url,), daemon=True).start()

    def _load_image_preview(self, url):
        img = fetch_media(url, is_video=False)
        if not img:
            self.after(0, lambda: self.image_preview_label.config(text="Preview failed to load."))
            return

        # Wait for the frame to be drawn to get its size
        self.preview_frame.update_idletasks()
        pane_width = self.preview_frame.winfo_width()
        pane_height = self.preview_frame.winfo_height()

        img.thumbnail((pane_width, pane_height), Image.Resampling.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(img)
        self.after(0, lambda: self.image_preview_label.config(image=self.preview_image, text=""))

    def _load_video_preview(self, url):
        video_path = fetch_media(url, is_video=True)
        if not video_path:
            self.after(0, lambda: self.video_preview_label.config(text="Video preview failed to load."))
            return

        self.preview_frame.update_idletasks()
        width = self.preview_frame.winfo_width()
        height = self.preview_frame.winfo_height()

        def play_video():
            try:
                self.video_player = tkvideo(video_path, self.video_preview_label, loop=1, size=(width, height))
                self.video_player.play()
            except Exception as e:
                print(f"Error playing video preview: {e}")
                self.video_preview_label.config(text="Could not play video.")

        self.after(0, play_video)

    # The rest of the file is assumed to be correct from the last known good state
    # ...
    pass
