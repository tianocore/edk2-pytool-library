# @file guid_list
#
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import logging
import re
from edk2toollib.gitignore_parser import parse_gitignore_lines

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

    # Regular Expressions for matching the guid name and guid value of Edk2 DEC files

    _DecGuidRegex = r'\s*([a-zA-Z]\w*)\s*\=\s*' + \
           r'\{\s*0x([0-9a-fA-F]{1,8})\s*,\s*' + \
           r'0x([0-9a-fA-F]{1,4})\s*,\s*' + \
           r'0x([0-9a-fA-F]{1,4})\s*,\s*' + \
           r'\s*\{\s*0x([0-9a-fA-F]{1,2})\s*,\s*' + \
           r'0x([0-9a-fA-F]{1,2})\s*,\s*' + \
           r'0x([0-9a-fA-F]{1,2})\s*,\s*' + \
           r'0x([0-9a-fA-F]{1,2})\s*,\s*' + \
           r'0x([0-9a-fA-F]{1,2})\s*,\s*' + \
           r'0x([0-9a-fA-F]{1,2})\s*,\s*' + \
           r'0x([0-9a-fA-F]{1,2})\s*,\s*' + \
           r'0x([0-9a-fA-F]{1,2})\s*\}\s*\}'

    DecGuidRegEx = re.compile(r'{}'.format(_DecGuidRegex))

    # Regular expressions for matching the guid name and guid value of Edk2 INF files

    _InfFileRegex = r'\s*BASE_NAME\s*\=\s*([a-zA-Z]\w*)\s*'
    _InfGuidRegex = r'\s*FILE_GUID\s*\=\s*([0-9a-fA-F]{8,8}-[0-9a-fA-F]{4,4}-[0-9a-fA-F]{4,4}-[0-9a-fA-F]{4,4}-[0-9a-fA-F]{12,12})\s*'

    InfNameRegEx = re.compile(r'{}'.format(_InfFileRegex))
    InfGuidRegEx = re.compile(r'{}'.format(_InfGuidRegex))

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
    def parse_guids_from_edk2_file(filename: str ) -> list:
      """ parse edk2 files for guids

      filename: abspath to dec file
      """
      if(filename.lower().endswith(".dec")):
        with open(filename, "r") as f:
          return GuidList.parse_guids_from_dec(f, filename)
      elif(filename.lower().endswith(".inf")):
        with open(filename, "r") as f:
          return GuidList.parse_guids_from_inf(f, filename)
      else:
        return []

    @staticmethod
    def parse_guids_from_dec(stream, filename: str) -> list:
      """ find all guids in a dec file contents contained with stream

      stream: lines of dec file content
      filename: abspath to dec file
      """
      results = []
      for line in stream:
        m = GuidList.DecGuidRegEx.match(line)
        if (m is not None):
            guidKey = '%s-%s-%s-%s%s-%s%s%s%s%s%s' % (m.group(2).upper().zfill(8), \
                                                      m.group(3).upper().zfill(4), \
                                                      m.group(4).upper().zfill(4), \
                                                      m.group(5).upper().zfill(2), m.group(6).upper().zfill(2), \
                                                      m.group(7).upper().zfill(2), m.group(8).upper().zfill(2), m.group(9).upper().zfill(2), \
                                                      m.group(10).upper().zfill(2), m.group(11).upper().zfill(2), m.group(12).upper().zfill(2))
            results.append( GuidListEntry(m.group(1), guidKey, filename))
      return results

    @staticmethod
    def parse_guids_from_inf(stream, filename: str) -> list:
      """ find the module guids in an Edk2 inf file contents contained with stream

      stream: lines of inf file content
      filename: abspath to inf file
      """
      name = None
      guid = None

      for line in stream:
          mFile = GuidList.InfNameRegEx.match(line)
          mGuid = GuidList.InfGuidRegEx.match(line)
          if (mFile is not None):
              name = mFile.group(1)
          elif (mGuid is not None):
              guid = mGuid.group(1).upper()
          if ((guid is not None) and (name is not None)):
              return [GuidListEntry(name, guid, filename)]
      return []
