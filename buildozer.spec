[app]
title = Kivy App
package.name = kivyapp
package.domain = org.rameez

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,txt

version = 1.0
orientation = portrait
fullscreen = 0

main.py = main.py

requirements = python3,kivy==2.3.0,kivymd==1.2.0,plyer,yt-dlp,python-dateutil,urllib3

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.ndk = 25b

android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2