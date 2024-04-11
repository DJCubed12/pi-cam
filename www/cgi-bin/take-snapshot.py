#!/bin/python3
from picamera2 import Picamera2

OUTPUT_FOLDER = "/var/www/html/"

cam = Picamera2()

cam.start_and_capture_file(OUTPUT_FOLDER + "snapshot.jpg")

print("Content-type: application/json")
print({"file": "snapshot.json"})
