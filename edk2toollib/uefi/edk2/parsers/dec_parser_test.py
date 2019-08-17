## @file dec_parser_test.py
# Contains unit test routines for the dec parser class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import os

from edk2toollib.uefi.edk2.parsers.dec_parser import LibraryClassDeclarationEntry
from edk2toollib.uefi.edk2.parsers.dec_parser import GuidDeclarationEntry
from edk2toollib.uefi.edk2.parsers.dec_parser import PpiDeclarationEntry
from edk2toollib.uefi.edk2.parsers.dec_parser import ProtocolDeclarationEntry
import uuid


class TestGuidDeclarationEntry(unittest.TestCase):

    def test_valid_input_guid(self):
        SAMPLE_DATA_GUID_DECL = '''gTestGuid       = { 0x66341ae8, 0x668f, 0x4192, { 0xb4, 0x4d, 0x5f, 0x87, 0xb8, 0x68, 0xf0, 0x41 }}''' #noqa: E501
        SAMPLE_DATA_GUID_STRING_REG_FORMAT = "{66341ae8-668f-4192-b44d-5f87b868f041}"
        a = GuidDeclarationEntry("TestPkg", SAMPLE_DATA_GUID_DECL)
        con = uuid.UUID(SAMPLE_DATA_GUID_STRING_REG_FORMAT)
        self.assertEqual(str(con), str(a.guid))
        self.assertEqual(a.name, "gTestGuid")
        self.assertEqual(a.package_name, "TestPkg")

    def test_valid_input_leading_zero_removed(self):
        SAMPLE_DATA_GUID_DECL = '''gTestGuid       = { 0x6341ae8, 0x668f, 0x4192, { 0xb4, 0x4d, 0x5f, 0x87, 0xb8, 0x68, 0xf0, 0x41 }}''' #noqa: E501
        SAMPLE_DATA_GUID_STRING_REG_FORMAT = "{06341ae8-668f-4192-b44d-5f87b868f041}"
        a = GuidDeclarationEntry("testpkg", SAMPLE_DATA_GUID_DECL)
        con = uuid.UUID(SAMPLE_DATA_GUID_STRING_REG_FORMAT)
        self.assertEqual(str(con), str(a.guid))

    def test_valid_input_reg_format_guid(self):
        SAMPLE_DATA_GUID_DECL = '''gTestGuid       = {06341ae8-668f-4192-b44d-5f87b868f041}'''
        SAMPLE_DATA_GUID_STRING_REG_FORMAT = "{06341ae8-668f-4192-b44d-5f87b868f041}"
        a = GuidDeclarationEntry("testpkg", SAMPLE_DATA_GUID_DECL)
        con = uuid.UUID(SAMPLE_DATA_GUID_STRING_REG_FORMAT)
        self.assertEqual(str(con), str(a.guid))

    def test_invalid_guid_format(self):
        SAMPLE_DATA_GUID_DECL = '''gTestGuid       = 0x6341ae8, 0x668f, 0x4192, 0xb4, 0x4d, 0x5f, 0x87, 0xb8, 0x68, 0xf0, 0x41''' #noqa: E501
        SAMPLE_DATA_GUID_STRING_REG_FORMAT = "{06341ae8-668f-4192-b44d-5f87b868f041}"
        with self.assertRaises(ValueError):
            a = GuidDeclarationEntry("testpkg", SAMPLE_DATA_GUID_DECL)

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
        SAMPLE_DATA_PROTOCOL_DECL = """gTestProtocolGuid    = {0xb6d12b5a, 0x5338, 0x44ac, {0xac, 0x31, 0x1e, 0x9f, 0xa8, 0xc7, 0xe0, 0x1e}}""" # noqa: E501
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

