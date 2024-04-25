# Pi-Cam Developer Notes

Resources, links, notes, and things to do in terms of future development.

## TODO

**High Priority**

* Fix glitchy color issue on recordings (main stream)
* Figure out how to add timestamps to videos
  * This will make ffmpeg stop complaining AND
  * This might allow scrolling in the video during playback
  * If not possible, add timestamp visual into recordings

**Low Priority**

* Switch to port 80
* Fix recordingEncoder.output usage to allow multiple video outputs at once (to allow /start-rec and /stop-rec)
  * This is LOW priority, maybe not necessary at all.
  * This may also require a Condition lock on recordingEncoder.output
  * If so, make a class to encapsulate and generalize this so I don't have to check if running, single output, multiple, etc...

**Future Ideas**

* A 'take snapshot' button for taking single images?
* HTML buttons to turn on/off recordings, camera, or change recording intervals?

## Helpful Docs

* [Raspberry Pi Camera software docs](https://www.raspberrypi.com/documentation/computers/camera_software.html) (libcamera)
* [The Picamera2 Library](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf) (using libcamera in Python)
  * [Source](https://github.com/raspberrypi/picamera2/tree/main) (Github)
  * [Picamera2 examples](https://github.com/ArduCAM/picamera2_examples/tree/main) (Unaffiliated Github)
* The [example code](https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py) that this project was adapted from.
* How to record & stream picamera output simultaneously
  * [Record and stream video from camera simultaneously](https://raspberrypi.stackexchange.com/questions/27041/record-and-stream-video-from-camera-simultaneously) (Rasp Pi Stack Overflow)
* Ffmpeg timestamp issue:
  * [Stack Overflow](https://stackoverflow.com/questions/75625226/ffmpeg-set-pts-for-vfr-video-from-list-of-values) (no answers)
  * [mkvmerge](https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.external_timestamp_files)
* How to [handle POST and PUT](https://stackoverflow.com/questions/66514500/how-do-i-configure-a-python-server-for-post) in Python HTTPServer. (Useful for possible future camera control buttons)

## Notes

### Camera Stopping issue

Recorded 20 min intervals successfully from 12:40am to 6:21am. MP4 files were 144 MB apiece until 3:41am, where they started gradually dropping after each recordings. 136, 106, 65, ..., and 25 MB on the last recording at 6:21am until all further h264 files are empty. Website and files were still successfully served tho.

Possibly an issue with the [Camera Module to Camera connector](https://forums.raspberrypi.com/viewtopic.php?t=315367#p1886681) (SUNNY).

### Program crashing after ssh exit (resolved)

When running python as a background task, any operations to stdout or stderr will cause the program to hang. When the user logs out or the terminal is closed, python will attempt to open stdout/err but will be forced to wait until it is in the foreground and can do so.