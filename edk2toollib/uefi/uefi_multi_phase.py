# @file
# Module contains defintions and structures from the UefiMultiPhase header file.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

"""Module for working with UEFI Authenticated Variable Atrributes."""

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

    _struct_format = "<I"  # UINT32
    _struct_size = struct.calcsize(_struct_format)

    SHORT_STRING_MAP = {
        EFI_VARIABLE_APPEND_WRITE: "AP",
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

    def __init__(self, attributes=0x0000_0000, decodefs=None) -> None:
        """Creates a EfiVariableAttributes object.

        Args:
            attributes (int | str): attributes to parse
            decodefs (io.BytesIO): filestream to decode from

        Returns:
            None
        """
        if decodefs:
            self.decode(decodefs)
        else:
            self.update(attributes)

    def update(self, attributes: 0x0000_00000) -> None:
        """Updates instance to provided attributes.

        Args:
            attributes (int | str): attributes to parse

        Returns:
            None

        Raises:
            TypeError: If the attribute provided is neither int or string
        """
        if isinstance(attributes, int):
            self.attributes = attributes
        elif isinstance(attributes, str):
            self.attributes = EfiVariableAttributes.parse_attributes_str(attributes)
        else:
            raise TypeError(
                f"Invalid type: {type(attributes)}")

    @staticmethod
    def parse_attributes_str(attributes_str) -> int:
        """Converts attributes string into integer representation.

        Args:
            attributes_str (str): string containing attributes that have been comma delimated.

        Examples:
            ```python
            parse_attributes_str("EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
            parse_attributes_str("EFI_VARIABLE_BOOTSERVICE_ACCESS, EFI_VARIABLE_NON_VOLATILE")
            parse_attributes_str("BS,NV")
            parse_attributes_str("BS, NV")
            ```

        Returns:
            Integer representation of the attributes

        Raises:
            ValueError: if the attribute provided is not supported
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

            # attempt to get the value from the INVERSE_STRING_MAP if it fails,
            # try to grab it from the INVERSE_SHORT_MAP
            attr_value = EfiVariableAttributes.INVERSE_STRING_MAP.get(
                attr,
                EfiVariableAttributes.INVERSE_SHORT_STRING_MAP.get(
                    attr,
                    0  # We should never get here since it would fail the above if condition
                )
            )

            attributes |= attr_value

        return attributes

    def decode(self, fs) -> int:
        """Reads in attributes from a file stream.

        This updates the attributes value of the object

        Args:
            fs (io.BytesIO): file stream to read from

        !!! Examples
            ```python
            with open (my_data_file, 'rb') as f:
                attributes = EfiVariableAttributes()
                attributes.decode(f)
            ```

        Returns:
            Attributes in integer form
        """
        attributes = struct.unpack(EfiVariableAttributes._struct_format, fs.read(EfiVariableAttributes._struct_size))[0]

        self.update(attributes)

        return attributes

    def encode(self) -> bytes:
        """Returns the attributes as a packed structure.

        !!! Examples
            ```python

            my_byte_array = b""

            attributes = EfiVariableAttributes("EFI_VARIABLE_NON_VOLATILE")
            my_byte_array += attributes.encode()
            ```

        Returns:
            Attributes in packed byte form
        """
        return struct.pack(EfiVariableAttributes._struct_format, self.attributes)

    def get_short_string(self) -> str:
        """Short form string representation of the attributes.

        !!! Examples
            ```python

            attributes = EfiVariableAttributes("EFI_VARIABLE_NON_VOLATILE")
            attributes.get_short_string() # "NV"
            ```

        Returns:
            Short form of the attributes (Ex. "BS,NV")
        """
        result = []
        for key in EfiVariableAttributes.STRING_MAP:
            if self.attributes & key:
                result.append(EfiVariableAttributes.SHORT_STRING_MAP[key])
        return ",".join(result)

    def __str__(self) -> str:
        """String representation of the attributes.

        Returns:
            Long form of the attributes (Ex. "EFI_VARIABLE_BOOTSERVICE_ACCESS,EFI_VARIABLE_NON_VOLATILE")
        """
        result = []
        for key in EfiVariableAttributes.STRING_MAP:
            if self.attributes & key:
                result.append(EfiVariableAttributes.STRING_MAP[key])
        return ",".join(result)

    def __int__(self):
        """Returns attributes as an int."""
        return self.attributes
