# @file dsc_recipe_translator
## Translates a DSC into a recipe or a recipe into a DSC
# It will also print that DSC to a file
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent

class DscRecipeTranslator():
    @classmethod
    def dsc_to_recipe(cls, dsc_obj):
        return None

    @classmethod
    def recipe_to_dsc(cls, rec):
        return None

    @classmethod
    def dsc_to_file(cls, dsc_obj, filepath):
        # first convert the DSC to a recipe
        rec = DscRecipeTranslator.dsc_to_recipe(dsc_obj)
        # then just output the recipe
        DscRecipeTranslator.recipe_to_dsc_file(rec, filepath)
        pass

    @classmethod
    def recipe_to_dsc_file(cls, rec, filepath):
        # create the file
        # output each element of the DSC into it?
        pass
