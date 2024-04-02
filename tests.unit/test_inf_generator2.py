## @file
# UnitTest for inf_generator.py
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import textwrap
import unittest

from edk2toollib.windows.capsule.inf_generator2 import (
    InfFile,
    InfFirmware,
    InfFirmwareSections,
    InfHeader,
    InfSourceFiles,
    InfStrings,
    OS_BUILD_VERSION_DIRID13_SUPPORT
)

class InfHeaderTest(unittest.TestCase):
    def test_header(self):
        Strings = InfStrings()
        Header = InfHeader("InfTest", "1.0.0.1", "01/01/2021", "amd64", "testprovider", "testmfr", Strings)

        ExpectedStr = textwrap.dedent(f"""\
            ;
            ; InfTest
            ; 1.0.0.1
            ; Copyright (C) Microsoft Corporation. All Rights Reserved.
            ;
            [Version]
            Signature="$WINDOWS NT$"
            Class=Firmware
            ClassGuid={{f2e7dd72-6468-4e36-b6f1-6488f42c1b52}}
            Provider=%Provider%
            DriverVer=01/01/2021,1.0.0.1
            PnpLockdown=1
            CatalogFile=InfTest.cat

            [Manufacturer]
            %MfgName% = Firmware,NTamd64.{OS_BUILD_VERSION_DIRID13_SUPPORT}

            """)
        self.assertEqual(ExpectedStr, str(Header))
        self.assertIn("Provider", Strings.LocalizableStrings)
        self.assertEqual("testprovider", Strings.LocalizableStrings['Provider'])
        self.assertIn("MfgName", Strings.LocalizableStrings)
        self.assertEqual("testmfr", Strings.LocalizableStrings['MfgName'])

    def test_header_should_throw_for_bad_input(self):
        Strings = InfStrings()

        with self.assertRaises(ValueError):
            InfHeader("InfTest ?? bad", "1.0.0.1", "01/01/2021", "amd64", "testprovider", "testmfr", Strings)

        with self.assertRaises(ValueError):
            InfHeader("InfTest", "this is not good", "01/01/2021", "amd64", "testprovider", "testmfr", Strings)

        with self.assertRaises(ValueError):
            InfHeader("InfTest", "1.0.0.1", "foobar", "amd64", "testprovider", "testmfr", Strings)

        with self.assertRaises(ValueError):
            InfHeader("InfTest", "1.0.0.1", "01/01/2021", "foobar", "testprovider", "testmfr", Strings)

        with self.assertRaises(TypeError):
            InfHeader(1, "1.0.0.1", "01/01/2021", "amd64", "testprovider", "testmfr", Strings)

        with self.assertRaises(AttributeError):
            InfHeader("InfTest", "1.0.0.1", "01/01/2021", "amd64", "testprovider", "testmfr", None)


