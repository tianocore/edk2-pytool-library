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
import textwrap
import tempfile
from edk2toollib.uefi.edk2.parsers.fdf_parser import FdfParser
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

TEST_PATH = os.path.realpath(os.path.dirname(__file__))


class TestBasicFdfParser(unittest.TestCase):
    def test_primary_defines(self):
        test_fdf = os.path.join(TEST_PATH, "SimpleDefines.fdf")
        parser = FdfParser().SetEdk2Path(Edk2Path(TEST_PATH, []))
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict["FD_BASE"], "0x00800000")
        self.assertEqual(parser.Dict["NUM_BLOCKS"], "0x410")
        self.assertFalse("EXTRA_DEF" in parser.Dict)

    def test_primary_conditional_defines(self):
        test_fdf = os.path.join(TEST_PATH, "SimpleDefines.fdf")
        parser = FdfParser().SetEdk2Path(Edk2Path(TEST_PATH, [])).SetInputVars({"TARGET": "TEST2"})
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict["FD_BASE"], "0x00800000")
        self.assertEqual(parser.Dict["NUM_BLOCKS"], "0x850")
        self.assertTrue("EXTRA_DEF" in parser.Dict)

    def test_included_defines(self):
        test_fdf = os.path.join(TEST_PATH, "IncludedDefinesParent.fdf")
        parser = FdfParser().SetEdk2Path(Edk2Path(TEST_PATH, []))
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict["FD_BASE"], "0x00800000")
        self.assertEqual(parser.Dict["EXTRA_BLOCK_SIZE"], "0x00001000")
        self.assertFalse("AM_I_YOU" in parser.Dict)

    def test_included_conditional_defines(self):
        test_fdf = os.path.join(TEST_PATH, "IncludedDefinesParent.fdf")
        pathobj = Edk2Path(TEST_PATH, [])
        parser = FdfParser().SetEdk2Path(pathobj)
        parser = FdfParser().SetEdk2Path(pathobj).SetInputVars({"TARGET": "TEST4"})
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict["FD_BASE"], "0x00800000")
        self.assertEqual(parser.Dict["EXTRA_BLOCK_SIZE"], "0x00001000")
        self.assertEqual(parser.Dict["NUM_BLOCKS"], "0x410")
        self.assertTrue("AM_I_YOU" in parser.Dict)
        self.assertFalse("CONDITIONAL_VALUE" in parser.Dict)

    def test_conditionally_included_defines(self):
        test_fdf = os.path.join(TEST_PATH, "IncludedDefinesParent.fdf")
        pathobj = Edk2Path(TEST_PATH, [])
        parser = FdfParser().SetEdk2Path(pathobj)
        parser = FdfParser().SetEdk2Path(pathobj).SetInputVars({"TARGET": "TEST5"})
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict["FD_BASE"], "0x00800000")
        self.assertEqual(parser.Dict["INTERNAL_VALUE"], "104")
        self.assertEqual(parser.Dict["NUM_BLOCKS"], "0x410")
        self.assertEqual(parser.Dict["CONDITIONAL_VALUE"], "121")


def test_section_guided():
    """Check that SECTION GUIDED can be added."""
    # Given
    # cSpell:ignore MAINFV
    SAMPLE_FDF_FILE = textwrap.dedent("""\
        [FV.MAINFV]
        FILE PEIM = aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa{
            SECTION GUIDED bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb
        }
    """)
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write(SAMPLE_FDF_FILE)
            fdf_path = f.name

        # When
        parser = FdfParser()
        parser.ParseFile(fdf_path)
    finally:
        os.remove(fdf_path)

    # Then
    assert (
        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb" in parser.FVs["MAINFV"]["Files"]["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]
    )


def test_file_raw_section_statements():
    """Check common file type statements from an FDF file"""

    SAMPLE_FDF_FILE1 = textwrap.dedent("""\
        [FV.MAINFV]
        FILEFILE RAW = aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa {
            SECTION COMPRESS {
                SECTION RAW = $(OUTPUT_DIRECTORY)/$(TARGET)_$(TOOL_CHAIN_TAG)/FV/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb.bin
            }
        }
    """)
    SAMPLE_FDF_FILE2 = textwrap.dedent("""\
        [FV.MAINFV]
        FILEFILE RAW = aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa {
            SECTION RAW = $(OUTPUT_DIRECTORY)/$(TARGET)_$(TOOL_CHAIN_TAG)/FV/something.bin
            SECTION PE32 = $(OUTPUT_DIRECTORY)/$(TARGET)_$(TOOL_CHAIN_TAG>/FV/Exec.efi
        }
    """)
    SAMPLE_FDF_FILE3 = textwrap.dedent("""\
        [FV.MAINFV]
        FILEFILE RAW = aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa {
            SECTION COMPRESS {
                SECTION RAW = binary.bin
                SECTION UI = a_ui.bin
                SECTION PE32 = some_efi_file.efi
                SECTION TE = some_te.te
            }
        }
    """)
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write(SAMPLE_FDF_FILE1)
            fdf_path = f.name

        parser = FdfParser()
        parser.ParseFile(fdf_path)
    finally:
        os.remove(fdf_path)

    assert (
        "$(OUTPUT_DIRECTORY)/$(TARGET)_$(TOOL_CHAIN_TAG)/FV/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb.bin"
        in parser.FVs["MAINFV"]["Files"]["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]["RAW"]
    )

    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write(SAMPLE_FDF_FILE2)
            fdf_path = f.name

        parser = FdfParser()
        parser.ParseFile(fdf_path)
    finally:
        os.remove(fdf_path)
    assert (
        "$(OUTPUT_DIRECTORY)/$(TARGET)_$(TOOL_CHAIN_TAG)/FV/something.bin"
        in parser.FVs["MAINFV"]["Files"]["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]["RAW"]
    )
    assert (
        "$(OUTPUT_DIRECTORY)/$(TARGET)_$(TOOL_CHAIN_TAG>/FV/Exec.efi"
        in parser.FVs["MAINFV"]["Files"]["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]["PE32"]
    )

    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as f:
            f.write(SAMPLE_FDF_FILE3)
            fdf_path = f.name

        parser = FdfParser()
        parser.ParseFile(fdf_path)
    finally:
        os.remove(fdf_path)

    assert "binary.bin" in parser.FVs["MAINFV"]["Files"]["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]["RAW"]
    assert "a_ui.bin" in parser.FVs["MAINFV"]["Files"]["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]["UI"]
    assert "some_efi_file.efi" in parser.FVs["MAINFV"]["Files"]["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]["PE32"]
    assert "some_te.te" in parser.FVs["MAINFV"]["Files"]["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]["TE"]
