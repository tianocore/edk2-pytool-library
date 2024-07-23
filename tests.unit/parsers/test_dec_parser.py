# @file dec_parser_test.py
# Contains unit test routines for the dec parser class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import io
import unittest
import uuid

from edk2toollib.uefi.edk2.parsers.dec_parser import (
    DecParser,
    GuidDeclarationEntry,
    LibraryClassDeclarationEntry,
    PcdDeclarationEntry,
    PpiDeclarationEntry,
    ProtocolDeclarationEntry,
)


class TestGuidDeclarationEntry(unittest.TestCase):

    def test_valid_input_guid(self):
        SAMPLE_DATA_GUID_DECL = '''gTestGuid       = { 0x66341ae8, 0x668f, 0x4192, { 0xb4, 0x4d, 0x5f, 0x87, 0xb8, 0x68, 0xf0, 0x41 }}'''  # noqa: E501
        SAMPLE_DATA_GUID_STRING_REG_FORMAT = "{66341ae8-668f-4192-b44d-5f87b868f041}"
        a = GuidDeclarationEntry("TestPkg", SAMPLE_DATA_GUID_DECL)
        con = uuid.UUID(SAMPLE_DATA_GUID_STRING_REG_FORMAT)
        self.assertEqual(str(con), str(a.guid))
        self.assertEqual(a.name, "gTestGuid")
        self.assertEqual(a.package_name, "TestPkg")

    def test_valid_input_leading_zero_removed(self):
        SAMPLE_DATA_GUID_DECL = '''gTestGuid       = { 0x6341ae8, 0x68f, 0x192, { 0x4, 0xd, 0xf, 0x7, 0x8, 0x8, 0x0, 0x1 }}'''  # noqa: E501
        SAMPLE_DATA_GUID_STRING_REG_FORMAT = "{06341ae8-068f-0192-040d-0f0708080001}"
        a = GuidDeclarationEntry("testpkg", SAMPLE_DATA_GUID_DECL)
        con = uuid.UUID(SAMPLE_DATA_GUID_STRING_REG_FORMAT)
        self.assertEqual(str(con), str(a.guid))

    def test_invalid_guid_format(self):
        SAMPLE_DATA_GUID_DECL = '''gTestGuid       = 0x6341ae8, 0x668f, 0x4192, 0xb4, 0x4d, 0x5f, 0x87, 0xb8, 0x68, 0xf0, 0x41'''  # noqa: E501
        with self.assertRaises(ValueError):
            GuidDeclarationEntry("testpkg", SAMPLE_DATA_GUID_DECL)


class TestPpiDeclarationEntry(unittest.TestCase):

    def test_valid_input_guid(self):
        SAMPLE_DATA_PPI_DECL = """gTestPpiGuid       = {0xa66cd455, 0xc078, 0x4753, {0xbe, 0x93, 0xdd, 0x58, 0xb2, 0xaf, 0xe9, 0xc4}}"""  # noqa: E501
        SAMPLE_DATA_PPI_STRING_REG_FORMAT = "{a66cd455-c078-4753-be93-dd58b2afe9c4}"
        a = PpiDeclarationEntry("testpkg", SAMPLE_DATA_PPI_DECL)
        con = uuid.UUID(SAMPLE_DATA_PPI_STRING_REG_FORMAT)
        self.assertEqual(str(con), str(a.guid))
        self.assertEqual(a.name, "gTestPpiGuid")
        self.assertEqual(a.package_name, "testpkg")


