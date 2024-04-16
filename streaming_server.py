#!/usr/bin/python3

# Based off the code at https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py

import io
import time
import logging
import subprocess
import socketserver
from pathlib import Path
from http import server
from threading import Condition, Thread

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, H264Encoder
from picamera2.outputs import FileOutput

PORT = 8000
VIDEO_SIZE = (720, 480)
RECORDING_INTERVAL = 60  # In seconds
RECORDINGS_FOLDER = Path("recordings")

with open("src/index.template.html", "r") as file:
    LIVESTREAM_TEMPLATE = (
        file.read()
        .replace("#WIDTH", str(VIDEO_SIZE[0]))
        .replace("#HEIGHT", str(VIDEO_SIZE[1]))
    )

with open("src/playback.template.html", "r") as file:
    PLAYBACK_TEMPLATE = (
        file.read()
        .replace("#WIDTH", str(VIDEO_SIZE[0]))
        .replace("#HEIGHT", str(VIDEO_SIZE[1]))
    )


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()
        elif self.path == "/index.html":
            self._index()
        # elif self.path == "/start-rec":
        #     if recordingEncoder.running:
        #         # Recording already started
        #         self.send_error(409, "Recording already running")
        #         self.end_headers()
        #         return

        #     # TODO: Provide second file to output timestamps to (part of FileOutput's ctor)
        #     recordingEncoder.output = FileOutput("recordings/playback.h264")
        #     recordingEncoder.start()

        #     self.send_response(200)
        #     self.end_headers()
        # elif self.path == "/stop-rec":
        #     if not recordingEncoder.running:
        #         # Must start with /start-rec first
        #         self.send_error(409, "Recording not running")
        #         self.end_headers()
        #         return

        #     recordingEncoder.stop()

        #     # TODO: Send back json with the saved file's name
        #     self.send_response(200)
        #     self.end_headers()

        #     # Convert recorded h264 to mp4
        #     subprocess.run(
        #         "ffmpeg -i recordings/playback.h264 -y -c:v copy -an recordings/playback.mp4",
        #         shell=True,
        #         check=True,
        #     )  # Raises error if issue occurred
        #     # Note: Output says the h264 file has no timestamps set, which is apparently deprecated
        #     if RECORDINGS_FOLDER / Path("playback.mp4").exists():
        #         (RECORDINGS_FOLDER / Path("playback.h264")).unlink()  # Delete H264 version
        elif self.path == "/playback.html":
            self._playback()
        elif self.path == "/stream.mjpg":
            self._livestream()
        elif self.path == "/playback.mp4":
            self._playback_video()
        else:
            self.send_error(404)
            self.end_headers()

    def _index(self):
        html = LIVESTREAM_TEMPLATE  # Replace any template variables here
        content = html.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def _playback(self):
        html = PLAYBACK_TEMPLATE.replace("#VIDEO_SRC", "playback.mp4")
        content = html.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def _playback_video(self):
        with open("recordings/latest.mp4", "rb") as file:
            data = file.read()

        self.send_response(200)
        self.send_header("Age", 0)
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def _livestream(self):
        """This is code from: https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py. It's best to leave it alone."""
        self.send_response(200)
        self.send_header("Age", 0)
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
        self.end_headers()
        try:
            while True:
                with streamingOutput.condition:
                    streamingOutput.condition.wait()
                    frame = streamingOutput.frame
                self.wfile.write(b"--FRAME\r\n")
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", len(frame))
                self.end_headers()
                self.wfile.write(frame)
                self.wfile.write(b"\r\n")
        except Exception as e:
            logging.warning(
                "Removed streaming client %s: %s", self.client_address, str(e)
            )


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def recordInBackground():
    """Records Pi-Cam's feed and saves to file at regular intervals."""
    # TODO: Current this does NOT allow simultaneous recording on recordingEncoder. Fix this by being more careful with recordingEncoder.output

    # This should be somewhat small to minimize shutdown time from thead.join()
    WAIT_INTERVAL = 5  # In seconds

    startTime = time.time()
    # TODO: Use CircularOutput to try to add some cushion and record as much as possible?

    currentFile = _createRecordingFilename(startTime)
    recordingEncoder.output = FileOutput(currentFile)
    recordingEncoder.start()
    while True:
        if not isRecordingInBackground:
            # Program has stopped or attempt has been made to stop recording
            break
        elif time.time() - startTime < RECORDING_INTERVAL:
            time.sleep(WAIT_INTERVAL)
        else:
            # Stop, save, restart
            recordingEncoder.stop()

            startTime = time.time()
            # Keep currentFile until we convert and delete last h264 recording
            _nextFile = _createRecordingFilename(startTime)
            recordingEncoder.output = FileOutput(_nextFile)
            recordingEncoder.start()

            mp4File = currentFile.with_suffix(".mp4")
            subprocess.run(
                f"ffmpeg -i {currentFile} -y -c:v copy -an {mp4File}",
                shell=True,
                check=True,
            )  # Raises error if issue occurred
            if mp4File.exists():
                currentFile.unlink()

            currentFile = _nextFile

    # Cleanup
    recordingEncoder.stop()


def _createRecordingFilename(timestamp: float) -> Path:
    """Filename in 'dd-mm-yyyy_h-m' format. Timestamp is epoch time in seconds as returned by time.time()."""
    t = time.localtime(timestamp)
    filename = Path(f"{t.tm_mday}-{t.tm_mon}-{t.tm_year}_{t.tm_hour}-{t.tm_min}")
    return (RECORDINGS_FOLDER / filename).with_suffix(".h264")


cam = Picamera2()
cam.configure(
    cam.create_video_configuration(
        main={"size": VIDEO_SIZE}, lores={"size": VIDEO_SIZE}
    )
)

recordingEncoder = H264Encoder()
recordingEncoder.output = FileOutput("/dev/null")  # Can't start without a file
# Set recording to main, but don't actually start recording yet
cam.start_encoder(recordingEncoder, name="main")
recordingEncoder.stop()
RECORDINGS_FOLDER.mkdir(exist_ok=True)  # Make recordings dir if it doesn't exist
isRecordingInBackground = True
backgroundRecorderThread = Thread(target=recordInBackground)

streamingOutput = StreamingOutput()
streamingEncoder = MJPEGEncoder()
streamingEncoder.output = FileOutput(streamingOutput)
cam.start_encoder(streamingEncoder, name="lores")

backgroundRecorderThread.start()
cam.start()

try:
    address = ("", PORT)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    # TODO: Stop all current recordings first
    isRecordingInBackground = False
    backgroundRecorderThread.join(10.0)
    cam.stop()
