## @file
# UnitTest for cat_generator.py based on various architecture/OS
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import os
import unittest
from edk2toollib.windows.capsule.cat_generator import CatGenerator


class CatGeneratorTest(unittest.TestCase):
    def test_win10_OS(self):
        o = CatGenerator("x64", "win10")
        self.assertEqual(o.OperatingSystem, "10")

    def test_10_OS(self):
        o = CatGenerator("x64", "10")
        self.assertEqual(o.OperatingSystem, "10")

    def test_10_AU_OS(self):
        o = CatGenerator("x64", "10_AU")
        self.assertEqual(o.OperatingSystem, "10_AU")

    def test_10_RS2_OS(self):
        o = CatGenerator("x64", "10_RS2")
        self.assertEqual(o.OperatingSystem, "10_RS2")

    def test_10_RS3_OS(self):
        o = CatGenerator("x64", "10_RS3")
        self.assertEqual(o.OperatingSystem, "10_RS3")

    def test_10_RS4_OS(self):
        o = CatGenerator("x64", "10_RS4")
        self.assertEqual(o.OperatingSystem, "10_RS4")

    def test_10_RS5_OS(self):
        o = CatGenerator("x64", "10_RS5")
        self.assertEqual(o.OperatingSystem, "10_RS5")

    def test_10_19H1_OS(self):
        o = CatGenerator("x64", "10_19H1")
        self.assertEqual(o.OperatingSystem, "10_19H1")

    def test_10_VB_OS(self):
        o = CatGenerator("x64", "10_VB")
        self.assertEqual(o.OperatingSystem, "10_VB")

    def test_10_CO_OS(self):
        o = CatGenerator("x64", "10_CO")
        self.assertEqual(o.OperatingSystem, "10_CO")

    def test_10_NI_OS(self):
        o = CatGenerator("x64", "10_NI")
        self.assertEqual(o.OperatingSystem, "10_NI")

    def test_win10Server_OS(self):
        o = CatGenerator("x64", "Server10")
        self.assertEqual(o.OperatingSystem, "Server10")

    def test_Server2016_OS(self):
        o = CatGenerator("x64", "Server2016")
        self.assertEqual(o.OperatingSystem, "Server2016")

    def test_ServerRS2_OS(self):
        o = CatGenerator("x64", "ServerRS2")
        self.assertEqual(o.OperatingSystem, "ServerRS2")

    def test_ServerRS3_OS(self):
        o = CatGenerator("x64", "ServerRS3")
        self.assertEqual(o.OperatingSystem, "ServerRS3")

    def test_ServerRS4_OS(self):
        o = CatGenerator("x64", "ServerRS4")
        self.assertEqual(o.OperatingSystem, "ServerRS4")

    def test_invalid_OS(self):
        with self.assertRaises(ValueError):
            CatGenerator("x64", "Invalid Junk")

    def test_x64_arch(self):
        o = CatGenerator("x64", "win10")
        self.assertEqual(o.Arch, "X64")

    def test_amd64_arch(self):
        o = CatGenerator("amd64", "win10")
        self.assertEqual(o.Arch, "X64")

    def test_arm_arch(self):
        o = CatGenerator("arm", "win10")
        self.assertEqual(o.Arch, "ARM")

    def test_arm64_arch(self):
        o = CatGenerator("arm64", "win10")
        self.assertEqual(o.Arch, "ARM64")

    def test_aarch64_arch(self):
        o = CatGenerator("aarch64", "win10")
        self.assertEqual(o.Arch, "ARM64")

    def test_invalid_arch(self):
        with self.assertRaises(ValueError):
            CatGenerator("Invalid Arch", "win10")

    def test_invalid_path_to_tool(self):
        o = CatGenerator("amd64", "10")
        with self.assertRaises(Exception) as cm:
            o.MakeCat("garbage", os.path.join("c:", "test", "badpath", "inf2cat.exe"))
        self.assertTrue(str(cm.exception).startswith("Can't find Inf2Cat on this machine."))
