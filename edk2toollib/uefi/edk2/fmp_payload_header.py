## @file
# Module that encodes and decodes a FMP_PAYLOAD_HEADER with a payload.
# The FMP_PAYLOAD_HEADER is processed by the FmpPayloadHeaderLib in the
# FmpDevicePkg.
#
# Copyright (c) 2018, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

"""Module that encodes and decodes a FMP_PAYLOAD_HEADER with a payload.

The FMP_PAYLOAD_HEADER is processed by the FmpPayloadHeaderLib in the
FmpDevicePkg.
"""

import struct


def _SIGNATURE_32(A: str, B: str, C: str, D: str) -> bytes:
    return struct.unpack("=I", bytearray(A + B + C + D, "ascii"))[0]


def _SIGNATURE_32_TO_STRING(Signature: int) -> bytes:
    return struct.pack("<I", Signature).decode()


class FmpPayloadHeaderClass(object):
    """An object representing a FMP_PAYLOAD_HEADER.

    typedef struct {
        UINT32  Signature;
        UINT32  HeaderSize;
        UINT32  FwVersion;
        UINT32  LowestSupportedVersion;
    } FMP_PAYLOAD_HEADER;

    #define FMP_PAYLOAD_HEADER_SIGNATURE SIGNATURE_32 ('M', 'S', 'S', '1')
    """

    _StructFormat = "<IIII"
    _StructSize = struct.calcsize(_StructFormat)

    _FMP_PAYLOAD_HEADER_SIGNATURE = _SIGNATURE_32("M", "S", "S", "1")

    def __init__(self) -> "FmpPayloadHeaderClass":
        """Inits an empty object."""
        self.Signature = self._FMP_PAYLOAD_HEADER_SIGNATURE
        self.HeaderSize = self._StructSize
        self.FwVersion = 0x00000000
        self.LowestSupportedVersion = 0x00000000
        self.Payload = b""

    def Encode(self) -> bytes:
        r"""Serializes the Header + payload.

        Returns:
            (bytes): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        FmpPayloadHeader = struct.pack(
            self._StructFormat, self.Signature, self.HeaderSize, self.FwVersion, self.LowestSupportedVersion
        )
        return FmpPayloadHeader + self.Payload

    def Decode(self, Buffer: bytes) -> bytes:
        """Loads data into the Object by parsing a buffer.

        Args:
            Buffer (obj): Buffer containing the data

        Returns:
            (str): string of binary representing the payload

        Raises:
            (ValueError): Invalid Buffer
            (ValueError): Invalid Signature
            (ValueError): Invalid Header size
        """
        if len(Buffer) < self._StructSize:
            raise ValueError
        (Signature, HeaderSize, FwVersion, LowestSupportedVersion) = struct.unpack(
            self._StructFormat, Buffer[0 : self._StructSize]
        )
        if Signature != self._FMP_PAYLOAD_HEADER_SIGNATURE:
            raise ValueError
        if HeaderSize < self._StructSize:
            raise ValueError
        self.Signature = Signature
        self.HeaderSize = HeaderSize
        self.FwVersion = FwVersion
        self.LowestSupportedVersion = LowestSupportedVersion
        self.Payload = Buffer[self.HeaderSize :]

        return self.Payload

    def DumpInfo(self) -> None:
        """Prints payload header information."""
        print(
            "FMP_PAYLOAD_HEADER.Signature              = {Signature:08X} ({SignatureString})".format(
                Signature=self.Signature, SignatureString=_SIGNATURE_32_TO_STRING(self.Signature)
            )
        )
        print("FMP_PAYLOAD_HEADER.HeaderSize             = {HeaderSize:08X}".format(HeaderSize=self.HeaderSize))
        print("FMP_PAYLOAD_HEADER.FwVersion              = {FwVersion:08X}".format(FwVersion=self.FwVersion))
        print(
            "FMP_PAYLOAD_HEADER.LowestSupportedVersion = {LowestSupportedVersion:08X}".format(
                LowestSupportedVersion=self.LowestSupportedVersion
            )
        )
        print("sizeof (Payload)                          = {Size:08X}".format(Size=len(self.Payload)))
