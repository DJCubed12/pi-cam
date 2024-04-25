#!/usr/bin/python3
"""Entry point file for the Pi-Cam Streaming Server. Please kill using a Keyboard Interrupt for graceful shutdowns."""

from http import server

from libcamera import Transform
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

from recorder import BackgroundRecorder
from resources import (
    cam,
    streamingOutput,
    streamingEncoder,
    logger,
    PORT,
    VIDEO_SIZE,
    VERTICAL_FLIP,
    RECORDING_FOLDER,
    RECORDING_INTERVAL,
)
from request_handler import StreamingHandler


class StreamingServer(server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def setup() -> BackgroundRecorder:
    """Configure global variables and start the camera and recorder."""
    logger.info("Server starting up...")

    cam.configure(
        cam.create_video_configuration(
            main={"size": VIDEO_SIZE},
            lores={"size": VIDEO_SIZE},
            transform=Transform(vflip=VERTICAL_FLIP),
        )
    )

    recordingEncoder = H264Encoder()
    recorder = BackgroundRecorder(
        recordingEncoder, RECORDING_FOLDER, RECORDING_INTERVAL
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

    return recorder


def server():
    """Server HTTP requests forever (until KeyboardInterrupt or Exception)."""
    try:
        address = ("", PORT)
        server = StreamingServer(address, StreamingHandler)
        logger.info("Server started")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt signal")
    except Exception as e:
        logger.error(f"SERVER STOPPED DUE TO EXCEPTION: \n{e}")
    finally:
        logger.info("Server stopped")
        cam.stop()


if __name__ == "__main__":
    recorder = setup()
    server()

    # Graceful shutdown
    # Is waiting to join the thread really necessary if it is daemon?
    # Would there be problems with ffmpeg if stopped in the middle of transcoding?
    recorder.signalStopRecording()
    recorder.join(recorder.SLEEP_INTERVAL * 2)
