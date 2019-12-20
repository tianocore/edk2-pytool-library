# @file dsc_parser.py
# Code to help parse DSC files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.limited_dsc_parser import LimitedDscParser
from edk2toollib.uefi.edk2.build_objects.dsc import dsc
from edk2toollib.uefi.edk2.build_objects.dsc import source_info
from edk2toollib.uefi.edk2.build_objects.dsc import component
from edk2toollib.uefi.edk2.build_objects.dsc import library
from edk2toollib.uefi.edk2.build_objects.dsc import build_option
from edk2toollib.uefi.edk2.build_objects.dsc import sku_id
from edk2toollib.uefi.edk2.build_objects.dsc import pcd
import os

class SectionProcessor():
    def __init__(self, PreviewLineFunc, ConsumeLineFunc, ObjectSet = set()):
        self.Preview = PreviewLineFunc
        self.Consume = ConsumeLineFunc
        self.Storage = ObjectSet

    def _GetSectionHeaderLowercase(self) -> str:
        ''' [Defines] -> defines '''
        line = self.Preview()
        return line.strip().replace("[", "").lower()

    def AttemptToProcessSection(self) -> bool:
        ''' Attempts to process the section, returning true if successful '''
        if not self._GetSectionHeaderLowercase().startswith(self.SECTION_TAG):
            return False
        else:
            line, source = self.Consume()
            section_data = self.GetSectionData(line, source)
        objects = self.ExtractObjects(section_data)
        self.HandleObjectExtraction(objects)

        return True

    def HandleObjectExtraction(self, objects):
        for obj in objects:
            self.Storage.add(obj)

    def GetSectionData(self, line, source):
        ''' returns the data in whatever format you want '''
        return None

    def ExtractObjects(self, current_mode = None) -> list:
        ''' extracts the data model objects from the current state '''
        objects = []
        while True:
            line = str(self.Preview())
            if line == None:
                break
            obj = self.ExtractObjectFromLine(line, current_mode)
            if obj is None:
                break
            objects.append(obj)
        return objects

    def ExtractObjectFromLine(self, line, current_mode = None) -> object:
        ''' see if you can extract an object from a line- make sure to consume it. Return None if you can't '''
        raise NotImplementedError()


class DefinesProcessor(SectionProcessor):
    SECTION_TAG = "defines"

    def ExtractObjectFromLine(self, line, current_mode = None) -> object:
        ''' extracts the data model objects from the current state '''
        if line.count("=") != 1 and not line.strip().lower().startswith("define "): # if we don't know what to do with it, don't worry about it
            return None
        line, source = self.Consume()

        return "TEST"

class PcdProcessor(SectionProcessor):
    SECTION_TAG = "pcd"

    def ExtractObjectFromLine(self, line, current_mode = None) -> object:
        ''' extracts the data model objects from the current state '''
        if line.count("|") == 0:
            return None
        if line.count(".") == 0:
            return None

        components = line.split("|")
        name_data = components[0]
        if name_data.count(".") != 1:
            return None
        namespace, name = name_data.split(".")
        _, source = self.Consume()
        value = components[1] # TODO: further split this        
        return pcd(namespace, name, value, source)

class SkuIdProcessor(SectionProcessor):
    SECTION_TAG = "skuids"

    def ExtractObjectFromLine(self, line, current_mode = None) -> object:
        ''' extracts the data model objects from the current state '''
        if line.count("|") < 1:
            return None
        line, source = self.Consume()
        parts = line.split("|")
        id_num = parts[0]
        name = parts[1]
        if len(parts) == 2:
            return sku_id(id_num, name)
        elif len(parts) == 3:
            return sku_id(id_num, name, parts[2])

class LibraryClassProcessor(SectionProcessor):
    SECTION_TAG = "libraryclasses"

    def ExtractObjectFromLine(self, line, current_mode = None) -> object:
        ''' extracts the data model objects from the current state '''
        if line.count("|") != 1:
            return None
        line, source = self.Consume()
        library_class, inf = line.split("|")
        return library(library_class, inf, source)

