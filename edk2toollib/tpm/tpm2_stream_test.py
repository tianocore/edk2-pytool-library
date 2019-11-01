# @file tpm2_stream_test.py
# This file contains utility classes to help marshal and un-marshal data to/from the TPM.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##


import unittest
import struct
from edk2toollib.tpm import tpm2_defs as Tpm2Defs
from edk2toollib.tpm import tpm2_stream as Tpm2Stream


class Tpm2StreamElement(unittest.TestCase):

    def test_object_has_zero_size_by_default(self):
        so = Tpm2Stream.Tpm2StreamElement()
        self.assertEqual(so.get_size(), 0)


class Tpm2CommandHeader(unittest.TestCase):

    def test_ch_marshals_correctly(self):
        ch1 = Tpm2Stream.TPM2_COMMAND_HEADER(0x4321, 0x00000000, 0xDEADBEEF)
        ch2 = Tpm2Stream.TPM2_COMMAND_HEADER(0x8001, 0x0000000A, Tpm2Defs.TPM_CC_Clear)

        self.assertEqual(ch1.marshal(), bytearray.fromhex('432100000000DEADBEEF'))
        self.assertEqual(ch2.marshal(), bytearray.fromhex('80010000000A') + struct.pack(">L", Tpm2Defs.TPM_CC_Clear))

    def test_ch_has_correct_size(self):
        ch1 = Tpm2Stream.TPM2_COMMAND_HEADER(0x4321, 0x00000000, 0xDEADBEEF)
        self.assertEqual(ch1.get_size(), 0x0A)

    def test_ch_size_can_be_updated(self):
        ch1 = Tpm2Stream.TPM2_COMMAND_HEADER(0x4321, 0x00000000, 0xDEADBEEF)
        self.assertEqual(ch1.marshal(), bytearray.fromhex('432100000000DEADBEEF'))
        ch1.update_size(0x1234)
        self.assertEqual(ch1.marshal(), bytearray.fromhex('432100001234DEADBEEF'))
