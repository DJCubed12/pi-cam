# This is temporarily being kept for reference

import time

from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

LENGTH = 10

cam = Picamera2()
config = cam.create_video_configuration(main={'size': (720, 480)}, lores={'size': (720, 480)})
cam.configure(config)

#output = FfmpegOutput('-pix_fmt yuv420p -f mp4 test.mp4')
output = FfmpegOutput('test.mp4')
encoder = H264Encoder()

cam.start_encoder(encoder)
cam.start()

input("Say when to start")
output.start()
encoder.output = [output]
print(f"Starting {LENGTH} second video...")
# output.start()
time.sleep(LENGTH)
output.stop()
print("Video stopped and saved")

cam.stop()
