# @file variable_format_Test.py
# Unit test harness for the VariableFormat module/classes.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##


import unittest
import edk2toollib.uefi.edk2.variable_format as VF


class TestVariableHeader(unittest.TestCase):

    def test_set_name(self):
        var = VF.VariableHeader()

        test_name = "MyNewName"
        var.set_name(test_name)

        self.assertEqual(var.Name, test_name)

    def test_get_packed_name(self):
        var = VF.VariableHeader()

        test_name = "MyNewName"
        var.set_name(test_name)

        test_name_packed = bytes.fromhex('4D0079004E00650077004E0061006D0065000000')
        self.assertEqual(var.get_packed_name(), test_name_packed)
