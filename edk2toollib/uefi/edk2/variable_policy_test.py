# @file
# Unit test harness for the VariablePolicy module/classes.
#
# Copyright (c) Microsoft Corporation
# SPDX-License-Identifier: BSD-2-Clause-Patent
##


import unittest
import uuid
from edk2toollib.uefi.edk2.variable_policy import VariableLockOnVarStatePolicy, VariablePolicyEntry


TEST_GUID_1 = uuid.UUID("48B5F961-3F7D-4B88-9BEE-D305ED8256DA")
TEST_GUID_2 = uuid.UUID("65D16747-FCBC-4FAE-A727-7B679A7B23F9")

TEST_POLICY_ENTRY = b''.fromhex("000001006A004600E222FFB0EA4A2547A6E55317FB8FD39C00000000FFFFFFFF000000000000000003AFAFAFC690F5ECF9F887438422486E3CCD8B2001AF45004F00440000004C0061007300740041007400740065006D00700074005300740061007400750073000000")
TEST_POLICY_ENTRY_GUID = uuid.UUID("B0FF22E2-4AEA-4725-A6E5-5317FB8FD39C")


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


class TestVariablePolicyEntry(unittest.TestCase):
    def test_create_and_to_string(self):
        test_vp = VariablePolicyEntry()
        to_string = str(test_vp)

        # Check for the LockType string.
        self.assertIn("NONE", to_string)

        test_vp.LockPolicyType = VariablePolicyEntry.TYPE_LOCK_ON_CREATE
        to_string = str(test_vp)

        # Check for the new LockType string.
        self.assertIn("CREATE", to_string)

    def test_csv_formatting(self):
        header_row = VariablePolicyEntry.csv_header()
        self.assertIn("Namespace", header_row)
        self.assertIn("LockPolicyType", header_row)

        test_vp = VariablePolicyEntry()
        test_vp.LockPolicyType = VariablePolicyEntry.TYPE_LOCK_ON_CREATE
        csv_row = test_vp.csv_row()
        self.assertEqual(len(header_row), len(csv_row))
        self.assertIn("ON_CREATE", csv_row)

    def test_decoding(self):
        test_vp = VariablePolicyEntry()
        test_vp.decode(TEST_POLICY_ENTRY)

        self.assertEqual(test_vp.Namespace, TEST_POLICY_ENTRY_GUID)
        self.assertEqual(test_vp.LockPolicyType, VariablePolicyEntry.TYPE_LOCK_ON_VAR_STATE)
        self.assertEqual(test_vp.Name, "LastAttemptStatus")
        self.assertEqual(test_vp.LockPolicy.Name, "EOD")