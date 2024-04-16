#!/bin/python3

# This is temporarily being kept for reference

import time
import os
from picamera2 import Picamera2

OUTPUT_FOLDER = "/var/www/html/"

# Quiet libcamera's logging, dear lord
Picamera2.set_logging(Picamera2.ERROR)
os.environ["LIBCAMERA_LOG_LEVELS"] = "4"

# Apache CGI header
print("Content-type: application/json")
print()

cam = Picamera2()
config = cam.create_still_configuration()
cam.configure(config)

cam.start_preview(False)  # Shorthand for using Preview.NULL

cam.start()
time.sleep(2)  # Gives system time to auto change focus, brightness, etc.
cam.capture_file(OUTPUT_FOLDER + "snapshot.jpg")

print({"file": "snapshot.json"})
