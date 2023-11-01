# @file utility_functions_test.py
# unit test for utility_functions module.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import io
import os
import sys
import unittest

import edk2toollib.utility_functions as utilities
import pytest


class DesiredClass():
    def __str__(self):
        return "DesiredClass"


class ChildOfDesiredClass(DesiredClass):
    def __str__(self):
        return "Child of DesiredClass"


class GrandChildOfDesiredClass(ChildOfDesiredClass):
    def __str__(self):
        return "GrandChild of DesiredClass"


'''
The current solution can't handle a brother class
class BrotherOfChildOfDesiredClass(DesiredClass):
    def __str__(self):
        return "Brother of Child of DesiredClass"
'''


class UtilityFunctionsTest(unittest.TestCase):

    def test_RunPythonScript(self):  # simple- run yourself!
        path = __file__
        working_dir = os.path.dirname(__file__)
        ret = utilities.RunPythonScript(path, "", working_dir)
        self.assertEqual(ret, 0)
        # test it with all the named parameters
        ret = utilities.RunPythonScript(path, "", capture=False, workingdir=working_dir,
                                        raise_exception_on_nonzero=True)
        self.assertEqual(ret, 0)
        # now try a bad path
        bad_path = __file__ + ".super.bad"
        ret = utilities.RunPythonScript(bad_path, "", capture=False, workingdir=None, raise_exception_on_nonzero=False)
        self.assertNotEqual(ret, 0)
        # now we expect it to throw an exception
        with self.assertRaises(Exception):
            ret = utilities.RunPythonScript(bad_path, "", capture=False, workingdir=None,
                                            raise_exception_on_nonzero=True)
            self.assertNotEqual(ret, 0)

    def test_locate_class_in_module(self):
        module = sys.modules[__name__]

        found_class = utilities.locate_class_in_module(module, DesiredClass)
        self.assertIsNotNone(found_class)
        self.assertEqual(found_class, GrandChildOfDesiredClass)


class HexdumpTest(unittest.TestCase):
    """Tests hexdump."""

    def test_hexdump_basic_usage(self):
        """Basic Usage Test."""
        test = b"Hello UEFI!"
        output = io.StringIO()

        newline = '\n'
        expected_output = f"0x00 - 0x48 0x65 0x6c 0x6c 0x6f 0x20 0x55 0x45 - 0x46 0x49 0x21                          Hello UEFI! {newline}" # noqa
        utilities.hexdump(test, outfs=output)
        self.assertEqual(expected_output, output.getvalue())

    def test_hexdump_basic_usage_offset_start(self):
        """Basic Usage Test."""
        test = b"Hello UEFI!"
        output = io.StringIO()

        newline = '\n'
        expected_output = f"0x40000000 - 0x48 0x65 0x6c 0x6c 0x6f 0x20 0x55 0x45 - 0x46 0x49 0x21                          Hello UEFI! {newline}" # noqa
        utilities.hexdump(test, offset_start=0x4000_0000, outfs=output)

        self.assertEqual(expected_output, output.getvalue())

    def test_hexdump_basic_usage_16_bytes(self):
        """Basic 16 byte Test."""
        test = b"0123456789abcdef"
        output = io.StringIO()

        newline = '\n'

        expected_output = f"0x00 - 0x30 0x31 0x32 0x33 0x34 0x35 0x36 0x37 - 0x38 0x39 0x61 0x62 0x63 0x64 0x65 0x66 0123456789abcdef {newline}" # noqa

        utilities.hexdump(test, outfs=output)

        self.assertEqual(expected_output, output.getvalue())

    def test_hexdump_basic_usage_32_bytes(self):
        """Basic 32 byte Test."""
        test = b"0123456789abcdef0123456789abcdef"
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"0x40000000 - 0x30 0x31 0x32 0x33 0x34 0x35 0x36 0x37 - 0x38 0x39 0x61 0x62 0x63 0x64 0x65 0x66 0123456789abcdef {newline}" # noqa
        expected_output += f"0x40000010 - 0x30 0x31 0x32 0x33 0x34 0x35 0x36 0x37 - 0x38 0x39 0x61 0x62 0x63 0x64 0x65 0x66 0123456789abcdef {newline}" # noqa

        utilities.hexdump(test, offset_start=0x4000_0000, outfs=output)

        self.assertEqual(expected_output, output.getvalue())

    def test_hexdump_basic_usage_33_bytes(self):
        """Basic 32 byte Test."""
        test = b"0123456789abcdef0123456789abcdef0"
        output = io.StringIO()

        newline = '\n'
        expected_output =  f"0x00 - 0x30 0x31 0x32 0x33 0x34 0x35 0x36 0x37 - 0x38 0x39 0x61 0x62 0x63 0x64 0x65 0x66 0123456789abcdef {newline}" # noqa
        expected_output += f"0x10 - 0x30 0x31 0x32 0x33 0x34 0x35 0x36 0x37 - 0x38 0x39 0x61 0x62 0x63 0x64 0x65 0x66 0123456789abcdef {newline}" # noqa
        expected_output += f"0x20 - 0x30                                                                              0 {newline}" # noqa

        utilities.hexdump(test, outfs=output)

        self.assertEqual(expected_output, output.getvalue())

    def test_hexdump_basic_usage_32_bytes_and_line_cont(self):
        """Basic line continuation Test."""
        test = b"0123456789abcde\\0123456789abcde\\"
        output = io.StringIO()

        newline = '\n'
        expected_output =  f"0x00 - 0x30 0x31 0x32 0x33 0x34 0x35 0x36 0x37 - 0x38 0x39 0x61 0x62 0x63 0x64 0x65 0x5c 0123456789abcde\\ {newline}" # noqa
        expected_output += f"0x10 - 0x30 0x31 0x32 0x33 0x34 0x35 0x36 0x37 - 0x38 0x39 0x61 0x62 0x63 0x64 0x65 0x5c 0123456789abcde\\ {newline}" # noqa

        utilities.hexdump(test, outfs=output)

        self.assertEqual(expected_output, output.getvalue())

    def test_hexdump_basic_usage_empty(self):
        """Ensures empty response."""
        test = io.BytesIO(b"")
        output = io.StringIO()
        newline = '\n'

        expected_output = f"{newline}"

        utilities.hexdump(test, outfs=output)

        self.assertEqual(expected_output, output.getvalue())


