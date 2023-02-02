# @file utility_functions_test.py
# unit test for utility_functions module.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import io
import os
import sys
import edk2toollib.utility_functions as utilities


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


class EnumClassTest(unittest.TestCase):
    def test_EnumClass_array(self):
        all_animals = ["Dog", "Cat", "Rabbit"]
        animals = utilities.Enum(all_animals)

        # make sure we have three animals
        self.assertEqual(len(animals), 3)
        self.assertTrue(hasattr(animals, "Dog"))
        self.assertFalse(hasattr(animals, "Rat"))
        self.assertFalse(hasattr(animals, "dog"))
        # check to make sure the values are unique
        self.assertNotEqual(animals.Dog, animals.Cat)

        # make sure we can iterate over the members
        for animal in animals.__members__:
            self.assertIn(animal, all_animals)

    def test_EnumClass_args(self):
        colors = utilities.Enum("Green", "Blue", "Red", "Yellow")
        # make sure we have four colors
        self.assertEqual(len(colors), 4)
        self.assertTrue(hasattr(colors, "Red"))
        self.assertFalse(hasattr(colors, "Purple"))
        # check to make sure the values are unique
        self.assertNotEqual(colors.Green, colors.Red)


class ExportCTypeArrayTest(unittest.TestCase):
    """Tests export_c_type_array"""

    def test_export_c_type_array_basic_usage(self):
        """Basic Usage Test"""
        test = io.BytesIO(b"Hello UEFI!")
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[] = {{{newline}"  # noqa
        expected_output += f"    0x48, 0x65, 0x6c, 0x6c, 0x6f, 0x20, 0x55, 0x45, 0x46, 0x49, 0x21                                 // Hello UEFI! {newline}"  # noqa
        expected_output += f"}};{newline*2}"
        expected_output += f"UINTN TestVariableLength = sizeof TestVariable;{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output)

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_16_bytes(self):
        """Basic 16 byte Test"""
        test = io.BytesIO(b"0123456789abcdef")
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[] = {{{newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66   // 0123456789abcdef {newline}"  # noqa
        expected_output += f"}};{newline*2}"
        expected_output += f"UINTN TestVariableLength = sizeof TestVariable;{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output)

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_32_bytes(self):
        """Basic 32 byte Test"""
        test = io.BytesIO(b"0123456789abcdef0123456789abcdef")
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[] = {{{newline}" # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66,  // 0123456789abcdef {newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66   // 0123456789abcdef {newline}"  # noqa
        expected_output += f"}};{newline*2}"
        expected_output += f"UINTN TestVariableLength = sizeof TestVariable;{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output)

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_33_bytes(self):
        """Basic 32 byte Test"""
        test = io.BytesIO(b"0123456789abcdef0123456789abcdef0")
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[] = {{{newline}" # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66,  // 0123456789abcdef {newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66,  // 0123456789abcdef {newline}"  # noqa
        expected_output += f"    0x30                                                                                             // 0 {newline}"  # noqa
        expected_output += f"}};{newline*2}"
        expected_output += f"UINTN TestVariableLength = sizeof TestVariable;{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output)

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_32_bytes_and_line_cont(self):
        """Basic line continuation Test"""
        test = io.BytesIO(b"0123456789abcde\\0123456789abcde\\")
        output = io.StringIO()

        newline = '\n'

        expected_output =  f"UINT8 TestVariable[] = {{{newline}" # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x5c,  // 0123456789abcde\\ {newline}"  # noqa
        expected_output += f"    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x61, 0x62, 0x63, 0x64, 0x65, 0x5c   // 0123456789abcde\\ {newline}"  # noqa
        expected_output += f"}};{newline*2}"
        expected_output += f"UINTN TestVariableLength = sizeof TestVariable;{newline*2}"

        utilities.export_c_type_array(test, "TestVariable", output)

        self.assertEqual(expected_output, output.getvalue())

    def test_export_c_type_array_empty(self):
        """Ensure exception is raised if the array is length 0"""
        binary_data = io.BytesIO(b"")
        output = io.StringIO()

        with self.assertRaises(ValueError):
            utilities.export_c_type_array(binary_data, "TestVariable", output)

# DO NOT PUT A MAIN FUNCTION HERE
# this test runs itself to test runpython script, which is a tad bit strange yes.
