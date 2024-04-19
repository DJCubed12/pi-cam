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
mainEncoder = H264Encoder()
loresEncoder = H264Encoder()

cam.start_encoder(mainEncoder, name="main")
cam.start_encoder(loresEncoder, name="lores")
cam.start()

print("Starting main video!")
mainOutput.start()
mainEncoder.output = mainOutput

input("> Enter to start lores video: ")
loresOutput.start()
loresEncoder.output = loresOutput

print(f"Lores video ends in {LENGTH} sec...")
time.sleep(LENGTH)
cam.stop_encoder(loresEncoder)
loresOutput.stop()
print("Lores video stopped and saved")

input("> Enter to stop main video: ")
cam.stop_encoder(mainEncoder)
mainOutput.stop()
cam.stop()

print("Main video stopped and saved")
