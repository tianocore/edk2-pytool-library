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
from edk2toollib.uefi.edk2.parsers.dsc_parser import DscParser


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
        ''' This tests whether includes work properly '''
        workspace = tempfile.gettempdir()

        file1_name = "file1.dsc"
        file2_name = "file2.dsc"
        file1_path = os.path.join(workspace, file1_name)
        file2_path = os.path.join(workspace, file2_name)

        file1_data = f"!include {file2_name}"
        file2_data = "[Defines]\nINCLUDED = TRUE"

        TestDscParserIncludes.write_to_file(file1_path, file1_data)
        TestDscParserIncludes.write_to_file(file2_path, file2_data)

        parser = DscParser()
        parser.SetBaseAbsPath(workspace)
        parser.ParseFile(file1_path)

        # test to make sure we did it right
        self.assertEqual(len(parser.LocalVars), 1)  # make sure we only have one define
        self.assertEqual(parser.LocalVars["INCLUDED"], "TRUE")  # make sure we got the defines
        self.assertEqual(len(parser.GetAllDscPaths()), 2)  # make sure we have two dsc paths

    def test_dsc_include_missing_file(self):
        ''' This tests whether includes work properly '''
        workspace = tempfile.gettempdir()

        file1_name = "file1.dsc"
        file1_path = os.path.join(workspace, file1_name)

        file1_data = "!include BAD_FILE.dsc"

        TestDscParserIncludes.write_to_file(file1_path, file1_data)

        parser = DscParser()
        parser.SetBaseAbsPath(workspace)
        with self.assertRaises(FileNotFoundError):
            parser.ParseFile(file1_path)

    def test_dsc_include_missing_file_no_fail_mode(self):
        ''' This tests whether includes work properly if no fail mode is on'''
        workspace = tempfile.gettempdir()

        file1_name = "file1.dsc"
        file1_path = os.path.join(workspace, file1_name)

        file1_data = "!include BAD_FILE.dsc"

        TestDscParserIncludes.write_to_file(file1_path, file1_data)

        parser = DscParser()
        parser.SetNoFailMode()
        parser.SetBaseAbsPath(workspace)
        parser.ParseFile(file1_path)
