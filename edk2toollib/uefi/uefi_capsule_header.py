## @file
# Module that encodes and decodes a EFI_CAPSULE_HEADER with a payload
#
# Copyright (c) 2018, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
"""Module for encoding and decoding a EFI_CAPSULE_HEADER with a payload."""

import struct
import uuid
from io import BytesIO

from edk2toollib.uefi.fmp_capsule_header import FmpCapsuleHeaderClass


class UefiCapsuleHeaderClass(object):
    r"""An object representing a UEFI_CAPSULE_HEADER.

    Attributes:
        CapsuleGuid (uuid.UUID):    6DCBD5ED-E82D-4C44-BDA1-7194199AD92A
        HeaderSize (int):           The size of the capsule header. This may be larger than the size of the
                                    EFI_CAPSULE_HEADER since CapsuleGuid may imply extended header entries
        OemFlags (int):             Bit-mapped list describing the capsule attributes. The Flag values of 0x0000 -
                                    0xFFFF are defined by CapsuleGuid. Flag values of 0x10000 - 0xFFFFFFFF are defined
                                    by this specification
        PersistAcrossReset (bool):  Flag pulled from OemFlags
        PopulateSystemTable (bool): Flag pulled from OemFlags
        InitiateReset (bool):       Flag pulled from OemFlags
        Payload (bytes):              string representing packed data as bytes (i.e. b'\x01\x00\x03')
        FmpCapsuleHeader (FmpCapsuleHeaderClass): Fmp Capsule Header

    ```
    typedef struct {
        EFI_GUID          CapsuleGuid;
        UINT32            HeaderSize;
        UINT32            Flags;
        UINT32            CapsuleImageSize;
    } EFI_CAPSULE_HEADER;

    #define CAPSULE_FLAGS_PERSIST_ACROSS_RESET          0x00010000
    #define CAPSULE_FLAGS_POPULATE_SYSTEM_TABLE         0x00020000
    #define CAPSULE_FLAGS_INITIATE_RESET                0x00040000
    ```
    """

    _StructFormat = "<16sIIII"
    _StructSize = struct.calcsize(_StructFormat)

    EFI_FIRMWARE_MANAGEMENT_CAPSULE_ID_GUID = uuid.UUID("6DCBD5ED-E82D-4C44-BDA1-7194199AD92A")

    _CAPSULE_FLAGS_PERSIST_ACROSS_RESET = 0x00010000
    _CAPSULE_FLAGS_POPULATE_SYSTEM_TABLE = 0x00020000
    _CAPSULE_FLAGS_INITIATE_RESET = 0x00040000

    def __init__(self) -> "UefiCapsuleHeaderClass":
        """Inits an empty object."""
        self.CapsuleGuid = self.EFI_FIRMWARE_MANAGEMENT_CAPSULE_ID_GUID
        self.HeaderSize = self._StructSize
        self.OemFlags = 0x0000
        self.PersistAcrossReset = False
        self.PopulateSystemTable = False
        self.InitiateReset = False
        self.CapsuleImageSize = self.HeaderSize
        self.Payload = b""
        self.FmpCapsuleHeader = None

    def Encode(self) -> bytes:
        r"""Serializes the Header + payload.

        Returns:
            (bytes): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        Flags = self.OemFlags
        if self.PersistAcrossReset:
            Flags = Flags | self._CAPSULE_FLAGS_PERSIST_ACROSS_RESET
        if self.PopulateSystemTable:
            Flags = Flags | self._CAPSULE_FLAGS_POPULATE_SYSTEM_TABLE
        if self.InitiateReset:
            Flags = Flags | self._CAPSULE_FLAGS_INITIATE_RESET

        # If we have an FmpCapsuleHeader, let's collapse that now.
        if self.FmpCapsuleHeader is not None:
            self.Payload = self.FmpCapsuleHeader.Encode()

        self.CapsuleImageSize = self.HeaderSize + len(self.Payload)

        UefiCapsuleHeader = struct.pack(
            self._StructFormat, self.CapsuleGuid.bytes_le, self.HeaderSize, Flags, self.CapsuleImageSize, 0
        )

        return UefiCapsuleHeader + self.Payload

    def Decode(self, Buffer: BytesIO) -> bytes:
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
        (CapsuleGuid, HeaderSize, Flags, CapsuleImageSize, Reserved) = struct.unpack(
            self._StructFormat, Buffer[0 : self._StructSize]
        )
        if HeaderSize < self._StructSize:
            raise ValueError
        if CapsuleImageSize != len(Buffer):
            raise ValueError
        self.CapsuleGuid = uuid.UUID(bytes_le=CapsuleGuid)
        self.HeaderSize = HeaderSize
        self.OemFlags = Flags & 0xFFFF
        self.PersistAcrossReset = (Flags & self._CAPSULE_FLAGS_PERSIST_ACROSS_RESET) != 0
        self.PopulateSystemTable = (Flags & self._CAPSULE_FLAGS_POPULATE_SYSTEM_TABLE) != 0
        self.InitiateReset = (Flags & self._CAPSULE_FLAGS_INITIATE_RESET) != 0
        self.CapsuleImageSize = CapsuleImageSize
        self.Payload = Buffer[self.HeaderSize :]
        if len(self.Payload) > 0 and self.CapsuleGuid == self.EFI_FIRMWARE_MANAGEMENT_CAPSULE_ID_GUID:
            self.FmpCapsuleHeader = FmpCapsuleHeaderClass()
            self.FmpCapsuleHeader.Decode(self.Payload)

        return self.Payload

    def DumpInfo(self) -> None:
        """Prints payload header information."""
        Flags = self.OemFlags
        if self.PersistAcrossReset:
            Flags = Flags | self._CAPSULE_FLAGS_PERSIST_ACROSS_RESET
        if self.PopulateSystemTable:
            Flags = Flags | self._CAPSULE_FLAGS_POPULATE_SYSTEM_TABLE
        if self.InitiateReset:
            Flags = Flags | self._CAPSULE_FLAGS_INITIATE_RESET
        print("EFI_CAPSULE_HEADER.CapsuleGuid      = {Guid}".format(Guid=str(self.CapsuleGuid).upper()))
        print("EFI_CAPSULE_HEADER.HeaderSize       = {Size:08X}".format(Size=self.HeaderSize))
        print("EFI_CAPSULE_HEADER.Flags            = {Flags:08X}".format(Flags=Flags))
        print("  OEM Flags                         = {Flags:04X}".format(Flags=self.OemFlags))
        if self.PersistAcrossReset:
            print("  CAPSULE_FLAGS_PERSIST_ACROSS_RESET")
        if self.PopulateSystemTable:
            print("  CAPSULE_FLAGS_POPULATE_SYSTEM_TABLE")
        if self.InitiateReset:
            print("  CAPSULE_FLAGS_INITIATE_RESET")
        print("EFI_CAPSULE_HEADER.CapsuleImageSize = {Size:08X}".format(Size=self.CapsuleImageSize))
        print("sizeof (Payload)                    = {Size:08X}".format(Size=len(self.Payload)))
        if self.FmpCapsuleHeader is not None:
            self.FmpCapsuleHeader.DumpInfo()
