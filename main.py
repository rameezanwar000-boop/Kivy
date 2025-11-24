# video_downloader_ultimate.py
# --------------------------------------------------------------
# FEATURES: KIVYMD, HINDI FONT, QUEUE MANAGER, INSTA/X SUPPORT, WA STATUS SAVER, CLEAR BTN
# --------------------------------------------------------------
import os
import sys
import ctypes
import json
import threading
import time
import queue
import subprocess
import shutil
import re
import traceback
from pathlib import Path
from datetime import datetime

# === FORCE MESA OPENGL 3.3 BEFORE KIVY ===
dll_path = os.path.join(os.path.dirname(__file__), 'opengl32.dll')
if os.name == "nt" and os.path.exists(dll_path):
    print(f"Loading Mesa OpenGL from: {dll_path}")
    try:
        ctypes.CDLL(dll_path)
        print("Mesa OpenGL 3.3 LOADED SUCCESSFULLY")
    except Exception as e:
        print("DLL LOAD FAILED:", e)
else:
    if os.name == "nt":
        print("WARNING: opengl32.dll NOT FOUND! GUI may fail on some systems.")

# === SAFE STREAM WRAPPER ===
class _SafeStream:
    def __init__(self, base_stream=None, fallback_devnull=True):
        self._base = None
        for candidate in (base_stream, getattr(sys, 'stderr', None), getattr(sys, 'stdout', None), getattr(sys, '__stderr__', None), getattr(sys, '__stdout__', None)):
            if candidate is None:
                continue
            if hasattr(candidate, 'write') and callable(getattr(candidate, 'write', None)):
                self._base = candidate
                break
        if self._base is None and fallback_devnull:
            self._base = open(os.devnull, 'w', encoding='utf-8', errors='replace')
    
    def write(self, s):
        try:
            if not isinstance(s, str):
                s = str(s)
            self._base.write(s)
        except Exception:
            pass
    
    def flush(self):
        try:
            self._base.flush()
        except Exception:
            pass
    
    def writelines(self, lines):
        for ln in lines:
            self.write(ln)
    
    @property
    def encoding(self):
        try:
            return getattr(self._base, "encoding", "utf-8")
        except Exception:
            return "utf-8"
    
    @property
    def buffer(self):
        if hasattr(self._base, "buffer"):
            return self._base.buffer
        class FakeBuffer:
            def __init__(self, parent):
                self.parent = parent
            def write(self, b):
                if isinstance(b, (bytes, bytearray)):
                    text = b.decode('utf-8', 'replace')
                else:
                    text = str(b)
                self.parent.write(text)
            def flush(self):
                self.parent.flush()
        return FakeBuffer(self)

# Install safe streams
def ensure_safe_streams():
    if not (hasattr(sys.stderr, 'write') and callable(sys.stderr.write)):
        sys.stderr = _SafeStream(base_stream=getattr(sys, '__stderr__', None))
    else:
        sys.stderr = _SafeStream(base_stream=sys.stderr)
    if not (hasattr(sys.stdout, 'write') and callable(sys.stdout.write)):
        sys.stdout = _SafeStream(base_stream=getattr(sys, '__stdout__', None))
    else:
        sys.stdout = _SafeStream(base_stream=sys.stdout)

ensure_safe_streams()

# === AUTO-UPDATE yt-dlp ===
def update_ytdlp():
    try:
        print("Updating yt-dlp...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True, check=False, timeout=30
        )
        print("yt-dlp updated (or already up-to-date).")
    except Exception as e:
        print("yt-dlp update failed (continuing):", e)

try:
    threading.Thread(target=update_ytdlp, daemon=True).start()
except Exception:
    update_ytdlp()

# === IMPORT KIVYMD & yt_dlp ===
from kivy.utils import platform
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem, TwoLineListItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, MDRectangleFlatIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.imagelist import MDSmartTile
from kivymd.uix.gridlayout import MDGridLayout
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty
from kivy.core.text import LabelBase
from plyer import filechooser

ensure_safe_streams()
from yt_dlp import YoutubeDL
import logging
logging.getLogger("yt_dlp").setLevel(logging.ERROR)

# === BULLETPROOF yt_dlp PATCHES ===
import yt_dlp.utils
_original_write_string = yt_dlp.utils.write_string

def safe_write_string(s, out=None, encoding=None, only_once=False):
    if out is None:
        out = sys.stderr
    if not hasattr(out, 'write'):
        out = sys.stderr
    try:
        return _original_write_string(s, out=out, encoding=encoding, only_once=only_once)
    except:
        try:
            sys.stderr.write(str(s) + '\n')
            sys.stderr.flush()
        except:
            pass
        return 0

yt_dlp.utils.write_string = safe_write_string

