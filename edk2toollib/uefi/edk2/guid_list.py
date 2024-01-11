# @file guid_list
#
# Simple list of GuidListEntry objects parsed from edk2 specific files.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Simple list of GuidListEntry objects parsed from edk2 specific files."""
import logging
import os
from typing import IO

from edk2toollib.gitignore_parser import parse_gitignore_lines
from edk2toollib.uefi.edk2.parsers.dec_parser import DecParser
from edk2toollib.uefi.edk2.parsers.inf_parser import InfParser


class GuidListEntry():
    """A object representing a Guid.

    Attributes:
        name (str): name of guid
        guid (str): registry format guid in string format
        filepath (str): absolute path to file where this guid was found
    """
    def __init__(self, name: str, guid: str, filepath: str) -> 'GuidListEntry':
        """Create GuidListEntry for later review and compare.

        Args:
            name (str): name of guid
            guid (str): registry format guid in string format
            filepath (str): absolute path to file where this guid was found
        """
        self.name = name
        self.guid = guid
        self.absfilepath = filepath

    def __str__(self) -> str:
        """String representation of the guid."""
        return f"GUID: {self.guid} NAME: {self.name} FILE: {self.absfilepath}"


class GuidList():
    """Static class for returning Guids."""
    @staticmethod
    def guidlist_from_filesystem(folder: str, ignore_lines: list = list()) -> list:
        """Create a list of GuidListEntry from files found in the file system.

        Args:
            folder (str): path string to root folder to walk
            ignore_lines (list): list of gitignore syntax to ignore files and folders

        Returns:
            (list[GuidListEntry]): guids
        """
        guids = []
        ignore = parse_gitignore_lines(ignore_lines, os.path.join(folder, "nofile.txt"), folder)
        for root, dirs, files in os.walk(folder):
            for d in dirs[:]:
                fullpath = os.path.join(root, d)
                if (ignore(fullpath)):
                    logging.debug(f"Ignore folder: {fullpath}")
                    dirs.remove(d)

            for name in files:
                fullpath = os.path.join(root, name)
                if (ignore(fullpath)):
                    logging.debug(f"Ignore file: {fullpath}")
                    continue

                new_guids = GuidList.parse_guids_from_edk2_file(fullpath)
                guids.extend(new_guids)
        return guids

    @staticmethod
    def parse_guids_from_edk2_file(filename: str) -> list:
        """Parse edk2 files for guids.

        Args:
            filename (str): abspath to dec file

        Returns:
            (list[GuidListEntry]): guids
        """
        if (filename.lower().endswith(".dec")):
            with open(filename, "r") as f:
                return GuidList.parse_guids_from_dec(f, filename)
        elif (filename.lower().endswith(".inf")):
            return GuidList.parse_guids_from_inf(filename)
        else:
            return []

    @staticmethod
    def parse_guids_from_dec(stream: IO, filename: str) -> list:
        """Find all guids in a dec file contents contained with stream.

        Args:
            stream: lines of dec file content
            filename: abspath to dec file

        Returns:
            (list[GuidListEntry]): Guids
        """
        results = []
        dec = DecParser()
        dec.ParseStream(stream)
        for p in dec.Protocols:
            results.append(GuidListEntry(p.name, str(p.guid).upper(), filename))
        for p in dec.PPIs:
            results.append(GuidListEntry(p.name, str(p.guid).upper(), filename))
        for p in dec.Guids:
            results.append(GuidListEntry(p.name, str(p.guid).upper(), filename))

        try:
            results.append(GuidListEntry(dec.Dict["PACKAGE_NAME"], dec.Dict["PACKAGE_GUID"], filename))
        except Exception:
            logging.warning("Failed to find Package Guid from dec file: " + filename)
        return results

    @staticmethod
    def parse_guids_from_inf(filename: str) -> list:
        """Find the module guid in an Edk2 inf file.

        Args:
            filename (str): abspath to inf file

        Returns:
            (list[GuidListEntry]): Guids
        """
        inf = InfParser()
        inf.ParseFile(filename)
        try:
            return [GuidListEntry(inf.Dict["BASE_NAME"], inf.Dict["FILE_GUID"].upper(), filename)]
        except Exception:
            logging.warning("Failed to find info from INF file: " + filename)
        return []
