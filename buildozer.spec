[app]
title = Kivy
package.name = kivy
package.domain = org.rameez
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,txt,ttf
version = 1.0
orientation = portrait
fullscreen = 0

main.py = main.py

requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,yt-dlp,python-dateutil,urllib3

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.enable_legacy_external_storage = True

android.api = 33
android.minapi = 21

# --- CRITICAL CHANGE HERE ---
# Use NDK r23b, which is often more compatible with libffi's autotools
# than r25b or newer.
android.ndk = 23b

android.sdk = 33 # Keep target SDK to 33
android.allow_backup = True

icon.filename = icon.png
presplash.filename = presplash.png

android.gradle_download = True
android.accept_sdk_license = True

p4a.local_recipes = 
p4a.branch = master

exclude_dirs = bin,tests,docs
exclude_patterns = *.md,*.rst

android.allow_rebuild = True

android.presplash_color = #FFFFFF