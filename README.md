# Pi-Cam

This is a Raspberry Pi Security Camera streaming server created by Carson Jones. This was an Honors Project for MS&T's CS 3610 - Computer Networks.

## Requirements

This project was written specifically for the _Raspberry Pi 4 Model B_ running _Debian GNU/Linux 12 (bookworm)_.

The following apt packages are required (all already installed on _bookworm_):

```
libcamera
python3
python3-picamera  # Install with --no-install-recommends
ffmpeg
```

This project was made using the _Raspberry Pi Camera Module v1_, however it should work with any Camera/Camera Module compatible with `libcamera`.

## Python Streaming Server

Run the streaming server and automatic recorder with:

```bash
nohup python streaming_server.py > error.log &
```

This will host a website on port `8000` (unless changed in `pi-cam.ini`) that serves the live camera feed, previously recorded videos, and a viewer for these videos. The website will be available at `http://<Pi's IP address>:<Port>`.

The automatic recorder within the streaming server saves files to `recordings/`. As this folder will fill up with large files, it is necessary to delete old ones every so often.

### Automatically deleting old recordings

Use `find` and `crontab` to delete old recordings.

The first step is to get the absolute path of the recordings folder:

```bash
realpath recordings
```

The following command will show all recordings more than 1 day old (>= 2 days old). Test to make sure this command is accurate; this should print all files in the `recordings/` directory:

```bash
find <PATH TO RECORDINGS FOLDER> -type f '(' -name '*.mp4' -o -name '*.h264' ')' -mtime +1
```

To delete files that are older than 3, 4, `x` days change `-mtime +1` to `mtime +x`. Or to delete files faster change it to `-mmin +x` where `x` is how old the target files are in minutes.

Then use `crontab -e` to open and edit your user's crontab. Add a [cron schedule expression](https://crontab.guru/) and your tested find command with a final `-delete` option to the crontab and save it:

```bash
0 12 * * * find <PATH TO RECORDINGS FOLDER> -type f '(' -name '*.mp4' -o -name '*.h264' ')' -mtime +1 -delete
```

The above example deletes recordings older than 1 day (>= 2 days old) at noon everyday.

### Stopping the Server

When you ssh back into the Pi, list running processes to find the streaming server (process name will say python):

```bash
ps -f -u <username>
```

Kill the server gracefully with:

```bash
kill -2 <PID>
```

The server attempts to safely save it's current recording file when shut down. Please expect and be patient for a 5-10 second delay for the process to end after killing it.

## Documentation

### HTTP Endpoints

* `/index.html`
  * This is the main page. You can view the camera's live feed here.
* `/recordings/index.html`
  * Pi-Cam constantly records it's output and saves them as mp4 files which are listed here.
  * Listed files have links to take you to their playback pages.
* `/playback.html`
  * Watch recorded mp4 files here.
  * This endpoint takes one URL parameter, `file` which must be an `mp4` filename available in the `recordings/` directory on the Pi itself.

### Configuration

The streaming server has certain variables that can be reconfigured in the `pi-cam.ini` config file. These variables include things like which port to listen on, video resolution, and what duration recording files are split into.

### Source Files

The noteworthy source files are:

* `streaming_server.py`
  * The "main" file. Sets up the `HTTPServer` and listens for requests.
* `request_handler.py`
  * Where HTTP endpoints are defined and implemented.
* `src/`
  * _Template_ HTML files. These are files that `request_handler.py` string-interpolates upon request to serve HTML pages.
* `recorder.py`
  * Houses the `BackgroundRecorder`: a Thread that can be used to concurrently record the camera's feed while running the server.

## Note for Honors Project

Admittedly the end project doesn't involve much networking beside's the use to HTTP using Python's built in `HTTPServer`. However, there was more networking involved in the earlier stages of the project.

Up to commit `94398d5`, the entire project was based in Apache. I had to learn more about Apache configuration (including working with the configuration files) and CGI scripts. A particular challenge was to change all response headers to tell browsers to stop caching my webpages!

I struggled a lot with understanding how I can serve a constant feed of live image/video data with Apache. Through research I realized that Apache wasn't really built for that kind of work. I was researching different streaming servers, how they worked, and alternatives to HTTP (TCP/UDP streams) when I stumbled upon [example code](https://github.com/raspberrypi/picamera2/blob/main/examples/mjpeg_server.py) of livestreaming a Raspberry Pi's Camera feed in Python.

Although this solution is rather abstracted from the underlying networking, I learned a lot through my tangential research.