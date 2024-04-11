#!/bin/python3
import time
from picamera2 import Picamera2

OUTPUT_FOLDER = "/var/www/html/"

# Apache CGI header
print("Content-type: application/json")
print()

cam = Picamera2()
cam.start_preview(False) # Shorthand for using Preview.NULL

cam.start_and_record_video(OUTPUT_FOLDER + "video.mp4", duration=2)

print({"file": "video.mp4"})
