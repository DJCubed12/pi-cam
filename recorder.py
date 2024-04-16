"""Functions for recording Pi-Cam's output to the files in the background."""

import time
import subprocess
from pathlib import Path
from threading import Thread
from types import FunctionType

from picamera2.outputs import FileOutput
from picamera2.encoders import H264Encoder


# _stopRecordingFlag = False


class BackgroundRecorder(Thread):
    """Records Pi-Cam's feed and saves to file at regular intervals."""

    RECORDING_INTERVAL = 60  # In seconds
    # This should be somewhat small to minimize shutdown time from thread.join()
    SLEEP_INTERVAL: int = 5  # In seconds

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
                    f"ffmpeg -i {currentFile} -y -c:v copy -an {mp4File}",
                    shell=True,
                    check=True,
                )  # Raises error if issue occurred
                if mp4File.exists():
                    currentFile.unlink()

                currentFile = _nextFile

    def _createRecordingFilename(self, timestamp: float) -> Path:
        """Filename in 'd-m-yyyy_h-m' format. Timestamp is epoch time in seconds as returned by time.time()."""
        t = time.localtime(timestamp)
        filename = Path(
            f"{t.tm_mday}-{t.tm_mon}-{t.tm_year}_{t.tm_hour}h{t.tm_min}m{t.tm_sec}s"
        )
        return (self.outputFolder / filename).with_suffix(".h264")
