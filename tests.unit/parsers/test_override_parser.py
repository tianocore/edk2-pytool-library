## @file override_parser_test.py
# Contains unit test routines for the OverrideParser class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import os

from edk2toollib.uefi.edk2.parsers.override_parser import OverrideParser

SAMPLE_DATA_SINGLE_OVERRIDE = (
    """#Override : 00000001 | My/Path/1 | 4e367990b327501d1ea6fbee4002f9c8 | 2018-11-27T22-36-30"""  # noqa: E501
)

SAMPLE_DATA_BAD_VERSION = (
    """#Override : 0000000X | My/Path/1 | 4e367990b327501d1ea6fbee4002f9c8 | 2018-11-27T22-36-30"""  # noqa: E501
)
SAMPLE_DATA_BAD_DATE = """#Override : 00000001 | My/Path/1 | 4e367990b327501d1ea6fbee4002f9c8 | NOTADATE"""

SAMPLE_DATA_TRIPLE_OVERRIDE = """
#Override : 00000001 | My/Path/1 | 4e367990b327501d1ea6fbee4002f9c8 | 2018-11-27T22-36-30
#Override : 00000001 | My/Path/2 | 4e367990b327501d1ea6fbee4002f9c8 | 2018-11-27T22-36-30
#Override : 00000001 | My/Path/3 | 4e367990b327501d1ea6fbee4002f9c8 | 2018-11-27T22-36-30
"""

SAMPLE_DATA_MIXED_CASE_OVERRIDE = """
#Override : 00000001 | My/Path/1 | 4e367990b327501d1ea6fbee4002f9c8 | 2018-11-27T22-36-30
#OVERRIDE : 00000001 | MY/PATH/2 | 4E367990B327501D1EA6FBEE4002F9C8 | 2018-11-27T22-36-30
#override : 00000001 | my/path/3 | 4e367990b327501d1ea6fbee4002f9c8 | 2018-11-27t22-36-30
"""

SAMPLE_DATA_NO_OVERRIDE = """This are just some lines of text.

Nothing to see here.

#OVER... not really, bet you thought it was an override.
"""

SAMPLE_DATA_REAL_WORLD = """## @file
# The DXE driver produces FORM DISPLAY ENGINE protocol.
#
# Copyright (c) 2007 - 2018, Intel Corporation. All rights reserved.<BR>
# Copyright (c) 2015 - 2018, Microsoft Corporation.
#
#  This program and the accompanying materials
#  are licensed and made available under the terms and conditions of the BSD License
#  which accompanies this distribution. The full text of the license may be found at
#  http://opensource.org/licenses/bsd-license.php
#
#  THE PROGRAM IS DISTRIBUTED UNDER THE BSD LICENSE ON AN "AS IS" BASIS,
#  WITHOUT WARRANTIES OR REPRESENTATIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED.
#
#
##

#Override : 00000001 | MdeModulePkg/Universal/DisplayEngineDxe/DisplayEngineDxe.inf | 2eba0bc48b8ab3b1399c26800d057102 | 2018-10-05T21-43-51

[Defines]
  INF_VERSION                    = 0x00010005
  BASE_NAME                      = DisplayEngine
  FILE_GUID                      = E660EA85-058E-4b55-A54B-F02F83A24707
  MODULE_TYPE                    = DXE_DRIVER
  VERSION_STRING                 = 1.0
  ENTRY_POINT                    = InitializeDisplayEngine
  UNLOAD_IMAGE                   = UnloadDisplayEngine

# MORE TEXT BELOW HERE...
"""  # noqa: E501


