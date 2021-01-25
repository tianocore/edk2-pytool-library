# @file dec_parser_test.py
# Contains unit test routines for the dec parser class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import os
import uuid
import io
from edk2toollib.uefi.edk2.parsers.fdf_parser import FdfParser

TEST_PATH = os.path.realpath(os.path.dirname(__file__))

class TestBasicFdfParser(unittest.TestCase):

    def test_primary_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'UefiPayloadPkg.fdf')
        parser = FdfParser().SetBaseAbsPath(TEST_PATH)
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.LocalVars['FD_BASE'], '0x00800000')
        self.assertEqual(parser.LocalVars['NUM_BLOCKS'], '0x410')

    def test_included_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'OvmfPkgX64.fdf')
        parser = FdfParser().SetBaseAbsPath(TEST_PATH)
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.LocalVars['BLOCK_SIZE'], '0x1000')
        self.assertEqual(parser.LocalVars['MEMFD_BASE_ADDRESS'], '0x800000')

