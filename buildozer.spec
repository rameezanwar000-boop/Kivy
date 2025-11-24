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

# Python & libraries - ADD LIBFFI EXPLICITLY
requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,yt-dlp,python-dateutil,urllib3,libffi

# Permissions your app needs
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.enable_legacy_external_storage = True

# API levels
android.api = 33
android.minapi = 21

# Supported CPU architectures
android.archs = arm64-v8a

# Java version
android.sdk = 33
android.ndk = 25b

# Allow backup
android.allow_backup = True

# Icon and splash (optional)
icon.filename = icon.png
presplash.filename = presplash.png

# Build optimizations
android.gradle_download = True
android.accept_sdk_license = True

# Fix for long paths on Windows
p4a.local_recipes = 
p4a.branch = master

# Avoid including large unnecessary modules
exclude_dirs = bin,tests,docs
exclude_patterns = *.md,*.rst

# Keep Python multiprocessing functional
android.allow_rebuild = True

# Presplash color
android.presplash_color = #FFFFFF

# ADD THESE NEW LINES FOR BETTER COMPATIBILITY
android.skip_update = False
android.gradle_plugin = 7.0.0