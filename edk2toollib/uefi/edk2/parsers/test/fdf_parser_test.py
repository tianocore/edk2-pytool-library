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
from edk2toollib.uefi.edk2.parsers.fdf_parser import FdfParser

TEST_PATH = os.path.realpath(os.path.dirname(__file__))


class TestBasicFdfParser(unittest.TestCase):

    def test_primary_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'SimpleDefines.fdf')
        print(test_fdf)
        parser = FdfParser().SetBaseAbsPath(TEST_PATH)
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict['FD_BASE'], '0x00800000')
        self.assertEqual(parser.Dict['NUM_BLOCKS'], '0x410')
        self.assertFalse("EXTRA_DEF" in parser.Dict)

    def test_primary_conditional_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'SimpleDefines.fdf')
        print(test_fdf)
        parser = FdfParser().SetBaseAbsPath(TEST_PATH).SetInputVars({"TARGET": "TEST2"})
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict['FD_BASE'], '0x00800000')
        self.assertEqual(parser.Dict['NUM_BLOCKS'], '0x850')
        self.assertTrue("EXTRA_DEF" in parser.Dict)

    def test_included_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'IncludedDefinesParent.fdf')
        parser = FdfParser().SetBaseAbsPath(TEST_PATH)
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict['FD_BASE'], '0x00800000')
        self.assertEqual(parser.Dict['EXTRA_BLOCK_SIZE'], '0x00001000')
        self.assertFalse("AM_I_YOU" in parser.Dict)

    def test_included_conditional_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'IncludedDefinesParent.fdf')
        parser = FdfParser().SetBaseAbsPath(TEST_PATH)
        parser = FdfParser().SetBaseAbsPath(TEST_PATH).SetInputVars({"TARGET": "TEST4"})
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict['FD_BASE'], '0x00800000')
        self.assertEqual(parser.Dict['EXTRA_BLOCK_SIZE'], '0x00001000')
        self.assertEqual(parser.Dict['NUM_BLOCKS'], '0x410')
        self.assertTrue("AM_I_YOU" in parser.Dict)
        self.assertFalse("CONDITIONAL_VALUE" in parser.Dict)

    def test_conditionally_included_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'IncludedDefinesParent.fdf')
        parser = FdfParser().SetBaseAbsPath(TEST_PATH)
        parser = FdfParser().SetBaseAbsPath(TEST_PATH).SetInputVars({"TARGET": "TEST5"})
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict['FD_BASE'], '0x00800000')
        self.assertEqual(parser.Dict['INTERNAL_VALUE'], '104')
        self.assertEqual(parser.Dict['NUM_BLOCKS'], '0x410')
        self.assertEqual(parser.Dict['CONDITIONAL_VALUE'], '121')
