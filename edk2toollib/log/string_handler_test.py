# @file string_handler_test.py
# Contains unit test routines for the string_handler functions
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import logging
import os
from edk2toollib.log.string_handler import StringStreamHandler
from edk2toollib.uefi.edk2.parsers.dsc_parser import DscParser


class TestStringStreamHandler(unittest.TestCase):

  def test_init(self):
    handler = StringStreamHandler()
    self.assertNotEqual(handler, None)

  def create_record(self, message="TEST", level=logging.INFO, name=""):
    return logging.LogRecord(name, level, __file__, 0, message, [], None)

  def test_readlines(self):
    # create the handler
    handler = StringStreamHandler()
    handler.setLevel(logging.DEBUG)
    LINES_TO_DEBUG = 10
    # create some records for it to process
    for i in range(LINES_TO_DEBUG):
      rec = self.create_record(f"test{i}")
      handler.handle(rec)
    # check to make sure we don't have any
    self.assertEqual(len(handler.readlines()), 0, "We shouldn't have anything because our stream is at the end")
    # go to the beginning and read the streams
    handler.seek_start()
    self.assertEqual(len(handler.readlines()), LINES_TO_DEBUG, "We should have at least a few")
    # go to the beginning but then back to the end
    handler.seek_start()
    handler.seek_end()
    self.assertEqual(len(handler.readlines()), 0, "We shouldn't have anything because our stream is at the end")