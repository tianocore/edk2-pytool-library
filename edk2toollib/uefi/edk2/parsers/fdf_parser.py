# @file fdf_parser.py
# Code to help parse EDK2 Fdf files
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from edk2toollib.uefi.edk2.parsers.limited_fdf_parser import LimitedFdfParser
from edk2toollib.uefi.edk2.build_objects.fdf import *
from edk2toollib.uefi.edk2.build_objects.dsc import definition
from edk2toollib.uefi.edk2.parsers.dsc_parser import SectionProcessor
from edk2toollib.uefi.edk2.parsers.dsc_parser import AccurateParser
import os


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


class FdProcessor(SectionProcessor):
    SECTION_TAG = "fd"

    def ExtractObjects(self, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        fd = fdf_fd()
        # the sections in a FD are the tokens
        while True:
            raw_line = self.Preview()
            if self.CheckForEnd(raw_line):
                break
            token = self.ExtractTokenFromLine(raw_line, current_section)
            if token is None:
                break
            fd.tokens.add(token)
        while True:
            raw_line = self.Preview()
            if self.CheckForEnd(raw_line):
                break
            region = self.ExtractRegion(current_section)
            if region is None:
                break
            fd.regions.add(region)
        return fd

    def CheckForEnd(self, raw_line):
        return raw_line is None or (raw_line.startswith("[") and raw_line.endswith("]"))

    def ExtractRegion(self, current_section=None) -> (object, list):
        line = self.Preview()
        # A Layout Region start with a eight digit hex offset (leading "0x"
        # required) followed by the pipe "|" character, followed by the size of
        # the region, also in hex with the leading "0x" characters. Like:
        # Offset|Size
        if line.count("|") != 1:
            return None
        parts = line.split("|")
        offset = parts[0].strip().lower()
        if not offset.startswith("0x"):
            return None
        size = parts[1].strip().lower()
        if not size.startswith("0x"):
            return None
        if size.count(" ") > 0:
            return None
        _, source = self.Consume()

        pcds = []

        # PcdOffsetCName|PcdSizeCName
        line = self.Preview()
        if line.count("|") == 1:
            # Process ruby
            if line.lower().startswith("0x"):
                return fdf_fd_region(offset, size, source_info=source)
            # process PCD's
            line, source = self.Consume()
            pcd1, pcd2 = line.split("|")
            pcd1 = pcd1.strip()
            pcd2 = pcd2.strip()
            # TODO: convert them into SET PCDS

        # process PCDS
        # TODO look for SET PCDS = VALUE

        # Process RegionType <FV, DATA, or FILE>
        line = self.Preview(until_balanced=True)
        fd = fdf_fd_region(offset, size, source_info=source)
        if line == None:
            return fd
        region = fdf_fd_region(offset, size, source_info=source)
        if line.count("=") == 1:
            parts = line.split("=", 1)
            reg_type = parts[0].strip()
            if fdf_fd_region.IsRegionType(reg_type):
                # if it's a valid region type
                fd = fdf_fd_region(offset, size, reg_type=reg_type, source_info=source)
                self.Consume()
        return fd

    def ExtractTokenFromLine(self, line, current_section=None) -> object:
        ''' see if you can extract an object from a line- make sure to consume it. Return None if you can't '''
        if line.count("=") != 1:
            return None

        parts = line.split("=")
        name = parts[0].strip()
        if not fdf_fd_token.IsValidTokenName(name):
            print(f"INVALID TOKEN: {name}")
            return None
        value = parts[1]
        _, source = self.Consume()
        return fdf_fd_token(name, value, source_info=source)

    def GetSectionData(self, line, source):
        data = super().GetSectionData(line, source)
        if data is None:
            return None
        if data.startswith("."):
            return data  # TODO: create a FD section type?
        return ""


class FvProcessor(SectionProcessor):
    SECTION_TAG = "fv"

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        if line == None or line.startswith("["):
            return None

        line, source = self.Consume()
        # print(f"Fv: {line}")
        return fdf_fv(source_info=source)


class CapsuleProcessor(SectionProcessor):
    SECTION_TAG = "capsule"

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        if line == None or line.startswith("["):
            return None

        line, source = self.Consume()
        #print(f"CAPSULE: {line}")
        return fdf_capsule(source_info=source)


class VtfProcessor(SectionProcessor):
    SECTION_TAG = "vtf"

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        if line == None or line.startswith("["):
            return None

        line, source = self.Consume()
        #print(f"VTF: {line}")
        return fdf_vtf(source_info=source)


class OptionRomProcessor(SectionProcessor):
    SECTION_TAG = "optionrom"

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        if line == None or line.startswith("["):
            return None

        line, source = self.Consume()
        #print(f"OptionRom: {line}")
        return fdf_vtf(source_info=source)


class RuleProcessor(SectionProcessor):
    SECTION_TAG = "rule"

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        if line == None or line.startswith("["):
            return None

        line, source = self.Consume()
        #print(f"RULE: {line}")
        return fdf_rule(source_info=source)

    def GetSectionData(self, line, source):
        return None


class FdfParser(LimitedFdfParser, AccurateParser):

    def __init__(self):
        LimitedFdfParser.__init__(self)
        self.SourcedLines = []

    def ParseFile(self, filepath):
        if self.Parsed != False:  # make sure we haven't already parsed the file
            return
        super().ParseFile(filepath)
        self.fdf = fdf(filepath)
        self.ResetLineIterator()
        callbacks = self.GetCallbacks()
        processors = [
            RuleProcessor(*callbacks, self._AddRuleItem),
            DefinesProcessor(*callbacks, self._AddDefineItem),
            FdProcessor(*callbacks, self._AddFdItem),
            FvProcessor(*callbacks, self._AddFvItem),
            CapsuleProcessor(*callbacks, self._AddCapsuleItem),
            VtfProcessor(*callbacks, self._AddVtfItem),
            OptionRomProcessor(*callbacks, self._AddOptionRomItem)
        ]
        while not self._IsAtEndOfLines:
            success = False
            for proc in processors:
                if proc.AttemptToProcessSection():
                    success = True
                    break
            if not success and not self._IsAtEndOfLines:
                line, source = self._ConsumeNextLine()
                self.Logger.warning(f"FDF Unknown line {line} @{source}")

        self.Parsed = True

        return self.fdf
    
    def _PreviewNextLine(self, until_balanced=False):
        if not until_balanced: 
            return super()._PreviewNextLine()
        balance = 0
        line = self._PreviewNextLine()
        balance = None
        line_count = 0
        lines = []
        while balance == None or balance > 0:
            line = self.SourcedLines[self._LineIter+line_count][0]
            if balance is None:
                balance = 0
            balance += line.count("{")
            balance -= line.count("}")
            line_count += 1
            lines.append(line)
        return " ".join(lines)

    def _ConsumeNextLine(self, until_balanced=False):
        if not until_balanced: 
            return super()._ConsumeNextLine()        
        raise RuntimeError()

    def _AddRuleItem(self, item, section):
        pass

    def _AddDefineItem(self, item, section):
        self.fdf.defines.add(item)

    def _AddFdItem(self, item, section):
        if section in self.fdf.fds:
            # TODO merge the two sections together
            pass
        self.fdf.fds[section] = item
        pass

    def _AddFvItem(self, item, section):
        pass

    def _AddCapsuleItem(self, item, section):
        pass

    def _AddVtfItem(self, item, section):
        pass

    def _AddOptionRomItem(self, item, section):
        pass
