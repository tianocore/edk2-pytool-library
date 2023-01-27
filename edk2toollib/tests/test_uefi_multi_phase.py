# @file
# Code to test UEFI MultiPhase module
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import unittest
from edk2toollib.uefi.uefi_multi_phase import (EfiVariableAttributes,
                                               EFI_VARIABLE_NON_VOLATILE, EFI_VARIABLE_RUNTIME_ACCESS,
                                               EFI_VARIABLE_BOOTSERVICE_ACCESS,
                                               EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS)


class TestUefiMultiphase (unittest.TestCase):

    def test_StringConversion(self):
        Attr = EfiVariableAttributes(EFI_VARIABLE_NON_VOLATILE
                                     | EFI_VARIABLE_RUNTIME_ACCESS | EFI_VARIABLE_BOOTSERVICE_ACCESS)
        string = str(Attr)

        self.assertTrue("EFI_VARIABLE_RUNTIME_ACCESS" in string)
        self.assertTrue("EFI_VARIABLE_NON_VOLATILE" in string)
        self.assertTrue("EFI_VARIABLE_BOOTSERVICE_ACCESS" in string)

    def test_Empty(self):
        Attr = EfiVariableAttributes(0)

        self.assertEqual(str(Attr), "")
        self.assertEqual(int(Attr), 0)

    def test_IntToAlternate(self):

        Attr = EfiVariableAttributes(EFI_VARIABLE_NON_VOLATILE)
        self.assertEqual(str(Attr), "EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_NON_VOLATILE)

        Attr.Update(EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)
        self.assertEqual(str(Attr), "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "BS,NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

        Attr.Update(EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS
                    | EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS)
        self.assertEqual(
            str(Attr), "EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS,EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "AT,BS,NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS
                         | EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

    def test_StringToAlternate(self):
        Attr = EfiVariableAttributes("EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(str(Attr), "EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_NON_VOLATILE)

        Attr.Update("EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(str(Attr), "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "BS,NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

        Attr.Update("EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS,EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(
            str(Attr), "EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS,EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "AT,BS,NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS
                         | EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

    def test_ShortStringToAlternate(self):
        Attr = EfiVariableAttributes("NV")
        self.assertEqual(str(Attr), "EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_NON_VOLATILE)

        Attr.Update("BS,NV")
        self.assertEqual(str(Attr), "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "BS,NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

        Attr.Update("AT,BS,NV")
        self.assertEqual(
            str(Attr), "EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS,EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "AT,BS,NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS
                         | EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

    def test_WithSpacesToAlternate(self):
        Attr = EfiVariableAttributes("BS, NV")
        self.assertEqual(str(Attr), "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "BS,NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

        Attr.Update("EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(str(Attr), "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(Attr.GetShortString(), "BS,NV")
        self.assertEqual(int(Attr), EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)
