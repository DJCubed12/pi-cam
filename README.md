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

The following paths are referring to URL endpoints.

### `/index.html`

Landing page. Displays `/snapshot.jpg` and provides a button to take a new snapshot using `/cgi-bin/take-snapshot.sh`.

### `/cgi-bin/take-snapshot.sh`

Takes a picture with the Pi Camera and saves it as `/snapshot.jpg` (overwritting the old snapshot).

## Helpful Dev Docs

* [Raspberry Pi Camera software docs](https://www.raspberrypi.com/documentation/computers/camera_software.html#python-bindings-for-libcamera) (libcamera)
* [The Picamera2 Library](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf) (use libcamera in Python)
  * [picamera](https://github.com/raspberrypi/picamera2/tree/main) (Github)
  * [Picamera2 examples](https://github.com/ArduCAM/picamera2_examples/tree/main)

## Dev Notes

**Left of at [Picamera2 4.2.1](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)**

Autofocus configurations at [5.2](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf).

[This article](https://forum.arducam.com/t/how-to-make-libcamera-still-faster/4898/7) seems to imply that the camera will operate much faster when used within a script. Setup the camera configuration once at beginning (~1 sec), then leave program running so configuration doesn't have to occur again. (How to make this work like an API if it's constantly running?)

Possible [answer](https://www.raspberrypi.com/documentation/computers/camera_software.html#network-streaming) to all my future streaming problems??

[How media streaming with HTTP works](https://superuser.com/questions/1112904/streaming-media-from-inside-html-pages-by-example)

## Requirements

Necessary apt packages:

```
apache2
libcamera  # Should already be installed for Raspbian OS
python3-picamera  # Install with --no-install recommends
ffmpeg
```
