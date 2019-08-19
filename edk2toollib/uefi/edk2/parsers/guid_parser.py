# @file guid_parser.py
# Code to help parse guid formats and make into UUIDs
#
# Some functionality copied from Tianocore/edk2 basetools
#
# Copyright (c) Microsoft Corporation
# Copyright (c) 2007 - 2019, Intel Corporation. All rights reserved.<BR>
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
import uuid
import re
import os


class GuidParser():
    """ Provide support functions for converting between different guid formats.  Also support str
        uuid and uuid to string.

        Common terms:
          C-Format:   {0xD3B36F2C, 0xD551, 0x11D4, {0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D}}
          Reg-Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    """

    _HexChar = r"[0-9a-fA-F]"
    # Regular expression for GUID c structure format
    _GuidCFormatPattern = r"{{\s*0[xX]{Hex}{{1,8}}\s*,\s*0[xX]{Hex}{{1,4}}\s*,\s*0[xX]{Hex}{{1,4}}" \
                          r"\s*,\s*{{\s*0[xX]{Hex}{{1,2}}\s*,\s*0[xX]{Hex}{{1,2}}" \
                          r"\s*,\s*0[xX]{Hex}{{1,2}}\s*,\s*0[xX]{Hex}{{1,2}}" \
                          r"\s*,\s*0[xX]{Hex}{{1,2}}\s*,\s*0[xX]{Hex}{{1,2}}" \
                          r"\s*,\s*0[xX]{Hex}{{1,2}}\s*,\s*0[xX]{Hex}{{1,2}}\s*}}\s*}}".format(Hex=_HexChar)
    GuidCFormatRegEx = re.compile(r"{}".format(_GuidCFormatPattern))

    _GuidPattern = r"{Hex}{{8}}-{Hex}{{4}}-{Hex}{{4}}-{Hex}{{4}}-{Hex}{{12}}".format(Hex=_HexChar)

    # Regular expressions for GUID matching
    GuidRegFormatRegEx = re.compile(r'{}'.format(_GuidPattern))

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

    _InfFileRegex = r'\s*BASE_NAME\s*\=\s*([a-zA-Z]\w*)\s*'
    _InfGuidRegex = r'\s*FILE_GUID\s*\=\s*([0-9a-fA-F]{8,8}-[0-9a-fA-F]{4,4}-[0-9a-fA-F]{4,4}-[0-9a-fA-F]{4,4}-[0-9a-fA-F]{12,12})\s*'

    InfNameRegEx = re.compile(r'{}'.format(_InfFileRegex))
    InfGuidRegEx = re.compile(r'{}'.format(_InfGuidRegex))

    @classmethod
    def is_guid_in_c_format(cls, guidstring: str) -> bool:
        """ determine if guidstring is in c format

        Args:
          guidstring: str: string containing guid

        Returns:
          True if in C format.  Otherwise False

        """
        guidstring = guidstring.strip()
        return cls.GuidCFormatRegEx.match(guidstring)

    @classmethod
    def is_guid_in_reg_format(cls, guidstring: str) -> bool:
        """ determine if guidstring is in registry format

        Args:
          guidstring: str: string containing guid

        Returns:
          True if in Registry format.  Otherwise False
        """
        guidstring = guidstring.strip().strip('} {')
        return cls.GuidRegFormatRegEx.match(guidstring)

    @classmethod
    def reg_guid_from_c_format(cls, guidstring: str) -> str:
        """ convert a c formatted guidstring to a registry formatted guidstring

        Args:
          guidstring: str: c format guidstring

        Returns:
          Success: guidstring in registry format
          Failure: empty string ''
        """
        guidstring = guidstring.strip()
        if not cls.is_guid_in_c_format(guidstring):
            return ''

        guidValueString = guidstring.lower().replace("{", "").replace("}", "").replace(" ", "").replace(";", "")
        guidValueList = guidValueString.split(",")
        if len(guidValueList) != 11:
            return ''
        try:
            return "%08x-%04x-%04x-%02x%02x-%02x%02x%02x%02x%02x%02x" % (
                int(guidValueList[0], 16),
                int(guidValueList[1], 16),
                int(guidValueList[2], 16),
                int(guidValueList[3], 16),
                int(guidValueList[4], 16),
                int(guidValueList[5], 16),
                int(guidValueList[6], 16),
                int(guidValueList[7], 16),
                int(guidValueList[8], 16),
                int(guidValueList[9], 16),
                int(guidValueList[10], 16)
            )
        except:
            return ''

    @classmethod
    def c_guid_from_reg_format(cls, guidstring: str) -> str:
        """Convert registry format guidstring to c format guidstring

        Args:
          guidstring: str: registry format guidstring

        Returns:
          Success: guidstring in c format
          Failure: empty string ''
        """
        guidstring = guidstring.strip().strip('} {')
        if(not cls.is_guid_in_reg_format(guidstring)):
            return ''

        GuidList = guidstring.split('-')
        Result = '{'
        for Index in range(0, 3, 1):
            Result = Result + '0x' + GuidList[Index] + ', '
        Result = Result + '{0x' + GuidList[3][0:2] + ', 0x' + GuidList[3][2:4]
        for Index in range(0, 12, 2):
            Result = Result + ', 0x' + GuidList[4][Index:Index + 2]
        Result += '}}'
        return Result

    @classmethod
    def uuid_from_guidstring(cls, guidstring: str) -> uuid.UUID:
        """ create a uuid object from the supplied guidstring"""

        if(cls.is_guid_in_c_format(guidstring)):
            return uuid.UUID(cls.reg_guid_from_c_format(guidstring))
        elif(cls.is_guid_in_reg_format(guidstring)):
            guidstring = guidstring.strip().strip('} {')
            return uuid.UUID(guidstring)
        else:
            return None

    @classmethod
    def c_guid_str_from_uuid(cls, guid: uuid.UUID) -> str:
        """ get a C string formatted guidstring from a uuid object

        Args:
          guid: uuid.UUID: valid uuid object

        Returns:
          Success: guidstring in C format
          Failure: empty string ''
        """
        reg = str(guid)
        return cls.c_guid_from_reg_format(reg)

    @classmethod
    def reg_guid_str_from_uuid(cls, guid: uuid.UUID) -> str:
        """ get a registry string formatted guidstring from a uuid object

        Args:
          guid: uuid.UUID: valid uuid object

        Returns:
          Success: guidstring in registry format
          Failure: empty string ''
        """
        return str(guid)

    @classmethod
    def find_guids_in_filesystem(cls, folder: str) -> list:
      guids = []
      for root, dirs, files in os.walk(folder):
        if "Build" in dirs:
          dirs.remove("Build")
        for name in files:
          fullpath = os.path.join(root, name)
          newg = GuidParser.parse_guids_from_edk2_file(fullpath)
          for entry in newg:
            guids.append(entry + (fullpath,))
          #guids.extend(newg)
      return guids


    @classmethod
    def parse_guids_from_edk2_file(cls, filename: str ) -> list:
      with open(filename, "r") as f:
        if(filename.lower().endswith(".dec")):
          return GuidParser.parse_guids_from_dec(f)
        elif(filename.lower().endswith(".inf")):
          return GuidParser.parse_guids_from_inf(f)
        else:
          return []

    @classmethod
    def parse_guids_from_dec(cls, stream) -> list:
      results = []
      for line in stream:
        m = GuidParser.DecGuidRegEx.match(line)
        if (m is not None):
            guidKey = '%s-%s-%s-%s%s-%s%s%s%s%s%s' % (m.group(2).upper().zfill(8), \
                                                      m.group(3).upper().zfill(4), \
                                                      m.group(4).upper().zfill(4), \
                                                      m.group(5).upper().zfill(2), m.group(6).upper().zfill(2), \
                                                      m.group(7).upper().zfill(2), m.group(8).upper().zfill(2), m.group(9).upper().zfill(2), \
                                                      m.group(10).upper().zfill(2), m.group(11).upper().zfill(2), m.group(12).upper().zfill(2))
            results.append((guidKey, m.group(1)))
      return results

    @classmethod
    def parse_guids_from_inf(cls, stream) -> list:
      name = None
      guid = None

      for line in stream:
          mFile = GuidParser.InfNameRegEx.match(line)
          mGuid = GuidParser.InfGuidRegEx.match(line)
          if (mFile is not None):
              name = mFile.group(1)
          elif (mGuid is not None):
              guid = mGuid.group(1).upper()
          if ((guid is not None) and (name is not None)):
              return [(name, guid)]
      return []

if __name__ == '__main__':
  gs = GuidParser.find_guids_in_filesystem(r"C:\src\edk2-plus-stuart-ci\edk2-staging")
  #for e in gs:
  #  print(e[2] + ": " + e[0] + " " + e[1])

  # To return a new list, use the sorted() built-in function...
  newlist = sorted(gs, key=lambda x: x[1], reverse=True)

  previous = (None, None, None)
  for index in range(len(newlist)):
    i = newlist[index]
    if i[1] == previous[1]:
      print("Error Dup: " + i[1])
      print("  " + i[0] + ": " + i[2])
      print("  " + previous[0] + ": " + previous[2])
    previous = i

