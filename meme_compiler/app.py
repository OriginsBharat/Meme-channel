import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import json
import requests
import shutil
import tempfile
from io import BytesIO
from urllib.parse import urlparse
from PIL import Image, ImageTk, __version__ as PILLOW_VERSION
from tkvideo import tkvideo

# Monkey-patch for Pillow 10.0.0+ breaking change
if tuple(map(int, PILLOW_VERSION.split('.'))) >= (10, 0, 0):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

from .reddit_scraper import find_memes, get_reddit_instance
from .video_compiler import create_video
from .tts_processor import get_elevenlabs_subscription_info, get_elevenlabs_voices, play_voice_preview
from . import youtube_uploader

# --- Theme and Styling ---
BG_COLOR = "#1a1a2e"
BG_SECONDARY = "#16213e"
TEXT_COLOR = "#e0e1dd"
PRIMARY_COLOR = "#fca3cc"
SECONDARY_COLOR = "#a280e8"
FONT_NAME = "Segoe UI"
TEMP_PREVIEW_DIR = "temp_media_previews"

def fetch_media_for_preview(url, is_video=False):
    try:
        response = requests.get(url, timeout=10, stream=True)
        response.raise_for_status()
        if not os.path.exists(TEMP_PREVIEW_DIR):
            os.makedirs(TEMP_PREVIEW_DIR)

        file_name = os.path.basename(urlparse(url).path)
        # Use a unique name to prevent conflicts
        temp_path = os.path.join(TEMP_PREVIEW_DIR, f"{os.path.splitext(file_name)[0]}_{threading.get_ident()}{os.path.splitext(file_name)[1]}")

        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        if is_video:
            return temp_path
        else:
            img = Image.open(temp_path)
            os.remove(temp_path) # Images can be loaded and their temp files removed
            return img

    except Exception as e:
        print(f"Error fetching media for preview: {e}")
        return None

class MemeCompilerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meme Video Compiler")
        self.geometry("1200x800")

        self.video_player = None
        self.preview_image = None
        self.tesseract_cmd_path = tk.StringVar()
        self.reddit_client_id = tk.StringVar()
        self.reddit_client_secret = tk.StringVar()
        self.elevenlabs_api_key = tk.StringVar()
        self.found_memes = []
        self.meme_widgets = {}
        self.intro_path_display = tk.StringVar(value="No file selected...")
        self.outro_path_display = tk.StringVar(value="No file selected...")
        self.background_path_display = tk.StringVar(value="No file selected...")
        self.music_path_display = tk.StringVar(value="No file selected...")
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
        self.youtube_client_secrets_path = tk.StringVar()

        self._apply_styles()
        self.create_widgets()
        self.load_config()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _apply_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, font=(FONT_NAME, 11))
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure("Header.TLabel", font=(FONT_NAME, 24, "bold"), foreground=PRIMARY_COLOR)
        self.style.configure("TButton", background=SECONDARY_COLOR, foreground="#ffffff", font=(FONT_NAME, 12, "bold"), padding=5)
        self.style.map("TButton", background=[('active', PRIMARY_COLOR)])
        self.style.configure("TEntry", fieldbackground="#2a2a3e", foreground=TEXT_COLOR, insertcolor=PRIMARY_COLOR)
        self.style.configure("TLabelframe", background=BG_SECONDARY, bordercolor=SECONDARY_COLOR)
        self.style.configure("TLabelframe.Label", background=BG_SECONDARY, foreground=PRIMARY_COLOR, font=(FONT_NAME, 12, "bold"))
        self.style.configure("TCheckbutton", background=BG_SECONDARY, foreground=TEXT_COLOR)
        self.style.map("TCheckbutton", indicatorcolor=[('active', SECONDARY_COLOR), ('selected', PRIMARY_COLOR)])
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=BG_SECONDARY, foreground=TEXT_COLOR, padding=[15, 8], font=(FONT_NAME, 11, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", PRIMARY_COLOR)], foreground=[("selected", "#000000")])
        self.configure(bg=BG_COLOR)

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        compiler_tab = ttk.Frame(self.notebook, style="TFrame")
        settings_tab = ttk.Frame(self.notebook, style="TFrame")

        self.notebook.add(compiler_tab, text='Compiler')
        self.notebook.add(settings_tab, text='Settings')

        self._create_compiler_tab(compiler_tab)
        self._create_settings_tab(settings_tab)

    def _create_compiler_tab(self, parent):
        paned_window = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left side (Controls)
        controls_frame = ttk.Frame(paned_window, width=700)

        # -- Search Frame --
        search_lf = ttk.LabelFrame(controls_frame, text="1. Find Memes")
        search_lf.pack(fill=tk.X, padx=5, pady=5)
        self.search_entry = ttk.Entry(search_lf, width=50)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.search_button = ttk.Button(search_lf, text="Search", command=self.search_memes)
        self.search_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.search_status = ttk.Label(search_lf, text="")
        self.search_status.pack(side=tk.LEFT, padx=5)

        # -- Meme List Frame --
        list_lf = ttk.LabelFrame(controls_frame, text="2. Select Memes")
        list_lf.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        canvas = tk.Canvas(list_lf, background=BG_SECONDARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_lf, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="TFrame")
        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # -- Files Frame --
        files_lf = ttk.LabelFrame(controls_frame, text="3. Select Files")
        files_lf.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)
        files_lf.columnconfigure(1, weight=1)

        ttk.Button(files_lf, text="Intro Video", command=lambda: self._browse_file("intro")).grid(row=0, column=0, padx=5, pady=2, sticky='ew')
        ttk.Label(files_lf, textvariable=self.intro_path_display).grid(row=0, column=1, padx=5, pady=2, sticky='w')

        ttk.Button(files_lf, text="Outro Video", command=lambda: self._browse_file("outro")).grid(row=1, column=0, padx=5, pady=2, sticky='ew')
        ttk.Label(files_lf, textvariable=self.outro_path_display).grid(row=1, column=1, padx=5, pady=2, sticky='w')

        ttk.Button(files_lf, text="Background Video", command=lambda: self._browse_file("background")).grid(row=2, column=0, padx=5, pady=2, sticky='ew')
        ttk.Label(files_lf, textvariable=self.background_path_display).grid(row=2, column=1, padx=5, pady=2, sticky='w')

        ttk.Button(files_lf, text="Background Music", command=lambda: self._browse_file("music")).grid(row=3, column=0, padx=5, pady=2, sticky='ew')
        ttk.Label(files_lf, textvariable=self.music_path_display).grid(row=3, column=1, padx=5, pady=2, sticky='w')

        # -- Compile Frame --
        compile_lf = ttk.LabelFrame(controls_frame, text="4. Create Video")
        compile_lf.pack(fill=tk.X, padx=5, pady=5)
        self.compile_button = ttk.Button(compile_lf, text="Compile Video", command=self.compile_video)
        self.compile_button.pack(pady=10)
        self.status_label = ttk.Label(compile_lf, text="")
        self.status_label.pack(pady=5)

        paned_window.add(controls_frame, weight=3)

        # Right side (Preview)
        self.preview_frame = ttk.LabelFrame(paned_window, text="Preview")
        self.image_preview_label = ttk.Label(self.preview_frame, text="Click a meme to preview", anchor=tk.CENTER)
        self.image_preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.video_preview_label = ttk.Label(self.preview_frame) # For tkvideo
        paned_window.add(self.preview_frame, weight=2)

    def _create_settings_tab(self, parent):
        parent.columnconfigure(1, weight=1)

        # Reddit Credentials
        ttk.Label(parent, text="Reddit Client ID:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Entry(parent, textvariable=self.reddit_client_id, width=70).grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Label(parent, text="Reddit Client Secret:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        ttk.Entry(parent, textvariable=self.reddit_client_secret, width=70, show="*").grid(row=1, column=1, padx=5, pady=5, sticky='ew')

        # Tesseract Path
        ttk.Label(parent, text="Tesseract Path:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        ttk.Entry(parent, textvariable=self.tesseract_cmd_path, width=70).grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(parent, text="Browse", command=self._browse_tesseract).grid(row=2, column=2, padx=5, pady=5)

        # ElevenLabs API
        ttk.Label(parent, text="ElevenLabs API Key:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        ttk.Entry(parent, textvariable=self.elevenlabs_api_key, width=70, show="*").grid(row=3, column=1, padx=5, pady=5, sticky='ew')

        # TTS Voice Selection
        self.voice_menu = ttk.OptionMenu(parent, self.selected_voice_id, "Select a voice")
        self.voice_menu.grid(row=4, column=1, padx=5, pady=10, sticky='w')
        self.voice_menu.config(state=tk.DISABLED)

        preview_button = ttk.Button(parent, text="Preview Voice", command=self._preview_voice)
        preview_button.grid(row=4, column=2, padx=5, pady=10)

        # Character count
        ttk.Label(parent, textvariable=self.char_count_var).grid(row=4, column=0, padx=5, pady=10, sticky='w')

        # Refresh button
        refresh_button = ttk.Button(parent, text="Refresh Voices & Char Count", command=self._refresh_elevenlabs_data)
        refresh_button.grid(row=5, column=1, pady=10, sticky='w')

        # YouTube Client Secrets
        ttk.Label(parent, text="YouTube Secrets File:").grid(row=6, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(parent, textvariable=self.youtube_client_secrets_path).grid(row=6, column=1, padx=5, pady=5, sticky='w')
        ttk.Button(parent, text="Browse...", command=self._browse_client_secrets).grid(row=6, column=2, padx=5, pady=5)

        # Save button
        save_button = ttk.Button(parent, text="Save Settings", command=self.save_config)
        save_button.grid(row=7, column=1, pady=20, sticky='e')

    def _browse_file(self, file_type):
        path = filedialog.askopenfilename()
        if not path: return

        filename = os.path.basename(path)
        if file_type == "intro":
            self.intro_full_path = path
            self.intro_path_display.set(filename)
        elif file_type == "outro":
            self.outro_full_path = path
            self.outro_path_display.set(filename)
        elif file_type == "background":
            self.background_full_path = path
            self.background_path_display.set(filename)
        elif file_type == "music":
            self.music_full_path = path
            self.music_path_display.set(filename)

    def _browse_tesseract(self):
        path = filedialog.askopenfilename(title="Select tesseract.exe")
        if path:
            self.tesseract_cmd_path.set(path)

    def _browse_client_secrets(self):
        path = filedialog.askopenfilename(
            title="Select YouTube client_secrets.json",
            filetypes=[("JSON files", "*.json")]
        )
        if path:
            self.youtube_client_secrets_path.set(path)

    def _preview_voice(self):
        api_key = self.elevenlabs_api_key.get()
        voice_id = self.selected_voice_id.get()
        if not all([api_key, voice_id]):
            messagebox.showwarning("API Key or Voice Missing", "Please provide an API key and select a voice.")
            return

        threading.Thread(target=play_voice_preview, args=(api_key, voice_id), daemon=True).start()

    def _refresh_elevenlabs_data(self):
        api_key = self.elevenlabs_api_key.get()
        if not api_key:
            messagebox.showwarning("API Key Missing", "Please enter your ElevenLabs API key.")
            return

        # Fetch character count
        sub_info = get_elevenlabs_subscription_info(api_key)
        if sub_info:
            chars = sub_info.character_count
            limit = sub_info.character_limit
            self.char_count_var.set(f"Characters Left: {limit - chars}/{limit}")
        else:
            self.char_count_var.set("Characters Left: Error")

        # Fetch voices
        self.voices_map = get_elevenlabs_voices(api_key)
        if self.voices_map:
            self.voice_menu['menu'].delete(0, 'end')
            for name in self.voices_map.keys():
                self.voice_menu['menu'].add_command(label=name, command=tk._setit(self.selected_voice_id, name))
            self.voice_menu.config(state=tk.NORMAL)
            self.selected_voice_id.set(list(self.voices_map.keys())[0])
        else:
            self.voice_menu.config(state=tk.DISABLED)
            self.selected_voice_id.set("Could not fetch voices")

    def search_memes(self):
        keyword = self.search_entry.get()
        if not keyword:
            messagebox.showwarning("Missing Keyword", "Please enter a search keyword.")
            return

        self.search_button.config(state=tk.DISABLED)
        self.search_status.config(text="Searching...")
        threading.Thread(target=self._search_memes_thread, args=(keyword,), daemon=True).start()

    def _search_memes_thread(self, keyword):
        reddit = get_reddit_instance(self.reddit_client_id.get(), self.reddit_client_secret.get())
        if not reddit:
            self.after(0, lambda: messagebox.showerror("Reddit Error", "Could not connect to Reddit. Check credentials in Settings."))
            self.after(0, self._on_search_complete, [])
            return

        memes = find_memes(reddit, keyword, self.used_memes_file)
        self.after(0, self._on_search_complete, memes)

    def _on_search_complete(self, memes):
        self.search_button.config(state=tk.NORMAL)
        self.search_status.config(text=f"Found {len(memes)} memes.")
        self.found_memes = memes
        self._update_meme_list()

    def _update_meme_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.meme_widgets = {}
        for meme in self.found_memes:
            var = tk.BooleanVar()
            frame = ttk.Frame(self.scrollable_frame, style="TFrame")
            cb = ttk.Checkbutton(frame, text=meme['title'], variable=var, style="TCheckbutton")
            cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
            cb.bind("<Button-1>", lambda e, url=meme['url']: self.update_meme_preview(url))
            frame.pack(fill=tk.X, padx=5, pady=2)
            self.meme_widgets[meme['url']] = var

    def update_meme_preview(self, url):
        if self.video_player:
            self.video_player.stop()
            self.video_player = None

        self.image_preview_label.pack_forget()
        self.video_preview_label.pack_forget()

        is_video = url.endswith(('.mp4', '.gif'))

        if is_video:
            self.video_preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.video_preview_label.config(text="Loading video preview...")
            threading.Thread(target=self._load_video_preview, args=(url,), daemon=True).start()
        else:
            self.image_preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.image_preview_label.config(image='', text="Loading image preview...")
            threading.Thread(target=self._load_image_preview, args=(url,), daemon=True).start()

    def _load_image_preview(self, url):
        img = fetch_media_for_preview(url, is_video=False)
        if not img:
            self.after(0, lambda: self.image_preview_label.config(text="Preview failed to load."))
            return

        self.preview_frame.update_idletasks()
        pane_width = self.preview_frame.winfo_width() - 10
        pane_height = self.preview_frame.winfo_height() - 10

        img.thumbnail((pane_width, pane_height), Image.Resampling.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(img)
        self.after(0, lambda: self.image_preview_label.config(image=self.preview_image, text=""))

    def _load_video_preview(self, url):
        video_path = fetch_media_for_preview(url, is_video=True)
        if not video_path:
            self.after(0, lambda: self.video_preview_label.config(text="Video preview failed to load."))
            return

        self.preview_frame.update_idletasks()
        width = self.preview_frame.winfo_width() - 10
        height = self.preview_frame.winfo_height() - 10

        def play_video():
            try:
                if self.video_preview_label.winfo_ismapped():
                    self.video_player = tkvideo(video_path, self.video_preview_label, loop=1, size=(width, height))
                    self.video_player.play()
            except Exception as e:
                print(f"Error playing video preview: {e}")
                self.video_preview_label.config(text="Could not play video.")

        self.after(0, play_video)

    def compile_video(self):
        if not all([self.intro_full_path, self.outro_full_path, self.background_full_path]):
            messagebox.showwarning("Missing Files", "Please select an intro, outro, and background video.")
            return

        selected_memes = [meme for meme in self.found_memes if self.meme_widgets.get(meme['url'], tk.BooleanVar(value=False)).get()]
        if not selected_memes:
            messagebox.showwarning("No Memes Selected", "Please select at least one meme.")
            return

        # Instead of asking for a path, create a temporary one.
        temp_fd, temp_video_path = tempfile.mkstemp(suffix=".mp4")
        os.close(temp_fd)

        self.compile_button.config(state=tk.DISABLED, text="Compiling...")
        self.status_label.config(text="Video compilation in progress...")

        args = {
            "selected_memes": selected_memes,
            "intro_path": self.intro_full_path,
            "outro_path": self.outro_full_path,
            "background_path": self.background_full_path,
            "output_path": temp_video_path, # Use the temp path
            "enable_tts": self.tts_enabled_var.get(),
            "elevenlabs_api_key": self.elevenlabs_api_key.get(),
            "tesseract_cmd_path": self.tesseract_cmd_path.get(),
            "voice_id": self.voices_map.get(self.selected_voice_id.get()),
            "vertical_format": self.vertical_format_var.get(),
            "music_path": self.music_full_path
        }
        threading.Thread(target=self._compile_video_thread, args=(args,), daemon=True).start()

    def _compile_video_thread(self, args):
        # `create_video` returns tts_failures list on success, or None on failure.
        result = create_video(**args)
        self.after(0, self._on_compile_complete, result, args["output_path"])

    def _on_compile_complete(self, result, video_path):
        self.compile_button.config(state=tk.NORMAL, text="Compile Video")
        self.status_label.config(text="")

        if result is None:
            messagebox.showerror("Error", "Video compilation failed. Check the console for details.")
            if os.path.exists(video_path):
                os.remove(video_path) # Clean up failed artifact
            return

        # If we are here, compilation was successful. `result` is the list of TTS failures.
        tts_failures = result

        # This method will be fully implemented in the next step.
        self.open_final_preview_window(video_path, tts_failures)

    def open_final_preview_window(self, video_path, tts_failures):
        FinalPreviewWindow(self, video_path, tts_failures)


class FinalPreviewWindow(tk.Toplevel):
    def __init__(self, master, video_path, tts_failures):
        super().__init__(master)
        self.master = master
        self.video_path = video_path
        self.video_player = None

        self.title("Final Preview & Upload")
        self.geometry("960x720")
        self.configure(bg=BG_COLOR)

        # Make window modal
        self.grab_set()
        self.focus_set()
        self.transient(master)

        # --- Widgets ---
        # Video Player
        self.video_label = ttk.Label(self, background=BG_SECONDARY)
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Button Frame
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        button_frame.columnconfigure([0, 1, 2], weight=1)

        ttk.Button(button_frame, text="Upload to YouTube", command=self.upload_to_youtube).grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        ttk.Button(button_frame, text="Save a Copy", command=self.save_a_copy).grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        ttk.Button(button_frame, text="Edit / Retry", command=self.edit_retry).grid(row=0, column=2, padx=5, pady=5, sticky='ew')

        # TTS Failures Display
        if tts_failures:
            failures_text = "TTS Failures:\n" + "\n".join([f"- {title}" for title, reason in tts_failures])
            ttk.Label(self, text=failures_text, justify=tk.LEFT, foreground="orange").pack(pady=5)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(100, self.play_video) # Delay to allow window to draw

    def play_video(self):
        try:
            self.video_player = tkvideo(self.video_path, self.video_label, loop=1, size=(940, 528)) # Approx 16:9
            self.video_player.play()
        except Exception as e:
            self.video_label.config(text=f"Error playing video preview: {e}")
            print(f"Error playing final preview: {e}")

    def upload_to_youtube(self):
        # The FinalPreviewWindow needs access to the main app's client_secrets_path
        # We can get it from self.master
        client_secrets_path = self.master.youtube_client_secrets_path.get()
        if not client_secrets_path:
            messagebox.showerror("YouTube Error", "Client secrets file not set. Please configure it in the Settings tab.")
            return

        UploadDialog(self, self.video_path, client_secrets_path)

    def save_a_copy(self):
        save_path = filedialog.asksaveasfilename(
            initialfile=os.path.basename(self.video_path),
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4")]
        )
        if save_path:
            try:
                shutil.copy(self.video_path, save_path)
                messagebox.showinfo("Success", f"Video saved successfully to {save_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save video: {e}")

    def edit_retry(self):
        self.cleanup_and_close()

    def on_closing(self):
        # Closing the window is the same as clicking "Edit / Retry"
        self.cleanup_and_close()

    def cleanup_and_close(self):
        if self.video_player:
            self.video_player.stop()

        # Delete the temporary video file
        if os.path.exists(self.video_path):
            try:
                os.remove(self.video_path)
                print(f"Removed temporary video file: {self.video_path}")
            except Exception as e:
                print(f"Error removing temporary video file: {e}")

        self.destroy()

    def save_config(self):
        config_data = {
            "reddit_client_id": self.reddit_client_id.get(),
            "reddit_client_secret": self.reddit_client_secret.get(),
            "tesseract_cmd_path": self.tesseract_cmd_path.get(),
            "elevenlabs_api_key": self.elevenlabs_api_key.get(),
            "selected_voice_id_name": self.selected_voice_id.get(),
            "tts_enabled": self.tts_enabled_var.get(),
            "vertical_format": self.vertical_format_var.get(),
            "youtube_client_secrets_path": self.youtube_client_secrets_path.get()
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings: {e}")

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            self.reddit_client_id.set(config_data.get("reddit_client_id", ""))
            self.reddit_client_secret.set(config_data.get("reddit_client_secret", ""))
            self.tesseract_cmd_path.set(config_data.get("tesseract_cmd_path", ""))
            self.elevenlabs_api_key.set(config_data.get("elevenlabs_api_key", ""))
            self.tts_enabled_var.set(config_data.get("tts_enabled", True))
            self.vertical_format_var.set(config_data.get("vertical_format", False))
            self.youtube_client_secrets_path.set(config_data.get("youtube_client_secrets_path", ""))

            # If API key exists, automatically refresh data
            if self.elevenlabs_api_key.get():
                self._refresh_elevenlabs_data()
                # Restore the previously selected voice
                saved_voice_name = config_data.get("selected_voice_id_name")
                if saved_voice_name in self.voices_map:
                    self.selected_voice_id.set(saved_voice_name)

        except FileNotFoundError:
            print("Config file not found. Starting with default settings.")
        except Exception as e:
            print(f"Error loading config: {e}")

    def on_closing(self):
        print("Closing application...")
        if self.video_player:
            self.video_player.stop()

        if os.path.exists(TEMP_PREVIEW_DIR):
            try:
                shutil.rmtree(TEMP_PREVIEW_DIR)
                print(f"Removed temporary preview directory: {TEMP_PREVIEW_DIR}")
            except Exception as e:
                print(f"Error removing temp directory: {e}")

        self.save_config()
        self.destroy()

if __name__ == "__main__":
    app = MemeCompilerApp()
    app.mainloop()


class UploadDialog(tk.Toplevel):
    def __init__(self, master, video_path, client_secrets_path):
        super().__init__(master)
        self.master = master # This is the FinalPreviewWindow
        self.video_path = video_path
        self.client_secrets_path = client_secrets_path

        self.title("YouTube Upload Details")
        self.geometry("500x400")
        self.configure(bg=BG_COLOR)
        self.grab_set()
        self.focus_set()
        self.transient(master)

        # --- Widgets ---
        self.title_var = tk.StringVar(value="My Awesome Meme Compilation")
        self.description_var = tk.StringVar(value="Check out this cool video I made!")
        self.privacy_var = tk.StringVar(value="private")

        ttk.Label(self, text="Title:").pack(pady=(10, 0))
        ttk.Entry(self, textvariable=self.title_var, width=80).pack(fill=tk.X, padx=10)

        ttk.Label(self, text="Description:").pack(pady=(10, 0))
        self.desc_text = tk.Text(self, height=5, background=BG_SECONDARY, foreground=TEXT_COLOR, insertbackground=PRIMARY_COLOR)
        self.desc_text.pack(fill=tk.X, padx=10)
        self.desc_text.insert("1.0", self.description_var.get())

        ttk.Label(self, text="Privacy:").pack(pady=(10, 0))
        privacy_menu = ttk.Combobox(self, textvariable=self.privacy_var, values=["public", "private", "unlisted"], state="readonly")
        privacy_menu.pack()

        self.status_label = ttk.Label(self, text="")
        self.status_label.pack(pady=10)

        self.upload_button = ttk.Button(self, text="Start Upload", command=self.start_upload)
        self.upload_button.pack(pady=10)

    def start_upload(self):
        self.upload_button.config(state=tk.DISABLED)
        self.status_label.config(text="Starting upload... Please check the console for authentication.")

        upload_details = {
            "file_path": self.video_path,
            "title": self.title_var.get(),
            "description": self.desc_text.get("1.0", tk.END),
            "privacy_status": self.privacy_var.get()
        }

        threading.Thread(target=self._upload_thread, args=(upload_details,), daemon=True).start()

    def _upload_thread(self, details):
        service = youtube_uploader.get_authenticated_service(self.client_secrets_path)

        if not service:
            self.after(0, self.on_upload_complete, False, "Failed to authenticate with YouTube.")
            return

        video_id = youtube_uploader.upload_video(
            youtube_service=service,
            file_path=details["file_path"],
            title=details["title"],
            description=details["description"],
            privacy_status=details["privacy_status"]
        )

        success = video_id is not None
        message = f"Upload successful! Video ID: {video_id}" if success else "Upload failed. Check console for details."
        self.after(0, self.on_upload_complete, success, message, details["file_path"])

    def on_upload_complete(self, success, message, video_path):
        messagebox.showinfo("Upload Complete", message) if success else messagebox.showerror("Upload Failed", message)
        self.upload_button.config(state=tk.NORMAL)
        self.status_label.config(text="")
        if success:
            self.destroy()
            # This is the FinalPreviewWindow, we need to tell it to close and clean up.
            self.master.cleanup_and_close()
