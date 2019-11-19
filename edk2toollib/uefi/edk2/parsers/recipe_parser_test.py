# @file recipe_parser_test.py
# Contains unit test routines for the dsc => recipe functionality.
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
from edk2toollib.uefi.edk2.build_objects.recipe import recipe


class TestRecipeParser(unittest.TestCase):

    def test_simple_dsc(self):
        rec = recipe()
        pass