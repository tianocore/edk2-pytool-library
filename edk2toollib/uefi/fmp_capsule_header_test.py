# @file tpm2_defs_test.py
# This file contains utility classes to help interpret definitions from the
# Tpm20.h header file in TianoCore.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import unittest
import pytest
from edk2toollib.uefi.fmp_capsule_header import FmpCapsuleHeaderClass


class TestFmpCapsuleHeaderClass(unittest.TestCase):
    @pytest.mark.skip(reason="test is incomplete")
    def test_should_successfully_decode_test_payload(self):
        pass

    def test_embedded_driver_count_should_track_additions(self):
        test_header = FmpCapsuleHeaderClass()
        self.assertEqual(test_header.EmbeddedDriverCount, 0)
        test_header.AddEmbeddedDriver(b'dummydriver')
        self.assertEqual(test_header.EmbeddedDriverCount, 1)
        test_header.AddEmbeddedDriver(b'dummydriver2')
        self.assertEqual(test_header.EmbeddedDriverCount, 2)

    def test_payload_item_count_should_track_additions(self):
        test_header = FmpCapsuleHeaderClass()
        self.assertEqual(test_header.PayloadItemCount, 0)
        test_header.AddFmpCapsuleImageHeader(b'dummyheader')
        self.assertEqual(test_header.PayloadItemCount, 1)
        test_header.AddFmpCapsuleImageHeader(b'dummyheader2')
        self.assertEqual(test_header.PayloadItemCount, 2)

    def test_encoding_twice_should_yield_identical_results(self):
        test_header = FmpCapsuleHeaderClass()
        test_header.AddEmbeddedDriver(b'dummydriver')
        encode_1 = test_header.Encode()
        encode_2 = test_header.Encode()
        self.assertEqual(encode_1, encode_2)
