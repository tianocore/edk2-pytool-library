# @file dsc_test.py
# Tests for the data model for the EDK II DSC
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import unittest
import os
import tempfile
from edk2toollib.uefi.edk2.build_objects.dsc import dsc
from edk2toollib.uefi.edk2.build_objects.dsc import library_class
from edk2toollib.uefi.edk2.build_objects.dsc import component
from edk2toollib.uefi.edk2.build_objects.dsc import definition

class TestDscObject(unittest.TestCase):

    def test_null_creation(self):
        d = dsc()
        self.assertNotEqual(d, None)
    
    def test_dsc_multple_defines(self):
        # When we add an object, it should overwrite the previous one
        d = TestDscObject.create_dsc_object()
        d.defines.add(definition("PLATFORM_NAME", "TEST2"))
        for defin in d.defines:
            if defin.name == "PLATFORM_NAME":  # check to make sure it matches
                self.assertEqual(defin.value, "TEST2")

    def test_get_library_classes(self):
        ''' This serves more as an example of how to walk the DSC to get a library class for a componenet '''
        pass


    @staticmethod
    def create_dsc_object():
        # Normally we would just read the dsc object
        d = dsc()
        # first add the defines
        d.defines.add(definition("PLATFORM_NAME", "TEST"))
        d.defines.add(definition("PLATFORM_GUID", "EB216561-961F-47EE-9EF9-CA426EF547C2"))
        d.defines.add(definition("OUTPUT_DIRECTORY", "Build/TEST"))
        d.defines.add(definition("SUPPORTED_ARCHITECTURES", "IA32 X64 AARCH64"))

        # Next add some library classes

        return d
        