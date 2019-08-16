# @file utility_functions_test.py
# unit test for locate_tools module.  Only runs on Windows machines.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import sys
import os
import edk2toollib.utility_functions as utilities


class UtilityFunctionsTest(unittest.TestCase):

    def test_RunPythonScript(self): # simple run yourself!
        path = __file__
        working_dir = os.path.dirname(__file__)
        utilities.RunPythonScript(path, "", working_dir)

# DO NOT PUT A MAIN FUNCTION HERE
#  this test runs itself to test runpython script, which is a tad bit strange yes.