# @file guid_parser_test.py
# Contains unit test routines for the guid parser class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
from edk2toollib.uefi.edk2.parsers.guid_parser import GuidParser


class TestGuidParser(unittest.TestCase):
    def test_valid_input_guid(self):
        SAMPLE_DATA_C_FORMAT_GUID = "{0x66341ae8, 0x668f, 0x4192, {0xb4, 0x4d, 0x5f, 0x87, 0xb8, 0x68, 0xf0, 0x41}}"  # noqa: E501
        SAMPLE_DATA_REG_FORMAT_GUID = "66341ae8-668f-4192-b44d-5f87b868f041"
        self.assertEqual(GuidParser.reg_guid_from_c_format(SAMPLE_DATA_C_FORMAT_GUID), SAMPLE_DATA_REG_FORMAT_GUID)
        self.assertEqual(GuidParser.c_guid_from_reg_format(SAMPLE_DATA_REG_FORMAT_GUID), SAMPLE_DATA_C_FORMAT_GUID)

        uuid_from_c = GuidParser.uuid_from_guidstring(SAMPLE_DATA_C_FORMAT_GUID)
        uuid_from_reg = GuidParser.uuid_from_guidstring(SAMPLE_DATA_REG_FORMAT_GUID)

        self.assertEqual(
            GuidParser.reg_guid_str_from_uuid(uuid_from_c), GuidParser.reg_guid_str_from_uuid(uuid_from_reg)
        )

        self.assertEqual(GuidParser.c_guid_str_from_uuid(uuid_from_c), GuidParser.c_guid_str_from_uuid(uuid_from_reg))

    def test_invalid_reg_format_to_uuid(self):
        SAMPLE_DATA_REG_FORMAT_GUID = "66341ae8-668f4192b44d-0087b868f041"
        u = GuidParser.uuid_from_guidstring(SAMPLE_DATA_REG_FORMAT_GUID)
        self.assertIsNone(u)

    def test_invalid_reg_format_to_c_format(self):
        SAMPLE_DATA_REG_FORMAT_GUID = "66341ae8-668f4192b44d-0087b868f041"
        u = GuidParser.c_guid_from_reg_format(SAMPLE_DATA_REG_FORMAT_GUID)
        self.assertEqual("", u)

    def test_invalid_c_format_to_uuid(self):
        SAMPLE_DATA_C_FORMAT_GUID = "{0x66341ae8, 0x668f 0x4192 {0xb4, 0x4d, 0x5f, 0x87, 0xb8, 0x68, 0xf0, 0x41}}"
        u = GuidParser.uuid_from_guidstring(SAMPLE_DATA_C_FORMAT_GUID)
        self.assertIsNone(u)

    def test_invalid_c_format_to_reg(self):
        SAMPLE_DATA_C_FORMAT_GUID = (
            "{0x66341ae8, 0x668f4192, 0x1234, {0xb4, 0x4d, 0x5f34, 0x87, 0xb8, 0x68, 0xf0, 0x41}}"  # noqa: E501
        )
        u = GuidParser.reg_guid_from_c_format(SAMPLE_DATA_C_FORMAT_GUID)
        self.assertEqual("", u)

    def test_valid_reg_input_with_brackets(self):
        """check the reg_format functions are able to handle extra {} as reg format sometimes has brackets"""
        SAMPLE_DATA_REG_FORMAT_GUID_WITH = "{66341ae8-668f-4192-b44d-5f87b868f041}"
        SAMPLE_DATA_REG_FORMAT_GUID = "66341ae8-668f-4192-b44d-5f87b868f041"
        u = GuidParser.uuid_from_guidstring(SAMPLE_DATA_REG_FORMAT_GUID_WITH)
        self.assertEqual(SAMPLE_DATA_REG_FORMAT_GUID, GuidParser.reg_guid_str_from_uuid(u))

    def test_valid_reg_input_with_spaces(self):
        """check the reg_format functions are able to handle extra spaces"""
        SAMPLE_DATA_REG_FORMAT_GUID_WITH = "    66341ae8-668f-4192-b44d-5f87b868f041           "
        SAMPLE_DATA_REG_FORMAT_GUID = "66341ae8-668f-4192-b44d-5f87b868f041"
        u = GuidParser.uuid_from_guidstring(SAMPLE_DATA_REG_FORMAT_GUID_WITH)
        self.assertEqual(SAMPLE_DATA_REG_FORMAT_GUID, GuidParser.reg_guid_str_from_uuid(u))

    def test_valid_c_format_input_with_spaces(self):
        """check the c_format functions are able to handle extra spaces"""
        SAMPLE_DATA_C_FORMAT_GUID = (
            "   {  0x66341ae8, 0x668f, 0x4192, {0xb4, 0x4d, 0x5f, 0x87, 0xb8, 0x68, 0xf0, 0x41  }  }   "  # noqa: E501
        )
        SAMPLE_DATA_REG_FORMAT_GUID = "66341ae8-668f-4192-b44d-5f87b868f041"
        u = GuidParser.uuid_from_guidstring(SAMPLE_DATA_C_FORMAT_GUID)
        self.assertEqual(SAMPLE_DATA_REG_FORMAT_GUID, GuidParser.reg_guid_str_from_uuid(u))
