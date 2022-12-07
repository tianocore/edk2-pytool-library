##
# unittest for ansi_handler
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import unittest
import logging
from edk2toollib.log.ansi_handler import ColoredFormatter
from edk2toollib.log.ansi_handler import ColoredStreamHandler

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class AnsiHandlerTest(unittest.TestCase):

    # we are mainly looking for exception to be thrown

    record = logging.makeLogRecord({"name": "", "level": logging.CRITICAL, "levelno": logging.CRITICAL,
                                    "levelname": "CRITICAL", "path": "test_path", "lineno": 0,
                                    "msg": "Test message"})
    record2 = logging.makeLogRecord({"name": "", "level": logging.INFO, "levelno": logging.INFO,
                                     "levelname": "INFO", "path": "test_path", "lineno": 0,
                                     "msg": "Test message"})

    def test_colored_formatter_init(self):
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        # if we didn't throw an exception, then we are good
        self.assertNotEqual(formatter, None)

    def test_colored_formatter_to_output_ansi(self):
        formatter = ColoredFormatter("%(levelname)s - %(message)s")

        output = formatter.format(AnsiHandlerTest.record)
        self.assertNotEqual(output, None)
        CSI = '\033['
        self.assertGreater(len(output), 0, "We should have some output")
        self.assertFalse((CSI not in output), "There was supposed to be a ANSI control code in that %s" % output)

    def test_color_handler_to_strip_ansi(self):
        stream = StringIO()
        # make sure we set out handler to strip the control sequence
        handler = ColoredStreamHandler(stream, strip=True, convert=False)
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        handler.formatter = formatter
        handler.level = logging.NOTSET

        handler.emit(AnsiHandlerTest.record)
        handler.flush()

        CSI = '\033['

        # check for ANSI escape code in stream
        stream.seek(0)
        lines = stream.readlines()
        self.assertGreater(len(lines), 0, "We should have some output %s" % lines)
        for line in lines:
            if CSI in line:
                self.fail("A control sequence was not stripped! %s" % lines)

    def test_color_handler_not_strip_ansi(self):
        stream = StringIO()
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        handler = ColoredStreamHandler(stream, strip=False, convert=False)
        handler.formatter = formatter
        handler.level = logging.NOTSET

        handler.emit(AnsiHandlerTest.record2)
        handler.flush()

        CSI = '\033['

        found_csi = False
        stream.seek(0)
        lines = stream.readlines()
        self.assertGreater(len(lines), 0, "We should have some output %s" % lines)
        for line in lines:
            if CSI in line:
                found_csi = True
        self.assertTrue(found_csi, "We are supposed to to have found an ANSI control character %s" % lines)