# Prevent YoutubeDL from breaking sys.stderr in __init__
_original_ydl_init = YoutubeDL.__init__

def safe_ydl_init(self, params=None, *args, **kwargs):
    if params is None:
        params = {}
    else:
        params = params.copy()
    params.pop('_out_files', None)
    _original_ydl_init(self, params, *args, **kwargs)
    self._out_files.out = sys.stdout
    self._out_files.error = sys.stderr
    if self.params.get('quiet') or self.params.get('no_warnings'):
        self.to_screen = lambda *_, **__: None
        self.to_stderr = lambda msg, *_, **__: sys.stderr.write(f"{msg}\n")

YoutubeDL.__init__ = safe_ydl_init

# --------------------------------------------------------------
# GLOBAL SETTINGS
# --------------------------------------------------------------
# --------------------------------------------------------------
# GLOBAL SETTINGS (ANDROID-SAFE)
# --------------------------------------------------------------
import os
from pathlib import Path
from kivy.utils import platform

# Android storage imports
if platform == "android":
    from android.storage import app_storage_path, primary_external_storage_path

APP_TITLE = "Kivy"
HISTORY_FILE = "history.json"

# === USER DATA DIRECTORY (cookies, history, settings) ===
if platform == "android":
    USER_DATA_DIR = Path(app_storage_path()) / "KiyyDownloader"
else:
    USER_DATA_DIR = Path(
        os.getenv("APPDATA") or
        os.getenv("XDG_CONFIG_HOME") or
        (Path.home() / ".config")
    ) / "KiyyDownloader"

USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

COOKIES_PATH = USER_DATA_DIR / "cookies.txt"

def ensure_valid_cookies_file():
    if not COOKIES_PATH.exists():
        COOKIES_PATH.write_text("# Netscape HTTP Cookie File\n", encoding='utf-8')

ensure_valid_cookies_file()

# === DOWNLOAD DIRECTORY ===
if platform == "android":
    # saves to internal app storage (always allowed)
    DOWNLOAD_DIR = str(Path(primary_external_storage_path()) / "KiyyDownloads")
else:
    DOWNLOAD_DIR = str(Path.home() / "Downloads" / "KiyyDownloads")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# --------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------
def short(s, n=60):
    s = str(s)
    return (s[:n-1] + "...") if len(s) > n else s

def format_file_size(size_bytes):
    if size_bytes is None:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=5)
        return True
    except:
        if os.name == "nt":
            try:
                subprocess.run(["ffmpeg.exe", "-version"], capture_output=True, check=True, timeout=5)
                return True
            except:
                pass
    return False

# --------------------------------------------------------------
# WHATSAPP STATUS LOGIC (ANDROID)
# --------------------------------------------------------------
def get_whatsapp_statuses():
    """
    Scans standard Android paths for WhatsApp statuses.
    Returns a list of file paths.
    """
    possible_paths = [
        "/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/.Statuses",
        "/storage/emulated/0/Android/media/com.whatsapp.w4b/WhatsApp Business/Media/.Statuses",
        "/storage/emulated/0/WhatsApp/Media/.Statuses",
        "/storage/emulated/0/WhatsApp Business/Media/.Statuses",
    ]
    
    # If on Windows for testing, maybe check a local dummy folder
    if os.name == 'nt':
        possible_paths.append(os.path.join(os.getcwd(), "dummy_statuses"))

    found_files = []
    for p in possible_paths:
        if os.path.exists(p):
            try:
                files = sorted(os.listdir(p), key=lambda x: os.path.getmtime(os.path.join(p, x)), reverse=True)
                for f in files:
                    if f.endswith(".jpg") or f.endswith(".mp4"):
                        found_files.append(os.path.join(p, f))
            except Exception as e:
                print(f"Access denied or error reading {p}: {e}")
    
    return found_files

# --------------------------------------------------------------
# HINDI FONT SUPPORT
# --------------------------------------------------------------
def configure_hindi_font():
    font_path = None
    font_name = "HindiSupport"
    
    local_font = os.path.join(os.path.dirname(__file__), 'font.ttf')
    if os.path.exists(local_font):
        font_path = local_font
    elif os.name == 'nt':
        potential_paths = [
            "C:/Windows/Fonts/Nirmala.ttf",
            "C:/Windows/Fonts/nirmala.ttf",
            "C:/Windows/Fonts/NirmalaS.ttf",
            "C:/Windows/Fonts/Mangal.ttf",
            "C:/Windows/Fonts/Arial.ttf"
        ]
        for p in potential_paths:
            if os.path.exists(p):
                font_path = p
                break
    else:
        potential_paths = [
            "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
            "/System/Library/Fonts/Supplemental/DevanagariMT.ttc"
        ]
        for p in potential_paths:
            if os.path.exists(p):
                font_path = p
                break

    if font_path:
        print(f"Loading Hindi Font from: {font_path}")
        LabelBase.register(name=font_name, fn_regular=font_path)
        return font_name
    
    print("No specific Hindi font found. Using default.")
    return None

