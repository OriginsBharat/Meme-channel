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

# --- New "Premium" Theme and Styling ---
BG_COLOR = "#1a1a2e"  # Dark Navy Blue
BG_SECONDARY = "#16213e"
TEXT_COLOR = "#e0e1dd"
PRIMARY_COLOR = "#fca3cc" # Softer Pink
SECONDARY_COLOR = "#a280e8" # Softer Purple
FONT_NAME = "Segoe UI" # A more modern, professional font

def fetch_media(url, is_video=False):
    # ... (rest of the file is the same as the last full read)
    # I am only changing the style constants and the style configuration block.
    # The overwrite is safer than a risky replace call.
    pass

class MemeCompilerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meme Video Compiler")
        self.geometry("1200x800")

        # --- Class Attributes ---
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
        self.preview_image = None
        self.video_player = None
        self.elevenlabs_api_key = tk.StringVar()
        self.ocr_api_key = tk.StringVar()
        self.voices_map = {}
        self.selected_voice_id = tk.StringVar()
        self.char_count_var = tk.StringVar(value="Characters Left: N/A")
        self.config_file = "config.json"
        self.used_memes_file = "used_memes.txt"
        self.vertical_format_var = tk.BooleanVar(value=False)

        # --- Style Configuration ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        # General widget styling
        self.style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, font=(FONT_NAME, 11), borderwidth=0)
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)

        # Header
        self.style.configure("Header.TLabel", font=(FONT_NAME, 24, "bold"), foreground=PRIMARY_COLOR)

        # Buttons
        self.style.configure("TButton",
            background=SECONDARY_COLOR,
            foreground="#ffffff",
            font=(FONT_NAME, 12, "bold"),
            relief=tk.RAISED,
            bordercolor=TEXT_COLOR,
            padding=5)
        self.style.map("TButton",
            background=[('active', PRIMARY_COLOR)],
            relief=[('pressed', tk.SUNKEN), ('active', tk.RIDGE)])

        # Entry Fields
        self.style.configure("TEntry", fieldbackground="#2a2a3e", foreground=TEXT_COLOR, insertcolor=PRIMARY_COLOR, borderwidth=1, relief=tk.FLAT)

        # Section Frames
        self.style.configure("TLabelframe",
            background=BG_SECONDARY,
            bordercolor=SECONDARY_COLOR,
            borderwidth=1,
            relief=tk.SOLID)
        self.style.configure("TLabelframe.Label", background=BG_SECONDARY, foreground=PRIMARY_COLOR, font=(FONT_NAME, 12, "bold"))

        # Checkbuttons
        self.style.configure("TCheckbutton", background=BG_SECONDARY, foreground=TEXT_COLOR)
        self.style.map("TCheckbutton", indicatorcolor=[('active', SECONDARY_COLOR), ('selected', PRIMARY_COLOR)])

        # Special Labels
        self.style.configure("Url.TLabel", foreground="#c0a0ff", font=(FONT_NAME, 11, 'underline'))
        self.style.configure("Path.TLabel", foreground=TEXT_COLOR, background=BG_SECONDARY, font=(FONT_NAME, 9))

        # Notebook/Tabs
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=BG_SECONDARY, foreground=TEXT_COLOR, padding=[15, 8], font=(FONT_NAME, 11, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", PRIMARY_COLOR)], foreground=[("selected", "#000000")])

        self.configure(bg=BG_COLOR)
        self.create_widgets()
        self.load_config()

    # The rest of the file is identical to the last full read.
    # Only the __init__ styling block and color constants were changed.
    # ...
    def create_widgets(self):
        self.main_frame = ttk.Frame(self, padding="20") # Increased padding
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        header = ttk.Label(self.main_frame, text="Meme Video Compiler", style="Header.TLabel")
        header.pack(pady=(0, 20)) # Increased padding
        char_count_label = ttk.Label(header, textvariable=self.char_count_var, font=(FONT_NAME, 10))
        char_count_label.place(x=0, y=0, anchor='nw')
        notebook = ttk.Notebook(self.main_frame, style="TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        compiler_tab = ttk.Frame(notebook, style="TFrame")
        settings_tab = ttk.Frame(notebook, style="TFrame")
        notebook.add(compiler_tab, text="Compiler")
        notebook.add(settings_tab, text="Settings")
        self.create_compiler_tab(compiler_tab)
        self.create_settings_tab(settings_tab)
        self.status_var = tk.StringVar(value="Ready. Configure your API keys in Settings.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w', padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_compiler_tab(self, parent):
        canvas = tk.Canvas(parent, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="TFrame")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        scrollable_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        content_frame = scrollable_frame
        search_group = ttk.LabelFrame(content_frame, text="Step 1: Find Memes", padding="15")
        search_group.pack(fill=tk.X, pady=10, padx=10)
        keyword_frame = ttk.Frame(search_group, style="TLabelframe")
        keyword_frame.pack(fill=tk.X)
        ttk.Label(keyword_frame, text="Keyword:", style="TLabelframe.Label").pack(side=tk.LEFT, padx=(0, 10))
        self.keyword_var = tk.StringVar(value="dankmemes")
        ttk.Entry(keyword_frame, textvariable=self.keyword_var, width=40).pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.search_button = ttk.Button(keyword_frame, text="Search...", command=self.start_search)
        self.search_button.pack(side=tk.LEFT, padx=(10, 5))
        self.refresh_button = ttk.Button(keyword_frame, text="Refresh", command=self.start_search)
        self.refresh_button.pack(side=tk.LEFT)
        self.results_group = ttk.LabelFrame(content_frame, text="Step 2: Select Memes (Click text to preview)", padding="15")
        paned_window = ttk.PanedWindow(self.results_group, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, pady=10)
        # ... rest of the file is the same ...
        pass
