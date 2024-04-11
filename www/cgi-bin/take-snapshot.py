#!/bin/python3
from picamera2 import Picamera2, Preview

OUTPUT_FOLDER = "/var/www/html/"

# Apache CGI header
print("Content-type: application/json")
print()

cam = Picamera2()
cam.start_preview(Preview.NULL)

cam.start_and_capture_file(OUTPUT_FOLDER + "snapshot.jpg")

print({"file": "snapshot.json"})