class BuildOptionsProcessor(SectionProcessor):
    """ Parses build option information """
    # EX: MSFT:*_*_*_CC_FLAGS = /D MDEPKG_NDEBU
    # {FAMILY}:{TARGET}_{TAGNAME}_{ARCH}_{TOOLCODE}_{ATTRIBUTE}
    SECTION_TAG = "buildoptions"

    def ExtractObjectFromLine(self, line, current_mode = None) -> object:
        ''' extracts the data model objects from the current state '''
        if line.count("=") < 1: # if we don't have an equals sign
            return None
        tag, _, data = line.partition("=")
        if tag.count(":") > 1:
            return None
        if tag.count("_") != 4:
            return None

        _, source = self.Consume()
        data = data.strip()
        
        replace = False
        if data.startswith("="):
            replace = True
            data = data[1:]
        
        tag_parts = tag.split(":", 1)
        family = None
        if len(tag_parts) > 1:
            family = tag_parts[0]
            tag_parts = tag_parts[1]
        else:
            tag_parts = tag_parts[0]
        target, tagname, arch, tool, attribute = tag_parts.split("_")
        return build_option(tool, attribute, data, target, tagname, arch, family, replace, source_info=source)

class ComponentsProcessor(SectionProcessor):
    SECTION_TAG = "components"

    def ExtractObjectFromLine(self, line, current_mode = None) -> object:
        ''' extracts the data model objects from the current state '''
        multi_section = False
        if line.endswith("{"):
            multi_section = True
            line = line.replace("{", "").strip()
        if not line.endswith(".inf"):
            return None
        inf = line
        _, source_info = self.Consume()
        comp = component(inf, source_info=source_info)

        if multi_section: # continue to parse
            self.ExtractSubSection(comp)
        return comp

    def ExtractSubSection(self, comp):
        while True:
            line, _ = self.Consume()
            if line == "}":
                return False

class DscParser(LimitedDscParser):
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
        self._BuildOptions = set()
        self._Defines = set()

    ## Augmented parsing

    def ParseFile(self, filepath):
        if self.Parsed != False:  # make sure we haven't already parsed the file
            return
        super().ParseFile(filepath)
        self._LineIter = 0
        # just go through and process as many sections as we can find
        self.dsc = dsc(filepath)
        processors = [
            PcdProcessor(self._PreviewNextLine, self._ConsumeNextLine, self.dsc.pcds),
            DefinesProcessor(self._PreviewNextLine, self._ConsumeNextLine, self.dsc.defines),
            LibraryClassProcessor(self._PreviewNextLine, self._ConsumeNextLine, self.dsc.libraries),
            SkuIdProcessor(self._PreviewNextLine, self._ConsumeNextLine, self.dsc.skus),
            ComponentsProcessor(self._PreviewNextLine, self._ConsumeNextLine, self.dsc.components),
            BuildOptionsProcessor(self._PreviewNextLine, self._ConsumeNextLine, self.dsc.build_options),
        ]
        while not self._IsAtEndOfLines:
            success = False
            for proc in processors:
                if proc.AttemptToProcessSection():
                    success = True
                    break
            if not success and not self._IsAtEndOfLines:
                line, _ = self._ConsumeNextLine()
                self.Logger.warning(f"Unknown line {line}")
        self.Parsed = True
        self.__PopulateDsc()
        return self.dsc

    def __PopulateDsc(self):
        ''' puts all the information we've collected into the DSC '''
        pass

    def _PreviewNextLine(self):
        ''' Previews the next line without consuming it '''
        if self._IsAtEndOfLines:
            return None
        return self.Lines[self._LineIter]
    

    @property
    def _IsAtEndOfLines(self):
        return self._LineIter == len(self.Lines)

    def _ConsumeNextLine(self):
        ''' Get the next line for processing '''
        line = self._PreviewNextLine()
        self._LineIter += 1
        # figure out where this line came from
        source = self._GetCurrentSource()
        return (line, source)

    def _GetCurrentSource(self):
        ''' Currently pretty inefficent '''
        if self._IsAtEndOfLines:
            return None
        file_path, lineno = self.Sources[self._LineIter]
        return source_info(file_path, lineno)

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
            for x in obj.skus:
                lines += cls.GetDscLinesFromObj(x)

            # Next do the components
            for x in obj.components:
                lines += cls.GetDscLinesFromObj(x)

        elif type(obj) is sku_id:
            lines.append(f"{obj.id}|{obj.name}|{obj.parent}")
            pass

        return lines

