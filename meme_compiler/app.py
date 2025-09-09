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
        if is_video:
            temp_dir = "temp_media"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            temp_path = os.path.join(temp_dir, os.path.basename(urlparse(url).path))
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return temp_path
        else:
            return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error fetching media for preview: {e}")
        return None

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
        self.reddit_client_id = tk.StringVar()
        self.reddit_client_secret = tk.StringVar()
        self.voices_map = {}
        self.selected_voice_id = tk.StringVar()
        self.char_count_var = tk.StringVar(value="Characters Left: N/A")
        self.config_file = "config.json"
        self.used_memes_file = "used_memes.txt"
        self.vertical_format_var = tk.BooleanVar(value=False)

        # --- Style Configuration ---
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

    def create_widgets(self):
        self.main_frame = ttk.Frame(self, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        header = ttk.Label(self.main_frame, text="Meme Video Compiler", style="Header.TLabel")
        header.pack(pady=(0, 20))
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
        def on_frame_configure(event): canvas.configure(scrollregion=canvas.bbox("all"))
        def on_canvas_configure(event): canvas.itemconfig(canvas_frame, width=event.width)
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
        list_canvas = tk.Canvas(paned_window, bg=BG_SECONDARY, highlightthickness=0)
        meme_scrollbar = ttk.Scrollbar(paned_window, orient="vertical", command=list_canvas.yview)
        self.meme_list_frame = ttk.Frame(list_canvas, style="TLabelframe")
        self.meme_list_frame.bind("<Configure>", lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))
        list_canvas.create_window((0, 0), window=self.meme_list_frame, anchor="nw")
        list_canvas.configure(yscrollcommand=meme_scrollbar.set)
        paned_window.add(list_canvas, weight=1)
        paned_window.add(meme_scrollbar)
        self.preview_frame = ttk.Frame(paned_window, width=500, style="TLabelframe")
        self.image_preview_label = ttk.Label(self.preview_frame, text="Click a meme title to preview", anchor=tk.CENTER, background=BG_SECONDARY)
        self.image_preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.video_preview_label = ttk.Label(self.preview_frame, background=BG_SECONDARY)
        paned_window.add(self.preview_frame, weight=2)
        self.bottom_controls_frame = ttk.Frame(content_frame)
        self.video_group = ttk.LabelFrame(self.bottom_controls_frame, text="Step 3: Add Your Video Files", padding="10")
        self.video_group.pack(fill=tk.X, pady=10, padx=10)
        file_select_frame = ttk.Frame(self.video_group, style="TLabelframe")
        file_select_frame.pack(fill=tk.X)
        ttk.Button(file_select_frame, text="Select Intro", command=lambda: self.select_file('intro')).pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Button(file_select_frame, text="Select Background", command=lambda: self.select_file('background')).pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Button(file_select_frame, text="Select Outro", command=lambda: self.select_file('outro')).pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Button(file_select_frame, text="Select BG Music", command=lambda: self.select_file('music')).pack(side=tk.LEFT, expand=True, padx=5)
        labels_frame = ttk.Frame(self.video_group, style="TLabelframe")
        labels_frame.pack(fill=tk.X, pady=(5,0))
        ttk.Label(labels_frame, textvariable=self.intro_path_display, wraplength=220, style="Path.TLabel").pack(side=tk.LEFT, expand=True, padx=5, anchor='w')
        ttk.Label(labels_frame, textvariable=self.background_path_display, wraplength=220, style="Path.TLabel").pack(side=tk.LEFT, expand=True, padx=5, anchor='w')
        ttk.Label(labels_frame, textvariable=self.outro_path_display, wraplength=220, style="Path.TLabel").pack(side=tk.LEFT, expand=True, padx=5, anchor='w')
        ttk.Label(labels_frame, textvariable=self.music_path_display, wraplength=220, style="Path.TLabel").pack(side=tk.LEFT, expand=True, padx=5, anchor='w')
        self.compile_group = ttk.LabelFrame(self.bottom_controls_frame, text="Step 4: Finish & Compile", padding="10")
        self.compile_group.pack(fill=tk.X, pady=10, padx=10, side=tk.BOTTOM)
        tts_frame = ttk.Frame(self.compile_group, style="TLabelframe")
        tts_frame.pack(fill=tk.X, pady=5)
        tts_check = ttk.Checkbutton(tts_frame, text="Add TTS Voiceover for Image Memes", variable=self.tts_enabled_var, style="TCheckbutton")
        tts_check.pack(anchor='w', side=tk.LEFT)
        self.voice_dropdown = ttk.Combobox(tts_frame, textvariable=self.selected_voice_id, state="readonly", width=30)
        self.voice_dropdown.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        self.preview_voice_button = ttk.Button(tts_frame, text="Preview Voice", command=self.preview_selected_voice)
        self.preview_voice_button.pack(side=tk.LEFT, padx=5)
        vertical_check = ttk.Checkbutton(self.compile_group, text="Create 9:16 Vertical Video (for Shorts/TikTok)", variable=self.vertical_format_var, style="TCheckbutton")
        vertical_check.pack(anchor='w', pady=5)
        self.compile_button = ttk.Button(self.compile_group, text="Compile Video!", command=self.start_compilation, state=tk.DISABLED)
        self.compile_button.pack(fill=tk.X, pady=5, ipady=10)

    def create_settings_tab(self, parent):
        reddit_group = ttk.LabelFrame(parent, text="Reddit Credentials", padding="10")
        reddit_group.pack(fill=tk.X, pady=10, padx=10)
        reddit_id_frame = ttk.Frame(reddit_group, style="TLabelframe")
        reddit_id_frame.pack(fill=tk.X, pady=5)
        ttk.Label(reddit_id_frame, text="Client ID:", style="TLabelframe.Label").pack(side=tk.LEFT, padx=(0, 5), ipadx=29)
        reddit_id_entry = ttk.Entry(reddit_id_frame, textvariable=self.reddit_client_id, width=50, show="*")
        reddit_id_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        reddit_secret_frame = ttk.Frame(reddit_group, style="TLabelframe")
        reddit_secret_frame.pack(fill=tk.X, pady=5)
        ttk.Label(reddit_secret_frame, text="Client Secret:", style="TLabelframe.Label").pack(side=tk.LEFT, padx=(0, 5), ipadx=10)
        reddit_secret_entry = ttk.Entry(reddit_secret_frame, textvariable=self.reddit_client_secret, width=50, show="*")
        reddit_secret_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        eleven_group = ttk.LabelFrame(parent, text="ElevenLabs TTS Configuration", padding="10")
        eleven_group.pack(fill=tk.X, pady=10, padx=10)
        eleven_api_frame = ttk.Frame(eleven_group, style="TLabelframe")
        eleven_api_frame.pack(fill=tk.X, pady=5)
        ttk.Label(eleven_api_frame, text="API Key:", style="TLabelframe.Label").pack(side=tk.LEFT, padx=(0, 5), ipadx=38)
        eleven_api_entry = ttk.Entry(eleven_api_frame, textvariable=self.elevenlabs_api_key, width=50, show="*")
        eleven_api_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        ocr_group = ttk.LabelFrame(parent, text="OCR.space Configuration", padding="10")
        ocr_group.pack(fill=tk.X, pady=10, padx=10)
        ocr_api_frame = ttk.Frame(ocr_group, style="TLabelframe")
        ocr_api_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ocr_api_frame, text="API Key:", style="TLabelframe.Label").pack(side=tk.LEFT, padx=(0, 5), ipadx=38)
        ocr_api_entry = ttk.Entry(ocr_api_frame, textvariable=self.ocr_api_key, width=50, show="*")
        ocr_api_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=20, padx=10)
        save_button = ttk.Button(button_frame, text="Save All Settings & Refresh Voices", command=self.save_settings)
        save_button.pack(side=tk.LEFT, padx=5)
        clear_button = ttk.Button(button_frame, text="Clear All Settings", command=self.clear_settings)
        clear_button.pack(side=tk.LEFT, padx=5)

    def update_meme_preview(self, meme_url):
        if self.video_player: self.video_player.stop(); self.video_player = None
        self.image_preview_label.pack_forget(); self.video_preview_label.pack_forget()
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
        if not img: self.after(0, lambda: self.image_preview_label.config(text="Preview failed to load.")); return
        pane_width, pane_height = self.preview_frame.winfo_width(), self.preview_frame.winfo_height()
        img.thumbnail((pane_width, pane_height), Image.Resampling.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(img)
        self.after(0, lambda: self.image_preview_label.config(image=self.preview_image, text=""))

    def _load_video_preview(self, url):
        video_path = fetch_media(url, is_video=True)
        if not video_path: self.after(0, lambda: self.video_preview_label.config(text="Video preview failed to load.")); return
        def play_video():
            try:
                self.video_player = tkvideo(video_path, self.video_preview_label, loop=1, size=(self.preview_frame.winfo_width(), self.preview_frame.winfo_height()))
                self.video_player.play()
            except Exception as e:
                print(f"Error playing video preview: {e}"); self.video_preview_label.config(text="Could not play video.")
        self.after(0, play_video)

    def select_file(self, file_type):
        filetypes = [("Audio Files", "*.mp3 *.wav")] if file_type == 'music' else [("Video/GIF Files", "*.mp4 *.mov *.avi *.gif")]
        filepath = filedialog.askopenfilename(title=f"Select {file_type.title()} File", filetypes=filetypes)
        if filepath:
            if file_type == 'intro': self.intro_full_path = filepath; self.intro_path_display.set(os.path.basename(filepath))
            elif file_type == 'outro': self.outro_full_path = filepath; self.outro_path_display.set(os.path.basename(filepath))
            elif file_type == 'background': self.background_full_path = filepath; self.background_path_display.set(os.path.basename(filepath))
            elif file_type == 'music': self.music_full_path = filepath; self.music_path_display.set(os.path.basename(filepath))
            self.check_compilation_readiness()

    def start_search(self):
        self.search_button.config(state=tk.DISABLED)
        self.status_var.set(f"Searching for '{self.keyword_var.get()}' memes...")
        if self.video_player: self.video_player.stop()
        for widget in self.meme_list_frame.winfo_children(): widget.destroy()
        self.meme_widgets.clear()
        self.results_group.pack_forget()
        self.bottom_controls_frame.pack_forget()
        threading.Thread(target=self.search_worker, daemon=True).start()

    def search_worker(self):
        try:
            reddit_instance = get_reddit_instance(self.reddit_client_id.get(), self.reddit_client_secret.get())
            if not reddit_instance:
                self.after(0, lambda: messagebox.showerror("Reddit Error", "Could not connect to Reddit. Please check your credentials in Settings."))
                return
            self.found_memes = find_memes(reddit_instance, self.keyword_var.get(), used_memes_log=self.used_memes_file)
            self.after(0, self.update_results_list)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Search Error", f"An error occurred: {e}"))
        finally:
            self.after(0, lambda: self.search_button.config(state=tk.NORMAL))

    def update_results_list(self):
        for widget in self.meme_list_frame.winfo_children(): widget.destroy()
        self.meme_widgets.clear()
        if self.found_memes:
            for i, meme in enumerate(self.found_memes):
                var = tk.BooleanVar()
                cb = ttk.Checkbutton(self.meme_list_frame, variable=var, command=self.check_compilation_readiness, style="TCheckbutton")
                cb.grid(row=i, column=0, sticky='w')
                lbl = ttk.Label(self.meme_list_frame, text=f"({meme['upvotes']}) {meme['title']}", style="Url.TLabel", cursor="hand2", wraplength=350)
                lbl.grid(row=i, column=1, sticky='w', padx=5)
                lbl.bind("<Button-1>", lambda e, url=meme['url']: self.update_meme_preview(url))
                self.meme_widgets[i] = {'var': var, 'meme': meme}
            self.status_var.set(f"Found {len(self.found_memes)} memes. Select some to continue.")
            self.results_group.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
            self.bottom_controls_frame.pack(fill=tk.X, pady=10, padx=10)
        else:
            self.status_var.set(f"No memes found for '{self.keyword_var.get()}'. Try another keyword.")
        self.check_compilation_readiness()

    def check_compilation_readiness(self):
        memes_selected = any(item['var'].get() for item in self.meme_widgets.values())
        videos_selected = all([self.intro_full_path, self.outro_full_path, self.background_full_path])
        self.compile_button.config(state=tk.NORMAL if memes_selected and videos_selected else tk.DISABLED)

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.elevenlabs_api_key.set(config.get("elevenlabs_api_key", ""))
                    self.ocr_api_key.set(config.get("ocr_api_key", ""))
                    self.reddit_client_id.set(config.get("reddit_client_id", ""))
                    self.reddit_client_secret.set(config.get("reddit_client_secret", ""))
                if self.elevenlabs_api_key.get() and self.ocr_api_key.get() and self.reddit_client_id.get():
                    self.status_var.set("All settings loaded. Ready to search.")
            else:
                self.status_var.set("No settings found. Please configure the app in the Settings tab.")
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to load config: {e}")

    def save_settings(self):
        config_data = {
            "elevenlabs_api_key": self.elevenlabs_api_key.get(),
            "ocr_api_key": self.ocr_api_key.get(),
            "reddit_client_id": self.reddit_client_id.get(),
            "reddit_client_secret": self.reddit_client_secret.get()
        }
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f)
        messagebox.showinfo("Settings Saved", "Your settings have been saved.")
        if config_data["elevenlabs_api_key"]:
            self.status_var.set("Settings saved. Fetching ElevenLabs voices...")
            threading.Thread(target=self.refresh_elevenlabs_data, daemon=True).start()

    def clear_settings(self):
        self.elevenlabs_api_key.set(""); self.ocr_api_key.set(""); self.reddit_client_id.set(""); self.reddit_client_secret.set("")
        self.voices_map.clear(); self.voice_dropdown['values'] = []; self.selected_voice_id.set('')
        self.char_count_var.set("Characters Left: N/A")
        if os.path.exists(self.config_file): os.remove(self.config_file)
        messagebox.showinfo("Settings Cleared", "All settings have been cleared.")
        self.status_var.set("Settings cleared. Please configure them to proceed.")

    def refresh_elevenlabs_data(self):
        key = self.elevenlabs_api_key.get()
        if not key: return
        sub_info = get_elevenlabs_subscription_info(key)
        if sub_info:
            used = sub_info.character_count; limit = sub_info.character_limit
            remaining = limit - used
            self.after(0, lambda: self.char_count_var.set(f"Characters Left: {remaining}"))
        else:
            self.after(0, lambda: self.char_count_var.set("Characters Left: Check API Key"))
        self.voices_map = get_elevenlabs_voices(key)
        if self.voices_map:
            voice_names = list(self.voices_map.keys())
            self.after(0, lambda: self.voice_dropdown.config(values=voice_names))
            if voice_names: self.after(0, lambda: self.selected_voice_id.set(voice_names[0]))
            self.after(0, lambda: self.status_var.set("Ready."))
        else:
            self.after(0, lambda: self.status_var.set("Could not fetch voices. Check API key or connection."))

    def preview_selected_voice(self):
        key = self.elevenlabs_api_key.get()
        voice_name = self.selected_voice_id.get()
        if not key or not voice_name: messagebox.showwarning("Preview Error", "Cannot preview voice without an API key and a selected voice."); return
        voice_id = self.voices_map.get(voice_name)
        if not voice_id: messagebox.showerror("Preview Error", "Could not find ID for selected voice."); return
        self.status_var.set(f"Generating preview for {voice_name}...")
        self.preview_voice_button.config(state=tk.DISABLED)
        threading.Thread(target=self._preview_worker, args=(key, voice_id), daemon=True).start()

    def _preview_worker(self, key, voice_id):
        try:
            play_voice_preview(key, voice_id)
            self.after(0, lambda: self.status_var.set("Preview finished."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Preview Error", f"Failed to play preview: {e}"))
            self.after(0, lambda: self.status_var.set("Preview failed."))
        finally:
            self.after(0, lambda: self.preview_voice_button.config(state=tk.NORMAL))

    def _log_used_memes(self, memes):
        with open(self.used_memes_file, "a") as f:
            for meme in memes:
                f.write(meme['url'] + "\n")

    def start_compilation(self):
        selected_memes = [item['meme'] for item in self.meme_widgets.values() if item['var'].get()]
        if not selected_memes: messagebox.showerror("Error", "No memes selected."); return

        tts_enabled = self.tts_enabled_var.get()
        elevenlabs_key = self.elevenlabs_api_key.get()
        ocr_key = self.ocr_api_key.get()
        voice_name = self.selected_voice_id.get()
        voice_id = self.voices_map.get(voice_name)
        vertical_format = self.vertical_format_var.get()
        music_path = self.music_full_path

        if tts_enabled and not all([elevenlabs_key, voice_id, ocr_key]):
            messagebox.showerror("TTS Error", "TTS is enabled, but an API key (ElevenLabs or OCR) is missing or a voice is not selected. Please check your settings.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4")])
        if not output_path: return

        self.status_var.set("Starting video compilation... This may take a while.")
        self.compile_button.config(state=tk.DISABLED)

        compilation_thread = threading.Thread(
            target=self.compilation_worker,
            args=(selected_memes, self.intro_full_path, self.outro_full_path, self.background_full_path, output_path, tts_enabled, elevenlabs_key, ocr_key, voice_id, vertical_format, music_path),
            daemon=True
        )
        compilation_thread.start()

    def compilation_worker(self, memes, intro, outro, bg, output, tts_enabled, elevenlabs_key, ocr_key, voice_id, vertical_format, music_path):
        try:
            tts_failures = create_video(memes, intro, outro, bg, output, enable_tts=tts_enabled, elevenlabs_api_key=elevenlabs_key, ocr_api_key=ocr_key, voice_id=voice_id, vertical_format=vertical_format, music_path=music_path)
            def handle_result():
                if tts_failures is None:
                    messagebox.showerror("Compilation Error", "A critical error occurred during video creation. Check the console for details.")
                    self.status_var.set("Error during compilation.")
                    return
                messagebox.showinfo("Success!", f"Video compiled and saved to:\n{output}")
                self.status_var.set("Compilation finished! Ready for a new task.")
                self._log_used_memes(memes)
                if tts_failures:
                    failure_details = []
                    for title, error in tts_failures:
                        failure_details.append(f" - {title}: {error}")
                    failed_titles_str = "\n".join(failure_details)
                    warning_message = f"The video was created, but TTS failed for the following memes:\n\n{failed_titles_str}\n\nCommon reasons include being out of credits or the API rejecting certain text/characters."
                    messagebox.showwarning("TTS Failures", warning_message)
            self.after(0, handle_result)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Compilation Error", f"An unexpected error occurred in the compilation thread: {e}"))
            self.after(0, lambda: self.status_var.set("Error during compilation."))
        finally:
            self.after(0, lambda: self.check_compilation_readiness())

if __name__ == "__main__":
    app = MemeCompilerApp()
    app.mainloop()
