# @file tpm2_defs_test.py
# This file contains utility classes to help interpret definitions from the
# Tpm20.h header file in TianoCore.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import unittest
import edk2toollib.tpm.tpm2_defs as t2d


class TestCommandCode(unittest.TestCase):

    def test_get_code_returns_codes(self):
        self.assertEqual(t2d.CommandCode.get_code('TPM_CC_Clear'), 0x00000126)
        self.assertEqual(t2d.CommandCode.get_code('TPM_CC_ActivateCredential'), 0x00000147)

    def test_get_code_returns_none_if_not_found(self):
        self.assertEqual(t2d.CommandCode.get_code('I_AM_NOT_A_VALID_CODE'), None)
        self.assertEqual(t2d.CommandCode.get_code(None), None)

    def test_get_string_returns_strings(self):
        self.assertEqual(t2d.CommandCode.get_string(0x00000126), 'TPM_CC_Clear')
        self.assertEqual(t2d.CommandCode.get_string(0x00000147), 'TPM_CC_ActivateCredential')

    def test_get_string_returns_none_if_not_found(self):
        self.assertEqual(t2d.CommandCode.get_string(0xFFFFFFFF), None)
