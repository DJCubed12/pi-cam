"""Record Pi-Cam's feed in the background with BackgroundRecorder (a Thread subclass)."""

import time
import subprocess
from pathlib import Path
from threading import Thread

from picamera2.outputs import FileOutput
from picamera2.encoders import H264Encoder


class BackgroundRecorder(Thread):
    """Records Pi-Cam's feed and saves to file at regular intervals. Call start() to start background recording and signalStopRecording to gracefully stop."""

    # This should be somewhat small to minimize shutdown time from thread.join()
    SLEEP_INTERVAL: int = 5  # In seconds

    # Use % to replace input filename and output filename (in that order)
    # -loglevel can be info, warning, or error
    FFMPEG_COMMAND = "ffmpeg -hide_banner -loglevel info -y -i %s  -c:v copy -an %s"

    def __init__(
        self, encoder: H264Encoder, outputFolder: Path, recordingInterval: int = 60
    ):
        """Ensure that the encoder is NOT running when BackgroundRecorder.start() is called. recordingInterval should be in seconds."""
        self.encoder = encoder
        self.outputFolder = outputFolder
        self._stopRecording = False
        self.recordingInterval = recordingInterval
        Thread.__init__(self, daemon=True)

    def signalStopRecording(self):
        """Signal the recorder thread to stop the recording."""
        self._stopRecording = True

    def run(self):
        """recordingLength is in seconds."""
        startTime = time.time()
        # TODO: Use CircularOutput to try to add some cushion and record as much as possible?
        currentFile = self._createRecordingFilename(startTime)
        self.encoder.output = FileOutput(currentFile)
        self.encoder.start()
        while True:
            if self._stopRecording:
                # Program has stopped or attempt has been made to stop recording
                break
            elif time.time() - startTime < self.recordingInterval:
                time.sleep(self.SLEEP_INTERVAL)
            else:
                # Stop, save, restart
                self.encoder.stop()

                startTime = time.time()
                # Keep currentFile until we convert and delete last h264 recording
                _nextFile = self._createRecordingFilename(startTime)
                self.encoder.output = FileOutput(_nextFile)
                self.encoder.start()

                # TODO: Properly log file saves and errors (and handle errors)
                mp4File = currentFile.with_suffix(".mp4")
                subprocess.run(
                    self.FFMPEG_COMMAND % (currentFile, mp4File),
                    shell=True,
                    check=True,
                )  # Raises error if issue occurred
                if mp4File.exists():
                    currentFile.unlink()

                currentFile = _nextFile

    def _createRecordingFilename(self, timestamp: float) -> Path:
        """Filename in 'dd-mm-yyyy_hhmmss' format. Timestamp is epoch time in seconds as returned by time.time()."""
        filename = time.strftime("%d-%m-%Y_%Hh%Mm%Ss", time.localtime(timestamp))
        return (self.outputFolder / Path(filename)).with_suffix(".h264")
