import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import shutil
import configparser
import praw
from PIL import Image, ImageTk
from .reddit_scraper import find_memes, get_reddit_instance
from .video_compiler import create_video
from .tts_processor import get_available_voices

# --- Reusable Components ---

class ScrollableFrame(ttk.Frame):
    """A scrollable frame that can hold widgets."""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self, bg=BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Bind mouse wheel scrolling
        self.scrollable_frame.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

# --- Theme and Styling ---
BG_COLOR = "#2a004f" # Dark Purple
BG_SECONDARY = "#1e0038"
TEXT_COLOR = "#f0e8ff"
PRIMARY_COLOR = "#ff00ff"  # Neon Pink
SECONDARY_COLOR = "#9d00ff" # Neon Purple
FONT_NAME = "Trebuchet MS"

class MemeCompilerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Meme Video Compiler")
        self.geometry("900x800")

        # --- Class Attributes ---
        self.found_memes = []
        self.thumbnail_dir = None
        self.intro_path = tk.StringVar()
        self.outro_path = tk.StringVar()
        self.background_path = tk.StringVar()
        self.tts_enabled_var = tk.BooleanVar(value=True)
        self.voices_map = get_available_voices()
        self.selected_voice_name = tk.StringVar()
        self.client_id_var = tk.StringVar()
        self.client_secret_var = tk.StringVar()
        self.user_agent_var = tk.StringVar()


        # --- Style Configuration ---
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure(".", background=BG_COLOR, foreground=TEXT_COLOR, font=(FONT_NAME, 11))
        self.style.configure("TFrame", background=BG_COLOR)
        self.style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR)
        self.style.configure("Header.TLabel", font=(FONT_NAME, 24, "bold"), foreground=PRIMARY_COLOR)
        self.style.configure("TButton", background=PRIMARY_COLOR, foreground=BG_COLOR, font=(FONT_NAME, 12, "bold"), borderwidth=0, padding=10)
        self.style.map("TButton",
            background=[('active', SECONDARY_COLOR), ('hover', '#ff4dff')],
            foreground=[('active', TEXT_COLOR)]
        )
        self.style.configure("TEntry", fieldbackground="#4a2a6f", foreground=TEXT_COLOR, insertcolor=PRIMARY_COLOR)
        self.style.configure("TLabelframe", background=BG_SECONDARY, bordercolor=PRIMARY_COLOR, relief=tk.RIDGE)
        self.style.configure("TLabelframe.Label", background=BG_SECONDARY, foreground=PRIMARY_COLOR, font=(FONT_NAME, 12, "bold"))
        self.style.configure("TCheckbutton", background=BG_SECONDARY, indicatorcolor=PRIMARY_COLOR)
        self.style.map("TCheckbutton", indicatorcolor=[('selected', SECONDARY_COLOR)])


        self.configure(bg=BG_COLOR)
        self.create_widgets()
        self.load_config()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        # Clean up the thumbnail directory before closing
        if self.thumbnail_dir and os.path.exists(self.thumbnail_dir):
            shutil.rmtree(self.thumbnail_dir)
        self.destroy()

    def create_widgets(self):
        # --- Main Layout ---
        header = ttk.Label(self, text="Meme Video Compiler", style="Header.TLabel", anchor="center")
        header.pack(pady=10, fill=tk.X)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)

        compiler_tab = ttk.Frame(self.notebook, padding="10")
        settings_tab = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(compiler_tab, text='Compiler')
        self.notebook.add(settings_tab, text='Settings')

        self._create_compiler_tab(compiler_tab)
        self._create_settings_tab(settings_tab)

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Ready. Check settings and then enter a keyword to start.")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w', padding=5)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_compiler_tab(self, parent):
        # --- Step 1: Search ---
        search_group = ttk.LabelFrame(parent, text="Step 1: Find Memes", padding="10")
        search_group.pack(fill=tk.X, pady=5, padx=5)

        keyword_frame = ttk.Frame(search_group, style="TLabelframe")
        keyword_frame.pack(fill=tk.X, expand=True, pady=5)
        ttk.Label(keyword_frame, text="Keyword:", style="TLabelframe.Label").pack(side=tk.LEFT, padx=(0, 10))
        self.keyword_var = tk.StringVar(value="dankmemes")
        ttk.Entry(keyword_frame, textvariable=self.keyword_var, width=40).pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.search_button = ttk.Button(keyword_frame, text="Search...", command=self.start_search)
        self.search_button.pack(side=tk.RIGHT, padx=(10, 0))

        # --- Step 2: Select Memes (Initially Hidden) ---
        self.results_group = ttk.LabelFrame(parent, text="Step 2: Select Your Memes", padding="10")
        self.results_frame = ScrollableFrame(self.results_group)
        self.results_frame.pack(fill="both", expand=True)

        # --- Step 3: Add Videos ---
        self.video_group = ttk.LabelFrame(parent, text="Step 3: Add Your Video Files", padding="10")

        file_select_frame = ttk.Frame(self.video_group, style="TLabelframe")
        file_select_frame.pack(fill=tk.X, pady=5)
        file_select_frame.columnconfigure((0, 1, 2), weight=1) # Make columns expand equally

        # --- Intro ---
        intro_frame = ttk.Frame(file_select_frame, style="TLabelframe")
        intro_frame.grid(row=0, column=0, padx=(0, 5), sticky='ew')
        ttk.Button(intro_frame, text="Select Intro", command=lambda: self.select_file(self.intro_path, "Intro")).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(intro_frame, text="X", command=lambda: self.clear_file_selection(self.intro_path), width=2).pack(side=tk.LEFT)

        # --- Background ---
        bg_frame = ttk.Frame(file_select_frame, style="TLabelframe")
        bg_frame.grid(row=0, column=1, padx=5, sticky='ew')
        ttk.Button(bg_frame, text="Select Background", command=lambda: self.select_file(self.background_path, "Background")).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(bg_frame, text="X", command=lambda: self.clear_file_selection(self.background_path), width=2).pack(side=tk.LEFT)

        # --- Outro ---
        outro_frame = ttk.Frame(file_select_frame, style="TLabelframe")
        outro_frame.grid(row=0, column=2, padx=(5, 0), sticky='ew')
        ttk.Button(outro_frame, text="Select Outro", command=lambda: self.select_file(self.outro_path, "Outro")).pack(side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(outro_frame, text="X", command=lambda: self.clear_file_selection(self.outro_path), width=2).pack(side=tk.LEFT)

        labels_frame = ttk.Frame(self.video_group, style="TLabelframe")
        labels_frame.pack(fill=tk.X, pady=5)
        ttk.Label(labels_frame, textvariable=self.intro_path, wraplength=280, style="TLabelframe.Label").pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Label(labels_frame, textvariable=self.background_path, wraplength=280, style="TLabelframe.Label").pack(side=tk.LEFT, expand=True, padx=5)
        ttk.Label(labels_frame, textvariable=self.outro_path, wraplength=280, style="TLabelframe.Label").pack(side=tk.LEFT, expand=True, padx=5)

        # --- Step 4: Compile (Initially Hidden) ---
        self.compile_group = ttk.LabelFrame(parent, text="Step 4: Finish & Compile", padding="10")
        tts_options_frame = ttk.Frame(self.compile_group, style="TLabelframe")
        tts_options_frame.pack(fill=tk.X, pady=5)
        tts_check = ttk.Checkbutton(tts_options_frame, text="Add TTS Voiceover", variable=self.tts_enabled_var, style="TCheckbutton")
        tts_check.pack(side=tk.LEFT, anchor='w')

        voice_label = ttk.Label(tts_options_frame, text="Select Voice:", style="TLabelframe.Label")
        voice_label.pack(side=tk.LEFT, padx=(20, 5))

        voice_menu = ttk.Combobox(tts_options_frame, textvariable=self.selected_voice_name, state='readonly', width=30)
        voice_menu.pack(side=tk.LEFT, expand=True, fill=tk.X)

        if self.voices_map:
            voice_menu['values'] = list(self.voices_map.keys())
            self.selected_voice_name.set(voice_menu['values'][0])
        else:
            self.tts_enabled_var.set(False)
            tts_check.config(state=tk.DISABLED)
            voice_menu.config(state=tk.DISABLED)
            self.selected_voice_name.set("No voices found")
        self.compile_button = ttk.Button(self.compile_group, text="Compile Video!", command=self.start_compilation)
        self.compile_button.pack(fill=tk.X, pady=5, ipady=10)

        # --- Progress Bar (Initially Hidden) ---
        self.progress_var = tk.DoubleVar()
        self.progress_label_var = tk.StringVar()
        self.progress_label = ttk.Label(self.compile_group, textvariable=self.progress_label_var, style="TLabelframe.Label")
        self.progress_bar = ttk.Progressbar(self.compile_group, variable=self.progress_var, maximum=100)

    def clear_file_selection(self, var_to_clear):
        var_to_clear.set("")
        self.status_var.set("File selection cleared.")
        self.check_compilation_readiness()

    def select_file(self, var, file_type):
        filepath = filedialog.askopenfilename(title=f"Select {file_type} File", filetypes=[("Video/GIF Files", "*.mp4 *.mov *.avi *.gif"), ("All files", "*.*")])
        if filepath:
            var.set(filepath)
            self.status_var.set(f"{file_type} file selected: {os.path.basename(filepath)}")
            self.check_compilation_readiness()

    def start_search(self):
        self.search_button.config(state=tk.DISABLED)
        self.status_var.set(f"Searching for '{self.keyword_var.get()}' memes...")
        self.results_listbox.delete(0, tk.END)
        self.results_group.pack_forget()
        self.video_group.pack_forget()
        self.compile_group.pack_forget()
        search_thread = threading.Thread(target=self.search_worker, daemon=True)
        search_thread.start()

    def search_worker(self):
        try:
            # Clean up previous search's thumbnail directory if it exists
            if self.thumbnail_dir and os.path.exists(self.thumbnail_dir):
                shutil.rmtree(self.thumbnail_dir)

            client_id = self.client_id_var.get()
            client_secret = self.client_secret_var.get()
            user_agent = self.user_agent_var.get()
            reddit = get_reddit_instance(client_id, client_secret, user_agent)
            self.found_memes, self.thumbnail_dir = find_memes(reddit, self.keyword_var.get())

            # Add a selection variable to each meme
            for meme in self.found_memes:
                meme['selected'] = tk.BooleanVar(value=False)

            self.after(0, self.update_results_list)
        except (ValueError, praw.exceptions.PRAWException) as e:
            logging.error("Failed to search for memes.", exc_info=True)
            self.after(0, lambda: messagebox.showerror("Search Error", f"Could not complete search.\n\nReason: {e}"))
            self.status_var.set("Error during search.")
        finally:
            self.after(0, lambda: self.search_button.config(state=tk.NORMAL))

    def update_results_list(self):
        # Clear previous results
        for widget in self.results_frame.scrollable_frame.winfo_children():
            widget.destroy()

        if self.found_memes:
            self.status_var.set(f"Found {len(self.found_memes)} memes. Select which to include.")

            for i, meme in enumerate(self.found_memes):
                card = ttk.Frame(self.results_frame.scrollable_frame, padding=5, style="TLabelframe")
                card.pack(fill=tk.X, pady=5, padx=5)

                # Thumbnail
                try:
                    img = Image.open(meme['thumbnail_path'])
                    img.thumbnail((150, 150))
                    meme['image'] = ImageTk.PhotoImage(img) # Keep a reference

                    thumb_label = ttk.Label(card, image=meme['image'])
                    thumb_label.pack(side=tk.LEFT, padx=5)
                except Exception as e:
                    logging.error(f"Failed to create thumbnail for {meme['thumbnail_path']}", exc_info=True)
                    # Add a placeholder
                    thumb_label = ttk.Label(card, text="[Image\nError]", style="TLabel")
                    thumb_label.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=10)

                # Details Frame
                details_frame = ttk.Frame(card)
                details_frame.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

                title_label = ttk.Label(details_frame, text=f"({meme['upvotes']}) {meme['title']}", wraplength=500, justify=tk.LEFT, style="TLabelframe.Label")
                title_label.pack(anchor='nw', fill=tk.X)

                subreddit_label = ttk.Label(details_frame, text=f"r/{meme['subreddit']}", style="TLabel")
                subreddit_label.pack(anchor='nw', fill=tk.X)

                # Selection Checkbox
                select_check = ttk.Checkbutton(card, variable=meme['selected'], text="Include", command=self.check_compilation_readiness)
                select_check.pack(side=tk.RIGHT, padx=5)

            self.results_group.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)
            self.video_group.pack(fill=tk.X, pady=5, padx=10)
        else:
            self.status_var.set(f"No memes found for '{self.keyword_var.get()}'. Try another keyword.")

        self.check_compilation_readiness()

    def check_compilation_readiness(self, event=None):
        memes_selected = any(meme['selected'].get() for meme in self.found_memes)
        videos_selected = all([self.intro_path.get(), self.outro_path.get(), self.background_path.get()])

        if memes_selected and videos_selected:
            self.compile_group.pack(fill=tk.X, pady=5, padx=10)
        else:
            self.compile_group.pack_forget()

    def start_compilation(self):
        selected_memes = [meme for meme in self.found_memes if meme['selected'].get()]

        if not selected_memes:
            messagebox.showerror("Error", "No memes selected.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Video", "*.mp4")])
        if not output_path:
            return

        self.status_var.set("Starting video compilation... This may take a while.")
        self.compile_button.config(state=tk.DISABLED)

        # Show and initialize the progress bar
        self.progress_label.pack(fill=tk.X, padx=5, pady=(5,0))
        self.progress_bar.pack(fill=tk.X, padx=5, pady=(0,5))
        self.update_progress(0, "Preparing to compile...")

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
            create_video(memes, intro, outro, bg, output, enable_tts=tts_enabled, voice_id=voice_id, progress_callback=self.update_progress)
            # The final progress update handles the success message
        except Exception as e:
            logging.error("Video compilation failed.", exc_info=True)
            self.after(0, lambda: messagebox.showerror("Compilation Error", f"An unexpected error occurred during video compilation.\n\n{e}\n\nCheck meme_compiler.log for details."))
            self.status_var.set("Error during compilation.")
        finally:
            # Hide progress bar and re-enable compile button
            self.after(0, lambda: self.progress_label.pack_forget())
            self.after(0, lambda: self.progress_bar.pack_forget())
            self.after(0, lambda: self.compile_button.config(state=tk.NORMAL))

    def update_progress(self, percent, message):
        def _update():
            self.progress_var.set(percent)
            self.progress_label_var.set(message)
            if percent == 100:
                self.status_var.set("Compilation finished! Ready for a new task.")
                messagebox.showinfo("Success!", "Video compilation successful!")

        self.after(0, _update)

    def _create_settings_tab(self, parent):
        # --- Reddit API Settings ---
        api_group = ttk.LabelFrame(parent, text="Reddit API Credentials", padding="10")
        api_group.pack(fill=tk.X, pady=5, padx=5)

        ttk.Label(api_group, text="Client ID:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        ttk.Entry(api_group, textvariable=self.client_id_var, width=60).grid(row=0, column=1, sticky='we', pady=5, padx=5)

        ttk.Label(api_group, text="Client Secret:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        ttk.Entry(api_group, textvariable=self.client_secret_var, width=60, show="*").grid(row=1, column=1, sticky='we', pady=5, padx=5)

        ttk.Label(api_group, text="User Agent:").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        ttk.Entry(api_group, textvariable=self.user_agent_var, width=60).grid(row=2, column=1, sticky='we', pady=5, padx=5)

        api_group.columnconfigure(1, weight=1)

        # --- Action Buttons ---
        button_frame = ttk.Frame(parent, style="TLabelframe")
        button_frame.pack(pady=20, padx=5, fill=tk.X, ipady=5)

        self.test_button = ttk.Button(button_frame, text="Test Credentials", command=self.start_test_credentials)
        self.test_button.pack(side=tk.RIGHT, padx=(10, 0))

        save_button = ttk.Button(button_frame, text="Save Settings", command=self.save_config)
        save_button.pack(side=tk.RIGHT, fill=tk.X, expand=True)


    def start_test_credentials(self):
        self.test_button.config(state=tk.DISABLED)
        self.status_var.set("Testing Reddit API credentials...")
        test_thread = threading.Thread(target=self.test_credentials_worker, daemon=True)
        test_thread.start()

    def test_credentials_worker(self):
        try:
            client_id = self.client_id_var.get()
            client_secret = self.client_secret_var.get()
            user_agent = self.user_agent_var.get()

            reddit = get_reddit_instance(client_id, client_secret, user_agent)
            redditor = reddit.user.me() # Authenticated call

            success_message = f"Successfully authenticated as u/{redditor.name}."
            self.after(0, lambda: messagebox.showinfo("Success", success_message))
            self.after(0, lambda: self.status_var.set("Credentials are valid."))

        except (ValueError, praw.exceptions.PRAWException) as e:
            logging.error("Credential test failed.", exc_info=True)
            error_message = f"Credential test failed.\n\nError: {e}"
            self.after(0, lambda: messagebox.showerror("Error", error_message))
            self.after(0, lambda: self.status_var.set("Credential test failed."))

        finally:
            self.after(0, lambda: self.test_button.config(state=tk.NORMAL))

    def load_config(self):
        config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            self.user_agent_var.set("MemeCompiler/0.1 by YourUsername") # Default
            return

        config.read('config.ini')
        if 'Reddit' in config:
            self.client_id_var.set(config['Reddit'].get('client_id', ''))
            self.client_secret_var.set(config['Reddit'].get('client_secret', ''))
            self.user_agent_var.set(config['Reddit'].get('user_agent', ''))
            self.status_var.set("Loaded settings from config.ini.")

    def save_config(self):
        config = configparser.ConfigParser()
        config['Reddit'] = {
            'client_id': self.client_id_var.get(),
            'client_secret': self.client_secret_var.get(),
            'user_agent': self.user_agent_var.get()
        }
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        self.status_var.set("Configuration saved successfully!")
        messagebox.showinfo("Settings Saved", "Your Reddit API settings have been saved to config.ini.")


import logging
import os
import imageio_ffmpeg
from .dependency_handler import check_dependencies

if __name__ == "__main__":
    # 1. Configure FFmpeg path for moviepy
    # This tells moviepy to use the ffmpeg executable that imageio-ffmpeg downloaded
    os.environ['FFMPEG_BINARY'] = imageio_ffmpeg.get_ffmpeg_exe()

    # 2. Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        filename='meme_compiler.log',
        filemode='w' # Overwrite log file on each run
    )
    logging.info("Application starting...")

    # 2. Check for external dependencies before starting the app
    missing_deps_error = check_dependencies()
    if missing_deps_error:
        # Need a dummy root to show the messagebox without the main window
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing Dependencies", missing_deps_error)
        root.destroy()
        exit()

    # 2. A check for Reddit credentials is now handled via the Settings tab.
    app = MemeCompilerApp()
    app.mainloop()