class InfFirmwareTest(unittest.TestCase):
    def test_firmware(self):
        Strings = InfStrings()
        SourceFiles = InfSourceFiles("diskname", Strings)

        Firmware = InfFirmware(
            "tag",
            "desc",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test.bin",
            Strings,
            SourceFiles)

        ExpectedStr = textwrap.dedent("""\
            [tag_Install.NT]
            CopyFiles = tag_CopyFiles

            [tag_CopyFiles]
            test.bin

            [tag_Install.NT.Services]
            AddService=,2

            [tag_Install.NT.Hw]
            AddReg = tag_AddReg

            [tag_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,%13%\\test.bin

            """)

        self.assertEqual(ExpectedStr, str(Firmware))
        self.assertEqual(Firmware.Description, "desc")
        self.assertIn("REG_DWORD", Strings.NonLocalizableStrings)
        self.assertEqual("0x00010001", Strings.NonLocalizableStrings['REG_DWORD'])
        self.assertIn("test.bin", SourceFiles.Files)

    def test_rollback_firmware(self):
        Strings = InfStrings()
        SourceFiles = InfSourceFiles("diskname", Strings)

        Firmware = InfFirmware(
            "tag",
            "desc",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test.bin",
            Strings,
            SourceFiles,
            Rollback=True)

        ExpectedStr = textwrap.dedent("""\
            [tag_Install.NT]
            CopyFiles = tag_CopyFiles
            AddReg = tag_DowngradePolicy_AddReg

            [tag_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{34e094e9-4079-44cd-9450-3f2cb7824c97},Policy,%REG_DWORD%,1

            [tag_CopyFiles]
            test.bin

            [tag_Install.NT.Services]
            AddService=,2

            [tag_Install.NT.Hw]
            AddReg = tag_AddReg

            [tag_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,%13%\\test.bin

            """)

        self.assertEqual(ExpectedStr, str(Firmware))
        self.assertEqual(Firmware.Description, "desc")
        self.assertIn("REG_DWORD", Strings.NonLocalizableStrings)
        self.assertEqual("0x00010001", Strings.NonLocalizableStrings['REG_DWORD'])
        self.assertIn("test.bin", SourceFiles.Files)

    def test_rollback_firmware_integrity(self):
        Strings = InfStrings()
        SourceFiles = InfSourceFiles("diskname", Strings)

        Firmware = InfFirmware(
            "tag",
            "desc",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test.bin",
            Strings,
            SourceFiles,
            Rollback=True,
            IntegrityFile="test2.bin")

        ExpectedStr = textwrap.dedent("""\
            [tag_Install.NT]
            CopyFiles = tag_CopyFiles
            AddReg = tag_DowngradePolicy_AddReg

            [tag_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{34e094e9-4079-44cd-9450-3f2cb7824c97},Policy,%REG_DWORD%,1

            [tag_CopyFiles]
            test.bin
            test2.bin

            [tag_Install.NT.Services]
            AddService=,2

            [tag_Install.NT.Hw]
            AddReg = tag_AddReg

            [tag_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,%13%\\test.bin
            HKR,,FirmwareIntegrityFilename,,%13%\\test2.bin

            """)

        self.assertEqual(ExpectedStr, str(Firmware))
        self.assertEqual(Firmware.Description, "desc")
        self.assertIn("REG_DWORD", Strings.NonLocalizableStrings)
        self.assertEqual("0x00010001", Strings.NonLocalizableStrings['REG_DWORD'])
        self.assertIn("test.bin", SourceFiles.Files)
        self.assertIn("test2.bin", SourceFiles.Files)

    def test_firmware_should_throw_for_bad_input(self):
        Strings = InfStrings()
        SourceFiles = InfSourceFiles("diskname", Strings)

        with self.assertRaises(ValueError):
            InfFirmware(
                "This is not a valid tag name",
                "desc",
                "34e094e9-4079-44cd-9450-3f2cb7824c97",
                "0x01000001",
                "test.bin",
                Strings,
                SourceFiles,
                Rollback=True,
                IntegrityFile="test2.bin")

        with self.assertRaises(ValueError):
            InfFirmware(
                "Tag",
                "desc",
                "This is not a valid UUID.",
                "0x01000001",
                "test.bin",
                Strings,
                SourceFiles,
                Rollback=True,
                IntegrityFile="test2.bin")

        with self.assertRaises(ValueError):
            InfFirmware(
                "Tag",
                "desc",
                "4e094e9-4079-44cd-9450-3f2cb7824c97",  # a more subtle not-valid UUID.
                "0x01000001",
                "test.bin",
                Strings,
                SourceFiles,
                Rollback=True,
                IntegrityFile="test2.bin")

        with self.assertRaises(ValueError):
            InfFirmware(
                "tag",
                "desc",
                "34e094e9-4079-44cd-9450-3f2cb7824c97",
                "foobar",
                "test.bin",
                Strings,
                SourceFiles,
                Rollback=True,
                IntegrityFile="test2.bin")


