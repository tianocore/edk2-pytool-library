##
# Copyright (C) Microsoft Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
# Python script that converts a raw IVRS table into a struct
##
# spell-checker:ignore IVMD, IOMMUEFR

import unittest
from edk2toollib.acpi.dmar_parser import DMARTable


class DmarParserTest(unittest.TestCase):

    dse_t_01h = None
    dse_t_03h = None
    dse_t_04h = None

    drhd_t = None
    rmrr_t = None

    def test_dmar_parser_dse_01h(self):
        # PCI Endpoint Device
        dse_t_01h = bytes([0x01, 0x08, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00])
        DmarParserTest.dse_t_01h = DMARTable.DeviceScopeStruct(dse_t_01h)
        self.assertNotEqual(DmarParserTest.dse_t_01h, None)
        self.assertEqual(DmarParserTest.dse_t_01h.Type, 0x01)
        self.assertEqual(DmarParserTest.dse_t_01h.Length, 0x08)
        self.assertEqual(DmarParserTest.dse_t_01h.Reserved, 0)
        self.assertEqual(DmarParserTest.dse_t_01h.EnumerationID, 0x00)
        self.assertEqual(DmarParserTest.dse_t_01h.StartBusNumber, 0x00)
        self.assertEqual(DmarParserTest.dse_t_01h.Path[0], ((0x02,), (0x00,)))
        self.assertEqual(DmarParserTest.dse_t_01h.TypeString, "PCI Endpoint Device")

        try:
            dse_01_str = str(DmarParserTest.dse_t_01h)
            self.assertNotEqual(dse_01_str, None)
        except:
            self.assertFalse(False, "Failed to convert Device Scope Entry type 0 object to string")

    def test_dmar_parser_dse_03h(self):
        # IOAPIC
        dse_t_03h = bytes([0x03, 0x08, 0x00, 0x00, 0x02, 0xf0, 0x1f, 0x00])
        DmarParserTest.dse_t_03h = DMARTable.DeviceScopeStruct(dse_t_03h)
        self.assertNotEqual(DmarParserTest.dse_t_03h, None)
        self.assertEqual(DmarParserTest.dse_t_03h.Type, 0x03)
        self.assertEqual(DmarParserTest.dse_t_03h.Length, 0x08)
        self.assertEqual(DmarParserTest.dse_t_03h.Reserved, 0)
        self.assertEqual(DmarParserTest.dse_t_03h.EnumerationID, 0x02)
        self.assertEqual(DmarParserTest.dse_t_03h.StartBusNumber, 0xf0)
        self.assertEqual(DmarParserTest.dse_t_03h.Path[0], ((0x1f,), (0x00,)))
        self.assertEqual(DmarParserTest.dse_t_03h.TypeString, "IOAPIC")

        try:
            dse_03_str = str(DmarParserTest.dse_t_03h)
            self.assertNotEqual(dse_03_str, None)
        except:
            self.assertFalse(False, "Failed to convert Device Scope Entry type 3 object to string")

    def test_dmar_parser_dse_04h(self):
        # MSI_CAPABLE_HPET
        dse_t_04h = bytes([0x04, 0x08, 0x00, 0x00, 0x00, 0x00, 0x1f, 0x00])
        DmarParserTest.dse_t_04h = DMARTable.DeviceScopeStruct(dse_t_04h)
        self.assertNotEqual(DmarParserTest.dse_t_04h, None)
        self.assertEqual(DmarParserTest.dse_t_04h.Type, 0x04)
        self.assertEqual(DmarParserTest.dse_t_04h.Length, 0x08)
        self.assertEqual(DmarParserTest.dse_t_04h.Reserved, 0)
        self.assertEqual(DmarParserTest.dse_t_04h.EnumerationID, 0x00)
        self.assertEqual(DmarParserTest.dse_t_04h.StartBusNumber, 0x00)
        self.assertEqual(DmarParserTest.dse_t_04h.Path[0], ((0x1f,), (0x00,)))
        self.assertEqual(DmarParserTest.dse_t_04h.TypeString, "MSI_CAPABLE_HPET")

        try:
            dse_04_str = str(DmarParserTest.dse_t_04h)
            self.assertNotEqual(dse_04_str, None)
        except:
            self.assertFalse(False, "Failed to convert Device Scope Entry type 4 object to string")

    def test_dmar_parser_drhd(self):
        # DRHD header
        drhd_t = bytes([0x00, 0x00,         # Type
                        0x10, 0x00,         # Length
                        0x00,               # Flags
                        0x00,               # Reserved
                        0x00, 0x00,         # Segment Number
                        0x00, 0x00, 0xd9, 0xfe, 0x00, 0x00, 0x00, 0x00])    # Register Base Address

        DmarParserTest.drhd_t = DMARTable.DRHDStruct(drhd_t, len(drhd_t))
        self.assertNotEqual(DmarParserTest.drhd_t, None)

        self.assertEqual(DmarParserTest.drhd_t.Type, 0x00)
        self.assertEqual(DmarParserTest.drhd_t.Length, 0x10)
        self.assertEqual(DmarParserTest.drhd_t.Flags, 0x00)
        self.assertEqual(DmarParserTest.drhd_t.Reserved, 0x00)
        self.assertEqual(DmarParserTest.drhd_t.SegmentNumber, 0x0000)
        self.assertEqual(DmarParserTest.drhd_t.RegisterBaseAddress, 0x00000000fed90000)

        try:
            drhd_xml = DmarParserTest.drhd_t.toXml()
            self.assertNotEqual(drhd_xml, None)
        except:
            self.assertFalse(False, "Failed to convert DRHD object to xml")

        try:
            drhd_str = str(DmarParserTest.drhd_t)
            self.assertNotEqual(drhd_str, None)
        except:
            self.assertFalse(False, "Failed to convert DRHD object to string")

    def test_dmar_parser_rmrr(self):
        # RMRR header
        rmrr_t = bytes([0x01, 0x00,             # Type
                        0x18, 0x00,             # Length
                        0x00, 0x00,             # Reserved
                        0x00, 0x00,             # SegmentNumber
                        0x00, 0x00, 0x00, 0x8d, 0x00, 0x00, 0x00, 0x00,     # ReservedMemoryBaseAddress
                        0xff, 0xff, 0x7f, 0x8f, 0x00, 0x00, 0x00, 0x00])    # ReservedMemoryRegionLimitAddress

        DmarParserTest.rmrr_t = DMARTable.RMRRStruct(rmrr_t, len(rmrr_t))
        self.assertNotEqual(DmarParserTest.rmrr_t, None)

        self.assertEqual(DmarParserTest.rmrr_t.Type, 0x01)
        self.assertEqual(DmarParserTest.rmrr_t.Length, 0x18)
        self.assertEqual(DmarParserTest.rmrr_t.Reserved, 0x00)
        self.assertEqual(DmarParserTest.rmrr_t.SegmentNumber, 0x00)
        self.assertEqual(DmarParserTest.rmrr_t.ReservedMemoryBaseAddress, 0x8d000000)
        self.assertEqual(DmarParserTest.rmrr_t.ReservedMemoryRegionLimitAddress, 0x8f7fffff)

        try:
            rmrr_xml = DmarParserTest.rmrr_t.toXml()
            self.assertNotEqual(rmrr_xml, None)
        except:
            self.assertFalse(False, "Failed to convert RMRR object to xml")

        try:
            rmrr_str = str(DmarParserTest.rmrr_t)
            self.assertNotEqual(rmrr_str, None)
        except:
            self.assertFalse(False, "Failed to convert RMRR object to string")

    def test_dmar_parser_acpi_header(self):
        # Just ACPI header only
        dmar_header = bytes([0x44, 0x4d, 0x41, 0x52,    # Signature: DMAR
                            0x30, 0x00, 0x00, 0x00,     # Length
                            0x01,                       # Revision
                            0xad,                       # Checksum
                            0x4d, 0x53, 0x46, 0x54, 0x20, 0x20,     # OEM ID: 'MSFT  '
                            0x4d, 0x53, 0x46, 0x54, 0x20, 0x20, 0x20, 0x20,     # OEM Table ID: 'MSFT    '
                            0x01, 0x00, 0x00, 0x00,     # OEM Revision
                            0x49, 0x4e, 0x54, 0x4c,     # CreatorID: 'INTL'
                            0x01, 0x00, 0x00, 0x00,     # Creator revision
                            0x26,                       # HostAddressWidth
                            0x05,                       # Flags
                            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # Reserved

        acpi_header = DMARTable.AcpiTableHeader(dmar_header)
        self.assertNotEqual(acpi_header, None)

        self.assertEqual(acpi_header.Signature, b'DMAR')
        self.assertEqual(acpi_header.Length, 0x30)
        self.assertEqual(acpi_header.Revision, 0x01)
        self.assertEqual(acpi_header.Checksum, 0xad)
        self.assertEqual(acpi_header.OEMID, b'MSFT  ')
        self.assertEqual(acpi_header.OEMTableID, b'MSFT    ')
        self.assertEqual(acpi_header.OEMRevision, 1)
        self.assertEqual(acpi_header.CreatorID, b'INTL')
        self.assertEqual(acpi_header.CreatorRevision, 1)
        self.assertEqual(acpi_header.HostAddressWidth, 0x26)
        self.assertEqual(acpi_header.Flags, 0x05)

        try:
            dmar_xml = acpi_header.toXml()
            self.assertNotEqual(dmar_xml, None)
        except:
            self.assertFalse(False, "Failed to convert ACPI header object to xml")

        try:
            dmar_str = str(acpi_header)
            self.assertNotEqual(dmar_str, None)
        except:
            self.assertFalse(False, "Failed to convert ACPI header object to string")

    def test_dmar_parser_ivrs_full(self):
        # finally a real deal, just to see if they are stitched properly
        full_table = bytes([0x44, 0x4d, 0x41, 0x52, 0x88, 0x00, 0x00, 0x00,
                            0x01, 0xad, 0x4d, 0x53, 0x46, 0x54, 0x20, 0x20,
                            0x4d, 0x53, 0x46, 0x54, 0x20, 0x20, 0x20, 0x20,
                            0x01, 0x00, 0x00, 0x00, 0x49, 0x4e, 0x54, 0x4c,
                            0x01, 0x00, 0x00, 0x00, 0x26, 0x05, 0x00, 0x00,
                            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                            0x00, 0x00, 0x18, 0x00, 0x00, 0x00, 0x00, 0x00,
                            0x00, 0x00, 0xd9, 0xfe, 0x00, 0x00, 0x00, 0x00,
                            0x01, 0x08, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00,
                            0x00, 0x00, 0x20, 0x00, 0x01, 0x00, 0x00, 0x00,
                            0x00, 0x10, 0xd9, 0xfe, 0x00, 0x00, 0x00, 0x00,
                            0x03, 0x08, 0x00, 0x00, 0x02, 0xf0, 0x1f, 0x00,
                            0x04, 0x08, 0x00, 0x00, 0x00, 0x00, 0x1f, 0x00,
                            0x01, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00,
                            0x00, 0x00, 0x00, 0x8d, 0x00, 0x00, 0x00, 0x00,
                            0xff, 0xff, 0x7f, 0x8f, 0x00, 0x00, 0x00, 0x00,
                            0x01, 0x08, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00])

        dmar_table = DMARTable(full_table)
        self.assertEqual(dmar_table.dmar_table.ANDDCount, 0)
        self.assertEqual(len(dmar_table.dmar_table.RMRRlist), 1)
        self.assertEqual(len(dmar_table.dmar_table.SubStructs), 3)

        try:
            dmar_xml = dmar_table.toXml()
            self.assertNotEqual(dmar_xml, None)
        except:
            self.assertFalse(False, "Failed to convert DMAR object to xml")

        try:
            dmar_str = str(dmar_table)
            self.assertNotEqual(dmar_str, None)
        except:
            self.assertFalse(False, "Failed to convert DMAR object to string")


if __name__ == '__main__':
    unittest.main()
