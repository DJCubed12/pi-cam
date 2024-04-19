#!/usr/bin/python3

# Based off the code at https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py

import os
from http import server

from picamera2 import Picamera2
from picamera2.outputs import FileOutput

from resources import (
    cam,
    streamingOutput,
    streamingEncoder,
    recordingEncoder,
    recorder,
    logger,
    PORT,
    VIDEO_SIZE,
    RECORDING_FOLDER,
)
from request_handler import StreamingHandler


class StreamingServer(server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def configureLogging():
    Picamera2.set_logging(Picamera2.ERROR)
    os.environ["LIBCAMERA_LOG_LEVELS"] = "4"


def serverSetup():
    """Configure global variables, start camera and recorder, and serve HTTPServer."""
    logger.info("Server starting up...")

    cam.configure(
        cam.create_video_configuration(
            main={"size": VIDEO_SIZE}, lores={"size": VIDEO_SIZE}
        )
    )

    recordingEncoder.output = FileOutput("/dev/null")  # Can't start without a file
    # Set stream to main, but don't actually start recording yet
    cam.start_encoder(recordingEncoder, name="main")
    recordingEncoder.stop()
    RECORDING_FOLDER.mkdir(exist_ok=True)  # Make recordings dir if it doesn't exist

    streamingEncoder.output = FileOutput(streamingOutput)
    cam.start_encoder(streamingEncoder, name="lores")

    recorder.start()  # Starts recordingEncoder internally
    cam.start()


def main():
    try:
        address = ("", PORT)
        server = StreamingServer(address, StreamingHandler)
        logger.info("Server started")
        server.serve_forever()
    finally:
        # Is waiting to join the thread really necessary if it is daemon?
        # Would there be problems with ffmpeg if stopped in the middle of transcoding?
        recorder.signalStopRecording()
        recorder.join(recorder.SLEEP_INTERVAL * 2)
        cam.stop()


if __name__ == "__main__":
    configureLogging()
    serverSetup()
    main()
