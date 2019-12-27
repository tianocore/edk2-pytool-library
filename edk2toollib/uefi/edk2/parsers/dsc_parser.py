# @file dsc_parser.py
# Code to help parse DSC files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.limited_dsc_parser import LimitedDscParser
from edk2toollib.uefi.edk2.build_objects.dsc import *
import os


class SectionProcessor():
    SECTION_TAG = ""

    def __init__(self, PreviewLineFunc, ConsumeLineFunc, ObjectSet=(lambda x: None)):
        self.Preview = PreviewLineFunc
        self.Consume = ConsumeLineFunc
        self.Storage = ObjectSet

    def _GetSectionHeaderLowercase(self, line) -> str:
        ''' [Defines] -> defines '''
        return line.strip().replace("[", "").lower()

    def AttemptToProcessSection(self) -> bool:
        ''' Attempts to process the section, returning true if successful '''
        section_data = None
        if not self.ValidSectionHeader(self.Preview()):
            return False
        else:
            line, source = self.Consume()
            section_data = self.GetSectionData(line, source)
        objects = self.ExtractObjects(section_data)
        self.HandleObjectExtraction(objects, section_data)

        return True

    def ValidSectionHeader(self, line):
        return self._GetSectionHeaderLowercase(line).startswith(self.SECTION_TAG)
            
    def HandleObjectExtraction(self, objects, section_data):
        for obj in objects:
            self.Storage(obj, section_data)

    def GetSectionData(self, line, source):
        ''' returns the data in whatever format you want '''
        if line.startswith("[") and line.endswith("]"):
            line = line[1:-1]  # remove the first and section place
        if line.count(",") > 0:
            parts = line.split(",")
            return [self.GetSectionData(x, source) for x in parts]
        if not line.lower().startswith(self.SECTION_TAG):
            return None
        if len(line) == len(self.SECTION_TAG):
            return ""
        return line[len(self.SECTION_TAG):]

    def ExtractObjects(self, current_section=None) -> list:
        ''' extracts the data model objects from the current state '''
        objects = []
        while True:
            line = str(self.Preview()).strip()
            if line == None:
                break
            if line.startswith("[") and line.endswith("]"):
                ''' this is a section header '''
                break
            obj = self.ProcessDefine(line, current_section)
            if obj is None:
                obj = self.ExtractObjectFromLine(line, current_section)
            if obj is None:
                break
            objects.append(obj)
        return objects

    def ProcessDefine(self, line, current_section=None) -> object:
        ''' process a defines '''
        if not line.upper().startswith("DEFINE"):
            return None
        if line.count("=") < 1:
            return None
        parts = line[6:].split("=", 1)
        print(parts)
        name = str(parts[0]).strip()
        if name.count(" ") > 0:
            return None
        value = str(parts[1]).strip()

        line, source = self.Consume()
        return definition(name, value, local=True, source_info=source)

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
        ''' see if you can extract an object from a line- make sure to consume it. Return None if you can't '''
        raise NotImplementedError()


class DefinesProcessor(SectionProcessor):
    SECTION_TAG = "defines"

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        if line.count("=") < 1:  # if we don't know what to do with it, don't worry about it
            return None

        parts = line.split("=", 1)
        name = str(parts[0]).strip()
        if name.count(" ") > 0:
            return None  # we don't know what to do with this
        value = parts[1]

        line, source = self.Consume()
        return definition(name, value, local=False, source_info=source)

    def GetSectionData(self, line, source):
        return None


class PcdProcessor(SectionProcessor):
    SECTION_TAG = "pcds"

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        if line.count("|") == 0:
            return None
        if line.count(".") == 0:
            return None
        if current_section is None:
            return None
        components = line.split("|", 1)
        name_data = components[0]
        if name_data.count(".") != 1:
            return None
        namespace, name = name_data.split(".")
        if len(components) == 1:
            return None
        
        value = components[1].strip()  # TODO: further split this

        #TODO: handle different sections
        # featureflag pcd's are only allowed to be 0, 1, TRUE, FALSE
        if current_section.pcd_type == "FEATUREFLAG":
            if value.upper() not in ["0","1", "TRUE", "FALSE"]:
                return None
        # 
        if value.count("|") == 0:
            if current_section.pcd_type == "PATCHABLEINMODULE":
                return None  # we can only do expanded PCD's in PATCHABLE
            _, source = self.Consume()
            return pcd(namespace, name, value, source)
        
        parts = value.split("|")
        
        if current_section.pcd_type == "PATCHABLEINMODULE":
            if len(parts) < 2 or len(parts) > 3:
                return None
            value = parts[0].strip()
            data_type = parts[1].strip().upper()
            if data_type == "VOID*" and len(parts) == 2:
                return None
            _, source = self.Consume()
            if len(parts) == 2:
                return pcd_typed(namespace, name, value, data_type, source_info=source)
            max_size = int(parts[2])
            return pcd_typed(namespace, name, value, data_type, max_size, source_info=source)
        

    def GetSectionData(self, line, source):
        data = super().GetSectionData(line, source)
        if type(data) == list:
            return data
        data = data.strip(".")  # strip any trailing .'s
        parts = data.split(".")
        pcd_type = parts[0]
        arch = DEFAULT_SECTION_TYPE if len(parts) < 2 else parts[1]
        if len(parts) == 3:
            sku = parts[2]
            return dsc_pcd_section_type(pcd_type, arch, sku)
        else:
            return dsc_pcd_section_type(pcd_type, arch)


