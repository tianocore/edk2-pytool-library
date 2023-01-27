# @file
# Module contains defintions and structures from the UefiMultiPhase header file.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import struct

EFI_VARIABLE_NON_VOLATILE = 0x00000001
EFI_VARIABLE_BOOTSERVICE_ACCESS = 0x00000002
EFI_VARIABLE_RUNTIME_ACCESS = 0x00000004
EFI_VARIABLE_HARDWARE_ERROR_RECORD = 0x00000008
EFI_VARIABLE_AUTHENTICATED_WRITE_ACCESS = 0x00000010
EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS = 0x00000020
EFI_VARIABLE_APPEND_WRITE = 0x00000040


class EfiVariableAttributes(object):
    """Object representing the different efi variable attributes."""

    _StructFormat = "<I"  # UINT32
    _StructSize = struct.calcsize(_StructFormat)

    SHORT_STRING_MAP = {
        EFI_VARIABLE_APPEND_WRITE: "PW",
        EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS: "AT",
        EFI_VARIABLE_AUTHENTICATED_WRITE_ACCESS: "AW",
        EFI_VARIABLE_HARDWARE_ERROR_RECORD: "HW",
        EFI_VARIABLE_RUNTIME_ACCESS: "RT",
        EFI_VARIABLE_BOOTSERVICE_ACCESS: "BS",
        EFI_VARIABLE_NON_VOLATILE: "NV"
    }
    INVERSE_SHORT_STRING_MAP = {v: k for k, v in SHORT_STRING_MAP.items()}

    STRING_MAP = {
        EFI_VARIABLE_APPEND_WRITE: "EFI_VARIABLE_APPEND_WRITE",
        EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS: "EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS",
        EFI_VARIABLE_AUTHENTICATED_WRITE_ACCESS: "EFI_VARIABLE_AUTHENTICATED_WRITE_ACCESS",
        EFI_VARIABLE_HARDWARE_ERROR_RECORD: "EFI_VARIABLE_HARDWARE_ERROR_RECORD",
        EFI_VARIABLE_RUNTIME_ACCESS: "EFI_VARIABLE_RUNTIME_ACCESS",
        EFI_VARIABLE_BOOTSERVICE_ACCESS: "EFI_VARIABLE_BOOTSERVICE_ACCESS",
        EFI_VARIABLE_NON_VOLATILE: "EFI_VARIABLE_NON_VOLATILE",
    }
    INVERSE_STRING_MAP = {v: k for k, v in STRING_MAP.items()}

    def __init__(self, attributes=0x0000_0000):
        """
        :param attributes: supported types [int, str], attributes to parse

        :param none
        """

        self.Update(attributes)

    def Update(self, attributes: 0x0000_00000):
        """
        Updates an instance of EfiVariableAttributes to new value

        :param attributes: supported types [int, str], attributes to parse

        :param none (implicit)
        """

        if isinstance(attributes, int):
            self.Attributes = attributes
        elif isinstance(attributes, str):
            self.Attributes = self._parse_attributes_str(attributes)
        else:
            raise ValueError(
                f"Invalid type: {type(attributes)}")

    def _parse_attributes_str(self, attributes_str):
        """
        converts attributes string integer representation

        :param attributes_str: string containing attributes that have been comma delimated.
            Examples: 
                "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE"
                "EFI_VARIABLE_BOOTSERVICE_ACCESS, EFI_VARIABLE_NON_VOLATILE"
                "BS,NV"
                "BS, NV"

        :return: int representation of the attributes
        """

        attributes = 0

        # Handle spaces
        attributes_str = attributes_str.replace(" ", "")

        # Loop over all the attributes
        for attr in attributes_str.split(','):
            attr = attr.upper()  # convert to upper for consistency

            if attr not in EfiVariableAttributes.INVERSE_STRING_MAP \
                    and attr not in EfiVariableAttributes.INVERSE_SHORT_STRING_MAP:
                raise ValueError(f"Attribute string \"{attr}\" not supported")

            # attempt to get the value from the INVERSE_STRING_MAP if it fails, try to grab it from the INVERSE_SHORT_MAP
            attr_value = EfiVariableAttributes.INVERSE_STRING_MAP.get(
                attr,
                EfiVariableAttributes.INVERSE_SHORT_STRING_MAP.get(
                    attr,
                    0  # We should never get here since it would fail the above if condition
                )
            )

            attributes |= attr_value

        return attributes

    def GetShortString(self):
        """
        Short string representation of the attributes.

        :return: 'short string' of the attributes
        """
        result = []
        for key in EfiVariableAttributes.STRING_MAP:
            if self.Attributes & key:
                result.append(EfiVariableAttributes.SHORT_STRING_MAP[key])
        return ",".join(result)

    def __str__(self):
        """
        String representation of the attributes.

        :return: 'short string' of the attributes
        """
        result = []
        for key in EfiVariableAttributes.STRING_MAP:
            if self.Attributes & key:
                result.append(EfiVariableAttributes.STRING_MAP[key])
        return ",".join(result)

    def __int__(self):
        return self.Attributes
