# @file locate_tools_test.py
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
import edk2toollib.windows.locate_tools as locate_tools


class LocateToolsTest(unittest.TestCase):

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_GetVsWherePath(self):
        # Gets VSWhere
        old_vs_path = locate_tools.GetVsWherePath()
        os.remove(old_vs_path)
        self.assertFalse(os.path.isfile(old_vs_path), "This should be deleted")
        vs_path = locate_tools.GetVsWherePath()
        self.assertTrue(os.path.isfile(vs_path), "This should be back")

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_FindWithVsWhere(self):
        # Finds something with VSWhere
        star_prod = locate_tools.FindWithVsWhere()
        self.assertNotEqual(star_prod, None, "We should have found this product")
        bad_prod = locate_tools.FindWithVsWhere("bad_prod")
        self.assertEqual(bad_prod, None, "We should not have found this product")

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_FindwithVsWhereVs2017(self):
        locate_tools.FindWithVsWhere(vs_version="vs2017")
        # not checking the result as no need to depend on machine state

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_FindwithVsWhereVs2019(self):
        locate_tools.FindWithVsWhere(vs_version="vs2019")
        # not checking the result as no need to depend on machine state

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_FindwithVsWhereVs2022(self):
        locate_tools.FindWithVsWhere(vs_version="vs2022")
        # not checking the result as no need to depend on machine state

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_FindWithVsWhereVs2015(self):
        with self.assertRaises(ValueError):
            locate_tools.FindWithVsWhere(vs_version="vs2015")

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_FindWithVsWhereUnsupported(self):
        with self.assertRaises(ValueError):
            locate_tools.FindWithVsWhere(vs_version="vs4096")

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_QueryVcVariables(self):
        keys = ["VCINSTALLDIR", "WindowsSDKVersion"]
        try:
            results = locate_tools.QueryVcVariables(keys)
        except ValueError:
            self.fail("We shouldn't assert in the QueryVcVariables")

        self.assertIsNotNone(results["VCINSTALLDIR"])
        self.assertIsNotNone(results["WindowsSDKVersion"])

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_FindInf2CatToolInWinSdk(self):
        results = locate_tools.FindToolInWinSdk("inf2cat.exe")
        self.assertIsNotNone(results)
        self.assertTrue(os.path.isfile(results))

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_FindToolInWinSdk(self):
        results = locate_tools.FindToolInWinSdk("signtool.exe")
        self.assertIsNotNone(results)
        self.assertTrue(os.path.isfile(results))

        results = locate_tools.FindToolInWinSdk("this_tool_should_never_exist.exe")
        self.assertIsNone(results)

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_QueryVcVariablesWithNoValidProduct(self):
        keys = ["VCINSTALLDIR", "WindowsSDKVersion"]
        with self.assertRaises(ValueError):
            locate_tools.QueryVcVariables(keys, product="YouWontFindThis")

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_QueryVcVariablesWithVariableNotFound(self):
        keys = ["YouWontFindMe", "WindowsSDKVersion"]
        with self.assertRaises(ValueError):
            locate_tools.QueryVcVariables(keys)

    @unittest.skipUnless(sys.platform.startswith("win"), "requires Windows")
    def test_FindToolInWinSdkWithNoValidProduct(self):
        results = locate_tools.FindToolInWinSdk("WontFind.exe", product="YouWontFindThis")
        self.assertIsNone(results)