class TestOverrideParser(unittest.TestCase):
    def test_no_inputs_raises_error(self):
        with self.assertRaises(ValueError):
            OverrideParser()

    def test_no_overrides_raises_error(self):
        with self.assertRaises(ValueError):
            OverrideParser(inf_contents=SAMPLE_DATA_NO_OVERRIDE)

    def test_bad_version_or_bad_date_raises_error(self):
        with self.assertRaises(ValueError):
            OverrideParser(inf_contents=SAMPLE_DATA_BAD_VERSION)
        with self.assertRaises(ValueError):
            OverrideParser(inf_contents=SAMPLE_DATA_BAD_DATE)

    def test_single_override_is_parsed(self):
        parser = OverrideParser(inf_contents=SAMPLE_DATA_SINGLE_OVERRIDE)

        self.assertEqual(len(parser.override_lines), 1)
        self.assertEqual(len(parser.overrides), 1)

        self.assertEqual(parser.overrides[0]["version"], 1)
        self.assertEqual(parser.overrides[0]["original_path"].upper(), os.path.normpath("MY/PATH/1"))
        self.assertEqual(parser.overrides[0]["current_hash"].upper(), "4E367990B327501D1EA6FBEE4002F9C8")
        self.assertEqual(parser.overrides[0]["datetime"].year, 2018)
        self.assertEqual(parser.overrides[0]["datetime"].month, 11)
        self.assertEqual(parser.overrides[0]["datetime"].day, 27)

    def test_real_world_override_is_parsed(self):
        parser = OverrideParser(inf_contents=SAMPLE_DATA_REAL_WORLD)

        self.assertEqual(len(parser.override_lines), 1)
        self.assertEqual(len(parser.overrides), 1)

        self.assertEqual(parser.overrides[0]["version"], 1)
        self.assertEqual(
            parser.overrides[0]["original_path"],
            os.path.normpath("MdeModulePkg/Universal/DisplayEngineDxe/DisplayEngineDxe.inf"),
        )
        self.assertEqual(parser.overrides[0]["current_hash"].upper(), "2EBA0BC48B8AB3B1399C26800D057102")
        self.assertEqual(parser.overrides[0]["datetime"].year, 2018)
        self.assertEqual(parser.overrides[0]["datetime"].month, 10)
        self.assertEqual(parser.overrides[0]["datetime"].day, 5)

    def test_triple_override_is_parsed(self):
        parser = OverrideParser(inf_contents=SAMPLE_DATA_TRIPLE_OVERRIDE)

        self.assertEqual(len(parser.override_lines), 3)
        self.assertEqual(len(parser.overrides), 3)

        self.assertEqual(parser.overrides[0]["version"], 1)
        self.assertEqual(parser.overrides[0]["current_hash"].upper(), "4E367990B327501D1EA6FBEE4002F9C8")
        self.assertEqual(parser.overrides[1]["version"], 1)
        self.assertEqual(parser.overrides[1]["current_hash"].upper(), "4E367990B327501D1EA6FBEE4002F9C8")
        self.assertEqual(parser.overrides[2]["version"], 1)
        self.assertEqual(parser.overrides[2]["current_hash"].upper(), "4E367990B327501D1EA6FBEE4002F9C8")

    def test_mixed_case_override_is_parsed(self):
        parser = OverrideParser(inf_contents=SAMPLE_DATA_MIXED_CASE_OVERRIDE)

        self.assertEqual(len(parser.override_lines), 3)
        self.assertEqual(len(parser.overrides), 3)

        self.assertEqual(parser.overrides[0]["version"], 1)
        self.assertEqual(parser.overrides[0]["current_hash"].upper(), "4E367990B327501D1EA6FBEE4002F9C8")
        self.assertEqual(parser.overrides[1]["version"], 1)
        self.assertEqual(parser.overrides[1]["current_hash"].upper(), "4E367990B327501D1EA6FBEE4002F9C8")
        self.assertEqual(parser.overrides[2]["version"], 1)
        self.assertEqual(parser.overrides[2]["current_hash"].upper(), "4E367990B327501D1EA6FBEE4002F9C8")

    def test_parses_all_versions(self):
        # TODO: Fill out this test if it's ever needed.
        pass
