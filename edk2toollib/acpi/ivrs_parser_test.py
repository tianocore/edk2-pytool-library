##
# Copyright (C) Microsoft Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
# Python script that converts a raw IVRS table into a struct
##

import unittest
import logging
from edk2toollib.acpi.ivrs_parser import IVRS_TABLE


class IvrsParserTest(unittest.TestCase):

    # we are mainly looking for exception to be thrown

    ivrs_header = bytes([0x49, 0x56, 0x52, 0x53,
                         0x30, 0x00, 0x00, 0x00,
                         0x02,
                         0xBC,
                         0x41, 0x4D, 0x44, 0x20, 0x20, 0x00,
                         0x41, 0x4D, 0x44, 0x20, 0x49, 0x56, 0x52, 0x53,
                         0x01, 0x00, 0x00, 0x00,
                         0x41, 0x4D, 0x44, 0x20,
                         0x00, 0x00, 0x00, 0x00,
                         0x43, 0x30, 0x20, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    ivhd_t_10h = bytes([0x10,
                        0x90,
                        0x18, 0x00,
                        0x02, 0x00,
                        0x40, 0x00,
                        0x00, 0x00, 0x28, 0xFD, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00,
                        0x00, 0x00,
                        0x6E, 0x8F, 0x04, 0x80])

    ivhd_t_11h = bytes([0x11,
                        0x90,
                        0x28, 0x00,
                        0x02, 0x00,
                        0x40, 0x00,
                        0x00, 0x00, 0x28, 0xFD, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00,
                        0x00, 0x00,
                        0x00, 0x02, 0x04, 0x00,
                        0xDA, 0x4A, 0x29, 0x22, 0xEF, 0x77, 0x4F, 0x00,
                        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    ivhd_t_40h = bytes([0x40,
                        0x90,
                        0x28, 0x00,
                        0x02, 0x00,
                        0x40, 0x00,
                        0x00, 0x00, 0x28, 0xFD, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00,
                        0x00, 0x00,
                        0x6E, 0x8F, 0x04, 0x80,
                        0xDA, 0x4A, 0x29, 0x22, 0xEF, 0x77, 0x4F, 0x00,
                        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    dte_t_00h = bytes([0x00, 0x00, 0x00, 0x00])
    dte_t_01h = bytes([0x01, 0x00, 0x00, 0x00])
    dte_t_02h = bytes([0x02, 0x02, 0x00, 0x00])
    dte_t_03h = bytes([0x03, 0x03, 0x00, 0x00])
    dte_t_04h = bytes([0x04, 0xFF, 0xFF, 0x00])

    dte_t_40h = bytes([0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    dte_t_42h = bytes([0x42, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    dte_t_43h = bytes([0x43, 0x00, 0xFF, 0x00, 0x00, 0xA4, 0x00, 0x00])
    dte_t_44h = bytes([0x44, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    dte_t_46h = bytes([0x46, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80])
    dte_t_47h = bytes([0x47, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80])
    dte_t_48h = bytes([0x48, 0x00, 0x00, 0x00, 0x22, 0x01, 0x00, 0x01])

    dte_t_f0h_0 = bytes([0xF0, 0x11, 0x11, 0xF6,
                        0x46, 0x41, 0x4B, 0x45, 0x30, 0x30, 0x30, 0x30,
                        0x43, 0x4F, 0x4D, 0x50, 0x30, 0x30, 0x30, 0x30,
                        0x00, 0x00])

    dte_t_f0h_1 = bytes([0xF0, 0x11, 0x11, 0xF6,
                        0x46, 0x41, 0x4B, 0x45, 0x30, 0x30, 0x30, 0x30,
                        0x43, 0x4F, 0x4D, 0x50, 0x30, 0x30, 0x30, 0x30,
                        0x01, 0x08,
                        0x0D, 0xF0, 0xED, 0xFE, 0xEF, 0xBE, 0xAD, 0xDE])

    dte_t_f0h_2 = bytes([0xF0, 0x11, 0x11, 0xF6,
                        0x46, 0x41, 0x4B, 0x45, 0x30, 0x30, 0x30, 0x30,
                        0x43, 0x4F, 0x4D, 0x50, 0x30, 0x30, 0x30, 0x30,
                        0x02, 0x09,
                        0x5C, 0x5F, 0x53, 0x42, 0x2E, 0x46, 0x55, 0x52, 0x30])

    ivmd_t_20h = bytes([0x20, 0x08, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00, 0xD1, 0xFE, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    ivmd_t_21h = bytes([0x21, 0x08, 0x20, 0x00, 0x75, 0x00, 0x00, 0x00,
                        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0xB0, 0x7E, 0xCF, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x00, 0x2F, 0x01, 0x00, 0x00, 0x00, 0x00])

    ivmd_t_22h = bytes([0x22, 0x08, 0x20, 0x00, 0x74, 0x00, 0x75, 0x00,
                        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0xB0, 0x7E, 0xCF, 0x00, 0x00, 0x00, 0x00,
                        0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    def test_ivrs_parser_init(self):
        ivrs = IVRS_TABLE(IvrsParserTest.ivrs_header)
        ivrs.DumpInfo()
        ivrs.ToXmlElementTree()
        self.assertNotEqual(ivrs, None)

        ivrs_byte = ivrs.Encode()
        ivrs2 = IVRS_TABLE(ivrs_byte)
        self.assertEqual(ivrs2.Encode(), ivrs_byte)

    def test_ivrs_parser_ivhd_10h(self):
        ivrs = IVRS_TABLE(IvrsParserTest.ivrs_header)
        ivhd = ivrs.IVHD_STRUCT(IvrsParserTest.ivhd_t_10h)
        dte_02h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_02h)
        dte_03h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_03h + IvrsParserTest.dte_t_04h)
        dte_00h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_00h)
        ivhd.addDTEEntry(dte_02h)
        ivhd.addDTEEntry(dte_03h)
        ivhd.addDTEEntry(dte_00h)
        ivrs.addIVHDEntry(ivhd)
        ivrs.DumpInfo()
        ivrs.ToXmlElementTree()
        self.assertNotEqual(ivrs, None)

        ivrs_byte = ivrs.Encode()
        ivrs2 = IVRS_TABLE(ivrs_byte)
        self.assertEqual(ivrs2.Encode(), ivrs_byte)

    def test_ivrs_parser_ivhd_11h(self):
        ivrs = IVRS_TABLE(IvrsParserTest.ivrs_header)
        ivhd = ivrs.IVHD_STRUCT(IvrsParserTest.ivhd_t_11h)
        dte_02h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_02h)
        dte_03h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_03h + IvrsParserTest.dte_t_04h)
        ivhd.addDTEEntry(dte_02h)
        ivhd.addDTEEntry(dte_03h)
        ivrs.addIVHDEntry(ivhd)
        ivrs.DumpInfo()
        ivrs.ToXmlElementTree()
        self.assertNotEqual(ivrs, None)

        ivrs_byte = ivrs.Encode()
        ivrs2 = IVRS_TABLE(ivrs_byte)
        self.assertEqual(ivrs2.Encode(), ivrs_byte)

    def test_ivrs_parser_ivhd_10h_2(self):
        ivrs = IVRS_TABLE(IvrsParserTest.ivrs_header)
        ivhd = ivrs.IVHD_STRUCT(IvrsParserTest.ivhd_t_10h)
        dte_42h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_42h)
        dte_43h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_43h + IvrsParserTest.dte_t_04h)
        dte_00h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_00h)
        dte_46h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_46h)
        dte_47h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_47h + IvrsParserTest.dte_t_04h)
        dte_48h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_48h)
        ivhd.addDTEEntry(dte_42h)
        ivhd.addDTEEntry(dte_43h)
        ivhd.addDTEEntry(dte_00h)
        ivhd.addDTEEntry(dte_46h)
        ivhd.addDTEEntry(dte_47h)
        ivhd.addDTEEntry(dte_48h)
        ivrs.addIVHDEntry(ivhd)
        ivrs.DumpInfo()
        ivrs.ToXmlElementTree()
        self.assertNotEqual(ivrs, None)

        ivrs_byte = ivrs.Encode()
        ivrs2 = IVRS_TABLE(ivrs_byte)
        self.assertEqual(ivrs2.Encode(), ivrs_byte)

    def test_ivrs_parser_ivhd_40h(self):
        ivrs = IVRS_TABLE(IvrsParserTest.ivrs_header)
        ivhd = ivrs.IVHD_STRUCT(IvrsParserTest.ivhd_t_40h)
        dte_f0h_0 = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_f0h_0)
        dte_f0h_1 = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_f0h_1)
        dte_f0h_2 = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_f0h_2)
        ivhd.addDTEEntry(dte_f0h_0)
        ivhd.addDTEEntry(dte_f0h_1)
        ivhd.addDTEEntry(dte_f0h_2)
        ivrs.addIVHDEntry(ivhd)
        ivrs.DumpInfo()
        ivrs.ToXmlElementTree()
        self.assertNotEqual(ivrs, None)

        ivrs_byte = ivrs.Encode()
        ivrs2 = IVRS_TABLE(ivrs_byte)
        self.assertEqual(ivrs2.Encode(), ivrs_byte)

    def test_ivrs_parser_ivmd_20h(self):
        ivrs = IVRS_TABLE(IvrsParserTest.ivrs_header)

        ivhd = ivrs.IVHD_STRUCT(IvrsParserTest.ivhd_t_11h)
        dte_02h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_02h)
        dte_03h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_03h + IvrsParserTest.dte_t_04h)
        ivhd.addDTEEntry(dte_02h)
        ivhd.addDTEEntry(dte_03h)
        ivrs.addIVHDEntry(ivhd)

        ivmd = ivrs.IVMD_STRUCT(IvrsParserTest.ivmd_t_20h)
        ivrs.addIVMDEntry(ivmd)

        ivrs.DumpInfo()
        ivrs.ToXmlElementTree()
        self.assertNotEqual(ivrs, None)

        ivrs_byte = ivrs.Encode()
        ivrs2 = IVRS_TABLE(ivrs_byte)
        self.assertEqual(ivrs2.Encode(), ivrs_byte)

    def test_ivrs_parser_ivmd_21h(self):
        ivrs = IVRS_TABLE(IvrsParserTest.ivrs_header)

        ivhd = ivrs.IVHD_STRUCT(IvrsParserTest.ivhd_t_11h)
        dte_02h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_02h)
        dte_03h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_03h + IvrsParserTest.dte_t_04h)
        ivhd.addDTEEntry(dte_02h)
        ivhd.addDTEEntry(dte_03h)
        ivrs.addIVHDEntry(ivhd)

        ivmd = ivrs.IVMD_STRUCT(IvrsParserTest.ivmd_t_21h)
        ivrs.addIVMDEntry(ivmd)

        ivrs.DumpInfo()
        ivrs.ToXmlElementTree()
        self.assertNotEqual(ivrs, None)

        ivrs_byte = ivrs.Encode()
        ivrs2 = IVRS_TABLE(ivrs_byte)
        self.assertEqual(ivrs2.Encode(), ivrs_byte)

    def test_ivrs_parser_ivmd_22h(self):
        ivrs = IVRS_TABLE(IvrsParserTest.ivrs_header)

        ivhd = ivrs.IVHD_STRUCT(IvrsParserTest.ivhd_t_11h)
        dte_02h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_02h)
        dte_03h = ivrs.DEVICE_TABLE_ENTRY(IvrsParserTest.dte_t_03h + IvrsParserTest.dte_t_04h)
        ivhd.addDTEEntry(dte_02h)
        ivhd.addDTEEntry(dte_03h)
        ivrs.addIVHDEntry(ivhd)

        ivmd = ivrs.IVMD_STRUCT(IvrsParserTest.ivmd_t_22h)
        ivrs.addIVMDEntry(ivmd)

        ivrs.DumpInfo()
        ivrs.ToXmlElementTree()
        self.assertNotEqual(ivrs, None)

        ivrs_byte = ivrs.Encode()
        ivrs2 = IVRS_TABLE(ivrs_byte)
        self.assertEqual(ivrs2.Encode(), ivrs_byte)


if __name__ == '__main__':
    unittest.main()
