## @file
# UnitTest for inf_generator.py
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import textwrap
from edk2toollib.windows.capsule.inf_generator2 import InfHeader, InfStrings, InfSourceFiles, InfFirmware
from edk2toollib.windows.capsule.inf_generator2 import InfFirmwareSections, InfFile


class InfHeaderTest(unittest.TestCase):
    def test_header(self):
        infStrings = InfStrings()
        infHeader = InfHeader("InfTest", "1.0.0.1", "01/01/2021", "amd64", "testprovider", "testmfr", infStrings)

        expectedStr = textwrap.dedent("""\
            ;
            ; InfTest
            ; 1.0.0.1
            ; Copyright (C) Microsoft Corporation. All Rights Reserved.
            ;
            [Version]
            Signature="$WINDOWS NT$"
            Class=Firmware
            ClassGuid={f2e7dd72-6468-4e36-b6f1-6488f42c1b52}
            Provider=%Provider%
            DriverVer=01/01/2021,1.0.0.1
            PnpLockdown=1
            CatalogFile=InfTest.cat

            [Manufacturer]
            %MfgName% = Firmware,NTamd64

            """)
        self.assertEqual(expectedStr, str(infHeader))
        self.assertIn("Provider", infStrings.localizableStrings)
        self.assertEqual("testprovider", infStrings.localizableStrings['Provider'])
        self.assertIn("MfgName", infStrings.localizableStrings)
        self.assertEqual("testmfr", infStrings.localizableStrings['MfgName'])


class InfFirmwareTest(unittest.TestCase):
    def test_firmware(self):
        infStrings = InfStrings()
        infSourceFiles = InfSourceFiles("diskname", infStrings)

        infFirmware = InfFirmware(
            "tag",
            "desc",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test.bin",
            infStrings,
            infSourceFiles)

        expectedStr = textwrap.dedent("""\
            [tag_Install.NT]
            CopyFiles = tag_CopyFiles

            [tag_CopyFiles]
            test.bin

            [tag_Install.NT.Hw]
            AddReg = tag_AddReg

            [tag_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,test.bin

            """)

        self.assertEqual(expectedStr, str(infFirmware))
        self.assertEqual(infFirmware.desc, "desc")
        self.assertIn("REG_DWORD", infStrings.nonlocalizableStrings)
        self.assertEqual("0x00010001", infStrings.nonlocalizableStrings['REG_DWORD'])
        self.assertIn("test.bin", infSourceFiles.files)

    def test_rollback_firmware(self):
        infStrings = InfStrings()
        infSourceFiles = InfSourceFiles("diskname", infStrings)

        infFirmware = InfFirmware(
            "tag",
            "desc",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test.bin",
            infStrings,
            infSourceFiles,
            rollback=True)

        expectedStr = textwrap.dedent("""\
            [tag_Install.NT]
            CopyFiles = tag_CopyFiles
            AddReg = tag_DowngradePolicy_AddReg

            [tag_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{34e094e9-4079-44cd-9450-3f2cb7824c97},Policy,%REG_DWORD%,1

            [tag_CopyFiles]
            test.bin

            [tag_Install.NT.Hw]
            AddReg = tag_AddReg

            [tag_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,test.bin

            """)

        self.assertEqual(expectedStr, str(infFirmware))
        self.assertEqual(infFirmware.desc, "desc")
        self.assertIn("REG_DWORD", infStrings.nonlocalizableStrings)
        self.assertEqual("0x00010001", infStrings.nonlocalizableStrings['REG_DWORD'])
        self.assertIn("test.bin", infSourceFiles.files)

    def test_rollback_firmware_integrity(self):
        infStrings = InfStrings()
        infSourceFiles = InfSourceFiles("diskname", infStrings)

        infFirmware = InfFirmware(
            "tag",
            "desc",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test.bin",
            infStrings,
            infSourceFiles,
            rollback=True,
            integrityFile="test2.bin")

        expectedStr = textwrap.dedent("""\
            [tag_Install.NT]
            CopyFiles = tag_CopyFiles
            AddReg = tag_DowngradePolicy_AddReg

            [tag_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{34e094e9-4079-44cd-9450-3f2cb7824c97},Policy,%REG_DWORD%,1

            [tag_CopyFiles]
            test.bin
            test2.bin

            [tag_Install.NT.Hw]
            AddReg = tag_AddReg

            [tag_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,test.bin
            HKR,,FirmwareIntegrityFilename,,test2.bin

            """)

        self.assertEqual(expectedStr, str(infFirmware))
        self.assertEqual(infFirmware.desc, "desc")
        self.assertIn("REG_DWORD", infStrings.nonlocalizableStrings)
        self.assertEqual("0x00010001", infStrings.nonlocalizableStrings['REG_DWORD'])
        self.assertIn("test.bin", infSourceFiles.files)
        self.assertIn("test2.bin", infSourceFiles.files)


