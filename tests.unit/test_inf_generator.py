## @file
# UnitTest for inf_generator.py
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import tempfile
import os
import datetime
from edk2toollib.windows.capsule.inf_generator import InfGenerator, InfSection


def _get_test_file():
    return TEST_FILE_CONTENTS.replace("<DATESUB>", datetime.date.today().strftime("%m/%d/%Y"))


class InfSectionTest(unittest.TestCase):
    def test_empty(self):
        section = InfSection('TestSection')
        self.assertEqual(str(section), "[TestSection]")

    def test_single(self):
        section = InfSection("Test")
        section.Items.append("Item")
        self.assertEqual(str(section), "[Test]\nItem")

    def test_multiple(self):
        section = InfSection("Test")
        section.Items.append("Item1")
        section.Items.append("Item2")
        self.assertEqual(str(section), "[Test]\nItem1\nItem2")


class InfGeneratorTest(unittest.TestCase):
    VALID_GUID_STRING = "3cad7a0c-d35b-4b75-96b1-03a9fb07b7fc"

    def test_valid(self):
        o = InfGenerator("test_name", "provider", InfGeneratorTest.VALID_GUID_STRING, "x64",
                         "description", "aa.bb.cc.dd", "0xaabbccdd")
        self.assertIsInstance(o, InfGenerator)
        self.assertEqual(o.Name, "test_name")
        self.assertEqual(o.Provider, "provider")
        self.assertEqual(o.EsrtGuid, InfGeneratorTest.VALID_GUID_STRING)
        self.assertEqual(o.Arch, InfGenerator.SUPPORTED_ARCH["x64"])
        self.assertEqual(o.Description, "description")
        self.assertEqual(int(o.VersionHex, 0), int("0xaabbccdd", 0))
        self.assertEqual(o.VersionString, "aa.bb.cc.dd")
        self.assertEqual(o.Manufacturer, "provider")

        # loop thru all supported arch and make sure it works
        for a in InfGenerator.SUPPORTED_ARCH.keys():
            with self.subTest(Arch=a):
                o.Arch = a
                self.assertEqual(InfGenerator.SUPPORTED_ARCH[a], o.Arch)

        # set manufacturer
        o.Manufacturer = "manufacturer"
        self.assertEqual("manufacturer", o.Manufacturer)

    def test_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inffile_path = os.path.join(tmpdir, "InfFile.inf")
            infgen = InfGenerator('TestName', 'TestProvider', InfGeneratorTest.VALID_GUID_STRING,
                                  "x64", "Test Description", "1.2.3.4", "0x01020304")
            infgen.MakeInf(inffile_path, "TestFirmwareRom.bin", False)

            with open(inffile_path, "r") as inffile:
                file_contents = inffile.read()
                # Remove all whitespace, just in case.
                file_contents = file_contents.replace("\n", "").replace("\t", "").replace(" ", "")
                test_contents = _get_test_file().replace("\n", "").replace("\t", "").replace(" ", "")
                self.assertEqual(test_contents, file_contents)

    def test_integrity_file_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            inffile_path = os.path.join(tmpdir, "InfFile.inf")
            infgen = InfGenerator('TestName', 'TestProvider', InfGeneratorTest.VALID_GUID_STRING,
                                  "x64", "Test Description", "1.2.3.4", "0x01020304")
            infgen.MakeInf(inffile_path, "TestFirmwareRom.bin", False)
            with open(inffile_path, "r") as inffile:
                file_contents = inffile.read()
                self.assertNotIn("SampleIntegrityFile.bin", file_contents)
                self.assertNotIn("FirmwareIntegrityFilename", file_contents)

            infgen.IntegrityFilename = "SampleIntegrityFile.bin"
            infgen.MakeInf(inffile_path, "TestFirmwareRom.bin", False)
            with open(inffile_path, "r") as inffile:
                file_contents = inffile.read()
                self.assertIn("SampleIntegrityFile.bin", file_contents)
                self.assertIn("FirmwareIntegrityFilename", file_contents)

    def test_invalid_name_symbol(self):

        InvalidChars = ['~', '`', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', ' ', '{', '[', '}', ']', '+', '=']
        for a in InvalidChars:
            with self.subTest(name="test{}name".format(a)):
                name = "test{}name".format(a)
                with self.assertRaises(ValueError):
                    InfGenerator(name, "provider", InfGeneratorTest.VALID_GUID_STRING, "x64",
                                 "description", "aa.bb", "0xaabbccdd")

    def test_version_string_format(self):
        with self.subTest(version_string="zero ."):
            with self.assertRaises(ValueError):
                InfGenerator("test_name", "provider", InfGeneratorTest.VALID_GUID_STRING, "x64",
                             "description", "1234", "0x100000000")

        with self.subTest(version_string="> 3 ."):
            with self.assertRaises(ValueError):
                InfGenerator("test_name", "provider", InfGeneratorTest.VALID_GUID_STRING, "x64",
                             "description", "1.2.3.4.5", "0x100000000")

    def test_version_hex_too_big(self):
        with self.subTest("hex string too big"):
            with self.assertRaises(ValueError):
                InfGenerator("test_name", "provider", InfGeneratorTest.VALID_GUID_STRING, "x64",
                             "description", "aa.bb", "0x100000000")

        with self.subTest("decimal too big"):
            with self.assertRaises(ValueError):
                InfGenerator("test_name", "provider", InfGeneratorTest.VALID_GUID_STRING, "x64",
                             "description", "aa.bb", "4294967296")

    def test_version_hex_can_support_decimal(self):
        o = InfGenerator("test_name", "provider", InfGeneratorTest.VALID_GUID_STRING, "x64",
                         "description", "aa.bb.cc.dd", "12356")
        self.assertEqual(int(o.VersionHex, 0), 12356)

    def test_invalid_guid_format(self):
        with self.assertRaises(ValueError):
            InfGenerator("test_name", "provider", "NOT A VALID GUID", "x64", "description", "aa.bb", "0x1000000")


# NOTE: Below are the expected contents of a a valid INF file.
#       Some fields will need to be generated (like the date).
TEST_FILE_CONTENTS = ''';
; TestName.inf
; 1.2.3.4
; Copyright (C) 2019 Microsoft Corporation.  All Rights Reserved.
;
[Version]
Signature="$WINDOWS NT$"
Class=Firmware
ClassGuid={f2e7dd72-6468-4e36-b6f1-6488f42c1b52}
Provider=%Provider%
DriverVer=<DATESUB>,1.2.3.4
PnpLockdown=1
CatalogFile=TestName.cat

[Manufacturer]
%MfgName% = Firmware,NTamd64

[Firmware.NTamd64]
%FirmwareDesc% = Firmware_Install,UEFI\\RES_{3cad7a0c-d35b-4b75-96b1-03a9fb07b7fc}

[Firmware_Install.NT]
CopyFiles = Firmware_CopyFiles

[Firmware_CopyFiles]
TestFirmwareRom.bin

[Firmware_Install.NT.Hw]
AddReg = Firmware_AddReg

[Firmware_AddReg]
HKR,,FirmwareId,,{3cad7a0c-d35b-4b75-96b1-03a9fb07b7fc}
HKR,,FirmwareVersion,%REG_DWORD%,0x1020304
HKR,,FirmwareFilename,,%13%\\TestFirmwareRom.bin

[SourceDisksNames]
1 = %DiskName%

[SourceDisksFiles]
TestFirmwareRom.bin = 1

[DestinationDirs]
DefaultDestDir = 13

[Strings]
; localizable
Provider     = "TestProvider"
MfgName      = "TestProvider"
FirmwareDesc = "Test Description"
DiskName     = "Firmware Update"

; non-localizable
DIRID_WINDOWS = 10
REG_DWORD     = 0x00010001
'''
