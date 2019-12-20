##
# Handle basic logging by streaming into stringIO
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import logging
import io


class StringStreamHandler(logging.StreamHandler):
    terminator = '\n'

    def __init__(self):
        logging.Handler.__init__(self)
        self.stream = io.StringIO()

    def handle(self, record):
        """
        Conditionally emit the specified logging record.
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
        return self.stream.readlines(hint)

    def seek_start(self):
        self.stream.seek(0, 0)

    def seek_end(self):
        self.stream.seek(0, io.SEEK_END)

    def seek(self, offset, whence):
        return self.stream.seek(offset, whence)