class SkuIdProcessor(SectionProcessor):
    SECTION_TAG = "skuids"

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
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

    def GetSectionData(self, line, source):
        return None


class LibraryClassProcessor(SectionProcessor):
    SECTION_TAG = "libraryclasses"

    def GetSectionData(self, line, source):
        data = super().GetSectionData(line, source)
        if type(data) == list:
            return data
        if data == "":
            return dsc_section_type()
        data = data.strip(".")  # strip any trailing .'s
        parts = data.split(".")
        arch = parts[0]
        module_type = parts[1] if len(parts) > 1 else DEFAULT_SECTION_TYPE
        if len(parts) > 2:
            raise ValueError(f"Invalid section header {line} {source}")
        return dsc_section_type(arch, module_type)

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
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

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        if line.count("=") < 1:  # if we don't have an equals sign
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

    def GetSectionData(self, line, source):
        raise RuntimeError()


class ComponentsProcessor(SectionProcessor):
    SECTION_TAG = "components"

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
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

        if multi_section:  # continue to parse
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
        self._Modules = dict()
        self._Libs = dict()
        self._Pcds = dict()
        self._Skus = dict()
        self._BuildOptions = dict()
        self._Defines = dict()

    # Augmented parsing

    def ParseFile(self, filepath):
        if self.Parsed != False:  # make sure we haven't already parsed the file
            return
        super().ParseFile(filepath)
        self._LineIter = 0
        # just go through and process as many sections as we can find
        self.dsc = dsc(filepath)
        processors = [
            PcdProcessor(self._PreviewNextLine, self._ConsumeNextLine, self._AddPcdItem),
            DefinesProcessor(self._PreviewNextLine, self._ConsumeNextLine, self._AddDefineItem),
            LibraryClassProcessor(self._PreviewNextLine, self._ConsumeNextLine, self._AddLibraryClassItem),
            SkuIdProcessor(self._PreviewNextLine, self._ConsumeNextLine, self._AddSkuItem),
            ComponentsProcessor(self._PreviewNextLine, self._ConsumeNextLine, self._AddCompItem),
            BuildOptionsProcessor(self._PreviewNextLine, self._ConsumeNextLine, self._AddBuildItem),
        ]
        while not self._IsAtEndOfLines:
            success = False
            for proc in processors:
                if proc.AttemptToProcessSection():
                    success = True
                    break
            if not success and not self._IsAtEndOfLines:
                line, source = self._ConsumeNextLine()
                self.Logger.warning(f"DSC Unknown line {line} @{source}")

        self.Parsed = True
        return self.dsc

    def _AddDefineItem(self, item, section):
        self.dsc.defines.add(item)

    def _AddSkuItem(self, item, section):
        # figure out where this goes
        self.dsc.skus.add(item)

    def _AddBuildItem(self, item, section):
        # figure out where this goes
        pass

    def _AddLibraryClassItem(self, item, section):
        # figure out where this goes
        pass

    def _AddCompItem(self, item, section):
        # figure out where this goes
        pass

    def _AddPcdItem(self, item, section):
        # figure out where this goes
        print(item)
        print(section)

    def _PreviewNextLine(self):
        ''' Previews the next line without consuming it '''
        if self._IsAtEndOfLines:
            return None
        return self.SourcedLines[self._LineIter][0]

    @property
    def _IsAtEndOfLines(self):
        return self._LineIter == len(self.Lines)

    def _ConsumeNextLine(self):
        ''' Get the next line for processing '''
        line = self._PreviewNextLine()
        # figure out where this line came from
        source = self._GetCurrentSource()
        self._LineIter += 1
        return (line, source)

    def _GetCurrentSource(self):
        ''' Currently pretty inefficent '''
        if self._IsAtEndOfLines:
            return None
        _, file_path, lineno = self.SourcedLines[self._LineIter]
        return source_info(file_path, lineno)