class InfFirmwareSectionsTest(unittest.TestCase):
    def test_one_section(self):
        Strings = InfStrings()
        SourceFiles = InfSourceFiles("diskname", Strings)

        Firmware = InfFirmware(
            "tag",
            "desc",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test.bin",
            Strings,
            SourceFiles)

        Sections = InfFirmwareSections('amd64', Strings)
        Sections.AddSection(Firmware)

        ExpectedStr = textwrap.dedent(f"""\
            [Firmware.NTamd64.{OS_BUILD_VERSION_DIRID13_SUPPORT}]
            %tagDesc% = tag_Install,UEFI\\RES_{{34e094e9-4079-44cd-9450-3f2cb7824c97}}

            [tag_Install.NT]
            CopyFiles = tag_CopyFiles

            [tag_CopyFiles]
            test.bin

            [tag_Install.NT.Services]
            AddService=,2

            [tag_Install.NT.Hw]
            AddReg = tag_AddReg

            [tag_AddReg]
            HKR,,FirmwareId,,{{34e094e9-4079-44cd-9450-3f2cb7824c97}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,%13%\\test.bin

            """)

        self.assertEqual(ExpectedStr, str(Sections))
        self.assertIn("tagDesc", Strings.LocalizableStrings)
        self.assertEqual("desc", Strings.LocalizableStrings['tagDesc'])
        self.assertIn("test.bin", SourceFiles.Files)

        self.assertIn("REG_DWORD", Strings.NonLocalizableStrings)
        self.assertEqual("0x00010001", Strings.NonLocalizableStrings['REG_DWORD'])

    def test_two_sections(self):
        self.maxDiff = None
        Strings = InfStrings()
        SourceFiles = InfSourceFiles("diskname", Strings)

        Firmware1 = InfFirmware(
            "tag1",
            "desc1",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test1.bin",
            Strings,
            SourceFiles)

        Firmware2 = InfFirmware(
            "tag2",
            "desc2",
            "bec9124f-9934-4ec0-a6ed-b8bc1c91d276",
            "0x01000002",
            "test2.bin",
            Strings,
            SourceFiles)

        Sections = InfFirmwareSections('amd64', Strings)
        Sections.AddSection(Firmware1)
        Sections.AddSection(Firmware2)

        ExpectedStr = textwrap.dedent(f"""\
            [Firmware.NTamd64.{OS_BUILD_VERSION_DIRID13_SUPPORT}]
            %tag1Desc% = tag1_Install,UEFI\\RES_{{34e094e9-4079-44cd-9450-3f2cb7824c97}}
            %tag2Desc% = tag2_Install,UEFI\\RES_{{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}}

            [tag1_Install.NT]
            CopyFiles = tag1_CopyFiles

            [tag1_CopyFiles]
            test1.bin

            [tag1_Install.NT.Services]
            AddService=,2

            [tag1_Install.NT.Hw]
            AddReg = tag1_AddReg

            [tag1_AddReg]
            HKR,,FirmwareId,,{{34e094e9-4079-44cd-9450-3f2cb7824c97}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,%13%\\test1.bin

            [tag2_Install.NT]
            CopyFiles = tag2_CopyFiles

            [tag2_CopyFiles]
            test2.bin

            [tag2_Install.NT.Services]
            AddService=,2

            [tag2_Install.NT.Hw]
            AddReg = tag2_AddReg

            [tag2_AddReg]
            HKR,,FirmwareId,,{{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000002
            HKR,,FirmwareFilename,,%13%\\test2.bin

            """)

        self.assertEqual(ExpectedStr, str(Sections))
        self.assertIn("tag1Desc", Strings.LocalizableStrings)
        self.assertEqual("desc1", Strings.LocalizableStrings['tag1Desc'])
        self.assertIn("test1.bin", SourceFiles.Files)
        self.assertIn("tag2Desc", Strings.LocalizableStrings)
        self.assertEqual("desc2", Strings.LocalizableStrings['tag2Desc'])
        self.assertIn("test2.bin", SourceFiles.Files)

        self.assertIn("REG_DWORD", Strings.NonLocalizableStrings)
        self.assertEqual("0x00010001", Strings.NonLocalizableStrings['REG_DWORD'])

    def test_firmware_sections_should_throw_for_bad_input(self):
        Strings = InfStrings()

        with self.assertRaises(ValueError):
            InfFirmwareSections('foobar', Strings)


