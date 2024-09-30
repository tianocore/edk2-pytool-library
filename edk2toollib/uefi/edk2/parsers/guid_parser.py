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
"""Code to help parse guid formats and transform into UUIDs.

Some functionality copied from Tianocore/edk2 basetools.
"""

import re
import uuid


class GuidParser:
    """Provide support functions for converting between different guid formats.

    Also support str uuid and uuid to string.

    Note:
      C-Format:   {0xD3B36F2C, 0xD551, 0x11D4, {0x9A, 0x46, 0x00, 0x90, 0x27, 0x3F, 0xC1, 0x4D}}
      Reg-Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    """

    _HexChar = r"[0-9a-fA-F]"
    # Regular expression for GUID c structure format
    _GuidCFormatPattern = (
        r"{{\s*0[xX]{Hex}{{1,8}}\s*,\s*0[xX]{Hex}{{1,4}}\s*,\s*0[xX]{Hex}{{1,4}}"
        r"\s*,\s*{{\s*0[xX]{Hex}{{1,2}}\s*,\s*0[xX]{Hex}{{1,2}}"
        r"\s*,\s*0[xX]{Hex}{{1,2}}\s*,\s*0[xX]{Hex}{{1,2}}"
        r"\s*,\s*0[xX]{Hex}{{1,2}}\s*,\s*0[xX]{Hex}{{1,2}}"
        r"\s*,\s*0[xX]{Hex}{{1,2}}\s*,\s*0[xX]{Hex}{{1,2}}\s*}}\s*}}".format(Hex=_HexChar)
    )
    GuidCFormatRegEx = re.compile(r"{}".format(_GuidCFormatPattern))

    _GuidPattern = r"{Hex}{{8}}-{Hex}{{4}}-{Hex}{{4}}-{Hex}{{4}}-{Hex}{{12}}".format(Hex=_HexChar)

    # Regular expressions for GUID matching
    GuidRegFormatRegEx = re.compile(r"{}".format(_GuidPattern))

    @classmethod
    def is_guid_in_c_format(cls: "GuidParser", guidstring: str) -> bool:
        """Determine if guidstring is in c format.

        Args:
          guidstring (str): string containing guid

        Returns:
          (bool): True if in C format. Otherwise False

        """
        guidstring = guidstring.strip()
        return cls.GuidCFormatRegEx.match(guidstring)

    @classmethod
    def is_guid_in_reg_format(cls: "GuidParser", guidstring: str) -> bool:
        """Determine if guidstring is in registry format.

        Args:
          guidstring (str): string containing guid

        Returns:
          (bool): True if in Registry format. Otherwise False
        """
        guidstring = guidstring.strip().strip("} {")
        return cls.GuidRegFormatRegEx.match(guidstring)

    @classmethod
    def reg_guid_from_c_format(cls: "GuidParser", guidstring: str) -> str:
        """Convert a c formatted guidstring to a registry formatted guidstring.

        Args:
          guidstring (str): c format guidstring

        Returns:
          (Success): guidstring in registry format
          (Failure): empty string ''
        """
        guidstring = guidstring.strip()
        if not cls.is_guid_in_c_format(guidstring):
            return ""

        guidValueString = guidstring.lower().replace("{", "").replace("}", "").replace(" ", "").replace(";", "")
        guidValueList = guidValueString.split(",")
        if len(guidValueList) != 11:
            return ""
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
                int(guidValueList[10], 16),
            )
        except Exception:
            return ""

    @classmethod
    def c_guid_from_reg_format(cls: "GuidParser", guidstring: str) -> str:
        """Convert registry format guidstring to c format guidstring.

        Args:
          guidstring (str): registry format guidstring

        Returns:
          (Success): guidstring in c format
          (Failure): empty string ''
        """
        guidstring = guidstring.strip().strip("} {")
        if not cls.is_guid_in_reg_format(guidstring):
            return ""

        GuidList = guidstring.split("-")
        Result = "{"
        for Index in range(0, 3, 1):
            Result = Result + "0x" + GuidList[Index] + ", "
        Result = Result + "{0x" + GuidList[3][0:2] + ", 0x" + GuidList[3][2:4]
        for Index in range(0, 12, 2):
            Result = Result + ", 0x" + GuidList[4][Index : Index + 2]
        Result += "}}"
        return Result

    @classmethod
    def uuid_from_guidstring(cls: "GuidParser", guidstring: str) -> uuid.UUID:
        """Create a uuid object from the supplied guidstring."""
        if cls.is_guid_in_c_format(guidstring):
            return uuid.UUID(cls.reg_guid_from_c_format(guidstring))
        elif cls.is_guid_in_reg_format(guidstring):
            guidstring = guidstring.strip().strip("} {")
            return uuid.UUID(guidstring)
        else:
            return None

    @classmethod
    def c_guid_str_from_uuid(cls: "GuidParser", guid: uuid.UUID) -> str:
        """Get a C string formatted guidstring from a uuid object.

        Args:
          guid (uuid.UUID): valid uuid object

        Returns:
          (Success): guidstring in C format
          (Failure): empty string ''
        """
        reg = str(guid)
        return cls.c_guid_from_reg_format(reg)

    @classmethod
    def reg_guid_str_from_uuid(cls: "GuidParser", guid: uuid.UUID) -> str:
        """Get a registry string formatted guidstring from a uuid object.

        Args:
          guid (uuid.UUID): valid uuid object

        Returns:
          (Success): guidstring in registry format
          (Failure): empty string ''
        """
        return str(guid)