# --------------------------------------------------------------
# KIVYMD UI
# --------------------------------------------------------------
KV = '''
<StatusTile>:
    size_hint_y: None
    height: "200dp"
    overlap: False
    
    # Overlay icon for video identification
    MDIcon:
        icon: "video"
        color: 1,1,1,0.8
        font_size: "40sp"
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
        opacity: 1 if root.is_video else 0

    MDIconButton:
        icon: "download-circle"
        theme_text_color: "Custom"
        text_color: 1, 1, 1, 1
        pos_hint: {"right": 0.95, "bottom": 0.05}
        on_release: root.save_status()

<VideoListItem>:
    orientation: "horizontal"
    size_hint_y: None
    height: "40dp"
    padding: "10dp"
    spacing: "10dp"
    
    MDCheckbox:
        id: chk
        size_hint: None, None
        size: "30dp", "30dp"
        on_active: root.checkbox_changed(self.active)
    
    MDLabel:
        id: lbl
        text: root.text
        size_hint_y: None
        height: "30dp"
        theme_text_color: "Primary"
        shorten: True
        shorten_from: 'right'

<DownloadListItem>:
    orientation: "horizontal"
    size_hint_y: None
    height: "60dp"
    padding: "10dp"
    spacing: "10dp"
    
    MDLabel:
        id: title_label
        text: root.title_text
        size_hint_x: 0.6
        theme_text_color: "Primary"
        halign: "left"
        valign: "center"
        shorten: True
        shorten_from: 'right'
    
    MDLabel:
        id: status_label
        text: root.status_text
        size_hint_x: 0.2
        theme_text_color: "Secondary"
        halign: "center"
        valign: "center"
        font_style: "Caption"
    
    MDIconButton:
        id: pause_resume_btn
        icon: "pause"
        theme_text_color: "Custom"
        icon_color: app.theme_cls.primary_color
        size_hint: None, None
        size: "40dp", "40dp"
        on_release: root.toggle_pause_resume()
    
    MDIconButton:
        id: cancel_btn
        icon: "close"
        theme_text_color: "Custom"
        icon_color: app.theme_cls.error_color
        size_hint: None, None
        size: "40dp", "40dp"
        on_release: root.cancel_download()

<SearchScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: "10dp"
        padding: "20dp"
        
        # === SMART SEARCH FIELD WITH CLEAR BUTTON ===
        MDFloatLayout:
            size_hint_x: None
            width: "300dp"
            size_hint_y: None
            height: "50dp"
            pos_hint: {"center_x": 0.5}
            
            MDTextField:
                id: search_field
                hint_text: "Paste URL (YouTube, Insta, X...)"
                mode: "round"
                size_hint_x: 1
                pos_hint: {"center_x": 0.5, "center_y": 0.5}
                icon_left: "link"
                on_text_validate: root.perform_search()
            
            MDIconButton:
                icon: "close-circle"
                theme_text_color: "Custom"
                text_color: app.theme_cls.disabled_hint_text_color
                pos_hint: {"right": 0.98, "center_y": 0.5}
                opacity: 1 if search_field.text else 0
                disabled: not search_field.text
                on_release: search_field.text = ""
        
        ScrollView:
            MDList:
                id: video_list

<StatusScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: "10dp"
        padding: "5dp"
        
        MDBoxLayout:
            size_hint_y: None
            height: "50dp"
            padding: "10dp"
            MDLabel:
                text: "WhatsApp Statuses"
                font_style: "H5"
            MDIconButton:
                icon: "refresh"
                on_release: root.load_statuses()

        MDLabel:
            id: no_status_label
            text: "No statuses found (Check Permissions)"
            halign: "center"
            opacity: 0
            size_hint_y: None
            height: "0dp"

        ScrollView:
            MDGridLayout:
                id: status_grid
                cols: 2
                spacing: "10dp"
                padding: "10dp"
                adaptive_height: True

<SettingsScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: "10dp"
        padding: "20dp"
        
        MDLabel:
            text: "Settings"
            theme_text_color: "Primary"
            font_style: "H4"
            size_hint_y: None
            height: self.texture_size[1]
        
        MDLabel:
            text: "Download Location"
            theme_text_color: "Secondary"
            font_style: "Subtitle1"
            size_hint_y: None
            height: self.texture_size[1]
        
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "40dp"
            spacing: "10dp"
            
            MDLabel:
                id: current_path
                text: root.current_download_path
                theme_text_color: "Primary"
                shorten: True
                shorten_from: 'right'
        
        MDRaisedButton:
            text: "Change Folder"
            on_release: root.change_download_path()
            pos_hint: {"center_x": 0.5}
        
        MDBoxLayout:
            size_hint_y: None
            height: "20dp"
        
        MDLabel:
            text: "Authentication (Cookies)"
            theme_text_color: "Secondary"
            font_style: "Subtitle1"
            size_hint_y: None
            height: self.texture_size[1]
        
        MDLabel:
            text: "Required for Instagram/Age-restricted content"
            theme_text_color: "Hint"
            font_style: "Caption"
            size_hint_y: None
            height: "20dp"

        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "40dp"
            spacing: "10dp"
            
            MDLabel:
                id: cookies_status
                text: root.cookies_status_text
                theme_text_color: "Primary"
                shorten: True
                shorten_from: 'right'
        
        MDRaisedButton:
            text: "Select Cookies File"
            on_release: root.select_cookies_file()
            pos_hint: {"center_x": 0.5}

        Widget:
            size_hint_y: 1

<DownloadsScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: "10dp"
        padding: "20dp"
        
        MDLabel:
            text: "Downloads"
            theme_text_color: "Primary"
            font_style: "H4"
            size_hint_y: None
            height: self.texture_size[1]
        
        MDLabel:
            text: "Videos being downloaded"
            theme_text_color: "Secondary"
            font_style: "Subtitle1"
            size_hint_y: None
            height: self.texture_size[1]
        
        ScrollView:
            MDList:
                id: download_list

<SearchResultsScreen>:
    BoxLayout:
        orientation: 'vertical'
        spacing: "10dp"
        padding: "20dp"
        
        MDLabel:
            text: root.playlist_title
            theme_text_color: "Primary"
            font_style: "H6"
            size_hint_y: None
            height: self.texture_size[1]
            bold: True
            shorten: True
            shorten_from: 'right'
        
        ScrollView:
            MDList:
                id: video_list
        
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "60dp"
            spacing: "15dp"
            padding: [20, 0, 20, 0]
            pos_hint: {"center_x": 0.5}
            adaptive_width: True
            
            MDLabel:
                text: "Quality:"
                size_hint_x: None
                width: "60dp"
                theme_text_color: "Secondary"
                valign: "center"
            
            MDRectangleFlatIconButton:
                id: format_btn
                text: "best"
                icon: "chevron-down"
                theme_text_color: "Custom"
                text_color: app.theme_cls.primary_color
                line_color: app.theme_cls.primary_color
                icon_color: app.theme_cls.primary_color
                size_hint_y: None
                height: "40dp"
                pos_hint: {'center_y': 0.5}
                on_release: root.open_menu()
            
            MDRaisedButton:
                text: "Download Selected"
                size_hint_y: None
                height: "40dp"
                pos_hint: {'center_y': 0.5}
                on_release: root.download_selected()

MDScreen:
    BoxLayout:
        orientation: 'vertical'
        
        MDBoxLayout:
            size_hint_y: None
            height: "64dp"
            md_bg_color: app.theme_cls.primary_color
            elevation: 0
            padding: 0
            spacing: 0
            
            MDFloatLayout:
                MDLabel:
                    text: "Kivy"
                    font_style: "H4"
                    bold: False
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 1
                    adaptive_size: True
                    pos_hint: {"center_x": 0.5, "center_y": 0.5}

        ScreenManager:
            id: screen_manager
            
            SearchScreen:
                name: "search"
                id: search_screen

            StatusScreen:
                name: "status"
                id: status_screen
            
            SettingsScreen:
                name: "settings"
                id: settings_screen
            
            DownloadsScreen:
                name: "downloads"
                id: downloads_screen
            
            SearchResultsScreen:
                name: "search_results"
                id: search_results_screen
        
        # === BOTTOM NAV ===
        MDBoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: "56dp"
            md_bg_color: app.theme_cls.primary_color
            spacing: 0
            padding: 0
            
            # 1. SEARCH
            MDFloatLayout:
                size_hint_x: 1/4
                Button:
                    background_color: 0, 0, 0, 0
                    size_hint: 1, 1
                    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                    on_release: app.switch_screen("search")
                
                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_size: True
                    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                    spacing: "2dp"
                    
                    MDIcon:
                        icon: "magnify"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_size: "26sp"
                        adaptive_size: True
                        pos_hint: {'center_x': 0.5}
                    
                    MDLabel:
                        text: "Search"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_style: "Caption"
                        font_size: "11sp"
                        adaptive_size: True
                        pos_hint: {'center_x': 0.5}

            # 2. STATUS
            MDFloatLayout:
                size_hint_x: 1/4
                Button:
                    background_color: 0, 0, 0, 0
                    size_hint: 1, 1
                    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                    on_release: app.switch_screen("status")
                
                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_size: True
                    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                    spacing: "2dp"
                    
                    MDIcon:
                        icon: "whatsapp"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_size: "26sp"
                        adaptive_size: True
                        pos_hint: {'center_x': 0.5}
                    
                    MDLabel:
                        text: "Status"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_style: "Caption"
                        font_size: "11sp"
                        adaptive_size: True
                        pos_hint: {'center_x': 0.5}

            # 3. SETTINGS
            MDFloatLayout:
                size_hint_x: 1/4
                Button:
                    background_color: 0, 0, 0, 0
                    size_hint: 1, 1
                    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                    on_release: app.switch_screen("settings")
                
                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_size: True
                    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                    spacing: "2dp"
                    
                    MDIcon:
                        icon: "cog"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_size: "26sp"
                        adaptive_size: True
                        pos_hint: {'center_x': 0.5}
                    
                    MDLabel:
                        text: "Settings"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_style: "Caption"
                        font_size: "11sp"
                        adaptive_size: True
                        pos_hint: {'center_x': 0.5}

            # 4. DOWNLOADS
            MDFloatLayout:
                size_hint_x: 1/4
                Button:
                    background_color: 0, 0, 0, 0
                    size_hint: 1, 1
                    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                    on_release: app.switch_screen("downloads")
                
                MDBoxLayout:
                    orientation: 'vertical'
                    adaptive_size: True
                    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                    spacing: "2dp"
                    
                    MDIcon:
                        icon: "download"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_size: "26sp"
                        adaptive_size: True
                        pos_hint: {'center_x': 0.5}
                    
                    MDLabel:
                        text: "Downloads"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        font_style: "Caption"
                        font_size: "11sp"
                        adaptive_size: True
                        pos_hint: {'center_x': 0.5}
'''

