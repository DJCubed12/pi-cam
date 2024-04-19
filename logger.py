"""Log server access, info, and errors to files or stdout."""

import sys
import time
from pathlib import Path


class Logger:
    """Prints info, errors, and debugging info. If a command line arg was provided, Logger will attempt to write all info and error logs to that file. If a second command line arg is provided, errors will be logged to that file instead."""

    PREFIX_FORMAT = "[%b %d %I:%M:%S %p] "

    def __init__(self):
        self._infoFile = None
        self._errorFile = None

        if len(sys.argv) > 1:
            try:
                self._infoFile = Path(sys.argv[1])
            except TypeError:
                pass
        if len(sys.argv) > 2:
            try:
                self._errorFile = Path(sys.argv[2])
            except TypeError:
                pass

    def debug(self, msg: str):
        """Print a debug message to stdout."""
        self._log(msg, 0)

    def info(self, msg: str):
        self._log(msg, 1)

    def error(self, msg: str):
        self._log(msg, 2)

    def _log(self, msg: str, level: int):
        """Level 1 is general info, level 2 is an error. Level 0 is for debugging."""
        prefix = time.strftime(self.PREFIX_FORMAT)

        if level >= 2 and self._errorFile != None:
            with open(self._errorFile, "a") as log:
                log.write(prefix + msg + '\n')
        elif level >= 1 and self._infoFile != None:
            with open(self._infoFile, "a") as log:
                log.write(prefix + msg + '\n')
        else:
            print(prefix + msg)
