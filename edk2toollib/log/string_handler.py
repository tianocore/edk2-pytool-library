##
# Handle basic logging by streaming into stringIO
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module for handling basic logging by streaming into StringIO."""
import io
import logging


class StringStreamHandler(logging.StreamHandler):
    """Class for logging via StringIO."""
    terminator = '\n'

    def __init__(self):
        """Init a StringStreamHandler."""
        logging.Handler.__init__(self)
        self.stream = io.StringIO()

    def handle(self, record):
        """Conditionally emit the specified logging record.

        Emission depends on filters which may have been added to the handler.
        Wrap the actual emission of the record with acquisition/release of
        the I/O thread lock. Returns whether the filter passed the record for
        emission.
        """
        rv = self.filter(record)
        if rv and record.levelno >= self.level:
            self.acquire()
            try:
                self.emit(record)
            finally:
                self.release()
        return rv

    def readlines(self, hint=-1):
        """Reads lines from stream and returns them."""
        return self.stream.readlines(hint)

    def seek_start(self):
        """Seeks to a specific point in the stream."""
        self.stream.seek(0, 0)

    def seek_end(self):
        """Seeks to the end of the stream."""
        self.stream.seek(0, io.SEEK_END)

    def seek(self, offset, whence):
        """Seek to a specific point in the stream."""
        return self.stream.seek(offset, whence)