class TestProtocolDeclarationEntry(unittest.TestCase):

    def test_valid_input_guid(self):
        SAMPLE_DATA_PROTOCOL_DECL = """gTestProtocolGuid    = {0xb6d12b5a, 0x5338, 0x44ac, {0xac, 0x31, 0x1e, 0x9f, 0xa8, 0xc7, 0xe0, 0x1e}}"""  # noqa: E501
        SAMPLE_DATA_PROTOCOL_GUID_REG_FORMAT = "{b6d12b5a-5338-44ac-ac31-1e9fa8c7e01e}"
        a = ProtocolDeclarationEntry("testpkg", SAMPLE_DATA_PROTOCOL_DECL)
        con = uuid.UUID(SAMPLE_DATA_PROTOCOL_GUID_REG_FORMAT)
        self.assertEqual(str(con), str(a.guid))
        self.assertEqual(a.name, "gTestProtocolGuid")
        self.assertEqual(a.package_name, "testpkg")


class TestLibraryClassDeclarationEntry(unittest.TestCase):

    def test_valid_input(self):
        SAMPLE_DATA_DECL = """BmpSupportLib|Include/Library/BmpSupportLib.h"""
        a = LibraryClassDeclarationEntry("testpkg", SAMPLE_DATA_DECL)
        self.assertEqual(a.path, "Include/Library/BmpSupportLib.h")
        self.assertEqual(a.name, "BmpSupportLib")


class TestPcdDeclarationEntry(unittest.TestCase):

    def test_valid_input(self):
        SAMPLE_DATA_DECL = """gEfiMdeModulePkgTokenSpaceGuid.PcdSupportUpdateCapsuleReset|FALSE|BOOLEAN|0x0001001d"""
        a = PcdDeclarationEntry("testpkg", SAMPLE_DATA_DECL)
        self.assertEqual(a.token_space_name, "gEfiMdeModulePkgTokenSpaceGuid")
        self.assertEqual(a.name, "PcdSupportUpdateCapsuleReset")
        self.assertEqual(a.default_value, "FALSE")
        self.assertEqual(a.type, "BOOLEAN")
        self.assertEqual(a.id, "0x0001001d")

    def test_invalid_input_no_tokenspace(self):
        SAMPLE_DATA_DECL = """garbage|FALSE|BOOLEAN|0x0001001d"""
        with self.assertRaises(Exception):
            PcdDeclarationEntry("testpkg", SAMPLE_DATA_DECL)

    def test_invalid_input_too_many_fields(self):
        SAMPLE_DATA_DECL = """garbage.garbageNAME|FALSE|BOOLEAN|0x0001001d|morestuff|questions|this|should|fail"""
        with self.assertRaises(Exception):
            PcdDeclarationEntry("testpkg", SAMPLE_DATA_DECL)

    def test_good_structured_input(self):
        SAMPLE_DATA_DECL = """gSomePkgTokenSpaceGuid.PcdThatInformation.Subfield|0x1"""
        a = PcdDeclarationEntry("testpkg", SAMPLE_DATA_DECL)
        self.assertEqual(a.token_space_name, "gSomePkgTokenSpaceGuid")
        self.assertEqual(a.name, "PcdThatInformation.Subfield")

    def test_bad_structured_input(self):
        SAMPLE_DATA_DECL = """gSomePkgTokenSpaceGuid.PcdThatInformation|0x1"""
        with self.assertRaises(Exception):
            PcdDeclarationEntry("testpkg", SAMPLE_DATA_DECL)

    def test_string_containing_a_pipe(self):
        SAMPLE_DATA_DECL = """gTestTokenSpaceGuid.PcdTestString | L"TestVal_1 | TestVal_2" | VOID* | 0x00010001"""
        a = PcdDeclarationEntry("testpkg", SAMPLE_DATA_DECL)
        self.assertEqual(a.token_space_name, "gTestTokenSpaceGuid")
        self.assertEqual(a.name, "PcdTestString")
        self.assertEqual(a.default_value, "L\"TestVal_1 | TestVal_2\"")
        self.assertEqual(a.type, "VOID*")
        self.assertEqual(a.id, "0x00010001")

        SAMPLE_DATA_DECL = """gTestTokenSpaceGuid.PcdTestString | L'TestVal_1 | TestVal_2' | VOID* | 0x00010001"""
        a = PcdDeclarationEntry("testpkg", SAMPLE_DATA_DECL)
        self.assertEqual(a.token_space_name, "gTestTokenSpaceGuid")
        self.assertEqual(a.name, "PcdTestString")
        self.assertEqual(a.default_value, "L'TestVal_1 | TestVal_2'")
        self.assertEqual(a.type, "VOID*")
        self.assertEqual(a.id, "0x00010001")

    def test_string_containing_single_quote(self):
        SAMPLE_DATA_DECL = """gTestTokenSpaceGuid.PcdSingleQuote|"eng'fraengfra"|VOID*|0x00010001"""
        a = PcdDeclarationEntry("testpkg", SAMPLE_DATA_DECL)
        self.assertEqual(a.token_space_name, "gTestTokenSpaceGuid")
        self.assertEqual(a.name, "PcdTestString")
        self.assertEqual(a.default_value, "\"eng'fraengfra\"")
        self.assertEqual(a.type, "VOID*")
        self.assertEqual(a.id, "0x00010001")

