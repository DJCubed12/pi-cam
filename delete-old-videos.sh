#!/bin/bash

# Files accessed >=2 days ago
find -atime +1

# Files modified >=2 days ago
find -mtime +1

# Files modified >=60 minutes ago
find -mmin +60

# Find video files
find -type f -name '*.h264'
find -type f -name '*.ts'
find -type f -name '*.mp4'

# Delete found files
find <tests, operators, etc...> -delete

# Test if found files are what you wanted
find <tests, operators, etc...> -print

# END COMMAND (Change -mmin value to however many minutes back you want files deleted)
find recordings -type f '(' -name '*.mp4' -o -name '*.h264' ')' -mmin +360

# TODO: Make this happen in a crontab (MAKE SURE recordings is replaced by the full absolute path)