import time

LENGTH = 10

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

cam = Picamera2()
config = cam.create_video_configuration(
    main={"size": (720, 480)}, lores={"size": (720, 480)}
)
cam.configure(config)

mainOutput = FfmpegOutput("test-main.mp4")
loresOutput = FfmpegOutput("test-lores.mp4")
encoder = H264Encoder()

cam.start_encoder(encoder)  # main
cam.start()

print("Starting main video!")
mainOutput.start()
encoder.output = mainOutput

input("> Enter to start lores video: ")
loresOutput.start()
encoder.output = [mainOutput, loresOutput]

print(f"Lores video ends in {LENGTH} sec...")
time.sleep(LENGTH)
encoder.output = mainOutput
loresOutput.stop()
print("Lores video stopped and saved")

input("> Enter to stop main video: ")
cam.stop_encoder(encoder)
mainOutput.stop()
cam.stop()

print("Main video stopped and saved")
