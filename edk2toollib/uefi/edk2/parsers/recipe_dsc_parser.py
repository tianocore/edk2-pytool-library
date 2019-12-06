# @file recipte_parser.py
# Code to help parse DSC files into recipes
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.dsc_parser import DscParser
from edk2toollib.uefi.edk2.build_objects.recipe import recipe
from edk2toollib.uefi.edk2.build_objects.recipe import source_info
from edk2toollib.uefi.edk2.build_objects.recipe import component
from edk2toollib.uefi.edk2.build_objects.recipe import sku_id
from edk2toollib.uefi.edk2.build_objects.recipe import pcd
import os


class RecipeBasedDscParser(DscParser):
    ''' 
    This acts like a normal DscParser, but outputs recipes 
    Returns none if a file has not been parsed yet
    '''

    def __init__(self):
        super().__init__()
        self.EmitWarnings = False
        self.Modules = set()
        self.Libs = set() # this is the a library class container
        self.Pcds = set()
        self.Skus = set()

    ## Augmented parsing

    
    def GetMods(self):
        # TODO create compatibility layer
        return None
        #return self.ThreeMods + self.SixMods

    def GetModsEnhanced(self):
        return self.Modules
    
    def GetLibs(self):
        # TODO create compatibility layer
        return None

    def GetLibsEnhanced(self):
        return self.Libs

    def GetSkus(self):
        return self.Skus

    def GetPcds(self):
        return self.Pcds

    ## DSC <=> Recipe translation methods
    
    @classmethod
    def GetDscFromRecipe(cls, rec) -> str:
        ''' Gets the DSC string for a recipe  '''
        if type(rec) is not recipe:
            raise ValueError(f"{rec} is not a recipe object")
        strings = cls.GetDscLinesFromObj(rec)
        return "\n".join(strings)
    
    @classmethod
    def GetDscLinesFromObj(cls, obj) -> list:
        ''' gets the DSC strings for an data model objects '''
        lines = []
        if type(obj) is recipe:
            lines.append("[Defines]")
            lines.append(f"OUTPUT_DIRECTORY = {obj.output_dir}")

            # Second do the Skus
            lines.append("[SkuIds]")
            #lines += [cls.GetDscLinesFromObj(x) for x in self.skus]

            # Next do the components
            #lines += [x.to_dsc(include_header=True) for x in self.components]


        return lines


    def GetRecipe(self):
        if not self.Parsed:
            return None
        rec = recipe()

        # Get output directory
        if "OUTPUT_DIRECTORY" in self.LocalVars:
            rec.output_dir = self.LocalVars["OUTPUT_DIRECTORY"]

        # process libraries
        libraries = self.GetLibsEnhanced()
        for library in libraries:
            pass

        # process Skus
        skus = self.GetSkus()
        for s in skus:
            rec.skus.add(sku_id(s["id"], s["name"], s["parent"]))

        # process PCD's
        pcds = self.GetPcds()
        pcd_store = set()
        for p in pcds:
            namespace, name = p.split(".")
            new_pcd = pcd(namespace, name)
            pcd_store.add(new_pcd)
            # TODO extend PCD in base parser

        #print(pcd_store)

        # process components
        modules = self.GetModsEnhanced()
        for module in modules:
            pass
            source = source_info(module['file'], module['lineno'])
            comp = component(module['data'], [], source)
            rec.components.add(comp)
            # TODO - we should have parsed all the libraries
            # TODO- we should have parsed the skus

            #raise ValueError()
        return rec
