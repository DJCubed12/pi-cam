#!/usr/bin/python3

# Based off the code at https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py

import io
import logging
import subprocess
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, H264Encoder
from picamera2.outputs import FileOutput

PORT = 8000
VIDEO_SIZE = (720, 480)

with open("html/index.html", "r") as file:
    LIVESTREAM_TEMPLATE = (
        file.read().replace("#WIDTH", VIDEO_SIZE[0]).replace("#HEIGHT", VIDEO_SIZE[1])
    )

with open("html/playback.html", "r") as file:
    PLAYBACK_TEMPLATE = (
        file.read().replace("#WIDTH", VIDEO_SIZE[0]).replace("#HEIGHT", VIDEO_SIZE[1])
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
        elif self.path == "/start-rec":
            if recordingEncoder.running:
                # Recording already started
                self.send_response(409)
                self.end_headers()
                return

            # TODO: Provide second file to output timestamps to (part of FileOutput's ctor)
            recordingEncoder.output = FileOutput("playback.h264")
            recordingEncoder.start()

            self.send_response(200)
            self.end_headers()
        elif self.path == "/stop-rec":
            if not recordingEncoder.running:
                # Must start with /start-rec first
                self.send_response(409)
                self.end_headers()
                return

            recordingEncoder.stop()

            # TODO: Send back json with the saved file's name
            self.send_response(200)
            self.end_headers()

            # Convert recorded h264 to mp4
            subprocess.run(
                "ffmpeg -i playback.h264 -y -c:v copy -an playback.mp4",
                shell=True,
                check=True,
            )
            # Note: Output says the h264 file has no timestamps set, which is apparently deprecated
        elif self.path == "/playback.html":
            self._playback()
        elif self.path == "/playback.mp4":
            self._playback_video()
        elif self.path == "/stream.mjpg":
            self._livestream()
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
        with open("playback.mp4", "rb") as file:
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

streamingOutput = StreamingOutput()
streamingEncoder = MJPEGEncoder()
streamingEncoder.output = FileOutput(streamingOutput)
cam.start_encoder(streamingEncoder, name="lores")

cam.start()

try:
    address = ("", PORT)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    # TODO: Stop all current recordings first
    cam.stop()
