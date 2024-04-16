"""Functions for recording Pi-Cam's output to the files in the background."""

import time
import subprocess
from pathlib import Path
from types import FunctionType

from picamera2.outputs import FileOutput
from picamera2.encoders import H264Encoder


RECORDING_INTERVAL = 60  # In seconds
# This should be somewhat small to minimize shutdown time from thread.join()
SLEEP_INTERVAL = 5  # In seconds


def recordInBackground(
    encoder: H264Encoder,
    stopRecording: FunctionType,
    outputFolder: Path = Path("recordings"),
):
    """Records Pi-Cam's feed and saves to file at regular intervals."""
    # TODO: Current this does NOT allow simultaneous recording on encoder. Fix this by being more careful with encoder.output.

    startTime = time.time()
    # TODO: Use CircularOutput to try to add some cushion and record as much as possible?
    currentFile = outputFolder / _createRecordingFilename(startTime)
    encoder.output = FileOutput(currentFile)
    encoder.start()
    while True:
        if stopRecording():
            # Program has stopped or attempt has been made to stop recording
            break
        elif time.time() - startTime < RECORDING_INTERVAL:
            time.sleep(SLEEP_INTERVAL)
        else:
            # Stop, save, restart
            encoder.stop()

            startTime = time.time()
            # Keep currentFile until we convert and delete last h264 recording
            _nextFile = outputFolder / _createRecordingFilename(startTime)
            encoder.output = FileOutput(_nextFile)
            encoder.start()

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
    encoder.stop()


def _createRecordingFilename(timestamp: float) -> Path:
    """Filename in 'd-m-yyyy_h-m' format. Timestamp is epoch time in seconds as returned by time.time()."""
    t = time.localtime(timestamp)
    filename = Path(
        f"{t.tm_mday}-{t.tm_mon}-{t.tm_year}_{t.tm_hour}h{t.tm_min}m{t.tm_sec}s"
    )
    return filename.with_suffix(".h264")