class StatusTile(MDSmartTile):
    file_path = StringProperty()
    is_video = BooleanProperty(False)
    
    def save_status(self):
        app = MDApp.get_running_app()
        try:
            filename = os.path.basename(self.file_path)
            dest = os.path.join(app.download_dir, f"Status_{filename}")
            shutil.copy2(self.file_path, dest)
            app.show_dialog("Saved", f"Status saved to {short(dest, 30)}")
        except Exception as e:
            app.show_dialog("Error", f"Failed to save: {e}")

class StatusScreen(Screen):
    def on_enter(self):
        self.load_statuses()

    def load_statuses(self):
        self.ids.status_grid.clear_widgets()
        files = get_whatsapp_statuses()
        
        if not files:
            self.ids.no_status_label.opacity = 1
            self.ids.no_status_label.height = "30dp"
            return
        
        self.ids.no_status_label.opacity = 0
        self.ids.no_status_label.height = "0dp"
        
        for f in files:
            is_vid = f.endswith(".mp4")
            tile = StatusTile(
                source=f,
                file_path=f,
                is_video=is_vid,
                box_color=(0, 0, 0, 0.5),
                pos_hint={"center_x": .5, "center_y": .5}
            )
            self.ids.status_grid.add_widget(tile)

class DownloadListItem(MDBoxLayout):
    title_text = StringProperty()
    status_text = StringProperty("Pending...")
    is_paused = BooleanProperty(False)
    download_index = NumericProperty(0)
    
    def __init__(self, download_data=None, **kwargs):
        super().__init__(**kwargs)
        self.download_data = download_data
        self.app = MDApp.get_running_app()
    
    def toggle_pause_resume(self):
        if self.is_paused:
            self.is_paused = False
            self.ids.pause_resume_btn.icon = "pause"
            self.status_text = "Resuming..."
            if hasattr(self.app, 'resume_specific_download'):
                self.app.resume_specific_download(self.download_index)
        else:
            self.is_paused = True
            self.ids.pause_resume_btn.icon = "play"
            self.status_text = "Paused"
            if hasattr(self.app, 'pause_specific_download'):
                self.app.pause_specific_download(self.download_index)
    
    def cancel_download(self):
        if hasattr(self.app, 'cancel_specific_download'):
            self.app.cancel_specific_download(self.download_index)
        self.status_text = "Cancelled"
        self.ids.pause_resume_btn.disabled = True
        self.ids.cancel_btn.disabled = True

