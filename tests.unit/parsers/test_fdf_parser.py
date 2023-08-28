# @file dec_parser_test.py
# Contains unit test routines for the dec parser class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import os
import tempfile
import textwrap
import unittest

from edk2toollib.uefi.edk2.parsers.fdf_parser import FdfParser
from edk2toollib.uefi.edk2.path_utilities import Edk2Path

TEST_PATH = os.path.realpath(os.path.dirname(__file__))


class TestBasicFdfParser(unittest.TestCase):

    def test_primary_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'SimpleDefines.fdf')
        parser = FdfParser().SetEdk2Path(Edk2Path(TEST_PATH, []))
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict['FD_BASE'], '0x00800000')
        self.assertEqual(parser.Dict['NUM_BLOCKS'], '0x410')
        self.assertFalse("EXTRA_DEF" in parser.Dict)

    def test_primary_conditional_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'SimpleDefines.fdf')
        parser = FdfParser().SetEdk2Path(Edk2Path(TEST_PATH, [])).SetInputVars({"TARGET": "TEST2"})
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict['FD_BASE'], '0x00800000')
        self.assertEqual(parser.Dict['NUM_BLOCKS'], '0x850')
        self.assertTrue("EXTRA_DEF" in parser.Dict)

    def test_included_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'IncludedDefinesParent.fdf')
        parser = FdfParser().SetEdk2Path(Edk2Path(TEST_PATH, []))
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict['FD_BASE'], '0x00800000')
        self.assertEqual(parser.Dict['EXTRA_BLOCK_SIZE'], '0x00001000')
        self.assertFalse("AM_I_YOU" in parser.Dict)

    def test_included_conditional_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'IncludedDefinesParent.fdf')
        pathobj = Edk2Path(TEST_PATH, [])
        parser = FdfParser().SetEdk2Path(pathobj)
        parser = FdfParser().SetEdk2Path(pathobj).SetInputVars({"TARGET": "TEST4"})
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict['FD_BASE'], '0x00800000')
        self.assertEqual(parser.Dict['EXTRA_BLOCK_SIZE'], '0x00001000')
        self.assertEqual(parser.Dict['NUM_BLOCKS'], '0x410')
        self.assertTrue("AM_I_YOU" in parser.Dict)
        self.assertFalse("CONDITIONAL_VALUE" in parser.Dict)

    def test_conditionally_included_defines(self):
        test_fdf = os.path.join(TEST_PATH, 'IncludedDefinesParent.fdf')
        pathobj = Edk2Path(TEST_PATH, [])
        parser = FdfParser().SetEdk2Path(pathobj)
        parser = FdfParser().SetEdk2Path(pathobj).SetInputVars({"TARGET": "TEST5"})
        parser.ParseFile(test_fdf)

        # Make sure that we can read local variables out of the file.
        self.assertEqual(parser.Dict['FD_BASE'], '0x00800000')
        self.assertEqual(parser.Dict['INTERNAL_VALUE'], '104')
        self.assertEqual(parser.Dict['NUM_BLOCKS'], '0x410')
        self.assertEqual(parser.Dict['CONDITIONAL_VALUE'], '121')


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
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
            f.write(SAMPLE_FDF_FILE)
            fdf_path = f.name

        # When
        parser = FdfParser()
        parser.ParseFile(fdf_path)
    finally:
        os.remove(fdf_path)

    # Then
    assert "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb" in \
        parser.FVs["MAINFV"]["Files"]["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]

def test_fdf_include_relative_paths(tmp_path):
    """This tests whether includes work properly with a relative path.

    Directory setup
    src
    └─ Platforms
       └─ PlatformPkg
          ├─ PlatformPkg.dsc
          └─ includes
             ├─ Libs1.dsc.inc
             └─ Libs2.dsc.inc

    Base FDF
    [LibraryClasses]
    !include includes/Libs1.dsc.inc
    !include includes/Libs2.dsc.inc
    """
    pp = tmp_path / "Platforms"
    pkg_dir = pp / "PlatformPkg"
    fdf = pkg_dir / "PlatformPkg.fdf"
    inc_dir = pkg_dir / "includes"

    # Create Platforms, Platforms/PlatformPkg, Platforms/PlatformPkg/includes
    inc_dir.mkdir(parents=True)

    with open(inc_dir / "Libs1.dsc.inc", "w") as f:
        f.write("Lib1|BaseLib1.inf\n")

    with open(inc_dir / "Libs2.dsc.inc", "w") as f:
        f.write("Lib2|BaseLib2.inf\n")

    with open(fdf, "w") as f:
        f.write("[LibraryClasses]\n")
        f.write("!include includes/Libs1.dsc.inc\n")
        f.write("!include includes/Libs2.dsc.inc\n")

    parser = FdfParser()
    parser.SetEdk2Path(Edk2Path(str(tmp_path), [str(pp)]))
    parser.ParseFile(fdf)
