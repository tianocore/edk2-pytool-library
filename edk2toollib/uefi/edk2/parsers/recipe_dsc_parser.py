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

class SectionProcessor():
    def __init__(self, PreviewLineFunc, ConsumeLineFunc):
        self.Preview = PreviewLineFunc
        self.Consume = ConsumeLineFunc
    
    def _GetSectionHeaderLowercase(cls) -> str:
        ''' [Defines] -> defines '''
        line = self.PreviewLineFunc()
        return line.strip().replace("[", "").lower()

    def AttemptToProcessSection(self, line: str) -> bool:
        ''' Attempts to processor section '''
        return False
    

class DefinesProcessor(SectionProcessor):
    def AttemptToProcessSection(self, line: str) -> bool:
        line = self._GetSectionHeaderLowercase()
        if not line.startswith("defines"):
            return False
        line, source = self.Consume()
        return True

class PcdProcessor(SectionProcessor):
    def AttemptToProcessSection(self, line: str) -> bool:
        line = SectionProcessor._GetSectionHeaderLowercase(self.PreviewLineFunc())
        if not line.startswith("pcd"):
            return False
        line, source = self.Consume()
        return True


class RecipeBasedDscParser(DscParser):
    ''' 
    This acts like a normal DscParser, but outputs recipes 
    Returns none if a file has not been parsed yet
    '''

    def __init__(self):
        super().__init__()
        self.EmitWarnings = False
        self._Modules = set()
        self._Libs = set() # this is the a library class container
        self._Pcds = set()
        self._Skus = set()

    ## Augmented parsing

    def ParseFile(self, filepath):
        if self.Parsed != False:  # make sure we haven't already parsed the file
            return
        super().ParseFile(filepath)
        self._LineIter = 0
        # just go through and process as many sections as we can find
        processors = [
            PcdProcessor(self._PreviewNextLine, self._ProcessSection),
            DefinesProcessor(self._PreviewNextLine, self._ProcessSection)
        ]
        while not self._IsAtEndOfLines:
            for proc in processors:
                if proc.CheckForSectionHeader():
                    break
                line, _ = self._ConsumeNextLine()
                self.Logger.warning(f"Unknown line {line}")

        self.Parsed = True

    def _PreviewNextLine(self):
        ''' Previews the next line without consuming it '''
        if self._IsAtEndOfLines:
            return None
        return self.Lines[self._LineIter]

    @property
    def _IsAtEndOfLines(self):
        return self._LineIter == len(self.Lines) - 1

    def _ConsumeNextLine(self):
        ''' Get the next line for processing '''
        line = self._PreviewNextLine()
        self._LineIter += 1
        # figure out where this line came from
        source = self._GetCurrentSource()
        return (line, source)
    
    def _GetCurrentSource(self):
        ''' Currently pretty inefficent '''
        file_path, lineno = self.Sources[self._LineIter]
        return source_info(file_path, lineno)
    
    def GetMods(self):
        # TODO create compatibility layer
        return None
        #return self.ThreeMods + self.SixMods

    def GetModsEnhanced(self):
        return self._Modules
    
    def GetLibs(self):
        # TODO create compatibility layer
        return None

    def GetLibsEnhanced(self):
        return self._Libs

    def GetSkus(self):
        # Todo 
        return self._Skus

    def GetPcds(self):
        return self._Pcds

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
            raise RuntimeError("You cannot get a recipe for a DSC you haven't parsed")
        rec = recipe()

        # Get output directory
        if "OUTPUT_DIRECTORY" in self.LocalVars:
            rec.output_dir = self.LocalVars["OUTPUT_DIRECTORY"]

        # process libraries
        libraries = self.GetLibsEnhanced()
        for library in libraries:
            pass

        # process Skus
        rec.skus = rec.skus.union(self._Skus)

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
