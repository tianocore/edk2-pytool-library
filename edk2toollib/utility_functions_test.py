# @file utility_functions_test.py
# unit test for utility_functions module.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import os
import sys
import edk2toollib.utility_functions as utilities
import time


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

    did_custom_target = False

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

    def test_run_cmd(self):
        cmd = "echo"
        args = '"Hello there"'
        ret = utilities.RunCmd(cmd, args)
        self.assertEqual(ret, 0)

    def test_run_cmd_with_bad_cmd(self):
        ret = utilities.RunCmd("not_a_real_command", "")
        self.assertNotEqual(ret, 0)

    def test_run_cmd_raise_exception_on_nonzero(self):
        with self.assertRaises(Exception):
            utilities.RunCmd("not_a_real_command", "", raise_exception_on_nonzero=True)

    def test_run_cmd_with_custom_target(self):
        cmd = "echo"
        args = '"Hello there"'

        self.did_custom_target = False

        def custom_target(*unused):
            self.did_custom_target = True

        ret = utilities.RunCmd(cmd, args, thread_target=custom_target)
        self.assertEqual(ret, 0)
        self.assertTrue(self.did_custom_target)

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_run_cmd_with_breaking_target(self):

        timeout_time = 10
        kill_time = 5

        def custom_target_break(filepath, outstream, stream, *unused):
            expirer_time = time.time() + kill_time
            while True:
                if time.time() > expirer_time:
                    break
                time.sleep(1)
            stream.close()
            return 0
        # Keep track of when we start
        start_time = time.time()
        ret = utilities.RunCmd("timeout", f"{timeout_time}", thread_target=custom_target_break)
        # make sure our elapsed time is less than our kill time + 1 (for wiggle room)
        self.assertLess(time.time() - start_time, kill_time + 1)

        # this time without the custom target
        timeout_time = 10
        start_time = time.time()
        ret = utilities.RunCmd("timeout", f"{timeout_time}", capture=False, thread_target=custom_target_break)
        # make sure our elapsed time is more than the timeout (minus some wiggle room)
        self.assertGreater(time.time() - start_time, timeout_time - 1)
        self.assertEqual(ret, 0)


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


# DO NOT PUT A MAIN FUNCTION HERE
# this test runs itself to test runpython script, which is a tad bit strange yes.
test = UtilityFunctionsTest()
test.test_run_cmd()
test.test_run_cmd_with_breaking_target()
test.test_run_cmd_raise_exception_on_nonzero()