class InfFirmwareSectionsTest(unittest.TestCase):
    def test_one_section(self):
        infStrings = InfStrings()
        infSourceFiles = InfSourceFiles("diskname", infStrings)

        infFirmware = InfFirmware(
            "tag",
            "desc",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test.bin",
            infStrings,
            infSourceFiles)

        infSections = InfFirmwareSections('amd64', infStrings)
        infSections.AddSection(infFirmware)

        expectedStr = textwrap.dedent("""\
            [Firmware.NTamd64]
            %tagDesc% = tag_Install,UEFI\\RES_{34e094e9-4079-44cd-9450-3f2cb7824c97}

            [tag_Install.NT]
            CopyFiles = tag_CopyFiles

            [tag_CopyFiles]
            test.bin

            [tag_Install.NT.Hw]
            AddReg = tag_AddReg

            [tag_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,test.bin

            """)

        self.assertEqual(expectedStr, str(infSections))
        self.assertIn("tagDesc", infStrings.localizableStrings)
        self.assertEqual("desc", infStrings.localizableStrings['tagDesc'])
        self.assertIn("test.bin", infSourceFiles.files)

        self.assertIn("REG_DWORD", infStrings.nonlocalizableStrings)
        self.assertEqual("0x00010001", infStrings.nonlocalizableStrings['REG_DWORD'])

    def test_two_sections(self):
        infStrings = InfStrings()
        infSourceFiles = InfSourceFiles("diskname", infStrings)

        infFirmware1 = InfFirmware(
            "tag1",
            "desc1",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test1.bin",
            infStrings,
            infSourceFiles)

        infFirmware2 = InfFirmware(
            "tag2",
            "desc2",
            "bec9124f-9934-4ec0-a6ed-b8bc1c91d276",
            "0x01000002",
            "test2.bin",
            infStrings,
            infSourceFiles)

        infSections = InfFirmwareSections('amd64', infStrings)
        infSections.AddSection(infFirmware1)
        infSections.AddSection(infFirmware2)

        expectedStr = textwrap.dedent("""\
            [Firmware.NTamd64]
            %tag1Desc% = tag1_Install,UEFI\\RES_{34e094e9-4079-44cd-9450-3f2cb7824c97}
            %tag2Desc% = tag2_Install,UEFI\\RES_{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}

            [tag1_Install.NT]
            CopyFiles = tag1_CopyFiles

            [tag1_CopyFiles]
            test1.bin

            [tag1_Install.NT.Hw]
            AddReg = tag1_AddReg

            [tag1_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,test1.bin

            [tag2_Install.NT]
            CopyFiles = tag2_CopyFiles

            [tag2_CopyFiles]
            test2.bin

            [tag2_Install.NT.Hw]
            AddReg = tag2_AddReg

            [tag2_AddReg]
            HKR,,FirmwareId,,{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000002
            HKR,,FirmwareFilename,,test2.bin

            """)

        self.assertEqual(expectedStr, str(infSections))
        self.assertIn("tag1Desc", infStrings.localizableStrings)
        self.assertEqual("desc1", infStrings.localizableStrings['tag1Desc'])
        self.assertIn("test1.bin", infSourceFiles.files)
        self.assertIn("tag2Desc", infStrings.localizableStrings)
        self.assertEqual("desc2", infStrings.localizableStrings['tag2Desc'])
        self.assertIn("test2.bin", infSourceFiles.files)

        self.assertIn("REG_DWORD", infStrings.nonlocalizableStrings)
        self.assertEqual("0x00010001", infStrings.nonlocalizableStrings['REG_DWORD'])


class InfSourceFilesTest(unittest.TestCase):
    def test_source_files(self):
        infStrings = InfStrings()
        infSourceFiles = InfSourceFiles("diskname", infStrings)
        infSourceFiles.addFile("test.bin")
        infSourceFiles.addFile("test2.bin")
        infSourceFiles.addFile("test3.bin")

        expectedStr = textwrap.dedent("""\
            [SourceDisksNames]
            1 = %DiskName%

            [SourceDisksFiles]
            test.bin = 1
            test2.bin = 1
            test3.bin = 1

            [DestinationDirs]
            DefaultDestDir = %DIRID_WINDOWS%,Firmware ; %SystemRoot%\\Firmware

            """)

        self.assertEqual(expectedStr, str(infSourceFiles))
        self.assertIn("DiskName", infStrings.localizableStrings)
        self.assertEqual("diskname", infStrings.localizableStrings['DiskName'])
        self.assertIn("DIRID_WINDOWS", infStrings.nonlocalizableStrings)
        self.assertEqual("10", infStrings.nonlocalizableStrings['DIRID_WINDOWS'])


