# @file tpm2_stream.py
# This file contains utility classes to help marshal and un-marshal data to/from the TPM.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module that contains utility classes to help marshal and un-marshal date to/from the TPM."""

import struct


class Tpm2StreamElement(object):
    """Tpm2 Stream Element."""
    def __init__(self) -> None:
        """Init an empty Tpm2StreamElement."""
        self.pack_string = ""

    def get_size(self) -> int:
        """The size of this structure when marshalled."""
        return struct.calcsize(self.pack_string)


class Tpm2StreamPrimitive(Tpm2StreamElement):
    """Tpm2 Stream Primitive.

    Attributes:
        size: size of the primitive. 1, 2, 4, or 8 bytes
        value: Value of primitive
    """
    def __init__(self, size: int, value: str) -> None:
        """Init a primitive value.

        Args:
            size: 1, 2, 4, or 8 bytes
            value: Value to stream.
        """
        super(Tpm2StreamPrimitive, self).__init__()

        if size not in (1, 2, 4, 8):
            raise ValueError("Size must be 1, 2, 4, or 8 bytes!")

        self.pack_string = {
            1: ">B",
            2: ">H",
            4: ">L",
            8: ">Q"
        }[size]
        self.value = value

    def marshal(self) -> bytes:
        r"""Serializes the Tpm2 primitive.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        return struct.pack(self.pack_string, self.value)


class TPM2_COMMAND_HEADER(Tpm2StreamElement):
    """Tpm2 Command header.

    Attributes:
        tag
        code
        size
    """
    def __init__(self, tag: str, size: str, code: str) -> None:
        """Init a Tpm2 command."""
        super(TPM2_COMMAND_HEADER, self).__init__()
        self.tag = tag
        self.code = code
        self.size = size
        self.pack_string = ">HLL"

    def update_size(self, size: int) -> None:
        """Update size of the whole command."""
        self.size = size

    def marshal(self) -> str:
        r"""Serializes the Tpm2 command header.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        return struct.pack(self.pack_string, self.tag, self.size, self.code)


class TPM2B(Tpm2StreamElement):
    """Tpm2 B."""
    def __init__(self, data: str) -> None:
        """Inits the object."""
        super(TPM2B, self).__init__()
        self.data = data
        self.size = len(data)
        self.pack_string = ">H%ds" % self.size

    def update_data(self, data: str) -> None:
        """Updates the data attribute."""
        self.data = data
        self.size = len(data)
        self.pack_string = ">H%ds" % self.size

    def marshal(self) -> str:
        r"""Serializes the Tpm2B object.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        return struct.pack(self.pack_string, self.size, self.data)


class Tpm2CommandStream(object):
    """Tpm2 Command Stream."""
    def __init__(self, tag: str, size: int, code: str) -> None:
        """Inits a Tpm2 Command stream object."""
        super(Tpm2CommandStream, self).__init__()
        self.header = TPM2_COMMAND_HEADER(tag, size, code)
        self.stream_size = self.header.get_size()
        self.header.update_size(self.stream_size)
        self.stream_elements = []

    def get_size(self) -> int:
        """Returns the stream size."""
        return self.stream_size

    def add_element(self, element: 'Tpm2StreamElement') -> None:
        """Adds an element to the stream list."""
        self.stream_elements.append(element)
        self.stream_size += element.get_size()
        self.header.update_size(self.stream_size)

    def get_stream(self) -> str:
        r"""Serializes the Header + elements.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        return self.header.marshal() + b''.join(element.marshal() for element in self.stream_elements)
