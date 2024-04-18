import re
import logging
from pathlib import Path
from http import server

from resources import streamingOutput, VIDEO_SIZE, RECORDING_FOLDER


##################
# HTML TEMPLATES #
##################

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


###################
# REQUEST HANDLER #
###################


class StreamingHandler(server.BaseHTTPRequestHandler):
    # SECURITY: It is important that '..' is not allowed in this match!
    _VIDEO_FILE_PATTERN_STR = r"([-_a-zA-Z0-9]+\.(mp4|h264))$"
    VIDEO_FILE_PATTERN = re.compile(_VIDEO_FILE_PATTERN_STR)
    VIDEO_FILE_ARG_PATTERN = re.compile(r"\?file=" + _VIDEO_FILE_PATTERN_STR)

    # Override log_request, log_error, log_message for custom error messages.

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
        recordings = [r for r in RECORDING_FOLDER.iterdir()]
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

    def _playback(self):
        arg = self.VIDEO_FILE_ARG_PATTERN.match(self.path.replace("/playback.html", ""))
        if arg:
            file = RECORDING_FOLDER / Path(arg.group(1))
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
        subpath = self.path.removeprefix("/" + str(RECORDING_FOLDER) + "/", "")
        fileMatch = self.VIDEO_FILE_PATTERN.match(subpath)
        try:
            file = RECORDING_FOLDER / Path(fileMatch.group(1))
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
