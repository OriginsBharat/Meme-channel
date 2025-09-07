import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import json
import requests
from io import BytesIO
from PIL import Image, ImageTk

from .reddit_scraper import find_memes, get_reddit_instance
from .video_compiler import create_video
from .tts_processor import get_elevenlabs_subscription_info, get_elevenlabs_voices, play_voice_preview
# --- Theme and Styling ---
BG_COLOR = "#2a004f" # Dark Purple
BG_SECONDARY = "#1e0038"
TEXT_COLOR = "#f0e8ff"
PRIMARY_COLOR = "#ff00ff"  # Neon Pink
SECONDARY_COLOR = "#9d00ff" # Neon Purple
FONT_NAME = "Trebuchet MS"

def fetch_image(url):
    """Downloads an image from a URL and returns it as a PIL Image object."""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error fetching image for preview: {e}")
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
        self.api_key = tk.StringVar()
        self.voices_map = {}
        self.selected_voice_id = tk.StringVar()
        self.char_count_var = tk.StringVar(value="Characters Left: N/A")
        self.config_file = "config.json"
        self.vertical_format_var = tk.BooleanVar(value=False)

        # --- Style Configuration ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, font=(FONT_NAME, 11))
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure("Header.TLabel", font=(FONT_NAME, 24, "bold"), foreground=PRIMARY_COLOR)
        self.style.configure("TButton", background=PRIMARY_COLOR, foreground=BG_COLOR, font=(FONT_NAME, 12, "bold"), borderwidth=0)
        self.style.map("TButton", background=[('active', SECONDARY_COLOR)])
        self.style.configure("TEntry", fieldbackground="#4a2a6f", foreground=TEXT_COLOR, insertcolor=PRIMARY_COLOR)
        self.style.configure("TLabelframe", background=BG_SECONDARY, bordercolor=PRIMARY_COLOR, relief=tk.RIDGE)
        self.style.configure("TLabelframe.Label", background=BG_SECONDARY, foreground=PRIMARY_COLOR, font=(FONT_NAME, 12, "bold"))
        self.style.configure("TCheckbutton", background=BG_SECONDARY, foreground=TEXT_COLOR)
        self.style.map("TCheckbutton", indicatorcolor=[('active', SECONDARY_COLOR), ('selected', PRIMARY_COLOR)])
        self.style.configure("Url.TLabel", foreground="#d0a0ff", font=(FONT_NAME, 11, 'underline'))
        self.style.configure("Path.TLabel", foreground=TEXT_COLOR, background=BG_SECONDARY, font=(FONT_NAME, 9))
        self.style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=BG_SECONDARY, foreground=TEXT_COLOR, padding=[10, 5], font=(FONT_NAME, 11, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", PRIMARY_COLOR)], foreground=[("selected", BG_COLOR)])


        self.configure(bg=BG_COLOR)
        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        # --- Main Layout ---
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(self.main_frame, text="Meme Video Compiler", style="Header.TLabel")
        header.pack(pady=10)

        # --- Character Count Display (Top Left) ---
        char_count_label = ttk.Label(header, textvariable=self.char_count_var, font=(FONT_NAME, 10))
        char_count_label.place(x=0, y=0, anchor='nw')

        # --- Tabbed Interface ---
        notebook = ttk.Notebook(self.main_frame, style="TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        compiler_tab = ttk.Frame(notebook, style="TFrame", padding=10)
        settings_tab = ttk.Frame(notebook, style="TFrame", padding=10)

        notebook.add(compiler_tab, text="Compiler")
        notebook.add(settings_tab, text="Settings")

        self.create_compiler_tab(compiler_tab)
        self.create_settings_tab(settings_tab)

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Ready. Configure your API key in Settings.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w', padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_compiler_tab(self, parent):
        # Create a canvas and a scrollbar
        canvas = tk.Canvas(parent, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="TFrame")

        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create a window in the canvas for the frame
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_frame_configure(event):
            # Update the scroll region to encompass the inner frame
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            # Resize the inner frame to match the canvas width
            canvas.itemconfig(canvas_frame, width=event.width)

        scrollable_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        # --- Place all widgets inside the scrollable_frame ---
        content_frame = scrollable_frame

        search_group = ttk.LabelFrame(content_frame, text="Step 1: Find Memes", padding="10")
        search_group.pack(fill=tk.X, pady=5, padx=10)
        keyword_frame = ttk.Frame(search_group, style="TLabelframe")
        keyword_frame.pack(fill=tk.X)
        ttk.Label(keyword_frame, text="Keyword:", style="TLabelframe.Label").pack(side=tk.LEFT, padx=(0, 5))
        self.keyword_var = tk.StringVar(value="dankmemes")
        ttk.Entry(keyword_frame, textvariable=self.keyword_var, width=40).pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.search_button = ttk.Button(keyword_frame, text="Search...", command=self.start_search)
        self.search_button.pack(side=tk.RIGHT, padx=(10, 0))

        self.results_group = ttk.LabelFrame(content_frame, text="Step 2: Select Memes (Click text to preview)", padding="10")
        paned_window = ttk.PanedWindow(self.results_group, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        list_canvas = tk.Canvas(paned_window, bg=BG_SECONDARY, highlightthickness=0)
        meme_scrollbar = ttk.Scrollbar(paned_window, orient="vertical", command=list_canvas.yview)
        self.meme_list_frame = ttk.Frame(list_canvas, style="TLabelframe")
        self.meme_list_frame.bind("<Configure>", lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))
        list_canvas.create_window((0, 0), window=self.meme_list_frame, anchor="nw")
        list_canvas.configure(yscrollcommand=meme_scrollbar.set)
        paned_window.add(list_canvas, weight=1)
        paned_window.add(meme_scrollbar)

        preview_frame = ttk.Frame(paned_window, width=500, style="TLabelframe")
        self.preview_label = ttk.Label(preview_frame, text="Click a meme title to preview", anchor=tk.CENTER, background=BG_SECONDARY)
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        paned_window.add(preview_frame, weight=2)

        self.bottom_controls_frame = ttk.Frame(content_frame)
        self.video_group = ttk.LabelFrame(self.bottom_controls_frame, text="Step 3: Add Your Video Files", padding="10")
        self.video_group.pack(fill=tk.X, pady=5, padx=10)

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
        self.compile_group.pack(fill=tk.X, pady=5, padx=10, side=tk.BOTTOM)

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
        settings_group = ttk.LabelFrame(parent, text="ElevenLabs Configuration", padding="10")
        settings_group.pack(fill=tk.X, pady=5, padx=10)

        api_key_frame = ttk.Frame(settings_group, style="TLabelframe")
        api_key_frame.pack(fill=tk.X, pady=5)
        ttk.Label(api_key_frame, text="API Key:", style="TLabelframe.Label").pack(side=tk.LEFT, padx=(0, 5))
        api_key_entry = ttk.Entry(api_key_frame, textvariable=self.api_key, width=60, show="*")
        api_key_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        button_frame = ttk.Frame(settings_group, style="TLabelframe")
        button_frame.pack(fill=tk.X, pady=10)
        save_button = ttk.Button(button_frame, text="Save and Refresh Voices", command=self.save_config_and_refresh)
        save_button.pack(side=tk.LEFT, padx=5)
        clear_button = ttk.Button(button_frame, text="Clear Key", command=self.clear_api_key)
        clear_button.pack(side=tk.LEFT, padx=5)

    def update_meme_preview(self, meme_url):
        self.preview_label.config(image='', text="Loading preview...")
        threading.Thread(target=self._load_preview_image, args=(meme_url,), daemon=True).start()

    def _load_preview_image(self, url):
        img = fetch_image(url)
        if not img:
            self.after(0, lambda: self.preview_label.config(text="Preview failed to load."))
            return
        pane_width, pane_height = 500, 400
        img.thumbnail((pane_width, pane_height), Image.Resampling.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(img)
        self.after(0, lambda: self.preview_label.config(image=self.preview_image, text=""))

    def select_file(self, file_type):
        if file_type == 'music':
            filetypes = [("Audio Files", "*.mp3 *.wav")]
        else:
            filetypes = [("Video/GIF Files", "*.mp4 *.mov *.avi *.gif")]

        filepath = filedialog.askopenfilename(title=f"Select {file_type.title()} File", filetypes=filetypes)

        if filepath:
            if file_type == 'intro':
                self.intro_full_path = filepath
                self.intro_path_display.set(os.path.basename(filepath))
            elif file_type == 'outro':
                self.outro_full_path = filepath
                self.outro_path_display.set(os.path.basename(filepath))
            elif file_type == 'background':
                self.background_full_path = filepath
                self.background_path_display.set(os.path.basename(filepath))
            elif file_type == 'music':
                self.music_full_path = filepath
                self.music_path_display.set(os.path.basename(filepath))
            self.check_compilation_readiness()

    def start_search(self):
        self.search_button.config(state=tk.DISABLED)
        self.status_var.set(f"Searching for '{self.keyword_var.get()}' memes...")
        for widget in self.meme_list_frame.winfo_children(): widget.destroy()
        self.meme_widgets.clear()
        self.results_group.pack_forget()
        self.bottom_controls_frame.pack_forget()
        search_thread = threading.Thread(target=self.search_worker, daemon=True)
        search_thread.start()

    def search_worker(self):
        try:
            reddit = get_reddit_instance()
            self.found_memes = find_memes(reddit, self.keyword_var.get())
            self.after(0, self.update_results_list)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Search Error", f"An error occurred: {e}"))
            self.status_var.set("Error during search.")
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
            self.results_group.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
            self.bottom_controls_frame.pack(fill=tk.X, pady=5, padx=10)
        else:
            self.status_var.set(f"No memes found for '{self.keyword_var.get()}'. Try another keyword.")
        self.check_compilation_readiness()

    def check_compilation_readiness(self):
        memes_selected = any(item['var'].get() for item in self.meme_widgets.values())
        videos_selected = all([self.intro_full_path, self.outro_full_path, self.background_full_path])
        if memes_selected and videos_selected:
            self.compile_button.config(state=tk.NORMAL)
        else:
            self.compile_button.config(state=tk.DISABLED)

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.api_key.set(config.get("api_key", ""))
                if self.api_key.get():
                    self.status_var.set("API Key loaded. Go to Settings to refresh data if needed.")
            else:
                self.status_var.set("No API key found. Please add one in the Settings tab.")
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to load config: {e}")

    def save_config_and_refresh(self):
        key = self.api_key.get()
        if not key:
            messagebox.showwarning("API Key", "Please enter an API key before saving.")
            return

        with open(self.config_file, 'w') as f:
            json.dump({"api_key": key}, f)

        messagebox.showinfo("API Key", "API Key saved successfully.")
        self.status_var.set("API Key saved. Fetching voices and account info...")
        # Run updates in a separate thread to keep UI responsive
        threading.Thread(target=self.refresh_elevenlabs_data, daemon=True).start()

    def clear_api_key(self):
        self.api_key.set("")
        self.voices_map.clear()
        self.voice_dropdown['values'] = []
        self.selected_voice_id.set('')
        self.char_count_var.set("Characters Left: N/A")
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        messagebox.showinfo("API Key", "API Key has been cleared.")
        self.status_var.set("API Key cleared. Add a new key to use TTS features.")

    def refresh_elevenlabs_data(self):
        key = self.api_key.get()
        if not key:
            return

        # Update character count
        sub_info = get_elevenlabs_subscription_info(key)
        if sub_info:
            used = sub_info.character_count
            limit = sub_info.character_limit
            remaining = limit - used
            self.after(0, lambda: self.char_count_var.set(f"Characters Left: {remaining}"))
        else:
            self.after(0, lambda: self.char_count_var.set("Characters Left: Check API Key"))

        # Update voices
        self.voices_map = get_elevenlabs_voices(key)
        if self.voices_map:
            voice_names = list(self.voices_map.keys())
            self.after(0, lambda: self.voice_dropdown.config(values=voice_names))
            if voice_names:
                self.after(0, lambda: self.selected_voice_id.set(voice_names[0]))
            self.after(0, lambda: self.status_var.set("Ready."))
        else:
            self.after(0, lambda: self.status_var.set("Could not fetch voices. Check API key or connection."))

    def preview_selected_voice(self):
        key = self.api_key.get()
        voice_name = self.selected_voice_id.get()
        if not key or not voice_name:
            messagebox.showwarning("Preview Error", "Cannot preview voice without an API key and a selected voice.")
            return

        voice_id = self.voices_map.get(voice_name)
        if not voice_id:
            messagebox.showerror("Preview Error", "Could not find ID for selected voice.")
            return

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

    def start_compilation(self):
        selected_memes = [item['meme'] for item in self.meme_widgets.values() if item['var'].get()]
        if not selected_memes:
            messagebox.showerror("Error", "No memes selected.")
            return

        tts_enabled = self.tts_enabled_var.get()
        api_key = self.api_key.get()
        voice_name = self.selected_voice_id.get()
        voice_id = self.voices_map.get(voice_name)
        vertical_format = self.vertical_format_var.get()
        music_path = self.music_full_path

        if tts_enabled and not all([api_key, voice_id]):
            messagebox.showerror("TTS Error", "TTS is enabled, but no API key is configured or voice is selected. Please check your settings.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4")])
        if not output_path: return

        self.status_var.set("Starting video compilation... This may take a while.")
        self.compile_button.config(state=tk.DISABLED)

        compilation_thread = threading.Thread(
            target=self.compilation_worker,
            args=(selected_memes, self.intro_full_path, self.outro_full_path, self.background_full_path, output_path, tts_enabled, api_key, voice_id, vertical_format, music_path),
            daemon=True
        )
        compilation_thread.start()

    def compilation_worker(self, memes, intro, outro, bg, output, tts_enabled, api_key, voice_id, vertical_format, music_path):
        try:
            create_video(memes, intro, outro, bg, output, enable_tts=tts_enabled, api_key=api_key, voice_id=voice_id, vertical_format=vertical_format, music_path=music_path)
            self.after(0, lambda: messagebox.showinfo("Success!", f"Video compiled and saved to:\n{output}"))
            self.status_var.set("Compilation finished! Ready for a new task.")
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Compilation Error", f"An error occurred: {e}"))
            self.status_var.set("Error during compilation.")
        finally:
            self.after(0, lambda: self.check_compilation_readiness())

if __name__ == "__main__":
    if not all([os.environ.get("REDDIT_CLIENT_ID"), os.environ.get("REDDIT_CLIENT_SECRET")]):
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("Missing Credentials", "Reddit API credentials are not set in environment variables. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET for the app to work.")
    app = MemeCompilerApp()
    app.mainloop()
