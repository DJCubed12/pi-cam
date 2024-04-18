"""Record Pi-Cam's feed in the background with BackgroundRecorder (a Thread subclass)."""

import time
import subprocess
from pathlib import Path
from threading import Thread

from picamera2.outputs import FileOutput
from picamera2.encoders import H264Encoder


class BackgroundRecorder(Thread):
    """Records Pi-Cam's feed and saves to file at regular intervals. Call start() to start background recording and signalStopRecording to gracefully stop."""

    RECORDING_INTERVAL = 60  # In seconds
    # This should be somewhat small to minimize shutdown time from thread.join()
    SLEEP_INTERVAL: int = 5  # In seconds

    # Use % to replace input filename and output filename (in that order)
    # -loglevel can be info, warning, or error
    FFMPEG_COMMAND = "ffmpeg -hide_banner -loglevel info -y -i %s  -c:v copy -an %s"

    def __init__(self, encoder: H264Encoder, outputFolder: Path = Path("recordings")):
        self.encoder = encoder
        self.outputFolder = outputFolder
        self._stopRecording = False
        Thread.__init__(self, daemon=True)

    def signalStopRecording(self):
        """Signal the recorder thread to stop the recording."""
        self._stopRecording = True

    def run(self):
        # TODO: Current this does NOT allow simultaneous recording on encoder. Fix this by being more careful with encoder.output.

        startTime = time.time()
        # TODO: Use CircularOutput to try to add some cushion and record as much as possible?
        currentFile = self._createRecordingFilename(startTime)
        self.encoder.output = FileOutput(currentFile)
        self.encoder.start()
        while True:
            if self._stopRecording:
                # Program has stopped or attempt has been made to stop recording
                break
            elif time.time() - startTime < self.RECORDING_INTERVAL:
                time.sleep(self.SLEEP_INTERVAL)
            else:
                # Stop, save, restart
                self.encoder.stop()

                startTime = time.time()
                # Keep currentFile until we convert and delete last h264 recording
                _nextFile = self._createRecordingFilename(startTime)
                self.encoder.output = FileOutput(_nextFile)
                self.encoder.start()

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
        """Filename in 'd-m-yyyy_h-m' format. Timestamp is epoch time in seconds as returned by time.time()."""
        filename = time.strftime("%d-%m-%Y_%Ih%Mm%Ss", time.localtime(timestamp))
        return (self.outputFolder / Path(filename)).with_suffix(".h264")
