# @file
# Code to test UEFI MultiPhase module
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import unittest
from edk2toollib.uefi.uefi_multi_phase import *


class TestUefiMultiphase (unittest.TestCase):

    def test_StringConversion(self):
        attr = EfiVariableAttributes(EFI_VARIABLE_NON_VOLATILE
                                     | EFI_VARIABLE_RUNTIME_ACCESS | EFI_VARIABLE_BOOTSERVICE_ACCESS)
        string = str(attr)

        self.assertTrue("EFI_VARIABLE_RUNTIME_ACCESS" in string)
        self.assertTrue("EFI_VARIABLE_NON_VOLATILE" in string)
        self.assertTrue("EFI_VARIABLE_BOOTSERVICE_ACCESS" in string)
