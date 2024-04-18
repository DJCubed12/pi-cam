"""Global Picamera2 related resource to be imported by other files."""

import configparser
from pathlib import Path
from io import BufferedIOBase
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, H264Encoder

from recorder import BackgroundRecorder


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


####################
# GLOBAL VARIABLES #
####################

cam = Picamera2()
streamingOutput = StreamingOutput()
streamingEncoder = MJPEGEncoder()
recordingEncoder = H264Encoder()
recorder = BackgroundRecorder(recordingEncoder, RECORDING_FOLDER, RECORDING_INTERVAL)


if __name__ == "__main__":
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
