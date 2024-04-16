#!/usr/bin/python3

# Based off the code at https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py

import io
import re
import logging
import subprocess
import socketserver
from pathlib import Path
from http import server
from threading import Condition

from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, H264Encoder
from picamera2.outputs import FileOutput

from recorder import BackgroundRecorder

PORT = 8000
VIDEO_SIZE = (720, 480)
RECORDING_INTERVAL = 60  # In seconds
RECORDINGS_FOLDER = Path("recordings")

with open("src/index.template.html", "r") as file:
    file.readline()  # Ignore top comment
    LIVESTREAM_TEMPLATE = (
        file.read()
        .replace("#WIDTH", str(VIDEO_SIZE[0]))
        .replace("#HEIGHT", str(VIDEO_SIZE[1]))
    )

with open("src/playback.template.html", "r") as file:
    file.readline()  # Ignore top comment
    PLAYBACK_TEMPLATE = (
        file.read()
        .replace("#WIDTH", str(VIDEO_SIZE[0]))
        .replace("#HEIGHT", str(VIDEO_SIZE[1]))
    )

with open("src/recordings.template.html", "r") as file:
    file.readline()
    RECORDINGS_TEMPLATE = file.read()


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    # SECURITY: It is important that '..' is not allowed in this match!
    _VIDEO_FILE_PATTERN_STR = r"([-_a-zA-Z0-9]+\.(mp4|h264))$"
    VIDEO_FILE_PATTERN = re.compile(_VIDEO_FILE_PATTERN_STR)
    VIDEO_FILE_ARG_PATTERN = re.compile(r"\?file=" + _VIDEO_FILE_PATTERN_STR)

    def do_GET(self):
        if self.path == "/":
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()
        elif self.path == "/index.html":
            self._index()
        elif self.path == "/stream.mjpg":
            self._livestream()
        elif self.path.startswith("/playback.html"):
            self._playback()
        elif self.path == "/recordings":
            self.send_response(301)
            self.send_header("Location", "/recordings/index.html")
            self.end_headers()
        elif self.path == "/recordings/index.html":
            self._recordings_list()
        elif self.path.startswith("/recordings/"):
            self._playback_video()
        # elif self.path == "/start-rec":
        #     self._start_rec()
        # elif self.path == "/stop-rec":
        #     self._stop_rec()
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

    def _recordings_list(self):
        # Sort recordings by most recent
        recordings = [r for r in RECORDINGS_FOLDER.iterdir()]
        recordings.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        html = ""
        for r in recordings:
            if r.suffix == ".mp4":
                html += f'<p><a href="/playback.html?file={r.name}">{r.name}</a></p>\n'
            elif r.suffix == ".h264":
                html += f"<p>{r.name}</p>\n"
            # Ignore non-video files
        content = RECORDINGS_TEMPLATE.replace("#FILE_LIST", html).encode("utf-8")

        self.send_response(200)
        self.send_header("Age", 0)
        self.send_header("Cache-Control", "no-cache, private")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def _start_rec(self):
        """WARNING: Does NOT work safely with BackgroundRecorder. (Non-thread-safe)"""
        if recordingEncoder.running:
            # Recording already started
            self.send_error(409, "Recording already running")
            self.end_headers()
            return

        # TODO: Provide second file to output timestamps to (part of FileOutput's ctor)
        recordingEncoder.output = FileOutput("recordings/playback.h264")
        recordingEncoder.start()

        self.send_response(200)
        self.end_headers()

    def _stop_rec(self):
        """WARNING: Does NOT work safely with BackgroundRecorder. (Non-thread-safe)"""
        if not recordingEncoder.running:
            # Must start with /start-rec first
            self.send_error(409, "Recording not running")
            self.end_headers()
            return

        recordingEncoder.stop()

        # TODO: Send back json with the saved file's name
        self.send_response(200)
        self.end_headers()

        # Convert recorded h264 to mp4
        subprocess.run(
            "ffmpeg -i recordings/playback.h264 -y -c:v copy -an recordings/playback.mp4",
            shell=True,
            check=True,
        )  # Raises error if issue occurred
        # Note: Output says the h264 file has no timestamps set, which is apparently deprecated
        if RECORDINGS_FOLDER / Path("playback.mp4").exists():
            (RECORDINGS_FOLDER / Path("playback.h264")).unlink()  # Delete H264 version

    def _playback(self):
        arg = self.VIDEO_FILE_ARG_PATTERN.match(self.path.replace("/playback.html", ""))
        if arg:
            file = "recordings" / Path(arg.group(1))
        else:
            # TODO: Use some kind of default video instead
            self.send_error(404)
            self.end_headers()
            return

        html = PLAYBACK_TEMPLATE.replace("#VIDEO_SRC", str(file)).replace(
            "#FILENAME", file.name
        )
        content = html.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(content))
        self.end_headers()
        self.wfile.write(content)

    def _playback_video(self):
        # Ensure entire path is matched
        fileMatch = self.VIDEO_FILE_PATTERN.match(self.path.replace("/recordings/", ""))
        try:
            file = RECORDINGS_FOLDER / Path(fileMatch.group(1))
        except (AttributeError, IndexError):
            # Kind of redundant
            self.send_error(404)
            self.end_headers()
            return

        # Only playback mp4 videos
        if file.suffix != ".mp4":
            self.send_error(403)
            self.end_headers()
            return
        elif not file.exists():
            self.send_error(404)
            self.end_headers()
            return

        with file.open("rb") as f:
            data = f.read()

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
RECORDINGS_FOLDER.mkdir(exist_ok=True)  # Make recordings dir if it doesn't exist
recorder = BackgroundRecorder(recordingEncoder, RECORDINGS_FOLDER)

streamingOutput = StreamingOutput()
streamingEncoder = MJPEGEncoder()
streamingEncoder.output = FileOutput(streamingOutput)
cam.start_encoder(streamingEncoder, name="lores")

recorder.start()  # Starts recordingEncoder internally
cam.start()

try:
    address = ("", PORT)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    # Is waiting to join the thread really necessary if it is daemon?
    # Would there be problems with ffmpeg if stopped in the middle of transcoding?
    recorder.signalStopRecording()
    recorder.join(recorder.SLEEP_INTERVAL * 2)
    cam.stop()
