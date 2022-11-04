##
# Handle basic logging outputting to files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module for handling basically logging to files."""
import logging


class FileHandler(logging.FileHandler):
    """Object for handling basic logging output to files."""
    def __init__(self, filename, mode='w+'):
        """Init a file handler for the specified file."""
        logging.FileHandler.__init__(self, filename, mode=mode)

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
