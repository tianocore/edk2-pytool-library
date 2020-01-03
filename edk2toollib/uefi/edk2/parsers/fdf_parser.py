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
from edk2toollib.uefi.edk2.build_objects.dsc import source_info
from edk2toollib.uefi.edk2.parsers.dsc_parser import SectionProcessor
from edk2toollib.uefi.edk2.parsers.dsc_parser import AccurateParser
import os

def split_strip(data, delimit=" ", limit=-1):
    return [str(x).strip() for x in data.split(delimit, limit)]


class DefinesProcessor(SectionProcessor):
    SECTION_TAG = "defines"

    def ExtractObjectFromLine(self, line, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        if line.count("=") < 1:  # if we don't know what to do with it, don't worry about it
            return None

        parts = split_strip(line, "=", 1)
        name = str(parts[0]).strip()
        if name.count(" ") > 0:
            return None  # we don't know what to do with this
        value = parts[1]

        line, source = self.Consume()
        return definition(name, value, local=False, source_info=source)

    def GetSectionData(self, line, source):
        return None

class WholeSectionProcessor():
   def CheckForEnd(self, raw_line):
        return raw_line is None or (raw_line.startswith("[") and raw_line.endswith("]"))

class FdProcessor(SectionProcessor, WholeSectionProcessor):
    SECTION_TAG = "fd"

    def ExtractObjects(self, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        fd = fdf_fd()
        # the sections in a FD are the tokens
        while True:
            raw_line = self.Preview()
            if self.CheckForEnd(raw_line):
                break
            define = self.ProcessDefine(raw_line, current_section)
            if define is not None:
                fd.defines.add(token)
                continue
            token = self.ExtractTokenFromLine(raw_line, current_section)
            if token is None:
                break
            if token in fd.tokens:
                raise ValueError(f"Unable to add {token} to the [FD{current_section}] {token.source_info}")
            fd.tokens.add(token)

        # Extract all the regions we can
        while True:
            raw_line = self.Preview()
            if self.CheckForEnd(raw_line):
                break
            region = self.ExtractRegion(current_section)
            if region is None:
                break
            fd.regions.add(region)
        return fd

    def ExtractRegion(self, current_section=None) -> (object, list):
        line = self.Preview()
        # A Layout Region start with a eight digit hex offset (leading "0x"
        # required) followed by the pipe "|" character, followed by the size of
        # the region, also in hex with the leading "0x" characters. Like:
        # Offset|Size
        if line.count("|") != 1:
            return None
        parts = line.split("|")
        offset = parts[0].strip().upper()
        if not offset.startswith("0X"):
            return None
        size = parts[1].strip().upper()
        if not size.startswith("0X"):
            return None
        if size.count(" ") > 0:
            return None
        _, source = self.Consume()

        pcds = []

        # PcdOffsetCName|PcdSizeCName
        line = self.Preview()
        if line is None:
            return fdf_fd_region(offset, size, source_info=source)
        if line.count("|") == 1 and line.count(".") == 2:
            # Process ruby
            if line.lower().startswith("0x"):
                return self.ExtractRegion(current_section)
            # process PCD's
            line, source = self.Consume()
            pcd1_text, pcd2_text = split_strip(line, "|")
            # TODO should this be broken out into a separate func?
            if pcd1_text.count(".") == 1:
                token, name = split_strip(pcd1_text, ".")
                pcds.append(fdf_fd_region_pcd(token, name, offset))
            if pcd1_text.count(".") == 1:
                token, name = split_strip(pcd2_text, ".")
                pcds.append(fdf_fd_region_pcd(token, name, size))

        # process PCDS
        # TODO look for SET PCDS = VALUE
        while True:
            pcd = self.ExtractSetPcdFromLine(self.Preview(), current_section)
            if pcd is None:
                break
            pcds.append(pcd)
        # Process RegionType <FV, DATA, or FILE>
        data = self.ExtractRegionData(current_section)
        return fdf_fd_region(offset, size, data, pcds, source_info=source)

    def ExtractRegionData(self, current_section=None) -> object:
        line = self.Preview()
        if line is None or line.count("=") == 0:
            return None
        parts = line.split("=", 1)
        reg_type = parts[0].strip().upper()
        if not fdf_fd_region_data.IsRegionType(reg_type):
            return None
        line, source = self.Consume(until_balanced=True)
        _, data = line.split("=", 1)
        data = data.strip()
        # TODO: figure out how to parse the data in a better format
        return fdf_fd_region_data(reg_type, data, source)

    def ExtractSetPcdFromLine(self, line, current_section=None) -> object:
        if line is None or not line.upper().startswith("SET "):
            return None
        line = line[3:]
        if line.count("=") != 1:
            return None
        namespace, value = split_strip(line, "=")
        if namespace.count(".") != 1:
            return None
        token_space, name = split_strip(namespace, ".")
        _, source = self.Consume()
        return fdf_fd_region_pcd(token_space, name, value, source)

    def ExtractTokenFromLine(self, line, current_section=None) -> object:
        ''' see if you can extract an object from a line- make sure to consume it. Return None if you can't '''
        if line.count("=") != 1:
            return None

        parts = line.split("=")
        name = parts[0].strip()
        if not fdf_fd_token.IsValidTokenName(name):
            print(f"INVALID TOKEN: {name}")
            return None
        value = parts[1].strip()
        _, source = self.Consume()
        if value.count("|") == 0:
            return fdf_fd_token(name, value, source_info=source)
        value, pcd = value.split("|")
        value = value.strip()
        pcd = pcd.strip()
        return fdf_fd_token(name, value, pcd, source_info=source)

    def GetSectionData(self, line, source):
        data = super().GetSectionData(line, source)
        if data is None:
            return None
        if data.startswith("."):
            return data  # TODO: create a FD section type?
        return ""

class FvProcessor(SectionProcessor, WholeSectionProcessor):
    SECTION_TAG = "fv"

    def ExtractObjects(self, current_section=None) -> object:
        ''' extracts the data model objects from the current state '''
        fv = fdf_fv()
        # the sections in a FD are the tokens
        while True:
            raw_line = self.Preview()
            if self.CheckForEnd(raw_line):
                break
            define = self.ProcessDefine(raw_line, current_section)
            if define is not None:
                fv.defines.add(token)
                continue
            token = self.ExtractTokenFromLine(raw_line, current_section)
            if token is not None:
                fv.tokens.add(token)
                continue
            apriori = self.ExtractApriori(raw_line, current_section)
            if apriori is not None:
                continue
            inf = self.ExtractFvInfFromLine(raw_line, current_section)
            if inf is not None:
                continue
            print(f"Unable to extract token {raw_line}")
            break
        return fv

    def ExtractTokenFromLine(self, line, current_section):
        if line.count("=") != 1:
            return None
        name, value = split_strip(line, "=", 1)
        name = name.upper()
        if name.count(" ") > 0:
            return None
        if not fdf_fv_token.IsValidTokenName(name):
            print("Invalid token name "+name)
            return None
        _, source = self.Consume()
        return fdf_fv_token(name, value, source_info=source)

    def ExtractApriori(self, line, current_section):
        if not line.startswith("APRIORI "):
            return None
        parts = split_strip(line, " ")
        name = parts[1].upper()
        whole_line, source = self.Consume(until_balanced=True)
        print(whole_line)

        return name

    def ExtractFvInfFromLine(self, line, current_section):
        if not line.startswith("INF "):
            return None
        parts = split_strip(line, " ")
        inf = parts[-1]
        print(inf)
        _, source = self.Consume()

        return inf

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
        line = super()._PreviewNextLine()
        if not until_balanced:
            return line
        balance = None
        line_count = 0
        lines = []
        while balance == None or balance > 0:
            if self._LineIter+line_count == len(self.SourcedLines):
                break
            line = self.SourcedLines[self._LineIter+line_count][0]
            if balance is None:
                balance = 0
            balance += line.count("{")
            balance -= line.count("}")
            line_count += 1
            lines.append(line)
        return " ".join(lines)

    def _ConsumeNextLine(self, until_balanced=False) -> (list, source_info):
        if not until_balanced:
            return super()._ConsumeNextLine()
        balance = None
        lines = []
        source = None
        while balance == None or balance > 0:
            line, new_source = super()._ConsumeNextLine()
            lines.append(line)
            if source is None:
                source = new_source
            if line is None:
                break
            if balance is None:
                balance = 0
            balance += line.count("{")
            balance -= line.count("}")
        lines = " ".join(lines)
        return (lines, source)

    def _AddRuleItem(self, item, section):
        pass

    def _AddDefineItem(self, item, section):
        self.fdf.defines.add(item)

    def _AddFdItem(self, item, section):
        if section in self.fdf.fds:
            # merge the two sections together
            item += self.fdf.fds[section]
        self.fdf.fds[section] = item

    def _AddFvItem(self, item, section):
        if section in self.fdf.fvs:
            # TODO merge the two sections together
            item += self.fdf.fvs[section]
        self.fdf.fvs[section] = item
        pass

    def _AddCapsuleItem(self, item, section):
        pass

    def _AddVtfItem(self, item, section):
        pass

    def _AddOptionRomItem(self, item, section):
        pass
