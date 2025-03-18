# @file locate_tools_test.py
# unit test for locate_tools module.  Only runs on Windows machines.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import pytest
import logging
import sys
import os
import edk2toollib.windows.locate_tools as locate_tools
from unittest.mock import patch


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
    @patch("edk2toollib.windows.locate_tools.QueryVcVariables")
    @patch("glob.iglob")
    def test_FindInf2CatToolInWinSdk(self, mock_iglob, mock_QueryVcVariables):
        # Mock dependencies to otherwise exercise the `FindToolInWinSdk`
        # function
        mock_QueryVcVariables.return_value = {"WindowsSdkDir": "C:/mock/sdk/dir", "WindowsSDKVersion": "10.0.12345.0"}
        mock_iglob.return_value = ["C:/mock/sdk/dir/10.0.12345.0/bin/x64/inf2cat.exe"]

        results = locate_tools.FindToolInWinSdk("inf2cat.exe")
        self.assertIsNotNone(results)

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


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="requires Windows")
def test_QueryVcVariablesWithLargePathEnv(caplog):
    """Tests QueryVcVariables with a PATH Env over 8191 characters.

    When calling a .bat file, the environment is passed in, however any environment variable greater
    than 8191 is quietly ignored. This can sometimes happen with the PATH variable, but we almost
    always need the PATH env variable when querying VcVariables, so we want to warn when the user
    when this happens.
    """
    with caplog.at_level(logging.WARNING):
        keys = ["WindowsSDKVersion"]
        locate_tools.QueryVcVariables(keys)
        assert (len(caplog.records)) == 0

        old_env = os.environ

        os.environ["PATH"] += "TEST;" * 1640  # Makes path over 8191 characters
        locate_tools.QueryVcVariables(keys)
        assert (len(caplog.records)) == 1

        os.environ = old_env


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="requires Windows")
def test_QueryVcVariablesWithLargEnv(caplog):
    """Tests QueryVcVariables when the entire Env is over 8191 character.

    calling a command on the cmd is limited to 8191 characters. The enviornment is counted in this limit. When the
    character limit is reached, the command simply errors out. Windows tries to fix this by not including any
    environment over 8191 characters (as seen in the test above), but when no individual environment variable is over
    8191 characters, but the to total enviornment is, the command will fail.
    """
    keys = ["WindowsSdkDir", "WindowsSDKVersion"]
    old_env = os.environ

    os.environ["PATH"] = "TEST;" * 1630  # Get close, but don't go over 8191 characters
    with pytest.raises(RuntimeError):
        locate_tools.QueryVcVariables(keys)

    os.environ = old_env


@pytest.mark.skipif(not sys.platform.startswith("win"), reason="requires Windows")
def test_QueryVcVariablesWithSpecificVc():
    """Tests QueryVcVariables with a specific VC version.

    This test will check that the function can query a specific VC version.
    """
    lookup = locate_tools.QueryVcVariables(["VCINSTALLDIR", "WindowsSDKVersion"])
    assert "VCINSTALLDIR" in lookup
    assert "WindowsSDKVersion" in lookup

    # Fail to complete the lookup because the vc_version does not exist
    try:
        lookup = locate_tools.QueryVcVariables(["VCINSTALLDIR", "WindowsSDKVersion"], vc_version="9.9.9")
    except ValueError as e:
        assert str(e).startswith("Missing keys when querying vcvarsall")
        lookup = None

    assert lookup is None
