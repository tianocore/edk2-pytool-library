# @file dec_parser.py
# Code to help parse DEC file
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Code to help parse DEC files."""

import os
import re
from typing import IO

from edk2toollib.uefi.edk2.parsers.base_parser import HashFileParser
from edk2toollib.uefi.edk2.parsers.guid_parser import GuidParser


class LibraryClassDeclarationEntry:
    """Object representing a Library Class Declaration Entry."""

    def __init__(self, packagename: str, rawtext: str = None) -> "LibraryClassDeclarationEntry":
        """Init a library Class Declaration Entry."""
        self.path = ""
        self.name = ""
        self.package_name = packagename
        if rawtext is not None:
            self._parse(rawtext)

    def _parse(self, rawtext: str) -> None:
        """Parses the rawtext line to collect the Library Class declaration information.

        information includes (name and package root relative path).

        Args:
          rawtext (str): raw text

        NOTE: expected format of rawtext is <library class name> | <package relative path to header file>
        """
        t = rawtext.partition("|")
        self.name = t[0].strip()
        self.path = t[2].strip()


class GuidedDeclarationEntry:
    """A baseclass for declaration types that have a name and guid.

    Attributes:
        name (str): name
        guidstring (str): guid
        guid (uuid.UUID): guid
        package_name (str): packagename
    """

    PROTOCOL = 1
    PPI = 2
    GUID = 3

    def __init__(self, packagename: str, rawtext: str = None) -> "GuidedDeclarationEntry":
        """Init a protocol/Ppi/or Guid declaration entry."""
        self.name = ""
        self.guidstring = ""
        self.guid = None
        self.package_name = packagename
        if rawtext is not None:
            self._parse(rawtext)

    def _parse(self, rawtext: str) -> None:
        """Parses the name and guid of a declaration.

        Args:
          rawtext (str): raw text
        """
        t = rawtext.partition("=")
        self.name = t[0].strip()
        self.guidstring = t[2].strip()
        self.guid = GuidParser.uuid_from_guidstring(self.guidstring)
        if self.guid is None:
            raise ValueError("Could not parse guid")


class ProtocolDeclarationEntry(GuidedDeclarationEntry):
    """Object representing a Protocol Declaration Entry."""

    def __init__(self, packagename: str, rawtext: str = None) -> "ProtocolDeclarationEntry":
        """Init a protocol declaration entry."""
        super().__init__(packagename, rawtext)
        self.type = GuidedDeclarationEntry.PROTOCOL


class PpiDeclarationEntry(GuidedDeclarationEntry):
    """Object representing a Ppi Declaration Entry."""

    def __init__(self, packagename: str, rawtext: str = None) -> "GuidedDeclarationEntry":
        """Init a Ppi declaration entry."""
        super().__init__(packagename, rawtext)
        self.type = GuidedDeclarationEntry.PPI


class GuidDeclarationEntry(GuidedDeclarationEntry):
    """Object representing a Guid Declaration Entry."""

    def __init__(self, packagename: str, rawtext: str = None) -> "GuidDeclarationEntry":
        """Init a Ppi declaration entry."""
        super().__init__(packagename, rawtext)
        self.type = GuidedDeclarationEntry.GUID


class PcdDeclarationEntry:
    """Object representing a Pcd Delcaration Entry.

    Attributes:
        token_space_name (str): token space name
        name (str): name
        default_value (str): value
        type (str): type
        id (str): id
        package_name: package name
    """

    def __init__(self, packagename: str, rawtext: str = None) -> "PcdDeclarationEntry":
        """Creates a PCD Declaration Entry for one PCD."""
        self.token_space_name = ""
        self.name = ""
        self.default_value = ""
        self.type = ""
        self.id = ""
        self.package_name = packagename
        if rawtext is not None:
            self._parse(rawtext)

    def _parse(self, rawtext: str) -> None:
        """Parses the PcdDeclaration Entry for one PCD."""
        sp = rawtext.partition(".")
        self.token_space_name = sp[0].strip()

        # Regular expression pattern to match the symbol '|' that is not inside quotes
        pattern = r'\|(?=(?:(?:[^\'"]*(?:\'[^\']*\'|"[^"]*"))*[^\'"]*)$)'
        op = re.split(pattern, sp[2])

        # if it's 2 long, we need to check that it's a structured PCD
        if len(op) == 2 and op[0].count(".") > 0:
            pass
        # otherwise it needs at least 4 parts
        elif len(op) < 4:
            raise Exception(f"Too few parts: {op}")
        # but also less than 5
        elif len(op) > 5:
            raise Exception(f"Too many parts: {rawtext}")
        elif len(op) == 5 and op[4].strip() != "{":
            raise Exception(f"Too many parts: {rawtext}")

        self.name = op[0].strip()
        self.default_value = op[1].strip()
        # if we don't know what the type and id, it's because it's structured
        self.type = op[2].strip() if len(op) > 2 else "STRUCTURED_PCD"
        self.id = op[3].strip() if len(op) > 2 else "STRUCTURED_PCD"


class DecParser(HashFileParser):
    """Parses an EDK2 DEC file.

    Attributes:
        Parsed (bool): If a DEC file has been parsed or not
        Lines (list): order list of lines in the Dec file
        Dict (dict): Dict of variables set in the DEC file
        LibraryClasses (list): list of Library classes
        PPIs (list): list of PPIs
        Protocols (list): list of Protocols
        Guids (list): list of Guids
        Pcds (list): list of Pcds
        IncludePaths (list): list of IncludePaths
        PackageName (str): Package Name variable also found in Dict
        Path (str): path to the DEC file
    """

    def __init__(self) -> "DecParser":
        """Init an empty Dec Parser."""
        HashFileParser.__init__(self, "DecParser")
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
        """Parses the EDK2 DEC file."""
        InDefinesSection = False
        InLibraryClassSection = False
        InProtocolsSection = False
        InGuidsSection = False
        InPPISection = False
        InPcdSection = False
        InStructuredPcdDeclaration = False
        InIncludesSection = False

        for line in self.Lines:
            sline = self.StripComment(line)

            if sline is None or len(sline) < 1:
                continue

            if InDefinesSection:
                if sline.strip()[0] == "[":
                    InDefinesSection = False
                else:
                    if sline.count("=") == 1:
                        tokens = sline.split("=", 1)
                        self.Dict[tokens[0].strip()] = tokens[1].strip()
                        if self.PackageName is None and tokens[0].strip() == "PACKAGE_NAME":
                            self.PackageName = self.Dict["PACKAGE_NAME"]
                        continue

            elif InLibraryClassSection:
                if sline.strip()[0] == "[":
                    InLibraryClassSection = False
                else:
                    t = LibraryClassDeclarationEntry(self.PackageName, sline)
                    self.LibraryClasses.append(t)
                    continue

            elif InProtocolsSection:
                if sline.strip()[0] == "[":
                    InProtocolsSection = False
                else:
                    t = ProtocolDeclarationEntry(self.PackageName, sline)
                    self.Protocols.append(t)
                    continue

            elif InGuidsSection:
                if sline.strip()[0] == "[":
                    InGuidsSection = False
                else:
                    t = GuidDeclarationEntry(self.PackageName, sline)
                    self.Guids.append(t)
                    continue

            elif InPcdSection:
                if sline.strip()[0] == "[":
                    InPcdSection = False
                elif sline.strip()[0] == "}":
                    InStructuredPcdDeclaration = False
                else:
                    if InStructuredPcdDeclaration:
                        continue
                    t = PcdDeclarationEntry(self.PackageName, sline)
                    self.Pcds.append(t)
                    if sline.rstrip()[-1] == "{":
                        InStructuredPcdDeclaration = True
                    continue

            elif InIncludesSection:
                if sline.strip()[0] == "[":
                    InIncludesSection = False
                else:
                    self.IncludePaths.append(sline.strip())
                    continue

            elif InPPISection:
                if sline.strip()[0] == "[":
                    InPPISection = False
                else:
                    t = PpiDeclarationEntry(self.PackageName, sline)
                    self.PPIs.append(t)
                    continue

            # check for different sections
            if sline.strip().lower().startswith("[defines"):
                InDefinesSection = True

            elif sline.strip().lower().startswith("[libraryclasses"):
                InLibraryClassSection = True

            elif sline.strip().lower().startswith("[protocols"):
                InProtocolsSection = True

            elif sline.strip().lower().startswith("[guids"):
                InGuidsSection = True

            elif sline.strip().lower().startswith("[ppis"):
                InPPISection = True

            elif sline.strip().lower().startswith("[pcd"):
                InPcdSection = True

            elif sline.strip().lower().startswith("[includes"):
                InIncludesSection = True

        self.Parsed = True

    def ParseStream(self, stream: IO) -> None:
        """Parse the supplied IO as a DEC file.

        Args:
            stream (IOBase): a file-like/stream object in which DEC file contents can be read
        """
        self.Path = "None:stream_given"
        self.Lines = stream.readlines()
        self._Parse()

    def ParseFile(self, filepath: str) -> None:
        """Parse the supplied file.

        Args:
          filepath (str): path to dec file to parse.  Can be either an absolute path or
            relative to your CWD
        """
        self.Logger.debug("Parsing file: %s" % filepath)
        if not os.path.isabs(filepath):
            fp = self.FindPath(filepath)
        else:
            fp = filepath
        self.Path = fp

        f = open(fp, "r")
        self.Lines = f.readlines()
        f.close()
        self._Parse()
