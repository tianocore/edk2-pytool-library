# @file recipte_parser.py
# Code to help parse DSC files into recipes
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.dsc_parser import DscParser
from edk2toollib.uefi.edk2.build_objects.recipe import recipe
import os


class RecipeParser(DscParser):
    ''' This acts like a normal DscParser, but outputs recipes '''
    def GetRecipe(self):
        recipe = recipe()
        return recipe