class VideoListItem(MDBoxLayout):
    text = StringProperty()
    checked = BooleanProperty(False)
    
    def __init__(self, video_data=None, **kwargs):
        super().__init__(**kwargs)
        self.video_data = video_data
    
    def checkbox_changed(self, active):
        self.checked = active

class SearchScreen(Screen):
    def perform_search(self):
        url = self.ids.search_field.text.strip()
        if url:
            self.ids.video_list.clear_widgets()
            loading_box = MDBoxLayout(
                orientation='vertical', 
                size_hint_y=None, 
                height="120dp", 
                padding="20dp",
                spacing="10dp"
            )
            spinner = MDSpinner(
                size_hint=(None, None), 
                size=("30dp", "30dp"), 
                pos_hint={'center_x': .5}, 
                active=True
            )
            lbl = MDLabel(
                text="Fetching info...\n(YouTube, Insta, X, etc)", 
                halign="center", 
                theme_text_color="Secondary"
            )
            loading_box.add_widget(spinner)
            loading_box.add_widget(lbl)
            self.ids.video_list.add_widget(loading_box)
            app = MDApp.get_running_app()
            app.fetch_videos(url)

class SettingsScreen(Screen):
    current_download_path = StringProperty(DOWNLOAD_DIR)
    cookies_status_text = StringProperty("No cookies loaded")
    
    def on_enter(self):
        self.current_download_path = short(MDApp.get_running_app().download_dir, 50)
        self.update_cookies_status()
        
    def update_cookies_status(self):
        app = MDApp.get_running_app()
        if app.cookies_path and os.path.exists(app.cookies_path):
            try:
                with open(app.cookies_path, 'r') as f:
                    if len(f.read().strip()) > 50: 
                         self.cookies_status_text = "Cookies Loaded"
                    else:
                         self.cookies_status_text = "No cookies loaded (Default)"
            except:
                 self.cookies_status_text = "Error reading cookies"
        else:
            self.cookies_status_text = "No cookies loaded"

    def change_download_path(self):
        try:
            filechooser.choose_dir(on_selection=self._handle_path_selection)
        except Exception as e:
            app = MDApp.get_running_app()
            app.show_dialog("Error", f"Cannot open folder chooser: {e}")
            
    def _handle_path_selection(self, selection):
        if selection:
            new_path = selection[0]
            app = MDApp.get_running_app()
            app.download_dir = new_path
            self.current_download_path = short(new_path, 50)

    def select_cookies_file(self):
        try:
            filechooser.open_file(on_selection=self._handle_cookies_selection, filters=[("Text Files", "*.txt")])
        except Exception as e:
            app = MDApp.get_running_app()
            app.show_dialog("Error", f"Cannot open file chooser: {e}")
            
    def _handle_cookies_selection(self, selection):
        if selection:
            src_file = selection[0]
            try:
                shutil.copy2(src_file, COOKIES_PATH)
                app = MDApp.get_running_app()
                app.cookies_path = str(COOKIES_PATH)
                self.update_cookies_status()
                app.show_dialog("Success", "Cookies loaded successfully!")
            except Exception as e:
                MDApp.get_running_app().show_dialog("Error", f"Failed to copy cookies: {e}")

