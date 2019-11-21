##
# Copyright (C) Microsoft Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
# Python script that converts a raw IVRS table into a struct
##

import unittest
from edk2toollib.acpi.ivrs_parser import IVRS_TABLE


class IvrsParserTest(unittest.TestCase):

    dte_00h = None
    dte_01h = None
    dte_02h = None
    dte_03h = None
    dte_42h = None
    dte_43h = None
    dte_46h = None
    dte_47h = None
    dte_48h = None
    dte_f0h_0 = None
    dte_f0h_1 = None
    dte_f0h_2 = None

    ivhd_10h = None
    ivhd_11h = None
    ivhd_40h = None

    ivmd_20h = None
    ivmd_21h = None
    ivmd_22h = None

    ivrs_table = None

    # All the dte types start with Type (1 byte), DeviceID (2 bytes), DTE Settings (1 byte)
    def test_ivrs_parser_dte_00h(self):
        # Reserved device
        dte_t_00h = bytes([0x00, 0x00, 0x00, 0x00])
        IvrsParserTest.dte_00h = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_00h)
        self.assertNotEqual(IvrsParserTest.dte_00h.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_00h.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RESERVED)
        self.assertEqual(IvrsParserTest.dte_00h.DeviceID, 0)
        self.assertEqual(IvrsParserTest.dte_00h.DTESetting, 0)

    def test_ivrs_parser_dte_01h(self):
        # All devices
        dte_t_01h = bytes([0x01, 0xFF, 0xFF, 0x00])
        IvrsParserTest.dte_01h = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_01h)
        self.assertEqual(IvrsParserTest.dte_01h.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALL)
        self.assertEqual(IvrsParserTest.dte_01h.DTESetting, 0)

    def test_ivrs_parser_dte_02h(self):
        # Select device
        dte_t_02h = bytes([0x02, 0x5A, 0x5A, 0x00])
        IvrsParserTest.dte_02h = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_02h)
        self.assertNotEqual(IvrsParserTest.dte_02h.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_02h.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.SELECT)
        self.assertEqual(IvrsParserTest.dte_02h.DeviceID, 0x5A5A)
        self.assertEqual(IvrsParserTest.dte_02h.DTESetting, 0)

    def test_ivrs_parser_dte_03h(self):
        # Start of device range
        dte_t_03h = bytes([0x03, 0xBE, 0xBA, 0x00])
        dte_t_04h = bytes([0x04, 0xFF, 0xFF, 0x00])
        IvrsParserTest.dte_03h = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_03h + dte_t_04h)
        self.assertNotEqual(IvrsParserTest.dte_03h.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_03h.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RANGE_START)
        self.assertEqual(IvrsParserTest.dte_03h.DeviceID, 0xBABE)
        self.assertEqual(IvrsParserTest.dte_03h.DTESetting, 0)
        self.assertEqual(IvrsParserTest.dte_03h.EndDeviceID, 0xFFFF)

    def test_ivrs_parser_dte_42h(self):
        # Alias select device
        dte_t_42h = bytes([0x42, 0xAD, 0xDE, 0x00, 0x00, 0xEF, 0xBE, 0x00])
        IvrsParserTest.dte_42h = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_42h)
        self.assertNotEqual(IvrsParserTest.dte_42h.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_42h.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALIAS_SELECT)
        self.assertEqual(IvrsParserTest.dte_42h.DeviceID, 0xDEAD)
        self.assertEqual(IvrsParserTest.dte_42h.DTESetting, 0)
        self.assertEqual(IvrsParserTest.dte_42h.SourceDeviceID, 0xBEEF)

    def test_ivrs_parser_dte_43h(self):
        # Alias range device
        dte_t_43h = bytes([0x43, 0xED, 0xFE, 0x00, 0x00, 0x0D, 0xF0, 0x00])
        dte_t_04h = bytes([0x04, 0xFF, 0xFF, 0x00])
        IvrsParserTest.dte_43h = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_43h + dte_t_04h)
        self.assertNotEqual(IvrsParserTest.dte_43h.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_43h.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALIAS_RANGE_START)
        self.assertEqual(IvrsParserTest.dte_43h.DeviceID, 0xFEED)
        self.assertEqual(IvrsParserTest.dte_43h.DTESetting, 0)
        self.assertEqual(IvrsParserTest.dte_43h.SourceDeviceID, 0xF00D)
        self.assertEqual(IvrsParserTest.dte_43h.EndDeviceID, 0xFFFF)

    def test_ivrs_parser_dte_46h(self):
        # Extended select device
        dte_t_46h = bytes([0x46, 0x05, 0xB1, 0x00, 0xFE, 0xCA, 0xEF, 0xBE])
        IvrsParserTest.dte_46h = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_46h)
        self.assertNotEqual(IvrsParserTest.dte_46h.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_46h.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.EX_SELECT)
        self.assertEqual(IvrsParserTest.dte_46h.DeviceID, 0xB105)
        self.assertEqual(IvrsParserTest.dte_46h.DTESetting, 0)
        self.assertEqual(IvrsParserTest.dte_46h.ExtendedDTESetting, 0xBEEFCAFE)

    def test_ivrs_parser_dte_47h(self):
        # Extended range of device
        dte_t_47h = bytes([0x47, 0xDE, 0xC0, 0x00, 0xBE, 0xBA, 0xAD, 0xAB])
        dte_t_04h = bytes([0x04, 0xFF, 0xFF, 0x00])
        IvrsParserTest.dte_47h = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_47h + dte_t_04h)
        self.assertNotEqual(IvrsParserTest.dte_47h.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_47h.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.EX_RANGE_START)
        self.assertEqual(IvrsParserTest.dte_47h.DeviceID, 0xC0DE)
        self.assertEqual(IvrsParserTest.dte_47h.DTESetting, 0)
        self.assertEqual(IvrsParserTest.dte_47h.ExtendedDTESetting, 0xABADBABE)
        self.assertEqual(IvrsParserTest.dte_47h.EndDeviceID, 0xFFFF)

    def test_ivrs_parser_dte_48h(self):
        # Special device (IOAPIC, HPET)
        dte_t_48h = bytes([0x48, 0x00, 0x00, 0x00, 0x15, 0xAD, 0xDE, 0x01])
        IvrsParserTest.dte_48h = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_48h)
        self.assertNotEqual(IvrsParserTest.dte_48h.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_48h.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.SPECIAL)
        self.assertEqual(IvrsParserTest.dte_48h.DTESetting, 0)
        self.assertEqual(IvrsParserTest.dte_48h.Handle, 0x15)
        self.assertEqual(IvrsParserTest.dte_48h.SourceDeviceID, 0xDEAD)
        self.assertEqual(IvrsParserTest.dte_48h.Variety, 0x01)

    def test_ivrs_parser_dte_f0h_0(self):
        # ACPI device without UID
        dte_t_f0h_0 = bytes([0xF0, 0x11, 0x11, 0xF6,
                            0x46, 0x41, 0x4B, 0x45, 0x30, 0x30, 0x30, 0x30,     # HID: 'FAKE0000'
                            0x43, 0x4F, 0x4D, 0x50, 0x30, 0x30, 0x30, 0x30,     # CID: 'COMP0000'
                            0x00,   # UID format
                            0x00])  # UID length
        IvrsParserTest.dte_f0h_0 = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_f0h_0)
        self.assertNotEqual(IvrsParserTest.dte_f0h_0.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_f0h_0.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ACPI)
        self.assertEqual(IvrsParserTest.dte_f0h_0.DeviceID, 0x1111)
        self.assertEqual(IvrsParserTest.dte_f0h_0.DTESetting, 0xF6)
        self.assertEqual(IvrsParserTest.dte_f0h_0.HID, b'FAKE0000')
        self.assertEqual(IvrsParserTest.dte_f0h_0.CID, b'COMP0000')
        self.assertEqual(IvrsParserTest.dte_f0h_0.UIDFormat, 0x00)
        self.assertEqual(IvrsParserTest.dte_f0h_0.UIDLength, 0x00)

    def test_ivrs_parser_dte_f0h_1(self):
        # ACPI device with integer UID
        dte_t_f0h_1 = bytes([0xF0, 0x11, 0x11, 0xF6,
                            0x46, 0x41, 0x4B, 0x45, 0x30, 0x30, 0x30, 0x30,     # HID: 'FAKE0000'
                            0x43, 0x4F, 0x4D, 0x50, 0x30, 0x30, 0x30, 0x30,     # CID: 'COMP0000'
                            0x01,   # UID format
                            0x08,   # UID length
                            0x0D, 0xF0, 0xED, 0xFE, 0xEF, 0xBE, 0xAD, 0xDE])    # UID: 0xDEADBEEFFEEDF00D
        IvrsParserTest.dte_f0h_1 = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_f0h_1)
        self.assertNotEqual(IvrsParserTest.dte_f0h_1.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_f0h_1.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ACPI)
        self.assertEqual(IvrsParserTest.dte_f0h_1.DeviceID, 0x1111)
        self.assertEqual(IvrsParserTest.dte_f0h_1.DTESetting, 0xF6)
        self.assertEqual(IvrsParserTest.dte_f0h_1.HID, b'FAKE0000')
        self.assertEqual(IvrsParserTest.dte_f0h_1.CID, b'COMP0000')
        self.assertEqual(IvrsParserTest.dte_f0h_1.UIDFormat, 0x01)
        self.assertEqual(IvrsParserTest.dte_f0h_1.UIDLength, 0x08)
        self.assertEqual(IvrsParserTest.dte_f0h_1.UID, 0xDEADBEEFFEEDF00D)

    def test_ivrs_parser_dte_f0h_2(self):
        # ACPI device with string UID
        dte_t_f0h_2 = bytes([0xF0, 0x11, 0x11, 0xF6,
                            0x46, 0x41, 0x4B, 0x45, 0x30, 0x30, 0x30, 0x30,     # HID: 'FAKE0000'
                            0x43, 0x4F, 0x4D, 0x50, 0x30, 0x30, 0x30, 0x30,     # CID: 'COMP0000'
                            0x02,   # UID format
                            0x09,   # UID length
                            0x5C, 0x5F, 0x53, 0x42, 0x2E, 0x46, 0x55, 0x52, 0x30])  # UID: '\_SB.FUR0'
        IvrsParserTest.dte_f0h_2 = IVRS_TABLE.DEVICE_TABLE_ENTRY(dte_t_f0h_2)
        self.assertNotEqual(IvrsParserTest.dte_f0h_2.Encode(), None)
        self.assertEqual(IvrsParserTest.dte_f0h_2.Type, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ACPI)
        self.assertEqual(IvrsParserTest.dte_f0h_2.DeviceID, 0x1111)
        self.assertEqual(IvrsParserTest.dte_f0h_2.DTESetting, 0xF6)
        self.assertEqual(IvrsParserTest.dte_f0h_2.HID, b'FAKE0000')
        self.assertEqual(IvrsParserTest.dte_f0h_2.CID, b'COMP0000')
        self.assertEqual(IvrsParserTest.dte_f0h_2.UIDFormat, 0x02)
        self.assertEqual(IvrsParserTest.dte_f0h_2.UIDLength, 0x09)
        self.assertEqual(IvrsParserTest.dte_f0h_2.UID, b'\\_SB.FUR0')

    def test_ivrs_parser_ivhd_10h(self):
        # I/O Virtualization Hardware Definition (IVHD) Type 10h header
        ivhd_t_10h = bytes([0x10,           # Type
                            0x90,           # Flags
                            0x18, 0x00,     # Length
                            0x02, 0x00,     # DeviceID
                            0x40, 0x00,     # Capability offset
                            0xEF, 0xBE, 0xAD, 0xDE, 0x0D, 0xF0, 0xED, 0xFE,     # IOMMU base address
                            0x00, 0x00,     # PCI Segment Group
                            0x00, 0x00,     # IOMMU info
                            0xBE, 0xBA, 0xAD, 0xAB])    # IOMMU Feature Reporting

        IvrsParserTest.ivhd_10h = IVRS_TABLE.IVHD_STRUCT(ivhd_t_10h)
        self.assertNotEqual(IvrsParserTest.ivhd_10h.Encode(), None)
        self.assertEqual(IvrsParserTest.ivhd_10h.Type, IVRS_TABLE.IVHD_STRUCT.IVHD_TYPE.TYPE_10H)
        self.assertEqual(IvrsParserTest.ivhd_10h.Flags, 0x90)
        self.assertEqual(IvrsParserTest.ivhd_10h.Length, 0x18)
        self.assertEqual(IvrsParserTest.ivhd_10h.DeviceID, 0x02)
        self.assertEqual(IvrsParserTest.ivhd_10h.CapabilityOffset, 0x40)
        self.assertEqual(IvrsParserTest.ivhd_10h.IOMMUBaseAddress, 0xFEEDF00DDEADBEEF)
        self.assertEqual(IvrsParserTest.ivhd_10h.SegmentGroup, 0)
        self.assertEqual(IvrsParserTest.ivhd_10h.IOMMUInfo, 0)
        self.assertEqual(IvrsParserTest.ivhd_10h.IOMMUFeatureInfo, 0xABADBABE)

    def test_ivrs_parser_ivhd_11h(self):
        # I/O Virtualization Hardware Definition (IVHD) Type 11h header
        ivhd_t_11h = bytes([0x11,           # Type
                            0x90,           # Flags
                            0x28, 0x00,     # Length
                            0x02, 0x00,     # DeviceID
                            0x40, 0x00,     # Capability offset
                            0xEF, 0xBE, 0xAD, 0xDE, 0x0D, 0xF0, 0xED, 0xFE,     # IOMMU base address
                            0x00, 0x00,     # PCI Segment Group
                            0x00, 0x00,     # IOMMU info
                            0xBE, 0xBA, 0xAD, 0xAB,    # IOMMU Attributes
                            0xDA, 0x4A, 0x29, 0x22, 0xEF, 0x77, 0x4F, 0x00,     # EFR Register Image
                            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])    # Reserved

        IvrsParserTest.ivhd_11h = IVRS_TABLE.IVHD_STRUCT(ivhd_t_11h)
        self.assertNotEqual(IvrsParserTest.ivhd_11h.Encode(), None)
        self.assertEqual(IvrsParserTest.ivhd_11h.Type, IVRS_TABLE.IVHD_STRUCT.IVHD_TYPE.TYPE_11H)
        self.assertEqual(IvrsParserTest.ivhd_11h.Flags, 0x90)
        self.assertEqual(IvrsParserTest.ivhd_11h.Length, 0x28)
        self.assertEqual(IvrsParserTest.ivhd_11h.DeviceID, 0x02)
        self.assertEqual(IvrsParserTest.ivhd_11h.CapabilityOffset, 0x40)
        self.assertEqual(IvrsParserTest.ivhd_11h.IOMMUBaseAddress, 0xFEEDF00DDEADBEEF)
        self.assertEqual(IvrsParserTest.ivhd_11h.SegmentGroup, 0)
        self.assertEqual(IvrsParserTest.ivhd_11h.IOMMUInfo, 0)
        self.assertEqual(IvrsParserTest.ivhd_11h.IOMMUFeatureInfo, 0xABADBABE)
        self.assertEqual(IvrsParserTest.ivhd_11h.IOMMUEFRImage, 0x4F77EF22294ADA)

    def test_ivrs_parser_ivhd_40h(self):
        # I/O Virtualization Hardware Definition (IVHD) Type 40h header
        ivhd_t_40h = bytes([0x40,           # Type
                            0x90,           # Flags
                            0x28, 0x00,     # Length
                            0x02, 0x00,     # DeviceID
                            0x40, 0x00,     # Capability offset
                            0xEF, 0xBE, 0xAD, 0xDE, 0x0D, 0xF0, 0xED, 0xFE,     # IOMMU base address
                            0x00, 0x00,     # PCI Segment Group
                            0x00, 0x00,     # IOMMU info
                            0xBE, 0xBA, 0xAD, 0xAB,    # IOMMU Attributes
                            0xDA, 0x4A, 0x29, 0x22, 0xEF, 0x77, 0x4F, 0x00,     # EFR Register Image
                            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])    # Reserved

        IvrsParserTest.ivhd_40h = IVRS_TABLE.IVHD_STRUCT(ivhd_t_40h)
        self.assertNotEqual(IvrsParserTest.ivhd_40h.Encode(), None)
        self.assertEqual(IvrsParserTest.ivhd_40h.Type, IVRS_TABLE.IVHD_STRUCT.IVHD_TYPE.TYPE_40H)
        self.assertEqual(IvrsParserTest.ivhd_40h.Flags, 0x90)
        self.assertEqual(IvrsParserTest.ivhd_40h.Length, 0x28)
        self.assertEqual(IvrsParserTest.ivhd_40h.DeviceID, 0x02)
        self.assertEqual(IvrsParserTest.ivhd_40h.CapabilityOffset, 0x40)
        self.assertEqual(IvrsParserTest.ivhd_40h.IOMMUBaseAddress, 0xFEEDF00DDEADBEEF)
        self.assertEqual(IvrsParserTest.ivhd_40h.SegmentGroup, 0)
        self.assertEqual(IvrsParserTest.ivhd_40h.IOMMUInfo, 0)
        self.assertEqual(IvrsParserTest.ivhd_40h.IOMMUFeatureInfo, 0xABADBABE)
        self.assertEqual(IvrsParserTest.ivhd_40h.IOMMUEFRImage, 0x4F77EF22294ADA)

    def test_ivrs_parser_ivmd_20h(self):
        # IVMD Types 20h Format
        ivmd_t_20h = bytes([0x20,           # Type
                            0x08,           # Flags
                            0x20, 0x00,     # Length
                            0x00, 0x00,     # DeviceID
                            0x00, 0x00,     # Auxiliary data
                            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,     # Reserved
                            0xEF, 0xBE, 0xAD, 0xDE, 0x0D, 0xF0, 0xED, 0xFE,     # IVMD start address
                            0x00, 0xAD, 0xBB, 0xDA, 0xDE, 0xC0, 0x05, 0xB1])    # IVMD memory block length

        IvrsParserTest.ivmd_20h = IVRS_TABLE.IVMD_STRUCT(ivmd_t_20h)
        self.assertNotEqual(IvrsParserTest.ivmd_20h.Encode(), None)
        self.assertEqual(IvrsParserTest.ivmd_20h.Type, IVRS_TABLE.IVMD_STRUCT.IVMD_TYPE.TYPE_20H)
        self.assertEqual(IvrsParserTest.ivmd_20h.Flags, 0x08)
        self.assertEqual(IvrsParserTest.ivmd_20h.Length, 0x20)
        self.assertEqual(IvrsParserTest.ivmd_20h.DeviceID, 0)
        self.assertEqual(IvrsParserTest.ivmd_20h.AuxiliaryData, 0)
        self.assertEqual(IvrsParserTest.ivmd_20h.Reserved, 0)
        self.assertEqual(IvrsParserTest.ivmd_20h.IVMDStartAddress, 0xFEEDF00DDEADBEEF)
        self.assertEqual(IvrsParserTest.ivmd_20h.IVMDMemoryBlockLength, 0xB105C0DEDABBAD00)

    def test_ivrs_parser_ivmd_21h(self):
        # IVMD Types 21h Format
        ivmd_t_21h = bytes([0x21,           # Type
                            0x08,           # Flags
                            0x20, 0x00,     # Length
                            0x00, 0x00,     # DeviceID
                            0x00, 0x00,     # Auxiliary data
                            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,     # Reserved
                            0xEF, 0xBE, 0xAD, 0xDE, 0x0D, 0xF0, 0xED, 0xFE,     # IVMD start address
                            0x00, 0xAD, 0xBB, 0xDA, 0xDE, 0xC0, 0x05, 0xB1])    # IVMD memory block length

        IvrsParserTest.ivmd_21h = IVRS_TABLE.IVMD_STRUCT(ivmd_t_21h)
        self.assertNotEqual(IvrsParserTest.ivmd_21h.Encode(), None)
        self.assertEqual(IvrsParserTest.ivmd_21h.Type, IVRS_TABLE.IVMD_STRUCT.IVMD_TYPE.TYPE_21H)
        self.assertEqual(IvrsParserTest.ivmd_21h.Flags, 0x08)
        self.assertEqual(IvrsParserTest.ivmd_21h.Length, 0x20)
        self.assertEqual(IvrsParserTest.ivmd_21h.DeviceID, 0)
        self.assertEqual(IvrsParserTest.ivmd_21h.AuxiliaryData, 0)
        self.assertEqual(IvrsParserTest.ivmd_21h.Reserved, 0)
        self.assertEqual(IvrsParserTest.ivmd_21h.IVMDStartAddress, 0xFEEDF00DDEADBEEF)
        self.assertEqual(IvrsParserTest.ivmd_21h.IVMDMemoryBlockLength, 0xB105C0DEDABBAD00)

    def test_ivrs_parser_ivmd_22h(self):
        # IVMD Types 22h Format
        ivmd_t_22h = bytes([0x22,           # Type
                            0x08,           # Flags
                            0x20, 0x00,     # Length
                            0x00, 0x00,     # DeviceID
                            0x00, 0x00,     # Auxiliary data
                            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,     # Reserved
                            0xEF, 0xBE, 0xAD, 0xDE, 0x0D, 0xF0, 0xED, 0xFE,     # IVMD start address
                            0x00, 0xAD, 0xBB, 0xDA, 0xDE, 0xC0, 0x05, 0xB1])    # IVMD memory block length

        IvrsParserTest.ivmd_22h = IVRS_TABLE.IVMD_STRUCT(ivmd_t_22h)
        self.assertNotEqual(IvrsParserTest.ivmd_22h.Encode(), None)
        self.assertEqual(IvrsParserTest.ivmd_22h.Type, IVRS_TABLE.IVMD_STRUCT.IVMD_TYPE.TYPE_22H)
        self.assertEqual(IvrsParserTest.ivmd_22h.Flags, 0x08)
        self.assertEqual(IvrsParserTest.ivmd_22h.Length, 0x20)
        self.assertEqual(IvrsParserTest.ivmd_22h.DeviceID, 0)
        self.assertEqual(IvrsParserTest.ivmd_22h.AuxiliaryData, 0)
        self.assertEqual(IvrsParserTest.ivmd_22h.Reserved, 0)
        self.assertEqual(IvrsParserTest.ivmd_22h.IVMDStartAddress, 0xFEEDF00DDEADBEEF)
        self.assertEqual(IvrsParserTest.ivmd_22h.IVMDMemoryBlockLength, 0xB105C0DEDABBAD00)

    def test_ivrs_parser_ivrs_empty(self):
        ivrs_header = bytes([0x49, 0x56, 0x52, 0x53,    # Signature: IVRS
                            0x30, 0x00, 0x00, 0x00,     # Length
                            0x02,                       # Rivision
                            0x9C,                       # Checksum
                            0x41, 0x4D, 0x44, 0x20, 0x20, 0x20,     # OEM ID: 'AMD  '
                            0x41, 0x4D, 0x44, 0x20, 0x49, 0x56, 0x52, 0x53,     # OEM Table ID: 'AMD IVRS'
                            0x01, 0x00, 0x00, 0x00,     # OEM Revision
                            0x41, 0x4D, 0x44, 0x20,     # CreatorID: 'AMD '
                            0x00, 0x00, 0x00, 0x00,     # Creator revision
                            0x43, 0x30, 0x20, 0x00,     # IVinfo
                            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])    # Reserved: 0

        IvrsParserTest.ivrs = IVRS_TABLE(ivrs_header)
        self.assertNotEqual(IvrsParserTest.ivrs.Encode(), None)

        self.assertEqual(IvrsParserTest.ivrs.acpi_header.Signature, b'IVRS')
        self.assertEqual(IvrsParserTest.ivrs.acpi_header.Length, 0x30)
        self.assertEqual(IvrsParserTest.ivrs.acpi_header.Revision, 0x02)
        self.assertEqual(IvrsParserTest.ivrs.acpi_header.Checksum, 0x9C)
        self.assertEqual(IvrsParserTest.ivrs.acpi_header.OEMID, b'AMD   ')
        self.assertEqual(IvrsParserTest.ivrs.acpi_header.OEMTableID, b'AMD IVRS')
        self.assertEqual(IvrsParserTest.ivrs.acpi_header.OEMRevision, 1)
        self.assertEqual(IvrsParserTest.ivrs.acpi_header.CreatorID, b'AMD ')
        self.assertEqual(IvrsParserTest.ivrs.acpi_header.CreatorRevision, 0)
        self.assertEqual(IvrsParserTest.ivrs.acpi_header.IVinfo, 0x00203043)
        self.assertEqual(IvrsParserTest.ivrs.acpi_header.Reserved, 0)

    def test_ivrs_parser_ivrs_full(self):
        # finally the big daddy... load it up!
        IvrsParserTest.ivhd_10h.addDTEEntry(IvrsParserTest.dte_01h)
        IvrsParserTest.ivhd_10h.addDTEEntry(IvrsParserTest.dte_02h)
        IvrsParserTest.ivhd_10h.addDTEEntry(IvrsParserTest.dte_03h)
        IvrsParserTest.ivhd_10h.addDTEEntry(IvrsParserTest.dte_00h)

        IvrsParserTest.ivhd_11h.addDTEEntry(IvrsParserTest.dte_42h)
        IvrsParserTest.ivhd_11h.addDTEEntry(IvrsParserTest.dte_43h)
        IvrsParserTest.ivhd_11h.addDTEEntry(IvrsParserTest.dte_46h)
        IvrsParserTest.ivhd_11h.addDTEEntry(IvrsParserTest.dte_47h)
        IvrsParserTest.ivhd_11h.addDTEEntry(IvrsParserTest.dte_48h)

        IvrsParserTest.ivhd_40h.addDTEEntry(IvrsParserTest.dte_f0h_0)
        IvrsParserTest.ivhd_40h.addDTEEntry(IvrsParserTest.dte_f0h_1)
        IvrsParserTest.ivhd_40h.addDTEEntry(IvrsParserTest.dte_f0h_2)

        IvrsParserTest.ivrs.addIVHDEntry(IvrsParserTest.ivhd_10h)
        IvrsParserTest.ivrs.addIVMDEntry(IvrsParserTest.ivmd_20h)
        IvrsParserTest.ivrs.addIVHDEntry(IvrsParserTest.ivhd_11h)
        IvrsParserTest.ivrs.addIVMDEntry(IvrsParserTest.ivmd_21h)
        IvrsParserTest.ivrs.addIVHDEntry(IvrsParserTest.ivhd_40h)
        IvrsParserTest.ivrs.addIVMDEntry(IvrsParserTest.ivmd_22h)

        IvrsParserTest.ivrs.DumpInfo()
        IvrsParserTest.ivrs.ToXmlElementTree()

        ivrs_byte = IvrsParserTest.ivrs.Encode()
        ivrs2 = IVRS_TABLE(ivrs_byte)
        self.assertEqual(ivrs2.Encode(), ivrs_byte)


if __name__ == '__main__':
    unittest.main()
