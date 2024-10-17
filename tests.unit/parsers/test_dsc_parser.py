# @file dsc_parser_test.py
# Contains unit test routines for the dsc parser class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import tempfile
import os
import textwrap
from edk2toollib.uefi.edk2.parsers.dsc_parser import DscParser
from edk2toollib.uefi.edk2.path_utilities import Edk2Path


class TestDscParserBasic(unittest.TestCase):
    def test_creation(self):
        a = DscParser()
        self.assertNotEqual(a, None)


class TestDscParserIncludes(unittest.TestCase):
    @staticmethod
    def write_to_file(file_path, data):
        f = open(file_path, "w")
        f.writelines(data)
        f.close()

    def test_dsc_include_single_file(self):
        """This tests whether includes work properly"""
        workspace = tempfile.mkdtemp()

        file1_name = "file1.dsc"
        file2_name = "file2.dsc"
        file1_path = os.path.join(workspace, file1_name)
        file2_path = os.path.join(workspace, file2_name)

        file1_data = f"!include {file2_name}"
        file2_data = "[Defines]\nINCLUDED = TRUE"

        TestDscParserIncludes.write_to_file(file1_path, file1_data)
        TestDscParserIncludes.write_to_file(file2_path, file2_data)

        parser = DscParser().SetEdk2Path(Edk2Path(workspace, []))
        parser.ParseFile(file1_path)

        # test to make sure we did it right
        self.assertEqual(len(parser.LocalVars), 1)  # make sure we only have one define
        self.assertEqual(parser.LocalVars["INCLUDED"], "TRUE")  # make sure we got the defines
        self.assertEqual(len(parser.GetAllDscPaths()), 2)  # make sure we have two dsc paths

    def test_dsc_include_missing_file(self):
        """This tests whether includes work properly"""
        workspace = tempfile.mkdtemp()

        file1_name = "file1.dsc"
        file1_path = os.path.join(workspace, file1_name)

        file1_data = "!include BAD_FILE.dsc"

        TestDscParserIncludes.write_to_file(file1_path, file1_data)

        pathobj = Edk2Path(workspace, [])
        parser = DscParser().SetEdk2Path(pathobj)
        with self.assertRaises(FileNotFoundError):
            parser.ParseFile(file1_path)

    def test_dsc_include_missing_file_no_fail_mode(self):
        """This tests whether includes work properly if no fail mode is on"""
        workspace = tempfile.mkdtemp()

        file1_name = "file1.dsc"
        file1_path = os.path.join(workspace, file1_name)

        file1_data = "!include BAD_FILE.dsc"

        TestDscParserIncludes.write_to_file(file1_path, file1_data)

        parser = DscParser()
        parser.SetNoFailMode()
        parser.SetEdk2Path(Edk2Path(workspace, []))
        parser.ParseFile(file1_path)

    def test_dsc_parse_file_on_package_path(self):
        """This tests whether includes work properly if no fail mode is on"""
        workspace = tempfile.mkdtemp()
        working_dir_name = "working"
        working2_dir_name = "working2"

        working_folder = os.path.join(workspace, working_dir_name)
        working2_folder = os.path.join(working_folder, working2_dir_name)
        os.makedirs(working_folder, exist_ok=True)
        os.makedirs(working2_folder, exist_ok=True)

        file1_name = "file1.dsc"
        file1_path = os.path.join(working2_folder, file1_name)
        file1_short_path = os.path.join(working2_dir_name, file1_name)
        file1_data = "[Defines]\n INCLUDED=TRUE"

        TestDscParserIncludes.write_to_file(file1_path, file1_data)
        with self.assertRaises(FileNotFoundError):
            parser = DscParser()
            parser.SetEdk2Path(Edk2Path(workspace, []))
            parser.ParseFile(file1_short_path)

        parser = DscParser()
        parser.SetEdk2Path(Edk2Path(workspace, []))
        parser.SetPackagePaths(
            [
                working_folder,
            ]
        )
        parser.ParseFile(file1_short_path)
        self.assertEqual(parser.LocalVars["INCLUDED"], "TRUE")  # make sure we got the defines

    def test_dsc_include_relative_path(self):
        """This tests whether includes work properly with a relative path"""
        workspace = tempfile.mkdtemp()
        outside_folder = os.path.join(workspace, "outside")
        inside_folder = os.path.join(outside_folder, "inside")
        inside2_folder = os.path.join(outside_folder, "inside2")
        random_folder = os.path.join(outside_folder, "random")
        os.makedirs(inside_folder, exist_ok=True)
        os.makedirs(inside2_folder, exist_ok=True)
        os.makedirs(random_folder, exist_ok=True)
        cwd = os.getcwd()
        os.chdir(random_folder)
        try:
            file1_name = "file1.dsc"
            file1_path = os.path.join(outside_folder, file1_name)

            file2_name = "file2.dsc"
            file2_path = os.path.join(inside_folder, file2_name)

            file3_name = "file3.dsc"
            file3_path = os.path.join(inside2_folder, file3_name)

            file1_data = "!include " + os.path.relpath(file2_path, os.path.dirname(file1_path)).replace("\\", "/")
            file2_data = "!include " + os.path.relpath(file3_path, os.path.dirname(file2_path)).replace("\\", "/")
            file3_data = "[Defines]\n INCLUDED=TRUE"

            print(f"{file1_path}: {file1_data}")
            print(f"{file2_path}: {file2_data}")
            print(f"{file3_path}: {file3_data}")

            TestDscParserIncludes.write_to_file(file1_path, file1_data)
            TestDscParserIncludes.write_to_file(file2_path, file2_data)
            TestDscParserIncludes.write_to_file(file3_path, file3_data)

            parser = DscParser()
            parser.SetEdk2Path(Edk2Path(workspace, []))
            parser.ParseFile(file1_path)

            self.assertEqual(parser.LocalVars["INCLUDED"], "TRUE")  # make sure we got the defines
        finally:
            os.chdir(cwd)

    def test_dsc_define_statements(self):
        """This test some dsc define statements"""
        SAMPLE_DSC_FILE1 = textwrap.dedent("""\
        [Defines]
            PLATFORM_NAME                  = SomePlatformPkg
            PLATFORM_GUID                  = aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa
            PLATFORM_VERSION               = 0.1
            DSC_SPECIFICATION              = 0x00010005
            OUTPUT_DIRECTORY               = Build/$(PLATFORM_NAME)    
            
            DEFINE  FLAG1 = 
            
            !if FLAG1 != ""
                FLAG2 = "hi"
            !endif
            
            !if $(FLAG2) == "hi"
              [Components.IA32]
                FakePath/FakePath2/FakeInf.inf
            !endif
            """)
        workspace = tempfile.mkdtemp()

        file1_name = "file1.dsc"
        file1_path = os.path.join(workspace, file1_name)
        TestDscParserIncludes.write_to_file(file1_path, SAMPLE_DSC_FILE1)
        try:
            parser = DscParser()
            parser.SetEdk2Path(Edk2Path(workspace, []))
            parser.ParseFile(file1_path)
        finally:
            os.remove(file1_path)
        assert any("FakePath/FakePath2/FakeInf.inf" in value for value in parser.Components)
