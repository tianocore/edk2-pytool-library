# @file guid_list
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import logging
import os
from edk2toollib.gitignore_parser import parse_gitignore_lines

from edk2toollib.uefi.edk2.parsers.dec_parser import DecParser
from edk2toollib.uefi.edk2.parsers.inf_parser import InfParser


class GuidListEntry():

    def __init__(self, name: str, guid: str, filepath: str):
        """ Create GuidListEntry for later review and compare.
        name: name of guid
        guid: registry format guid in string format
        filepath: absolute path to file where this guid was found
        """
        self.name = name
        self.guid = guid
        self.absfilepath = filepath

    def __str__(self):
        return f"GUID: {self.guid} NAME: {self.name} FILE: {self.absfilepath}"


class GuidList():

    @staticmethod
    def guidlist_from_filesystem(folder: str, ignore_lines: list = list()) -> list:
        """ Create a list of GuidListEntry from files found in the file system

        folder: path string to root folder to walk
        ignore_lines: list of gitignore syntax to ignore files and folders
        """
        guids = []
        ignore = parse_gitignore_lines(ignore_lines, os.path.join(folder, "nofile.txt"), folder)
        for root, dirs, files in os.walk(folder):
            for d in dirs[:]:
                fullpath = os.path.join(root, d)
                if(ignore(fullpath)):
                    logging.debug(f"Ignore folder: {fullpath}")
                    dirs.remove(d)

            for name in files:
                fullpath = os.path.join(root, name)
                if(ignore(fullpath)):
                    logging.debug(f"Ignore file: {fullpath}")
                    continue

                newg = GuidList.parse_guids_from_edk2_file(fullpath)
                guids.extend(newg)
        return guids

    @staticmethod
    def parse_guids_from_edk2_file(filename: str) -> list:
        """ parse edk2 files for guids

        filename: abspath to dec file
        """
        if(filename.lower().endswith(".dec")):
            with open(filename, "r") as f:
                return GuidList.parse_guids_from_dec(f, filename)
        elif(filename.lower().endswith(".inf")):
            return GuidList.parse_guids_from_inf(filename)
        else:
            return []

    @staticmethod
    def parse_guids_from_dec(stream, filename: str) -> list:
        """ find all guids in a dec file contents contained with stream

        stream: lines of dec file content
        filename: abspath to dec file
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
        except:
            logging.warn("Failed to find Package Guid from dec file: " + filename)
        return results

    @staticmethod
    def parse_guids_from_inf(filename: str) -> list:
        """ find the module guid in an Edk2 inf file

        filename: abspath to inf file
        """
        inf = InfParser()
        inf.ParseFile(filename)
        try:
            return [GuidListEntry(inf.Dict["BASE_NAME"], inf.Dict["FILE_GUID"].upper(), filename)]
        except:
            logging.warn("Failed to find info from INF file: " + filename)
        return []
