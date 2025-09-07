import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import requests
from io import BytesIO
from PIL import Image, ImageTk

from .reddit_scraper import find_memes, get_reddit_instance
from .video_compiler import create_video
from .tts_processor import get_available_voices
from .dependency_handler import check_dependencies

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
        self.geometry("1200x800") # Increased width for preview

        # --- Class Attributes ---
        self.found_memes = []
        self.intro_path = tk.StringVar()
        self.outro_path = tk.StringVar()
        self.background_path = tk.StringVar()
        self.tts_enabled_var = tk.BooleanVar(value=True)
        self.voices_map = get_available_voices()
        self.selected_voice_name = tk.StringVar()
        self.preview_image = None # To hold a reference to the PhotoImage

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
        self.style.configure("TCheckbutton", background=BG_SECONDARY, indicatorcolor=PRIMARY_COLOR)
        self.style.map("TCheckbutton", indicatorcolor=[('selected', SECONDARY_COLOR)])

        self.configure(bg=BG_COLOR)
        self.create_widgets()

    def create_widgets(self):
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(self.main_frame, text="Meme Video Compiler", style="Header.TLabel")
        header.pack(pady=10)

        # --- Step 1: Search ---
        search_group = ttk.LabelFrame(self.main_frame, text="Step 1: Find Memes", padding="10")
        search_group.pack(fill=tk.X, pady=5, padx=10)

        keyword_frame = ttk.Frame(search_group, style="TLabelframe")
        keyword_frame.pack(fill=tk.X)
        ttk.Label(keyword_frame, text="Keyword:", style="TLabelframe.Label").pack(side=tk.LEFT, padx=(0, 5))
        self.keyword_var = tk.StringVar(value="dankmemes")
        ttk.Entry(keyword_frame, textvariable=self.keyword_var, width=40).pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.search_button = ttk.Button(keyword_frame, text="Search...", command=self.start_search)
        self.search_button.pack(side=tk.RIGHT, padx=(10, 0))

        # --- Step 2: Select Memes (Initially Hidden) ---
        self.results_group = ttk.LabelFrame(self.main_frame, text="Step 2: Select Your Memes", padding="10")

        # PanedWindow to allow resizing between list and preview
        paned_window = ttk.PanedWindow(self.results_group, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Left pane: Listbox
        list_frame = ttk.Frame(paned_window, width=400)
        self.results_listbox = tk.Listbox(list_frame, bg="#333", fg=TEXT_COLOR, selectbackground=SECONDARY_COLOR, height=15, selectmode=tk.MULTIPLE, relief=tk.FLAT)
        self.results_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        self.results_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_listbox.bind('<<ListboxSelect>>', self.on_meme_select)
        paned_window.add(list_frame, weight=1)

        # Right pane: Preview
        preview_frame = ttk.Frame(paned_window, width=500)
        self.preview_label = ttk.Label(preview_frame, text="Select a meme to preview", anchor=tk.CENTER, background=BG_SECONDARY)
        self.preview_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        paned_window.add(preview_frame, weight=2)

        # --- Step 3 & 4 (Combined and initially hidden) ---
        self.bottom_controls_frame = ttk.Frame(self.main_frame)

        self.video_group = ttk.LabelFrame(self.bottom_controls_frame, text="Step 3: Add Your Video Files", padding="10")
        self.video_group.pack(fill=tk.X, pady=5, padx=0)
        file_select_frame = ttk.Frame(self.video_group, style="TLabelframe")
        file_select_frame.pack(fill=tk.X)
        ttk.Button(file_select_frame, text="Select Intro", command=lambda: self.select_file(self.intro_path)).pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Button(file_select_frame, text="Select Background", command=lambda: self.select_file(self.background_path)).pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Button(file_select_frame, text="Select Outro", command=lambda: self.select_file(self.outro_path)).pack(side=tk.LEFT, expand=True, padx=5)

        self.compile_group = ttk.LabelFrame(self.bottom_controls_frame, text="Step 4: Finish & Compile", padding="10")
        self.compile_group.pack(fill=tk.X, pady=5, padx=0, side=tk.BOTTOM)
        tts_options_frame = ttk.Frame(self.compile_group, style="TLabelframe")
        tts_options_frame.pack(fill=tk.X, pady=5)
        tts_check = ttk.Checkbutton(tts_options_frame, text="Add TTS Voiceover", variable=self.tts_enabled_var, style="TCheckbutton")
        tts_check.pack(side=tk.LEFT, anchor='w')
        ttk.Label(tts_options_frame, text="Select Voice:", style="TLabelframe.Label").pack(side=tk.LEFT, padx=(20, 5))
        voice_menu = ttk.Combobox(tts_options_frame, textvariable=self.selected_voice_name, state='readonly', width=30)
        voice_menu['values'] = list(self.voices_map.keys())
        if voice_menu['values']: self.selected_voice_name.set(voice_menu['values'][0])
        voice_menu.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.compile_button = ttk.Button(self.compile_group, text="Compile Video!", command=self.start_compilation, state=tk.DISABLED)
        self.compile_button.pack(fill=tk.X, pady=5, ipady=10)

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Ready. Enter a keyword to start.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w', padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def on_meme_select(self, event=None):
        self.check_compilation_readiness()
        self.update_meme_preview()

    def update_meme_preview(self):
        selections = self.results_listbox.curselection()
        if not selections:
            return

        selected_index = selections[0] # Preview the first selected item
        meme = self.found_memes[selected_index]
        url = meme['url']

        if not url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            self.preview_label.config(image='', text="Video/Link cannot be previewed.")
            return

        self.preview_label.config(image='', text="Loading preview...")
        threading.Thread(target=self._load_preview_image, args=(url,), daemon=True).start()

    def _load_preview_image(self, url):
        img = fetch_image(url)
        if not img:
            self.after(0, lambda: self.preview_label.config(text="Preview failed to load."))
            return

        # Resize image to fit the preview pane
        pane_width = self.preview_label.winfo_width()
        pane_height = self.preview_label.winfo_height()
        if pane_width < 2 or pane_height < 2: # Check if the widget is visible
            pane_width, pane_height = 500, 400 # Fallback size

        img.thumbnail((pane_width, pane_height), Image.Resampling.LANCZOS)

        self.preview_image = ImageTk.PhotoImage(img)
        self.after(0, lambda: self.preview_label.config(image=self.preview_image, text=""))

    def select_file(self, var):
        filepath = filedialog.askopenfilename(title=f"Select Video File", filetypes=[("Video/GIF Files", "*.mp4 *.mov *.avi *.gif"), ("All files", "*.*")])
        if filepath:
            var.set(os.path.basename(filepath)) # Show only filename
            self.check_compilation_readiness()

    def start_search(self):
        self.search_button.config(state=tk.DISABLED)
        self.status_var.set(f"Searching for '{self.keyword_var.get()}' memes...")
        self.results_listbox.delete(0, tk.END)
        self.results_group.pack_forget()
        self.bottom_controls_frame.pack_forget()
        search_thread = threading.Thread(target=self.search_worker, daemon=True)
        search_thread.start()

    def search_worker(self):
        try:
            # Assumes credentials are set via env vars for now
            reddit = get_reddit_instance()
            self.found_memes = find_memes(reddit, self.keyword_var.get())
            self.after(0, self.update_results_list)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Search Error", f"An error occurred: {e}"))
            self.status_var.set("Error during search.")
        finally:
            self.after(0, lambda: self.search_button.config(state=tk.NORMAL))

    def update_results_list(self):
        if self.found_memes:
            for meme in self.found_memes:
                self.results_listbox.insert(tk.END, f"({meme['upvotes']}) {meme['title']}")
            self.status_var.set(f"Found {len(self.found_memes)} memes. Select some to continue.")
            self.results_group.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
            self.bottom_controls_frame.pack(fill=tk.X, pady=5, padx=10)
        else:
            self.status_var.set(f"No memes found for '{self.keyword_var.get()}'. Try another keyword.")
        self.check_compilation_readiness()

    def check_compilation_readiness(self, event=None):
        memes_selected = len(self.results_listbox.curselection()) > 0
        videos_selected = all([self.intro_path.get(), self.outro_path.get(), self.background_path.get()])

        if memes_selected and videos_selected:
            self.compile_button.config(state=tk.NORMAL)
        else:
            self.compile_button.config(state=tk.DISABLED)

    def start_compilation(self):
        selected_indices = self.results_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Error", "No memes selected.")
            return

        selected_memes = [self.found_memes[i] for i in selected_indices]

        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4")])
        if not output_path:
            return

        self.status_var.set("Starting video compilation... This may take a while.")
        self.compile_button.config(state=tk.DISABLED)

        tts_enabled = self.tts_enabled_var.get()
        voice_name = self.selected_voice_name.get()
        voice_id = self.voices_map.get(voice_name)

        compilation_thread = threading.Thread(
            target=self.compilation_worker,
            args=(selected_memes, self.intro_path.get(), self.outro_path.get(), self.background_path.get(), output_path, tts_enabled, voice_id),
            daemon=True
        )
        compilation_thread.start()

    def compilation_worker(self, memes, intro, outro, bg, output, tts_enabled, voice_id):
        try:
            create_video(memes, intro, outro, bg, output, enable_tts=tts_enabled, voice_id=voice_id)
            self.after(0, lambda: messagebox.showinfo("Success!", f"Video compiled and saved to:\n{output}"))
            self.status_var.set("Compilation finished! Ready for a new task.")
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Compilation Error", f"An error occurred: {e}"))
            self.status_var.set("Error during compilation.")
        finally:
            self.after(0, lambda: self.check_compilation_readiness()) # Re-enable if still valid

if __name__ == "__main__":
    missing_deps_error = check_dependencies()
    if missing_deps_error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependencies", missing_deps_error)
        root.destroy()
        exit()

    if not all([os.environ.get("REDDIT_CLIENT_ID"), os.environ.get("REDDIT_CLIENT_SECRET")]):
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("Missing Credentials", "Reddit API credentials are not set in environment variables. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET for the app to work.")
        root.destroy()

    app = MemeCompilerApp()
    app.mainloop()
