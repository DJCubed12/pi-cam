#!/usr/bin/python3

# Based off the code at https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py
# Run this script, then point a web browser at http:<this-ip-address>:8000
# Note: needs simplejpeg to be installed (pip3 install simplejpeg).

import io
import logging
import socketserver
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput

PORT = 8000
SIZE = (720, 480)

PAGE = f"""\
<html>
<head>
<title>Pi-Cam</title>
</head>
<body>
<h1>Raspberry Pi Security Camera!</h1>
<img src="stream.mjpg" width="{SIZE[0]}" height="{SIZE[1]}" />
</body>
</html>
"""


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
            recordingOutput.fileoutput = "playback.mjpg"
            recordingOutput.start()

            self.send_response(200)
            self.end_headers()
        elif self.path == "/playback.html":
            playbackHTML = PAGE.replace("stream.mjpg", "playback.mjpg").encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(playbackHTML))
            self.end_headers()
            self.wfile.write(playbackHTML)
        elif self.path == "/playback.mjpg":
            self._playback()
        elif self.path == "/stream.mjpg":
            self._livestream()
        else:
            self.send_error(404)
            self.end_headers()

    def _index(self):
        content = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def _playback(self):
        recordingOutput.stop()  # Check if it actually is recording first

        with open("playback.mjpg", "rb") as file:
            data = file.read()

        self.send_response(200)
        self.send_header("Age", 0)
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "video/x-motion-jpeg")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def _livestream(self):
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
cam.configure(cam.create_video_configuration(main={"size": SIZE}, lores={"size": SIZE}))

streamingOutput = StreamingOutput()
livestream = FileOutput(streamingOutput)
recordingOutput = FileOutput()
encoder = MJPEGEncoder()
encoder.output = [livestream, recordingOutput]

cam.start_encoder(encoder)
cam.start()

try:
    address = ("", PORT)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    # TODO: stop any ongoing recordings first
    cam.stop()
