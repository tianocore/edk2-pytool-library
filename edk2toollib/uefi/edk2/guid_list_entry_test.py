# @file guid_list_test.py
# Contains unit test routines for the guid list class.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import io
import os
from edk2toollib.uefi.edk2.guid_list import GuidListEntry



class TestGuidListEntry(unittest.TestCase):

    def test_valid_input(self):
        GUID = "66341ae8-668f-4192-b44d-5f87b868f041"
        NAME = "testguid"
        FILEPATH = os.path.dirname(os.path.abspath(__file__))
        t = GuidListEntry(NAME, GUID, FILEPATH)
        self.assertEqual(t.name, NAME)
        self.assertEqual(t.guid, GUID)
        self.assertEqual(t.absfilepath, FILEPATH)
        self.assertTrue(GUID in str(t))
        self.assertTrue(FILEPATH in str(t))
        self.assertTrue(NAME in str(t))