class ExportCTypeArrayTest(unittest.TestCase):
    """Tests export_c_type_array."""

    def test_export_c_type_array_basic_usage(self):
        """Basic Usage Test."""
        original_bytes = b"Hello UEFI!"
        length = len(original_bytes)
        test = io.BytesIO(original_bytes)
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[{length}] = {{{newline}"  # noqa
        expected_output += f"    0x48, 0x65, 0x6c, 0x6c, 0x6f, 0x20, 0x55, 0x45, 0x46, 0x49, 0x21                                 // Hello UEFI! {newline}"  # noqa
        expected_output += f"}};{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output)

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_include_length_variable(self):
        """Basic Usage Test."""
        original_bytes = b"Hello UEFI!"
        length = len(original_bytes)
        test = io.BytesIO(original_bytes)
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[{length}] = {{{newline}"  # noqa
        expected_output += f"    0x48, 0x65, 0x6c, 0x6c, 0x6f, 0x20, 0x55, 0x45, 0x46, 0x49, 0x21                                 // Hello UEFI! {newline}"  # noqa
        expected_output += f"}};{newline*2}"
        expected_output += f"UINTN TestVariableLength = sizeof TestVariable;{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output, length_variable_name="TestVariableLength")

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_16_bytes(self):
        """Basic 16 byte Test."""
        original_bytes = b"0123456789abcdef"
        length = len(original_bytes)
        test = io.BytesIO(original_bytes)
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[{length}] = {{{newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66   // 0123456789abcdef {newline}"  # noqa
        expected_output += f"}};{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output)

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_32_bytes(self):
        """Basic 32 byte Test."""
        original_bytes = b"0123456789abcdef0123456789abcdef"
        length = len(original_bytes)
        test = io.BytesIO(original_bytes)
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[{length}] = {{{newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66,  // 0123456789abcdef {newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66   // 0123456789abcdef {newline}"  # noqa
        expected_output += f"}};{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output)

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_33_bytes(self):
        """Basic 32 byte Test."""
        original_bytes = b"0123456789abcdef0123456789abcdef0"
        length = len(original_bytes)
        test = io.BytesIO(original_bytes)
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[{length}] = {{{newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66,  // 0123456789abcdef {newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66,  // 0123456789abcdef {newline}"  # noqa
        expected_output += f"    0x30                                                                                             // 0 {newline}"  # noqa
        expected_output += f"}};{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output)

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_32_bytes_and_line_cont(self):
        """Basic line continuation Test."""
        original_bytes = b"0123456789abcde\\0123456789abcde\\"
        length = len(original_bytes)
        test = io.BytesIO(original_bytes)
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[{length}] = {{{newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x5c,  // 0123456789abcde\\ {newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x5c   // 0123456789abcde\\ {newline}"  # noqa
        expected_output += f"}};{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output)

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_empty(self):
        """Ensure exception is raised if the array is length 0."""
        binary_data = io.BytesIO(b"")
        output = io.StringIO()

        with self.assertRaises(ValueError):
            utilities.export_c_type_array(binary_data, "TestVariable", output)

class TestRemoveTree:
    """Tests the RemoveTree function."""
    pytest.mark.skipif(not sys.platform.startswith('win'), reason="Long Paths are only an issue on Windows")
    def test_long_path_remove_tree(self, tmp_path):
        """Tests RemoveTree's ability to remove a directory on a Windows System with LongPaths Disabled."""
        import winreg

        sub_key = r"SYSTEM\CurrentControlSet\Control\FileSystem"
        value_name = "LongPathsEnabled"

        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_key)
        value, _ = winreg.QueryValueEx(key, value_name)
        if value == 1:
            pytest.skip(r"Long paths are enabled. To run the test, disable long paths with the registry key located at: HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystemLongPathsEnabled")  # noqa: E501

        long_path = str(tmp_path / ("a" * 250)) # A single folder cannot be longer than 260 characters.
        assert len(str(long_path)) > 260 # Make sure the path is actually long.

        # Must use the \\?\ prefix to be able to create a long path when Long Paths are disabled.
        os.mkdir('\\\\?\\' + long_path)
        with open('\\\\?\\' + long_path + "\\file.txt", "w") as f:
            f.write("Hello World!")

        utilities.RemoveTree(long_path)

# DO NOT PUT A MAIN FUNCTION HERE
# this test runs itself to test runpython script, which is a tad bit strange yes.
