#!/bin/python3
import cgi
from picamera2 import Picamera2

OUTPUT_FOLDER = "/var/www/html/"
VIDEO_LENGTH_RANGE = (2, 30)

# Apache CGI header
print("Content-type: application/json")
print()

videoLen = 2

# Parse HTML Arguments
args = cgi.FieldStorage()
if "length" in args:
    try:
        lengthArg = int(args["length"])
    except ValueError:
        pass

    if (lengthArg >= VIDEO_LENGTH_RANGE[0]) and (lengthArg <= VIDEO_LENGTH_RANGE[1]):
        videoLen = lengthArg

# Take and save video
cam = Picamera2()
cam.start_preview(False)  # Shorthand for using Preview.NULL

cam.start_and_record_video(OUTPUT_FOLDER + "video.mp4", duration=videoLen)

# Return data
print({"file": "video.mp4", "length": videoLen})