class DownloadsScreen(Screen):
    download_in_progress = BooleanProperty(False)

class SearchResultsScreen(Screen):
    playlist_title = StringProperty("Playlist Name / Single Video")
    menu = None
    
    def open_menu(self):
        if not self.menu:
            menu_items = [
                {
                    "text": i,
                    "viewclass": "OneLineListItem",
                    "height": dp(54),
                    "on_release": lambda x=i: self.set_format(x),
                } for i in ["best", "1080p", "720p", "480p", "360p", "audio"]
            ]
            self.menu = MDDropdownMenu(
                caller=self.ids.format_btn,
                items=menu_items,
                width_mult=3,
                max_height=dp(240),
            )
        self.menu.open()
    
    def set_format(self, text_item):
        self.ids.format_btn.text = text_item
        self.menu.dismiss()

    def download_selected(self):
        app = MDApp.get_running_app()
        selected_videos = []
        for item in self.ids.video_list.children:
            if hasattr(item, 'checked') and item.checked and hasattr(item, 'video_data'):
                selected_videos.append(item.video_data)
        
        if selected_videos:
            format_choice = self.ids.format_btn.text
            app.download_videos(selected_videos, format_choice)
        else:
            app.show_dialog("Error", "Please select at least one video to download.")

# --------------------------------------------------------------
# MAIN APP
# --------------------------------------------------------------
class KiyyDownloaderApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_dir = DOWNLOAD_DIR
        self.video_items = []
        self.worker = None
        self.downloading = False
        self.history = []
        self.ffmpeg_available = check_ffmpeg()
        self.cookies_path = str(COOKIES_PATH)
        self.po_token = ""
        self.dialog = None
        self.active_downloads = []
        self.download_processes = {}
        self.current_format = None
    
    def build(self):
        self.title = APP_TITLE
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        Window.size = (900, 600)
        
        hindi_font = configure_hindi_font()
        if hindi_font:
            for style in self.theme_cls.font_styles:
                if style != 'Icon':
                    self.theme_cls.font_styles[style][0] = hindi_font
        
        self.load_history()
        return Builder.load_string(KV)
    
    def on_start(self):
        # === REQUEST ANDROID PERMISSIONS FOR STATUS SAVER ===
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            
        self.switch_screen("search")
    
    def switch_screen(self, screen_name):
        self.root.ids.screen_manager.current = screen_name
    
    # === HISTORY MANAGEMENT ===
    def load_history(self):
        p = USER_DATA_DIR / HISTORY_FILE
        if p.exists():
            try:
                self.history = json.loads(p.read_text(encoding="utf-8"))
            except:
                self.history = []
    
    def save_history(self):
        p = USER_DATA_DIR / HISTORY_FILE
        try:
            p.write_text(json.dumps(self.history[:200], ensure_ascii=False, indent=2), encoding="utf-8")
        except:
            pass
    
    def show_dialog(self, title, text):
        if self.dialog:
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()
    
    # === VIDEO FETCHING ===
    def fetch_videos(self, url):
        threading.Thread(target=self.fetch_worker, args=(url,), daemon=True).start()
    
    def fetch_worker(self, url):
        try:
            opts = {
                "quiet": True,
                "skip_download": True,
                "extract_flat": "in_playlist",
                "no_warnings": True,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            }
            
            if self.cookies_path and os.path.exists(self.cookies_path):
                opts["cookiefile"] = self.cookies_path
            
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            self.video_items = []
            playlist_title = ""
            
            if "entries" in info:
                entries = list(info["entries"])
                for i, e in enumerate(entries, 1):
                    title = e.get("title") or e.get("description") or e.get("id") or "Unknown Media"
                    weburl = e.get("webpage_url") or e.get("url") or url
                    self.video_items.append({"title": title, "url": weburl, "number": f"{i:02d}"})
                playlist_title = f"{info.get('title','Playlist')} — {len(self.video_items)} items"
            else:
                title = info.get("title") or info.get("description") or info.get("id") or "Unknown Media"
                self.video_items.append({"title": title, "url": info.get("webpage_url") or url, "number": "01"})
                playlist_title = f"Single: {short(title, 40)}"
            
            def on_success(dt):
                search_screen = self.root.ids.screen_manager.get_screen("search")
                search_screen.ids.video_list.clear_widgets()
                self.update_search_results(playlist_title, self.video_items)
            
            Clock.schedule_once(on_success)
            
        except Exception as e:
            err = traceback.format_exc()
            print("FETCH ERROR:", err)
            error_msg = str(e)
            
            def on_error(dt):
                search_screen = self.root.ids.screen_manager.get_screen("search")
                search_screen.ids.video_list.clear_widgets()
                self.show_dialog("Error", f"Failed to fetch info. Did you load cookies? Error: {short(error_msg, 100)}")
                
            Clock.schedule_once(on_error)
    
    def update_search_results(self, playlist_title, videos):
        results_screen = self.root.ids.screen_manager.get_screen("search_results")
        results_screen.playlist_title = playlist_title
        results_screen.ids.video_list.clear_widgets()
        
        for video in videos:
            item = VideoListItem(
                text=f"{video['number']}. {short(video['title'], 70)}",
                video_data=video
            )
            results_screen.ids.video_list.add_widget(item)
        
        self.switch_screen("search_results")
    
    # === DOWNLOAD MANAGEMENT (QUEUE) ===
    def download_videos(self, videos, format_choice):
        if not videos:
            self.show_dialog("Error", "No videos selected")
            return
        
        self.downloading = True
        self.current_format = format_choice
        
        downloads_screen = self.root.ids.screen_manager.get_screen("downloads")
        downloads_screen.download_in_progress = True
        downloads_screen.ids.download_list.clear_widgets()
        self.active_downloads = []
        self.download_processes = {}
        
        for idx, video in enumerate(videos):
            download_item = DownloadListItem(
                title_text=short(video['title'], 50),
                status_text="Pending...",
                download_index=idx,
                download_data=video
            )
            downloads_screen.ids.download_list.add_widget(download_item)
            self.active_downloads.append({
                'item': download_item,
                'video': video,
                'paused': False,
                'cancelled': False,
                'status': 'pending',
                'process': None
            })
        
        self.switch_screen("downloads")
        threading.Thread(target=self.download_manager, daemon=True).start()
    
    def pause_specific_download(self, index):
        if index < len(self.active_downloads):
            self.active_downloads[index]['paused'] = True
    
    def resume_specific_download(self, index):
        if index < len(self.active_downloads):
            self.active_downloads[index]['paused'] = False
    
    def cancel_specific_download(self, index):
        if index < len(self.active_downloads):
            self.active_downloads[index]['cancelled'] = True
            process = self.download_processes.get(index)
            if process and process.poll() is None:
                try:
                    process.kill()
                except:
                    pass
    
    def update_download_status(self, index, status):
        if index < len(self.active_downloads):
            download_info = self.active_downloads[index]
            download_info['item'].status_text = status
    
    def download_manager(self):
        while self.downloading:
            active_count = 0
            pending_index = -1
            all_done = True

            for i, d in enumerate(self.active_downloads):
                state = d['status']
                
                if state == 'downloading':
                    active_count += 1
                
                if state == 'pending' and pending_index == -1:
                    pending_index = i
                
                if state in ['pending', 'downloading', 'paused']:
                    all_done = False

            if active_count == 0 and pending_index != -1:
                self.active_downloads[pending_index]['status'] = 'downloading'
                threading.Thread(target=self.download_task, args=(pending_index,), daemon=True).start()

            if all_done:
                self.downloading = False
                Clock.schedule_once(lambda dt: self.show_dialog("Status", "All downloads processed."))
                break

            time.sleep(1)

    # === DOWNLOAD TASK (UNIVERSAL) ===
    def download_task(self, idx):
        download_info = self.active_downloads[idx]
        item_data = download_info['video']
        fmt = self.current_format
        
        # Clean title
        raw_title = item_data['title']
        safe_title = re.sub(r'[<>:"/\\|?*]', '', raw_title) 
        safe_title = safe_title[:50] 
        title = f"{item_data['number']}. {safe_title}"
        
        Clock.schedule_once(lambda dt: self.update_download_status(idx, "Downloading..."))
        
        proc = None
        try:
            cmd = [
                sys.executable, "-m", "yt_dlp",
                "--newline", "--no-warnings", "--ignore-config",
                "--socket-timeout", "10", "--retries", "3", "--http-chunk-size", "1M",
            ]
            
            if self.cookies_path and os.path.exists(self.cookies_path):
                cmd += ["--cookies", self.cookies_path]
            
            # FORMAT LOGIC
            if fmt == "audio":
                if self.ffmpeg_available:
                    cmd += ["-f", "bestaudio/best", "--extract-audio", "--audio-format", "mp3"]
                else:
                    cmd += ["-f", "bestaudio[ext=m4a]/bestaudio"]
            elif fmt in ["1080p", "720p", "480p", "360p"]:
                h = {"1080p": "1080", "720p": "720", "480p": "480", "360p": "360"}[fmt]
                if self.ffmpeg_available:
                    cmd += ["-f", f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best", "--merge-output-format", "mp4"]
                else:
                    cmd += ["-f", f"best[height<={h}][ext=mp4]/best[height<={h}]/best"]
            else:
                if self.ffmpeg_available:
                    cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]
                else:
                    cmd += ["-f", "best[ext=mp4]/best"]
            
            outtmpl = os.path.join(self.download_dir, f"{title} [%(id)s].%(ext)s")
            cmd += ["-o", outtmpl, item_data["url"]]
            
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True
            )
            self.download_processes[idx] = proc
            
            pattern = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%\s+of\s+~?([\d.]+)([KMGT]?)i?B\s+at\s+([\d.]+)([KMGT]?)i?B/s\s+ETA\s+(\d+:\d+|\d+s)")
            
            for line in iter(proc.stdout.readline, ''):
                if download_info['cancelled']: break
                
                while download_info['paused'] and not download_info['cancelled']:
                    download_info['status'] = 'paused'
                    Clock.schedule_once(lambda dt: self.update_download_status(idx, "Paused"))
                    time.sleep(0.5)
                    if not download_info['paused']:
                         download_info['status'] = 'downloading'
                
                if download_info['cancelled']: break
                
                m = pattern.search(line)
                if m:
                    status_text = f"Downloading... {m.group(1)}% - ETA: {m.group(6)}"
                    Clock.schedule_once(lambda dt: self.update_download_status(idx, status_text))

            if download_info['cancelled']:
                if proc.poll() is None: proc.kill()
                download_info['status'] = 'cancelled'
                Clock.schedule_once(lambda dt: self.update_download_status(idx, "Cancelled"))
                return

            proc.wait()
            
            if proc.returncode == 0:
                self.history.insert(0, {
                    "title": title, "url": item_data["url"], 
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "format": fmt
                })
                self.save_history()
                download_info['status'] = 'completed'
                Clock.schedule_once(lambda dt: self.update_download_status(idx, "Completed"))
            else:
                download_info['status'] = 'error'
                Clock.schedule_once(lambda dt: self.update_download_status(idx, "Failed (Check Cookies?)"))

        except Exception as e:
            if proc and proc.poll() is None:
                try: proc.kill()
                except: pass
            download_info['status'] = 'error'
            Clock.schedule_once(lambda dt: self.update_download_status(idx, f"Error: {str(e)}"))

if __name__ == '__main__':
    KiyyDownloaderApp().run()