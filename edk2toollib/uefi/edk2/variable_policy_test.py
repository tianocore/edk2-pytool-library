# @file
# Unit test harness for the VariablePolicy module/classes.
#
# Copyright (c) Microsoft Corporation
# SPDX-License-Identifier: BSD-2-Clause-Patent
##


import unittest
import uuid
from edk2toollib.uefi.edk2.variable_policy import VariableLockOnVarStatePolicy


TEST_GUID_1 = uuid.UUID("48B5F961-3F7D-4B88-9BEE-D305ED8256DA")
TEST_GUID_2 = uuid.UUID("65D16747-FCBC-4FAE-A727-7B679A7B23F9")


class TestVariableLockOnVarStatePolicy(unittest.TestCase):
    def test_remaining_buffer(self):
        test_vpl = VariableLockOnVarStatePolicy()
        test_remainder = b'123'
        test_buffer = TEST_GUID_2.bytes_le + b'\x00\x00' + b'\x00A\x00\x00' + test_remainder

        self.assertEqual(test_remainder, test_vpl.decode(test_buffer))

    def test_missing_name(self):
        test_vpl = VariableLockOnVarStatePolicy()

        # Test with no Name field at all.
        test1 = TEST_GUID_1.bytes_le + b'\x00\x00'
        with self.assertRaises(Exception):
            test_vpl.decode(test1)

        # Test with an empty string.
        test2 = test1 + b'\x00\x00'
        with self.assertRaises(Exception):
            test_vpl.decode(test2)

        # Test successful.
        test3 = test1 + b'\x00A\x00\x00'
        _ = test_vpl.decode(test3)

    def test_malformed_name(self):
        test_vpl = VariableLockOnVarStatePolicy()

        # Test with no termination.
        test1 = TEST_GUID_1.bytes_le + b'\x00\x00' + b'\x00A\x00B'
        with self.assertRaises(Exception):
            test_vpl.decode(test1)

        # Test with an unaligned termination.
        test2 = TEST_GUID_1.bytes_le + b'\x00\x00' + b'A\x00B\x00' + b'C' + b'\x00\x00'
        with self.assertRaises(Exception):
            test_vpl.decode(test2)

    def test_to_string(self):
        test_vpl = VariableLockOnVarStatePolicy()
        test_buffer = TEST_GUID_2.bytes_le + b'\x00\x00' + b'A\x00B\x00C\x00\x00\x00'

        test_vpl.decode(test_buffer)

        self.assertEqual(test_vpl.Name, "ABC")
