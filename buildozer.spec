[app]
# Application title and package
title = Kivy App
package.name = kivyapp
package.domain = org.rameez

# Source code
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,txt

# Application version
version = 1.0

# Application orientation
orientation = portrait

# Whether the app is fullscreen or not
fullscreen = 0

# Main entry point
main.py = main.py

# Requirements
requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,yt-dlp,python-dateutil,urllib3

# Android permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Android API configuration
android.api = 33
android.minapi = 21

# Android architecture
android.arch = arm64-v8a

# Android NDK version
android.ndk = 25b

# Android build tools
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk
android.ndk_path = /home/runner/.buildozer/android/platform/android-ndk-r25b

# Android build settings
android.allow_backup = True
android.accept_sdk_license = True

# Icon and presplash (uncomment if you have these files)
# icon.filename = icon.png
# presplash.filename = presplash.png
# android.presplash_color = #FFFFFF

[buildozer]
# Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2