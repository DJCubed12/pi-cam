# Pi-Cam

This is a Raspberry Pi Security Camera.

## Python Streaming Server

Run the streaming server and automatic recorder with:

```bash
nohup python streaming_server.py > error.log &
```

This will host a website on port 8000 that serves the live camera feed, previously recorded videos, and a viewer for said videos.

The automatic recorder within the streaming server saves files to `recordings/`. As this folder will fill up with large files, it is necessary to delete old ones every so often.

### Automatically deleting old recordings

Use `find` and `crontab` to delete old recordings.

The first step is to get the absolute path of the recordings folder:

```bash
realpath recordings
```

The following command will show all recordings more than 1 day old (>= 2 days old). Test to make sure this command is accurate; this should print all files in the `recordings/` directory.

```bash
find <PATH TO RECORDINGS FOLDER> -type f '(' -name '*.mp4' -o -name '*.h264' ')' -mtime +1
```

To delete files that are older than 3, 4, `x` days change `-mtime +1` to `mtime +x`. Or to delete files faster change it to `-mmin +x` where `x` is how old the target files are in minutes.

Then use `crontab -e` to open and edit your user's crontab. Add a [cron schedule expression](https://crontab.guru/) and your tested find command to the crontab and save it:

The above example deletes recordings older than 1 day (>= 2 days old) at noon everyday.

```bash
0 12 * * * find <PATH TO RECORDINGS FOLDER> -type f '(' -name '*.mp4' -o -name '*.h264' ')' -mtime +1 -delete
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
* The [example](https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py) code that most of this project was based off of.
* How to record & stream picamera output simultaneously
  * [record and stream video from camera simultaneously](https://raspberrypi.stackexchange.com/questions/27041/record-and-stream-video-from-camera-simultaneously) (Rasp Pi Stack Overflow)
* Ffmpeg timestamp issue:
  * [Stack Overflow (no answers)](https://stackoverflow.com/questions/75625226/ffmpeg-set-pts-for-vfr-video-from-list-of-values)
  * [mkvmerge](https://mkvtoolnix.download/doc/mkvmerge.html#mkvmerge.external_timestamp_files)

## Dev Notes

How to [handle POST and PUT](https://stackoverflow.com/questions/66514500/how-do-i-configure-a-python-server-for-post) in Python HTTPServer.

When running python as a background task, any operations to stdout or stderr will cause the program to hang. When the user logs out or the terminal is closed, python will attempt to open stdout/err but will be forced to wait until it is in the foreground and can do so.

To find the streaming server process when ssh'ing back in:
```bash
ps -f -u DJCubed12 -U DJCubed12
```

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
libcamera  # Should already be installed for Raspbian OS
python3
python3-picamera  # Install with --no-install recommends
ffmpeg
```