class InfSourceFilesTest(unittest.TestCase):
    def test_source_files(self):
        Strings = InfStrings()
        SourceFiles = InfSourceFiles("diskname", Strings)
        SourceFiles.AddFile("test.bin")
        SourceFiles.AddFile("test2.bin")
        SourceFiles.AddFile("test3.bin")

        ExpectedStr = textwrap.dedent("""\
            [SourceDisksNames]
            1 = %DiskName%

            [SourceDisksFiles]
            test.bin = 1
            test2.bin = 1
            test3.bin = 1

            [DestinationDirs]
            DefaultDestDir = 13

            """)

        self.assertEqual(ExpectedStr, str(SourceFiles))
        self.assertIn("DiskName", Strings.LocalizableStrings)
        self.assertEqual("diskname", Strings.LocalizableStrings['DiskName'])
        self.assertIn("DIRID_WINDOWS", Strings.NonLocalizableStrings)
        self.assertEqual("10", Strings.NonLocalizableStrings['DIRID_WINDOWS'])

    def test_source_files_should_throw_on_bad_input(self):
        Strings = InfStrings()
        SourceFiles = InfSourceFiles("diskname", Strings)

        with self.assertRaises(ValueError):
            SourceFiles.AddFile("Who Names Files Like This?.bin")


class InfStringsTest(unittest.TestCase):
    def test_inf_strings(self):
        Strings = InfStrings()
        Strings.AddLocalizableString("DiskName", "Firmware Update")
        Strings.AddLocalizableString("Provider", "Test Provider")
        Strings.AddLocalizableString("Tag1Desc", "Test Firmware")

        Strings.AddNonLocalizableString("DIRID_WINDOWS", "10")
        Strings.AddNonLocalizableString("REG_DWORD", "0x00010001")

        ExpectedStr = textwrap.dedent("""\
            [Strings]
            ; localizable
            DiskName = "Firmware Update"
            Provider = "Test Provider"
            Tag1Desc = "Test Firmware"

            ; non-localizable
            DIRID_WINDOWS = 10
            REG_DWORD     = 0x00010001
            """)

        self.assertEqual(ExpectedStr, str(Strings))

    def test_inf_strings_should_throw_on_bad_input(self):
        Strings = InfStrings()

        with self.assertRaises(TypeError):
            Strings.AddLocalizableString(1, 2)

        with self.assertRaises(ValueError):
            Strings.AddLocalizableString("foo bar", "value")

        with self.assertRaises(ValueError):
            Strings.AddLocalizableString("ThisIsNotAllowed;", "value")

        with self.assertRaises(TypeError):
            Strings.AddNonLocalizableString(1, 2)

        with self.assertRaises(ValueError):
            Strings.AddNonLocalizableString("foo bar", "value")

        with self.assertRaises(ValueError):
            Strings.AddNonLocalizableString("ThisIsNotAllowed;", "value")


