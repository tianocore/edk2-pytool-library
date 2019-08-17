# @file dec_parser.py
# Code to help parse DEC file
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import os
import uuid
from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser


class LibraryClassDeclarationEntry():

    def __init__(self, packagename: str, rawtext: str = None):
        """Init a library Class Declaration Entry"""
        self.path = ""
        self.name = ""
        self.package_name = packagename
        if (rawtext is not None):
            self._parse(rawtext)

    def _parse(self, rawtext: str) -> None:
        """Parses the rawtext line to collect the Library Class declaration
           information (name and package root relative path).

        Args:
          rawtext: str
          expected format is <library class name> | <package relative path to header file>

        Returns:
          None

        """
        t = rawtext.partition("|")
        self.name = t[0].strip()
        self.path = t[2].strip()


class GuidedDeclarationEntry():
    """A baseclass for declaration types that have a name and guid."""
    PROTOCOL = 1
    PPI = 2
    GUID = 3

    def __init__(self, packagename: str, rawtext: str = None):
        """Init a protocol/Ppi/or Guid declaration entry"""
        self.name = ""
        self.guidstring = ""
        self.guid = None
        self.package_name = packagename
        if(rawtext is not None):
            self._parse(rawtext)

    def _parse(self, rawtext: str) -> None:
        """Parses the name and guid of a declaration

        Args:
          rawtext: str:

        Returns:

        """
        t = rawtext.partition("=")
        self.name = t[0].strip()
        self.guidstring = t[2].strip()
        self.guid = self._convert_guid_to_uuid(self.guidstring)

    def _is_guid_in_include_format(self, guidstring: str) -> bool:
        """will look at guidstring to make sure it looks like:
        { 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}

        Args:
          guidstring: str:

        Returns:
            TRUE - if format is c style
            FALSE - all other cases

        """
        if(guidstring.count("{") == 2 and guidstring.count("}") == 2 and guidstring.count(",") == 10):
            return True
        return False

    def _parse_guid_to_reg_from_include_format(self, guid_string: str) -> str:
        """parse a guid in format
        # { 0xD3B36F2C, 0xD551, 0x11D4, { 0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D }}
        # into F7FDE4A6-294C-493c-B50F-9734553BB757  (NOTE these are not same guid this is just example of format)

        Args:
          guid_string: str:

        Returns:

        """
        entries = guid_string.lstrip(' {').rstrip(' }').split(',')
        gu = entries[0].lstrip(' 0').lstrip('x').strip()
        # pad front until 8 chars
        while(len(gu) < 8):
            gu = "0" + gu

        gut = entries[1].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 4):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[2].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 4):
            gut = "0" + gut
        gu = gu + "-" + gut

        # strip off extra {
        gut = entries[3].lstrip(' { 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[4].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[5].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + "-" + gut

        gut = entries[6].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[7].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[8].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[9].lstrip(' 0').lstrip('x').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        gut = entries[10].split()[0].lstrip(' 0').lstrip('x').rstrip(' } ').strip()
        while(len(gut) < 2):
            gut = "0" + gut
        gu = gu + gut

        return gu.upper()

    def _convert_guid_to_uuid(self, guid_string: str) -> uuid.UUID:
        """

        Args:
          guid_string: str:

        Returns:

        """
        if(self._is_guid_in_include_format(guid_string)):
            reg = self._parse_guid_to_reg_from_include_format(guid_string)
            return uuid.UUID(reg)
        return uuid.UUID(guid_string)


class ProtocolDeclarationEntry(GuidedDeclarationEntry):

    def __init__(self, packagename: str, rawtext: str = None):
        """Init a protocol declaration entry"""
        super().__init__(packagename, rawtext)
        self.type = GuidedDeclarationEntry.PROTOCOL


class PpiDeclarationEntry(GuidedDeclarationEntry):

    def __init__(self, packagename: str, rawtext: str = None):
        """Init a Ppi declaration entry"""
        super().__init__(packagename, rawtext)
        self.type = GuidedDeclarationEntry.PPI


class GuidDeclarationEntry(GuidedDeclarationEntry):

    def __init__(self, packagename: str, rawtext: str = None):
        """Init a Ppi declaration entry"""
        super().__init__(packagename, rawtext)
        self.type = GuidedDeclarationEntry.GUID


class PcdDeclarationEntry():

    def __init__(self, packagename: str, rawtext: str = None):
        """Creates a PCD Declaration Entry for one PCD"""
        self.token_space_name = ""
        self.name = ""
        self.default_value = ""
        self.type = ""
        self.id = ""
        self.package_name = packagename
        if (rawtext is not None):
            self._parse(rawtext)

    def _parse(self, rawtext: str):
        """

        Args:
          rawtext: str:

        Returns:

        """
        sp = rawtext.partition(".")
        self.token_space_name = sp[0].strip()
        op = sp[2].split("|")

        if(len(op) != 4):
            raise Exception("Too many parts")

        self.name = op[0].strip()
        self.default_value = op[1].strip()
        self.type = op[2].strip()
        self.id = op[3].strip()


class DecParser(HashFileParser):
    """Parses an EDK2 DEC file"""

    def __init__(self):
        HashFileParser.__init__(self, 'DecParser')
        self.Lines = []
        self.Parsed = False
        self.Dict = {}
        self.LibraryClasses = []
        self.PPIs = []
        self.Protocols = []
        self.Guids = []
        self.Pcds = []
        self.IncludePaths = []
        self.Path = ""
        self.PackageName = None

    def _Parse(self) -> None:

        InDefinesSection = False
        InLibraryClassSection = False
        InProtocolsSection = False
        InGuidsSection = False
        InPPISection = False
        InPcdSection = False
        InIncludesSection = False

        for line in self.Lines:
            sline = self.StripComment(line)

            if(sline is None or len(sline) < 1):
                continue

            if InDefinesSection:
                if sline.strip()[0] == '[':
                    InDefinesSection = False
                else:
                    if sline.count("=") == 1:
                        tokens = sline.split('=', 1)
                        self.Dict[tokens[0].strip()] = tokens[1].strip()
                        if(self.PackageName is None and tokens[0].strip() == "PACKAGE_NAME"):
                            self.PackageName = self.Dict["PACKAGE_NAME"]
                        continue

            elif InLibraryClassSection:
                if sline.strip()[0] == '[':
                    InLibraryClassSection = False
                else:
                    t = LibraryClassDeclarationEntry(self.PackageName, sline)
                    self.LibraryClasses.append(t)
                    continue

            elif InProtocolsSection:
                if sline.strip()[0] == '[':
                    InProtocolsSection = False
                else:
                    t = ProtocolDeclarationEntry(self.PackageName, sline)
                    self.Protocols.append(t)
                    continue

            elif InGuidsSection:
                if sline.strip()[0] == '[':
                    InGuidsSection = False
                else:
                    t = GuidDeclarationEntry(self.PackageName, sline)
                    self.Guids.append(t)
                    continue

            elif InPcdSection:
                if sline.strip()[0] == '[':
                    InPcdSection = False
                else:
                    t = PcdDeclarationEntry(self.PackageName, sline)
                    self.Pcds.append(t)
                    continue

            elif InIncludesSection:
                if sline.strip()[0] == '[':
                    InIncludesSection = False
                else:
                    self.IncludePaths.append(sline.strip())
                    continue

            elif InPPISection:
                if (sline.strip()[0] == '['):
                    InPPISection = False
                else:
                    t = PpiDeclarationEntry(self.PackageName, sline)
                    self.PPIs.append(t)
                    continue

            # check for different sections
            if sline.strip().lower().startswith('[defines'):
                InDefinesSection = True

            elif sline.strip().lower().startswith('[libraryclasses'):
                InLibraryClassSection = True

            elif sline.strip().lower().startswith('[protocols'):
                InProtocolsSection = True

            elif sline.strip().lower().startswith('[guids'):
                InGuidsSection = True

            elif sline.strip().lower().startswith('[ppis'):
                InPPISection = True

            elif sline.strip().lower().startswith('[pcd'):
                InPcdSection = True

            elif sline.strip().lower().startswith('[includes'):
                InIncludesSection = True

        self.Parsed = True

    def ParseStream(self, stream) -> None:
        """
        parse the supplied IO as a DEC file
        Args:
            stream: a file-like/stream object in which DEC file contents can be read

        Returns:
            None - Existing object now contains parsed data

        """
        self.Path = "None:stream_given"
        self.Lines = stream.readlines()
        self._Parse()

    def ParseFile(self, filepath: str) -> None:
        """
        Parse the supplied file.
        Args:
          filepath: path to dec file to parse.  Can be either an absolute path or
          relative to your CWD

        Returns:
          None - Existing object now contains parsed data

        """
        self.Logger.debug("Parsing file: %s" % filepath)
        if(not os.path.isabs(filepath)):
            fp = self.FindPath(filepath)
        else:
            fp = filepath
        self.Path = fp

        f = open(fp, "r")
        self.Lines = f.readlines()
        f.close()
        self._Parse()
