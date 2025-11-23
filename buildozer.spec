[app]
title = Kivy
package.name = kivy
package.domain = org.rameez
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,txt,ttf
version = 1.0
orientation = portrait
fullscreen = 0

# Main entry point
main.py = main.py

# Python & libraries - FIXED VERSIONS FOR STABILITY
requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,yt-dlp,python-dateutil,urllib3

# Permissions your app needs
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.enable_legacy_external_storage = True

# API levels - OPTIMIZED
android.api = 33
android.minapi = 21

# Supported CPU architectures - SIMPLIFY FOR FASTER BUILD
android.archs = arm64-v8a

# Java version - UPDATED
android.sdk = 33
android.ndk = 25b

# Allow backup
android.allow_backup = True

# Icon and splash (optional – remove if not available)
icon.filename = icon.png
presplash.filename = presplash.png

# Build optimizations
android.gradle_download = True
android.accept_sdk_license = True

# Fix for long paths on Windows (safe to keep)
p4a.local_recipes = 
p4a.branch = master

# Avoid including large unnecessary modules
exclude_dirs = bin,tests,docs
exclude_patterns = *.md,*.rst

# Keep Python multiprocessing functional
android.allow_rebuild = True

# (Optional) If your font is named font.ttf
android.presplash_color = #FFFFFF