# Pi-Cam

This is a Raspberry Pi Security Camera.

## Apache Server Setup

This project uses Apache. Make sure it is installed (`sudo apt install apache2`).

This project makes use of CGI scripts. Raspbian is a flavor of Debian, which requires Apache CGI scripts to be enabled as so:

```bash
sudo a2enconf serve-cgi-bin
sudo a2enmod cgid
```

_Note: In Debian the cgi-bin is stored in /usr/lib._

When Apache is running it uses a user named `www-data` to serve files and run CGI scripts. `www-data` will need to run CGI scripts that access `/dev/media#`, requiring `www-data` to be in the `video` group.

```bash
sudo useradd www-data video
```

The `apache-setup.sh` script will do the rest:
* Move files
* Create directories
* Change file permissions
* Start apache2.service

Be sure to run it with sudo.

## Python Streaming Server

Run with:

```bash
python streaming_server.py &
```

## Documentation

The server provides the following endpoints:

### `/index.html`

This is the main page. You can view the camera's live feed here.

### `/recordings/index.html`

Pi-Cam constantly records it's output and saves them as mp4 files which are listed here. Listed files have links to take you to their playback pages.

### `/playback.html`

Watch recorded mp4 files here.

## Helpful Dev Docs

* [Raspberry Pi Camera software docs](https://www.raspberrypi.com/documentation/computers/camera_software.html#python-bindings-for-libcamera) (libcamera)
* [The Picamera2 Library](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf) (use libcamera in Python)
  * [picamera](https://github.com/raspberrypi/picamera2/tree/main) (Github)
  * [Picamera2 examples](https://github.com/ArduCAM/picamera2_examples/tree/main)
* How to record & stream picamera output simultaneously
  * [record and stream video from camera simultaneously](https://raspberrypi.stackexchange.com/questions/27041/record-and-stream-video-from-camera-simultaneously) (Rasp Pi Stack Overflow)

## Dev Notes

How to [handle POST and PUT](https://stackoverflow.com/questions/66514500/how-do-i-configure-a-python-server-for-post) in Python HTTPServer.

TODO:
* Fix glitchy color issue on recordings (main stream)
* Move constants to config file
* Figure out how to add timestamps to videos
  * This will make ffmpeg stop complaining AND
  * This will allow scrolling in the video during playback (i think)
* Make logging to my liking; separate error logs from access logs.
* See how large recorded files are, decide how far back to keep them.
  * Automatically delete after certain age
* Switch to port 80
* Fix recordingEncoder.output usage to allow multiple video outputs at once (to allow /start-rec and /stop-rec)
  * This may also require a Condition lock on recordingEncoder.output
  * If so, make a class to encapsulate and generalize this so I don't have to check if running, single output, multiple, etc...
* HTML buttons to do recordings.
* On/off buttons

## Requirements

Necessary apt packages:

```
apache2
libcamera  # Should already be installed for Raspbian OS
python3-picamera  # Install with --no-install recommends
ffmpeg
```
