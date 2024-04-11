from picamera2 import Picamera2

cam = Picamera2()

cam.start_and_capture_file("/var/www/html/snapshot.jpg")