class TestDecParser(unittest.TestCase):

    SAMPLE_DEC_FILE = \
        """## @file
TestDecFile
##

[Defines]
  DEC_SPECIFICATION              = 0x00010005
  PACKAGE_NAME                   = TestDecParserPkg
  PACKAGE_UNI_FILE               = TestDecParserPkg.uni
  PACKAGE_GUID                   = 57e8a49e-1b3f-41a0-a552-55ad831c15a8
  PACKAGE_VERSION                = 0.1

[Includes]
  Include

[LibraryClasses]
  ##  @libraryclass  Provide comment for fakelib
  #
  FakeLib|Include/Library/FakeLib.h

[Guids]
  gFakeTokenSpace =  {0x7c004f69, 0xd730, 0x4904, {0x83, 0xe1, 0x4b, 0xbf, 0x39, 0x3a, 0xfc, 0xb1}}
  gFake2TokenSpace = {0x7c004f69, 0xd730, 0x4904, {0x83, 0xe1, 0x4b, 0xbf, 0x39, 0x3a, 0xfc, 0xb2}}
  gFakeT3okenSpace = {0x7c004f69, 0xd730, 0x4904, {0x83, 0xe1, 0x4b, 0xbf, 0x39, 0x3a, 0xfc, 0xb3}}

#
# [Error.gPcAtChipsetPkgTokenSpaceGuid]
#   0x80000001 | Invalid value provided.
#

[Protocols]
  ## None
  gFakeProtocol     = {0xe63e2ccd, 0x786e, 0x4754, {0x96, 0xf8, 0x5e, 0x88, 0xa3, 0xf0, 0xaf, 0x85}}

[Ppis]
  gFakePpi  =  {0xeeef868e, 0x5bf5, 0x4e48, {0x92, 0xa1, 0xd7, 0x6e, 0x02, 0xe5, 0xb9, 0xa7}}
  gFake2Ppi =  {0xeeef868e, 0x5bf5, 0x4e48, {0x92, 0xa1, 0xd7, 0x6e, 0x02, 0xe5, 0xb9, 0xa8}}

## Copied PCDs from PcAtChipsetPkg for testing

[PcdsFeatureFlag]
  ## Indicates the HPET Timer will be configured to use MSI interrupts if the HPET
  #   TRUE  - Configures the HPET Timer to use MSI interrupts if the HPET Timer supports them.<BR>
  #   FALSE - Configures the HPET Timer to use I/O APIC interrupts.<BR>
  # @Prompt Configure HPET to use MSI.
  gPcAtChipsetPkgTokenSpaceGuid.PcdHpetMsiEnable|TRUE|BOOLEAN|0x00001000

[PcdsFixedAtBuild, PcdsDynamic, PcdsDynamicEx, PcdsPatchableInModule]
  ## Pcd8259LegacyModeMask defines the default mask value for platform. This value is determined<BR><BR>
  #  1) If platform only support pure UEFI, value should be set to 0xFFFF or 0xFFFE;
  #     Because only clock interrupt is allowed in legacy mode in pure UEFI platform.<BR>
  #  2) If platform install CSM and use thunk module:<BR>
  #     a) If thunk call provided by CSM binary requires some legacy interrupt support, the corresponding bit
  #        should be opened as 0.<BR>
  #        For example, if keyboard interfaces provided CSM binary use legacy keyboard interrupt in 8259 bit 1, then
  #        the value should be set to 0xFFFC.<BR>
  #     b) If all thunk call provied by CSM binary do not require legacy interrupt support, value should be set
  #        to 0xFFFF or 0xFFFE.<BR>
  #
  #  The default value of legacy mode mask could be changed by EFI_LEGACY_8259_PROTOCOL->SetMask(). But it is rarely
  #  need change it except some special cases such as when initializing the CSM bin
  gPcAtChipsetPkgTokenSpaceGuid.Pcd8259LegacyModeMask|0xFFFF|UINT16|0x00000001

  ## Pcd8259LegacyModeEdgeLevel defines the default edge level for legacy mode's interrupt controller.
  #  For the corresponding bits, 0 = Edge triggered and 1 = Level triggered.
  # @Prompt 8259 Legacy Mode edge level.
  gPcAtChipsetPkgTokenSpaceGuid.Pcd8259LegacyModeEdgeLevel|0x0000|UINT16|0x00000002

  ## Indicates if we need enable IsaAcpiCom1 device.<BR><BR>
  #   TRUE  - Enables IsaAcpiCom1 device.<BR>
  #   FALSE - Doesn't enable IsaAcpiCom1 device.<BR>
  # @Prompt Enable IsaAcpiCom1 device.
  gPcAtChipsetPkgTokenSpaceGuid.PcdIsaAcpiCom1Enable|TRUE|BOOLEAN|0x00000003

  ## Indicates if we need enable IsaAcpiCom2 device.<BR><BR>
  #   TRUE  - Enables IsaAcpiCom2 device.<BR>
  #   FALSE - Doesn't enable IsaAcpiCom2 device.<BR>
  # @Prompt Enable IsaAcpiCom12 device.
  gPcAtChipsetPkgTokenSpaceGuid.PcdIsaAcpiCom2Enable|TRUE|BOOLEAN|0x00000004

  ## Indicates if we need enable IsaAcpiPs2Keyboard device.<BR><BR>
  #   TRUE  - Enables IsaAcpiPs2Keyboard device.<BR>
  #   FALSE - Doesn't enable IsaAcpiPs2Keyboard device.<BR>
  # @Prompt Enable IsaAcpiPs2Keyboard device.
  gPcAtChipsetPkgTokenSpaceGuid.PcdIsaAcpiPs2KeyboardEnable|TRUE|BOOLEAN|0x00000005

  ## Indicates if we need enable IsaAcpiPs2Mouse device.<BR><BR>
  #   TRUE  - Enables IsaAcpiPs2Mouse device.<BR>
  #   FALSE - Doesn't enable IsaAcpiPs2Mouse device.<BR>
  # @Prompt Enable IsaAcpiPs2Mouse device.
  gPcAtChipsetPkgTokenSpaceGuid.PcdIsaAcpiPs2MouseEnable|TRUE|BOOLEAN|0x00000006

  ## Indicates if we need enable IsaAcpiFloppyA device.<BR><BR>
  #   TRUE  - Enables IsaAcpiFloppyA device.<BR>
  #   FALSE - Doesn't enable IsaAcpiFloppyA device.<BR>
  # @Prompt Enable IsaAcpiFloppyA device.
  gPcAtChipsetPkgTokenSpaceGuid.PcdIsaAcpiFloppyAEnable|TRUE|BOOLEAN|0x00000007

  ## Indicates if we need enable IsaAcpiFloppyB device.<BR><BR>
  #   TRUE  - Enables IsaAcpiFloppyB device.<BR>
  #   FALSE - Doesn't enable IsaAcpiFloppyB device.<BR>
  # @Prompt Enable IsaAcpiFloppyB device.
  gPcAtChipsetPkgTokenSpaceGuid.PcdIsaAcpiFloppyBEnable|TRUE|BOOLEAN|0x00000008

  ## This PCD specifies the base address of the HPET timer.
  # @Prompt HPET base address.
  gPcAtChipsetPkgTokenSpaceGuid.PcdHpetBaseAddress|0xFED00000|UINT32|0x00000009

  ## This PCD specifies the Local APIC Interrupt Vector for the HPET Timer.
  # @Prompt HPET local APIC vector.
  gPcAtChipsetPkgTokenSpaceGuid.PcdHpetLocalApicVector|0x40|UINT8|0x0000000A

  ## This PCD specifies the defaut period of the HPET Timer in 100 ns units.
  #  The default value of 100000 100 ns units is the same as 10 ms.
  # @Prompt Default period of HPET timer.
  gPcAtChipsetPkgTokenSpaceGuid.PcdHpetDefaultTimerPeriod|100000|UINT64|0x0000000B

  ## This PCD specifies the base address of the IO APIC.
  # @Prompt IO APIC base address.
  gPcAtChipsetPkgTokenSpaceGuid.PcdIoApicBaseAddress|0xFEC00000|UINT32|0x0000000C

  ## This PCD specifies the minimal valid year in RTC.
  # @Prompt Minimal valid year in RTC.
  gPcAtChipsetPkgTokenSpaceGuid.PcdMinimalValidYear|1998|UINT16|0x0000000D

  ## This PCD specifies the maximal valid year in RTC.
  # @Prompt Maximal valid year in RTC.
  # @Expression 0x80000001 | gPcAtChipsetPkgTokenSpaceGuid.PcdMaximalValidYear
  gPcAtChipsetPkgTokenSpaceGuid.PcdMaximalValidYear|2097|UINT16|0x0000000E

[PcdsFixedAtBuild, PcdsPatchableInModule]
  ## Defines the ACPI register set base address.
  #  The invalid 0xFFFF is as its default value. It must be configured to the real value.
  # @Prompt ACPI Timer IO Port Address
  gPcAtChipsetPkgTokenSpaceGuid.PcdAcpiIoPortBaseAddress         |0xFFFF|UINT16|0x00000010

  ## Defines the PCI Bus Number of the PCI device that contains the BAR and Enable for ACPI hardware registers.
  # @Prompt ACPI Hardware PCI Bus Number
  gPcAtChipsetPkgTokenSpaceGuid.PcdAcpiIoPciBusNumber            |  0x00| UINT8|0x00000011

  ## Defines the PCI Device Number of the PCI device that contains the BAR and Enable for ACPI hardware registers.
  #  The invalid 0xFF is as its default value. It must be configured to the real value.
  # @Prompt ACPI Hardware PCI Device Number
  gPcAtChipsetPkgTokenSpaceGuid.PcdAcpiIoPciDeviceNumber         |  0xFF| UINT8|0x00000012

  ## Defines the PCI Function Number of the PCI device that contains the BAR and Enable for ACPI hardware registers.
  #  The invalid 0xFF is as its default value. It must be configured to the real value.
  # @Prompt ACPI Hardware PCI Function Number
  gPcAtChipsetPkgTokenSpaceGuid.PcdAcpiIoPciFunctionNumber       |  0xFF| UINT8|0x00000013

  ## Defines the PCI Register Offset of the PCI device that contains the Enable for ACPI hardware registers.
  #  The invalid 0xFFFF is as its default value. It must be configured to the real value.
  # @Prompt ACPI Hardware PCI Register Offset
  gPcAtChipsetPkgTokenSpaceGuid.PcdAcpiIoPciEnableRegisterOffset |0xFFFF|UINT16|0x00000014

  ## Defines the bit mask that must be set to enable the APIC hardware register BAR.
  # @Prompt ACPI Hardware PCI Bar Enable BitMask
  gPcAtChipsetPkgTokenSpaceGuid.PcdAcpiIoBarEnableMask           |  0x00| UINT8|0x00000015

  ## Defines the PCI Register Offset of the PCI device that contains the BAR for ACPI hardware registers.
  #  The invalid 0xFFFF is as its default value. It must be configured to the real value.
  # @Prompt ACPI Hardware PCI Bar Register Offset
  gPcAtChipsetPkgTokenSpaceGuid.PcdAcpiIoPciBarRegisterOffset    |0xFFFF|UINT16|0x00000016

  ## Defines the offset to the 32-bit Timer Value register that resides within the ACPI BAR.
  # @Prompt Offset to 32-bit Timer register in ACPI BAR
  gPcAtChipsetPkgTokenSpaceGuid.PcdAcpiPm1TmrOffset              |0x0008|UINT16|0x00000017

  ## Defines the bit mask to retrieve ACPI IO Port Base Address
  # @Prompt ACPI IO Port Base Address Mask
  gPcAtChipsetPkgTokenSpaceGuid.PcdAcpiIoPortBaseAddressMask     |0xFFFE|UINT16|0x00000018

  ## Reset Control Register address in I/O space.
  # @Prompt Reset Control Register address
  gPcAtChipsetPkgTokenSpaceGuid.PcdResetControlRegister|0x64|UINT64|0x00000019

  ## 8bit Reset Control Register value for cold reset.
  # @Prompt Reset Control Register value for cold reset
  gPcAtChipsetPkgTokenSpaceGuid.PcdResetControlValueColdReset|0xFE|UINT8|0x0000001A

  ## Specifies the initial value for Register_A in RTC.
  # @Prompt Initial value for Register_A in RTC.
  gPcAtChipsetPkgTokenSpaceGuid.PcdInitialValueRtcRegisterA|0x26|UINT8|0x0000001B

  ## Specifies the initial value for Register_B in RTC.
  # @Prompt Initial value for Register_B in RTC.
  gPcAtChipsetPkgTokenSpaceGuid.PcdInitialValueRtcRegisterB|0x02|UINT8|0x0000001C

  ## Specifies the initial value for Register_D in RTC.
  # @Prompt Initial value for Register_D in RTC.
  gPcAtChipsetPkgTokenSpaceGuid.PcdInitialValueRtcRegisterD|0x00|UINT8|0x0000001D

  ## Specifies RTC Index Register address in I/O space.
  # @Prompt RTC Index Register address
  gPcAtChipsetPkgTokenSpaceGuid.PcdRtcIndexRegister|0x70|UINT8|0x0000001E

  ## Specifies RTC Target Register address in I/O space.
  # @Prompt RTC Target Register address
  gPcAtChipsetPkgTokenSpaceGuid.PcdRtcTargetRegister|0x71|UINT8|0x0000001F

[PcdsFixedAtBuild]
  ## Defines the UART base address.
  # @Prompt UART IO Port Base Address
  gPcAtChipsetPkgTokenSpaceGuid.PcdUartIoPortBaseAddress         |0x3F8|UINT16|0x00000020     ## MS_CHANGE

[UserExtensions.TianoCore."ExtraFiles"]
  PcAtChipsetPkgExtra.uni
"""

    def test_valid_input(self):
        a = DecParser()
        st = io.StringIO(TestDecParser.SAMPLE_DEC_FILE)
        a.ParseStream(st)
        self.assertEqual(a.Dict["PACKAGE_NAME"], "TestDecParserPkg")
        self.assertEqual(a.Dict["PACKAGE_GUID"], "57e8a49e-1b3f-41a0-a552-55ad831c15a8")
        self.assertEqual(len(a.Guids), 3)
        self.assertEqual(len(a.Protocols), 1)
        self.assertEqual(len(a.PPIs), 2)
