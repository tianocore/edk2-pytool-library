# @file guid_parser_test.py
# Contains unit test routines for the guid parser class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser


class TestBaseParser(unittest.TestCase):

    def test_parse_new_section(self):
        parser = HashFileParser("")
        section1 = "[Defines]"
        res, sect = parser.ParseNewSection(section1)
        self.assertTrue(res)
        self.assertEqual(sect, "Defines")
        # invalud section
        section2 = "[Defines"
        res, sect = parser.ParseNewSection(section2)
        self.assertFalse(res)
        # multiple parts with multiple definitions
        section3 = "[Components.X64, Components.IA32]"
        res, sect = parser.ParseNewSection(section3)
        self.assertTrue(res)
        self.assertEqual(sect, "Components")
        # try multiple parts on a single
        section4 = "[ Defines.Common.Section ]"
        res, sect = parser.ParseNewSection(section4)
        self.assertTrue(res)
        self.assertEqual(sect, "Defines")

    def test_strip_comment(self):
        parser = HashFileParser("")
        lines = ["Test", "MagicLib|Include/Magic", ""]
        comments = ["\t#this shouldn't show up", " # test", ""]
        for line in lines:
            for comment in comments:
                test_line = line + comment
                result = parser.StripComment(test_line)
                self.assertEqual(result, line)
