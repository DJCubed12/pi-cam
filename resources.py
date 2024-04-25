"""Global resources and configurations to be imported by other files."""

import os
import configparser
from pathlib import Path
from io import BufferedIOBase
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder

from logger import Logger

# Remove Picamera2 logging
Picamera2.set_logging(Picamera2.ERROR)
os.environ["LIBCAMERA_LOG_LEVELS"] = "4"


##############
# STRUCTURES #
##############


class StreamingOutput(BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


##################
# PROJECT CONFIG #
##################

_config = configparser.ConfigParser()
_config.read("pi-cam.ini")

PORT = int(_config.get("DEFAULT", "PORT"))
VIDEO_SIZE = (
    int(_config.get("DEFAULT", "VIDEO_WIDTH")),
    int(_config.get("DEFAULT", "VIDEO_HEIGHT")),
)
RECORDING_INTERVAL = int(_config.get("DEFAULT", "RECORDING_INTERVAL"))
RECORDING_FOLDER = Path(_config.get("DEFAULT", "RECORDING_FOLDER"))

_INFO_LOG = Path(_config.get("DEFAULT", "INFO_LOG"))
_ERROR_LOG = Path(_config.get("DEFAULT", "ERROR_LOG"))


####################
# GLOBAL VARIABLES #
####################

cam = Picamera2()
streamingOutput = StreamingOutput()
streamingEncoder = MJPEGEncoder()
logger = Logger(_INFO_LOG, _ERROR_LOG)


if __name__ == "__main__":
    # For debugging: making sure pi-cam.ini is being read properly
    print("Project Configuration is:")
    for secName, section in _config.items():
        print("SECTION:", secName)
        for item in section.items():
            print(item[0], "=", item[1])
        print()

    print("Interpreted constants are:")
    print("PORT =", PORT)
    print("VIDEO_SIZE =", VIDEO_SIZE)
    print("RECORDING_INTERVAL =", RECORDING_INTERVAL)
    print("RECORDING_FOLDER =", RECORDING_FOLDER)