class InfFileTest(unittest.TestCase):
    def test_inf_file(self):
        File = InfFile("CapsuleName", "1.0.0.1", "01/01/2021", "Test Provider", "Test Manufacturer")

        File.AddFirmware(
            "tag1",
            "desc1",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test1.bin")

        File.AddFirmware(
            "tag2",
            "desc2",
            "bec9124f-9934-4ec0-a6ed-b8bc1c91d276",
            "0x01000002",
            "test2.bin")

        ExpectedStr = textwrap.dedent(f"""\
            ;
            ; CapsuleName
            ; 1.0.0.1
            ; Copyright (C) Microsoft Corporation. All Rights Reserved.
            ;
            [Version]
            Signature="$WINDOWS NT$"
            Class=Firmware
            ClassGuid={{f2e7dd72-6468-4e36-b6f1-6488f42c1b52}}
            Provider=%Provider%
            DriverVer=01/01/2021,1.0.0.1
            PnpLockdown=1
            CatalogFile=CapsuleName.cat

            [Manufacturer]
            %MfgName% = Firmware,NTamd64.{OS_BUILD_VERSION_DIRID13_SUPPORT}

            [Firmware.NTamd64.{OS_BUILD_VERSION_DIRID13_SUPPORT}]
            %tag1Desc% = tag1_Install,UEFI\\RES_{{34e094e9-4079-44cd-9450-3f2cb7824c97}}
            %tag2Desc% = tag2_Install,UEFI\\RES_{{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}}

            [tag1_Install.NT]
            CopyFiles = tag1_CopyFiles

            [tag1_CopyFiles]
            test1.bin

            [tag1_Install.NT.Services]
            AddService=,2

            [tag1_Install.NT.Hw]
            AddReg = tag1_AddReg

            [tag1_AddReg]
            HKR,,FirmwareId,,{{34e094e9-4079-44cd-9450-3f2cb7824c97}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,%13%\\test1.bin

            [tag2_Install.NT]
            CopyFiles = tag2_CopyFiles

            [tag2_CopyFiles]
            test2.bin

            [tag2_Install.NT.Services]
            AddService=,2

            [tag2_Install.NT.Hw]
            AddReg = tag2_AddReg

            [tag2_AddReg]
            HKR,,FirmwareId,,{{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000002
            HKR,,FirmwareFilename,,%13%\\test2.bin

            [SourceDisksNames]
            1 = %DiskName%

            [SourceDisksFiles]
            test1.bin = 1
            test2.bin = 1

            [DestinationDirs]
            DefaultDestDir = 13

            [Strings]
            ; localizable
            DiskName = "Firmware Update"
            Provider = "Test Provider"
            MfgName  = "Test Manufacturer"
            tag1Desc = "desc1"
            tag2Desc = "desc2"

            ; non-localizable
            DIRID_WINDOWS = 10
            REG_DWORD     = 0x00010001
            """)

        self.assertEqual(ExpectedStr, str(File))

    def test_inf_file_rollback(self):
        File = InfFile("CapsuleName", "1.0.0.1", "01/01/2021", "Test Provider", "Test Manufacturer")

        File.AddFirmware(
            "tag1",
            "desc1",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test1.bin",
            Rollback=True)

        File.AddFirmware(
            "tag2",
            "desc2",
            "bec9124f-9934-4ec0-a6ed-b8bc1c91d276",
            "0x01000002",
            "test2.bin",
            Rollback=True)

        ExpectedStr = textwrap.dedent(f"""\
            ;
            ; CapsuleName
            ; 1.0.0.1
            ; Copyright (C) Microsoft Corporation. All Rights Reserved.
            ;
            [Version]
            Signature="$WINDOWS NT$"
            Class=Firmware
            ClassGuid={{f2e7dd72-6468-4e36-b6f1-6488f42c1b52}}
            Provider=%Provider%
            DriverVer=01/01/2021,1.0.0.1
            PnpLockdown=1
            CatalogFile=CapsuleName.cat

            [Manufacturer]
            %MfgName% = Firmware,NTamd64.{OS_BUILD_VERSION_DIRID13_SUPPORT}

            [Firmware.NTamd64.{OS_BUILD_VERSION_DIRID13_SUPPORT}]
            %tag1Desc% = tag1_Install,UEFI\\RES_{{34e094e9-4079-44cd-9450-3f2cb7824c97}}
            %tag2Desc% = tag2_Install,UEFI\\RES_{{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}}

            [tag1_Install.NT]
            CopyFiles = tag1_CopyFiles
            AddReg = tag1_DowngradePolicy_AddReg

            [tag1_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{{34e094e9-4079-44cd-9450-3f2cb7824c97}},Policy,%REG_DWORD%,1

            [tag1_CopyFiles]
            test1.bin

            [tag1_Install.NT.Services]
            AddService=,2

            [tag1_Install.NT.Hw]
            AddReg = tag1_AddReg

            [tag1_AddReg]
            HKR,,FirmwareId,,{{34e094e9-4079-44cd-9450-3f2cb7824c97}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,%13%\\test1.bin

            [tag2_Install.NT]
            CopyFiles = tag2_CopyFiles
            AddReg = tag2_DowngradePolicy_AddReg

            [tag2_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}},Policy,%REG_DWORD%,1

            [tag2_CopyFiles]
            test2.bin

            [tag2_Install.NT.Services]
            AddService=,2

            [tag2_Install.NT.Hw]
            AddReg = tag2_AddReg

            [tag2_AddReg]
            HKR,,FirmwareId,,{{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000002
            HKR,,FirmwareFilename,,%13%\\test2.bin

            [SourceDisksNames]
            1 = %DiskName%

            [SourceDisksFiles]
            test1.bin = 1
            test2.bin = 1

            [DestinationDirs]
            DefaultDestDir = 13

            [Strings]
            ; localizable
            DiskName = "Firmware Update"
            Provider = "Test Provider"
            MfgName  = "Test Manufacturer"
            tag1Desc = "desc1"
            tag2Desc = "desc2"

            ; non-localizable
            DIRID_WINDOWS = 10
            REG_DWORD     = 0x00010001
            """)

        self.assertEqual(ExpectedStr, str(File))

    def test_inf_file_rollback_integrity(self):
        File = InfFile("CapsuleName", "1.0.0.1", "01/01/2021", "Test Provider", "Test Manufacturer")

        File.AddFirmware(
            "tag1",
            "desc1",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test1.bin",
            Rollback=True,
            IntegrityFile="integrity1.bin")

        File.AddFirmware(
            "tag2",
            "desc2",
            "bec9124f-9934-4ec0-a6ed-b8bc1c91d276",
            "0x01000002",
            "test2.bin",
            Rollback=True,
            IntegrityFile="integrity2.bin")

        ExpectedStr = textwrap.dedent(f"""\
            ;
            ; CapsuleName
            ; 1.0.0.1
            ; Copyright (C) Microsoft Corporation. All Rights Reserved.
            ;
            [Version]
            Signature="$WINDOWS NT$"
            Class=Firmware
            ClassGuid={{f2e7dd72-6468-4e36-b6f1-6488f42c1b52}}
            Provider=%Provider%
            DriverVer=01/01/2021,1.0.0.1
            PnpLockdown=1
            CatalogFile=CapsuleName.cat

            [Manufacturer]
            %MfgName% = Firmware,NTamd64.{OS_BUILD_VERSION_DIRID13_SUPPORT}

            [Firmware.NTamd64.{OS_BUILD_VERSION_DIRID13_SUPPORT}]
            %tag1Desc% = tag1_Install,UEFI\\RES_{{34e094e9-4079-44cd-9450-3f2cb7824c97}}
            %tag2Desc% = tag2_Install,UEFI\\RES_{{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}}

            [tag1_Install.NT]
            CopyFiles = tag1_CopyFiles
            AddReg = tag1_DowngradePolicy_AddReg

            [tag1_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{{34e094e9-4079-44cd-9450-3f2cb7824c97}},Policy,%REG_DWORD%,1

            [tag1_CopyFiles]
            test1.bin
            integrity1.bin

            [tag1_Install.NT.Services]
            AddService=,2

            [tag1_Install.NT.Hw]
            AddReg = tag1_AddReg

            [tag1_AddReg]
            HKR,,FirmwareId,,{{34e094e9-4079-44cd-9450-3f2cb7824c97}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,%13%\\test1.bin
            HKR,,FirmwareIntegrityFilename,,%13%\\integrity1.bin

            [tag2_Install.NT]
            CopyFiles = tag2_CopyFiles
            AddReg = tag2_DowngradePolicy_AddReg

            [tag2_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}},Policy,%REG_DWORD%,1

            [tag2_CopyFiles]
            test2.bin
            integrity2.bin

            [tag2_Install.NT.Services]
            AddService=,2

            [tag2_Install.NT.Hw]
            AddReg = tag2_AddReg

            [tag2_AddReg]
            HKR,,FirmwareId,,{{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000002
            HKR,,FirmwareFilename,,%13%\\test2.bin
            HKR,,FirmwareIntegrityFilename,,%13%\\integrity2.bin

            [SourceDisksNames]
            1 = %DiskName%

            [SourceDisksFiles]
            test1.bin = 1
            integrity1.bin = 1
            test2.bin = 1
            integrity2.bin = 1

            [DestinationDirs]
            DefaultDestDir = 13

            [Strings]
            ; localizable
            DiskName = "Firmware Update"
            Provider = "Test Provider"
            MfgName  = "Test Manufacturer"
            tag1Desc = "desc1"
            tag2Desc = "desc2"

            ; non-localizable
            DIRID_WINDOWS = 10
            REG_DWORD     = 0x00010001
            """)

        self.assertEqual(ExpectedStr, str(File))
