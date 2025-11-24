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

# Python & libraries
requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,yt-dlp,python-dateutil,urllib3

# Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# API levels
android.api = 33
android.minapi = 21

# Supported architectures
android.arch = arm64-v8a

# Build tools
android.ndk = 25b
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk
android.ndk_path = /home/runner/.buildozer/android/platform/android-ndk-r25b

# Build settings
android.allow_backup = True
android.accept_sdk_license = True

# Icons (if available)
# icon.filename = icon.png
# presplash.filename = presplash.png

[buildozer]
log_level = 2