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

    def test_string_conversion(self):
        attributes = EfiVariableAttributes(EFI_VARIABLE_NON_VOLATILE
                                           | EFI_VARIABLE_RUNTIME_ACCESS | EFI_VARIABLE_BOOTSERVICE_ACCESS)
        string = str(attributes)

        self.assertTrue("EFI_VARIABLE_RUNTIME_ACCESS" in string)
        self.assertTrue("EFI_VARIABLE_NON_VOLATILE" in string)
        self.assertTrue("EFI_VARIABLE_BOOTSERVICE_ACCESS" in string)

    def test_empty(self):
        attributes = EfiVariableAttributes(0)

        self.assertEqual(str(attributes), "")
        self.assertEqual(int(attributes), 0)

    def test_int_to_alternate(self):

        attributes = EfiVariableAttributes(EFI_VARIABLE_NON_VOLATILE)
        self.assertEqual(str(attributes), "EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(attributes.get_short_string(), "NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_NON_VOLATILE)

        attributes.update(EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)
        self.assertEqual(str(attributes), "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(attributes.get_short_string(), "BS,NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

        attributes.update(EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS
                          | EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS)
        self.assertEqual(
            str(attributes), "EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS,EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")  # noqa
        self.assertEqual(attributes.get_short_string(), "AT,BS,NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS
                         | EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

    def test_string_to_alternate(self):
        attributes = EfiVariableAttributes("EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(str(attributes), "EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(attributes.get_short_string(), "NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_NON_VOLATILE)

        attributes.update("EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(str(attributes), "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(attributes.get_short_string(), "BS,NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

        attributes.update(
            "EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS,EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")  # noqa
        self.assertEqual(
            str(attributes), "EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS,EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")  # noqa
        self.assertEqual(attributes.get_short_string(), "AT,BS,NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS
                         | EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

    def test_short_string_to_alternate(self):
        attributes = EfiVariableAttributes("NV")
        self.assertEqual(str(attributes), "EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(attributes.get_short_string(), "NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_NON_VOLATILE)

        attributes.update("BS,NV")
        self.assertEqual(str(attributes), "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(attributes.get_short_string(), "BS,NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

        attributes.update("AT,BS,NV")
        self.assertEqual(
            str(attributes), "EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS,EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")  # noqa
        self.assertEqual(attributes.get_short_string(), "AT,BS,NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS
                         | EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

    def test_with_spaces_to_alternate(self):
        attributes = EfiVariableAttributes("BS, NV")
        self.assertEqual(str(attributes), "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(attributes.get_short_string(), "BS,NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)

        attributes.update("EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(str(attributes), "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        self.assertEqual(attributes.get_short_string(), "BS,NV")
        self.assertEqual(int(attributes), EFI_VARIABLE_NON_VOLATILE | EFI_VARIABLE_BOOTSERVICE_ACCESS)