class InfStringsTest(unittest.TestCase):
    def test_inf_strings(self):
        infStrings = InfStrings()
        infStrings.addLocalizableString("DiskName", "Firmware Update")
        infStrings.addLocalizableString("Provider", "Test Provider")
        infStrings.addLocalizableString("Tag1Desc", "Test Firmware")

        infStrings.addNonlocalizableString("DIRID_WINDOWS", "10")
        infStrings.addNonlocalizableString("REG_DWORD", "0x00010001")

        expectedStr = textwrap.dedent("""\
            [Strings]
            ; localizable
            DiskName = "Firmware Update"
            Provider = "Test Provider"
            Tag1Desc = "Test Firmware"

            ; non-localizable
            DIRID_WINDOWS = 10
            REG_DWORD     = 0x00010001
            """)

        self.assertEqual(expectedStr, str(infStrings))


class InfFileTest(unittest.TestCase):
    def test_inf_file(self):
        infFile = InfFile("CapsuleName", "1.0.0.1", "01/01/2021", "Test Provider", "Test Manufacturer")

        infFile.addFirmware(
            "tag1",
            "desc1",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test1.bin")

        infFile.addFirmware(
            "tag2",
            "desc2",
            "bec9124f-9934-4ec0-a6ed-b8bc1c91d276",
            "0x01000002",
            "test2.bin")

        expectedStr = textwrap.dedent("""\
            ;
            ; CapsuleName
            ; 1.0.0.1
            ; Copyright (C) Microsoft Corporation. All Rights Reserved.
            ;
            [Version]
            Signature="$WINDOWS NT$"
            Class=Firmware
            ClassGuid={f2e7dd72-6468-4e36-b6f1-6488f42c1b52}
            Provider=%Provider%
            DriverVer=01/01/2021,1.0.0.1
            PnpLockdown=1
            CatalogFile=CapsuleName.cat

            [Manufacturer]
            %MfgName% = Firmware,NTamd64

            [Firmware.NTamd64]
            %tag1Desc% = tag1_Install,UEFI\\RES_{34e094e9-4079-44cd-9450-3f2cb7824c97}
            %tag2Desc% = tag2_Install,UEFI\\RES_{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}

            [tag1_Install.NT]
            CopyFiles = tag1_CopyFiles

            [tag1_CopyFiles]
            test1.bin

            [tag1_Install.NT.Hw]
            AddReg = tag1_AddReg

            [tag1_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,test1.bin

            [tag2_Install.NT]
            CopyFiles = tag2_CopyFiles

            [tag2_CopyFiles]
            test2.bin

            [tag2_Install.NT.Hw]
            AddReg = tag2_AddReg

            [tag2_AddReg]
            HKR,,FirmwareId,,{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000002
            HKR,,FirmwareFilename,,test2.bin

            [SourceDisksNames]
            1 = %DiskName%

            [SourceDisksFiles]
            test1.bin = 1
            test2.bin = 1

            [DestinationDirs]
            DefaultDestDir = %DIRID_WINDOWS%,Firmware ; %SystemRoot%\\Firmware

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

        self.assertEqual(expectedStr, str(infFile))

    def test_inf_file_rollback(self):
        infFile = InfFile("CapsuleName", "1.0.0.1", "01/01/2021", "Test Provider", "Test Manufacturer")

        infFile.addFirmware(
            "tag1",
            "desc1",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test1.bin",
            rollback=True)

        infFile.addFirmware(
            "tag2",
            "desc2",
            "bec9124f-9934-4ec0-a6ed-b8bc1c91d276",
            "0x01000002",
            "test2.bin",
            rollback=True)

        expectedStr = textwrap.dedent("""\
            ;
            ; CapsuleName
            ; 1.0.0.1
            ; Copyright (C) Microsoft Corporation. All Rights Reserved.
            ;
            [Version]
            Signature="$WINDOWS NT$"
            Class=Firmware
            ClassGuid={f2e7dd72-6468-4e36-b6f1-6488f42c1b52}
            Provider=%Provider%
            DriverVer=01/01/2021,1.0.0.1
            PnpLockdown=1
            CatalogFile=CapsuleName.cat

            [Manufacturer]
            %MfgName% = Firmware,NTamd64

            [Firmware.NTamd64]
            %tag1Desc% = tag1_Install,UEFI\\RES_{34e094e9-4079-44cd-9450-3f2cb7824c97}
            %tag2Desc% = tag2_Install,UEFI\\RES_{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}

            [tag1_Install.NT]
            CopyFiles = tag1_CopyFiles
            AddReg = tag1_DowngradePolicy_AddReg

            [tag1_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{34e094e9-4079-44cd-9450-3f2cb7824c97},Policy,%REG_DWORD%,1

            [tag1_CopyFiles]
            test1.bin

            [tag1_Install.NT.Hw]
            AddReg = tag1_AddReg

            [tag1_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,test1.bin

            [tag2_Install.NT]
            CopyFiles = tag2_CopyFiles
            AddReg = tag2_DowngradePolicy_AddReg

            [tag2_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{bec9124f-9934-4ec0-a6ed-b8bc1c91d276},Policy,%REG_DWORD%,1

            [tag2_CopyFiles]
            test2.bin

            [tag2_Install.NT.Hw]
            AddReg = tag2_AddReg

            [tag2_AddReg]
            HKR,,FirmwareId,,{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000002
            HKR,,FirmwareFilename,,test2.bin

            [SourceDisksNames]
            1 = %DiskName%

            [SourceDisksFiles]
            test1.bin = 1
            test2.bin = 1

            [DestinationDirs]
            DefaultDestDir = %DIRID_WINDOWS%,Firmware ; %SystemRoot%\\Firmware

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

        self.assertEqual(expectedStr, str(infFile))

    def test_inf_file_rollback_integrity(self):
        self.maxDiff = None
        infFile = InfFile("CapsuleName", "1.0.0.1", "01/01/2021", "Test Provider", "Test Manufacturer")

        infFile.addFirmware(
            "tag1",
            "desc1",
            "34e094e9-4079-44cd-9450-3f2cb7824c97",
            "0x01000001",
            "test1.bin",
            rollback=True,
            integrityFile="integrity1.bin")

        infFile.addFirmware(
            "tag2",
            "desc2",
            "bec9124f-9934-4ec0-a6ed-b8bc1c91d276",
            "0x01000002",
            "test2.bin",
            rollback=True,
            integrityFile="integrity2.bin")

        expectedStr = textwrap.dedent("""\
            ;
            ; CapsuleName
            ; 1.0.0.1
            ; Copyright (C) Microsoft Corporation. All Rights Reserved.
            ;
            [Version]
            Signature="$WINDOWS NT$"
            Class=Firmware
            ClassGuid={f2e7dd72-6468-4e36-b6f1-6488f42c1b52}
            Provider=%Provider%
            DriverVer=01/01/2021,1.0.0.1
            PnpLockdown=1
            CatalogFile=CapsuleName.cat

            [Manufacturer]
            %MfgName% = Firmware,NTamd64

            [Firmware.NTamd64]
            %tag1Desc% = tag1_Install,UEFI\\RES_{34e094e9-4079-44cd-9450-3f2cb7824c97}
            %tag2Desc% = tag2_Install,UEFI\\RES_{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}

            [tag1_Install.NT]
            CopyFiles = tag1_CopyFiles
            AddReg = tag1_DowngradePolicy_AddReg

            [tag1_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{34e094e9-4079-44cd-9450-3f2cb7824c97},Policy,%REG_DWORD%,1

            [tag1_CopyFiles]
            test1.bin
            integrity1.bin

            [tag1_Install.NT.Hw]
            AddReg = tag1_AddReg

            [tag1_AddReg]
            HKR,,FirmwareId,,{34e094e9-4079-44cd-9450-3f2cb7824c97}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000001
            HKR,,FirmwareFilename,,test1.bin
            HKR,,FirmwareIntegrityFilename,,integrity1.bin

            [tag2_Install.NT]
            CopyFiles = tag2_CopyFiles
            AddReg = tag2_DowngradePolicy_AddReg

            [tag2_DowngradePolicy_AddReg]
            HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{bec9124f-9934-4ec0-a6ed-b8bc1c91d276},Policy,%REG_DWORD%,1

            [tag2_CopyFiles]
            test2.bin
            integrity2.bin

            [tag2_Install.NT.Hw]
            AddReg = tag2_AddReg

            [tag2_AddReg]
            HKR,,FirmwareId,,{bec9124f-9934-4ec0-a6ed-b8bc1c91d276}
            HKR,,FirmwareVersion,%REG_DWORD%,0x1000002
            HKR,,FirmwareFilename,,test2.bin
            HKR,,FirmwareIntegrityFilename,,integrity2.bin

            [SourceDisksNames]
            1 = %DiskName%

            [SourceDisksFiles]
            test1.bin = 1
            integrity1.bin = 1
            test2.bin = 1
            integrity2.bin = 1

            [DestinationDirs]
            DefaultDestDir = %DIRID_WINDOWS%,Firmware ; %SystemRoot%\\Firmware

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

        self.assertEqual(expectedStr, str(infFile))
