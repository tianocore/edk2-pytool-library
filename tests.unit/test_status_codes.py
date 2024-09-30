# @file
# Code to test UEFI status code module
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import unittest
from edk2toollib.uefi.status_codes import UefiStatusCode


class TestUefiStatusCodes(unittest.TestCase):
    def test_Hex64ToString_NotError(self):
        StatusCode = "0x0000000000000000"
        self.assertEqual(UefiStatusCode().ConvertHexString64ToString(StatusCode), "Success")

    def test_Hex64ToString_ErrorNotFound(self):
        StatusCode = "0x800000000000000E"
        self.assertEqual(UefiStatusCode().ConvertHexString64ToString(StatusCode), "Not Found")

    def test_Hex64ToString_Error_Invalid_Len(self):
        StatusCode = hex(len(UefiStatusCode.ErrorCodeStrings) + 0x8000000000000000)
        self.assertEqual(UefiStatusCode().ConvertHexString64ToString(StatusCode), "Undefined StatusCode")

    def test_Hex32ToString_NotError(self):
        StatusCode = "0x00000000"
        self.assertEqual(UefiStatusCode().ConvertHexString32ToString(StatusCode), "Success")

    def test_Hex32ToString_ErrorInvalidParameter(self):
        StatusCode = "0x80000002"
        self.assertEqual(UefiStatusCode().ConvertHexString32ToString(StatusCode), "Invalid Parameter")

    def test_Hex32ToString_Error_Invalid_Len(self):
        StatusCode = hex(len(UefiStatusCode.ErrorCodeStrings) + 0x80000000)
        self.assertEqual(UefiStatusCode().ConvertHexString32ToString(StatusCode), "Undefined StatusCode")

    def test_Hex32ToString_NonError_Invalid_Len(self):
        StatusCode = hex(len(UefiStatusCode.NonErrorCodeStrings))
        self.assertEqual(UefiStatusCode().ConvertHexString32ToString(StatusCode), "Undefined StatusCode")
