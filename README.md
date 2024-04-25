# Pi-Cam

This is a Raspberry Pi Security Camera streaming server created by Carson Jones. This was an Honors Project for MS&T's CS 3610 - Computer Networks.

## Requirements

Necessary apt packages:

```
libcamera  # Should already be installed for Raspbian OS
python3
python3-picamera  # Install with --no-install recommends
ffmpeg
```

## Python Streaming Server

Run the streaming server and automatic recorder with:

```bash
nohup python streaming_server.py > error.log &
```

This will host a website on port `8000` that serves the live camera feed, previously recorded videos, and a viewer for said videos.

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

The server provides the following endpoints:

### `/index.html`

This is the main page. You can view the camera's live feed here.

### `/recordings/index.html`

Pi-Cam constantly records it's output and saves them as mp4 files which are listed here. Listed files have links to take you to their playback pages.

### `/playback.html`

Watch recorded mp4 files here.
