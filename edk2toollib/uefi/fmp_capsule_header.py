## @file
# Module that encodes and decodes a EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER with
# a payload.
#
# Copyright (c) 2018 - 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

"""Module for encoding and decoding EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER with payloads."""

import struct
import uuid
from typing import IO

from edk2toollib.uefi.fmp_auth_header import FmpAuthHeaderClass


class FmpCapsuleImageHeaderClass (object):
    r"""An object representing an EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.

    Can parse or produce an EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER structure/byte buffer.

    Attributes:
        Version (int):                 EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER_INIT_VERSION
        UpdateImageTypeId (uuid.UUID): Used to identify device firmware targeted by this update. This guid is matched
                                       by system firmware against ImageTypeId field within a
                                       EFI_FIRMWARE_IMAGE_DESCRIPTOR
        UpdateImageIndex (int):        Passed as ImageIndex in call to EFI_FIRMWARE_MANAGEMENT_PROTOCOL.SetImage ()
        UpdateImageSize (int):         Size of the binary update image which immediately follows this structure
        UpdateVendorCodeSize (int):    Size of the VendorCode bytes which optionally immediately follow binary update
                                       image in the capsule
        UpdateHardwareInstance (int):  The HardwareInstance to target with this update. If value is zero it means match
                                       all HardwareInstances.
        Payload (str):                 String representing payload as bytes (i.e. b'\x01\x00\x03')

    ```
    typedef struct {
        UINT32   Version;
        EFI_GUID UpdateImageTypeId;
        UINT8    UpdateImageIndex;
        UINT8    reserved_bytes[3];
        UINT32   UpdateImageSize;
        UINT32   UpdateVendorCodeSize;
        UINT64   UpdateHardwareInstance;
    } EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER;

    #define EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER_INIT_VERSION 0x00000002
    ```
    """
    _StructFormat = '<I16sB3BIIQ'  # spell-checker: disable-line
    _StructSize = struct.calcsize(_StructFormat)

    EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER_INIT_VERSION = 0x00000002

    def __init__(self) -> None:
        """Inits an empty object."""
        self.Version = self.EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER_INIT_VERSION
        self.UpdateImageTypeId = uuid.UUID('00000000-0000-0000-0000-000000000000')
        self.UpdateImageIndex = 0
        self.UpdateImageSize = 0
        self.UpdateVendorCodeSize = 0
        self.UpdateHardwareInstance = 0x0000000000000000
        self.Payload = b''
        self.VendorCodeBytes = b''
        self.FmpAuthHeader = None

    def Encode(self) -> bytes:
        r"""Serializes the object.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        # If we have an FmpAuthHeader, let's collapse that now.
        if self.FmpAuthHeader is not None:
            self.Payload = self.FmpAuthHeader.Encode()

        self.UpdateImageSize = len(self.Payload)
        self.UpdateVendorCodeSize = len(self.VendorCodeBytes)
        FmpCapsuleImageHeader = struct.pack(
            self._StructFormat,
            self.Version,
            self.UpdateImageTypeId.bytes_le,
            self.UpdateImageIndex,
            0, 0, 0,
            self.UpdateImageSize,
            self.UpdateVendorCodeSize,
            self.UpdateHardwareInstance
        )
        return FmpCapsuleImageHeader + self.Payload + self.VendorCodeBytes

    def Decode(self, Buffer: IO) -> bytes:
        """Loads data into the object from a filestream.

        Args:
            Buffer: Buffer containing data

        Returns:
            bytes: remaining buffer

        Raises:
            (ValueError): Invalid buffer length
            (ValueError): Invalid Version
        """
        if len(Buffer) < self._StructSize:
            raise ValueError
        (Version, UpdateImageTypeId, UpdateImageIndex, r0, r1, r2,
            UpdateImageSize, UpdateVendorCodeSize, UpdateHardwareInstance) = struct.unpack(
                self._StructFormat,
                Buffer[0:self._StructSize]
        )

        if Version < self.EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER_INIT_VERSION:
            raise ValueError
        if UpdateImageIndex < 1:
            raise ValueError
        if UpdateImageSize + UpdateVendorCodeSize != len(Buffer[self._StructSize:]):
            raise ValueError

        self.Version = Version
        self.UpdateImageTypeId = uuid.UUID(bytes_le=UpdateImageTypeId)
        self.UpdateImageIndex = UpdateImageIndex
        self.UpdateImageSize = UpdateImageSize
        self.UpdateVendorCodeSize = UpdateVendorCodeSize
        self.UpdateHardwareInstance = UpdateHardwareInstance
        self.Payload = Buffer[self._StructSize:self._StructSize + UpdateImageSize]
        if len(self.Payload) > 0:
            self.FmpAuthHeader = FmpAuthHeaderClass()
            self.FmpAuthHeader.Decode(self.Payload)
        self.VendorCodeBytes = Buffer[self._StructSize + UpdateImageSize:]
        return Buffer[self._StructSize:]

    def DumpInfo(self) -> None:
        """Prints object to Console."""
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.Version                = {Version:08X}'
              .format(Version=self.Version))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.UpdateImageTypeId      = {UpdateImageTypeId}'
              .format(UpdateImageTypeId=str(self.UpdateImageTypeId).upper()))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.UpdateImageIndex       = {UpdateImageIndex:08X}'
              .format(UpdateImageIndex=self.UpdateImageIndex))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.UpdateImageSize        = {UpdateImageSize:08X}'
              .format(UpdateImageSize=self.UpdateImageSize))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.UpdateVendorCodeSize   = {UpdateVendorCodeSize:08X}'
              .format(UpdateVendorCodeSize=self.UpdateVendorCodeSize))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER.UpdateHardwareInstance = {UpdateHardwareInstance:016X}'
              .format(UpdateHardwareInstance=self.UpdateHardwareInstance))
        print('sizeof (Payload)                                                    = {Size:08X}'
              .format(Size=len(self.Payload)))
        print('sizeof (VendorCodeBytes)                                            = {Size:08X}'
              .format(Size=len(self.VendorCodeBytes)))
        if self.FmpAuthHeader is not None:
            self.FmpAuthHeader.DumpInfo()


class FmpCapsuleHeaderClass (object):
    """An object representing a EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER_INIT_VERSION.

    Can parse or produce an EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER_INIT_VERSION structure/byte buffer.

    Attributes:
        Version (int): EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER_INIT_VERSION
        EmbeddedDriverCount (int): The number of drivers included in the capsule and the number of corresponding
                                   offsets stored in ItemOffsetList array.
        PayloadItemCount (int):    The number of payload items included in the capsule and the number of corresponding
                                   offsets stored in the ItemOffsetList array.

    ```
    typedef struct {
        UINT32 Version;
        UINT16 EmbeddedDriverCount;
        UINT16 PayloadItemCount;
        UINT64 ItemOffsetList[];
    } EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER;
    #define EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER_INIT_VERSION       0x00000001
    ```
    """
    _StructFormat = '<IHH'
    _StructSize = struct.calcsize(_StructFormat)

    _ItemOffsetFormat = '<Q'
    _ItemOffsetSize = struct.calcsize(_ItemOffsetFormat)

    EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER_INIT_VERSION = 0x00000001

    def __init__(self) -> None:
        """Inits an empty object."""
        self.Version = self.EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER_INIT_VERSION
        self.EmbeddedDriverCount = 0
        self.PayloadItemCount = 0
        self._EmbeddedDriverList = []
        self._FmpCapsuleImageHeaderList = []

    def AddEmbeddedDriver(self, EmbeddedDriver: bytes) -> None:
        """Adds an embedded driver to the list."""
        self._EmbeddedDriverList.append(EmbeddedDriver)
        self.EmbeddedDriverCount += 1

    def GetEmbeddedDriver(self, Index: int) -> bytes:
        """Returns the embedded driver at the index."""
        return self._EmbeddedDriverList[Index]

    def AddFmpCapsuleImageHeader(self, FmpCapsuleHeader: 'FmpCapsuleImageHeaderClass') -> None:
        """Adds an Fmp Capsule Image header to the list."""
        self._FmpCapsuleImageHeaderList.append(FmpCapsuleHeader)
        self.PayloadItemCount += 1

    def GetFmpCapsuleImageHeader(self, Index: int) -> 'FmpCapsuleImageHeaderClass':
        """Returns the Fmp Capsule Image header at the index."""
        return self._FmpCapsuleImageHeaderList[Index]

    def Encode(self) -> bytes:
        r"""Serializes the object.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        self.EmbeddedDriverCount = len(self._EmbeddedDriverList)
        self.PayloadItemCount = len(self._FmpCapsuleImageHeaderList)

        FmpCapsuleHeader = struct.pack(
            self._StructFormat,
            self.Version,
            self.EmbeddedDriverCount,
            self.PayloadItemCount
        )

        FmpCapsuleData = b''
        offset_list = []
        Offset = self._StructSize + (self.EmbeddedDriverCount + self.PayloadItemCount) * self._ItemOffsetSize
        for EmbeddedDriver in self._EmbeddedDriverList:
            FmpCapsuleData = FmpCapsuleData + EmbeddedDriver
            offset_list.append(Offset)
            Offset = Offset + len(EmbeddedDriver)
        for FmpCapsuleImageHeader in self._FmpCapsuleImageHeaderList:
            FmpCapsuleImage = FmpCapsuleImageHeader.Encode()
            FmpCapsuleData = FmpCapsuleData + FmpCapsuleImage
            offset_list.append(Offset)
            Offset = Offset + len(FmpCapsuleImage)

        for Offset in offset_list:
            FmpCapsuleHeader = FmpCapsuleHeader + struct.pack(self._ItemOffsetFormat, Offset)

        return FmpCapsuleHeader + FmpCapsuleData

    def Decode(self, Buffer: IO) -> bytes:
        """Loads data into the object from a Buffer.

        Args:
            Buffer (obj): The buffer containing the data.

        Returns:
            (obj): Reaming buffer

        Raises:
            (ValueError): Invalid Buffer
            (ValueError): Invalid Version
        """
        if len(Buffer) < self._StructSize:
            raise ValueError
        (Version, EmbeddedDriverCount, PayloadItemCount) = struct.unpack(
            self._StructFormat,
            Buffer[0:self._StructSize]
        )
        if Version < self.EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER_INIT_VERSION:
            raise ValueError

        self.Version = Version
        self.EmbeddedDriverCount = EmbeddedDriverCount
        self.PayloadItemCount = PayloadItemCount
        self._EmbeddedDriverList = []
        self._FmpCapsuleImageHeaderList = []

        offset_list = []

        #
        # Parse the ItemOffsetList values
        #
        Offset = self._StructSize
        for Index in range(EmbeddedDriverCount + PayloadItemCount):
            ItemOffset = struct.unpack(self._ItemOffsetFormat, Buffer[Offset:Offset + self._ItemOffsetSize])[0]
            if ItemOffset >= len(Buffer):
                raise ValueError
            offset_list.append(ItemOffset)
            Offset = Offset + self._ItemOffsetSize
        Result = Buffer[Offset:]

        #
        # Parse the EmbeddedDrivers
        #
        for Index in range(EmbeddedDriverCount):
            Offset = offset_list[Index]
            if Index < (len(offset_list) - 1):
                Length = offset_list[Index + 1] - Offset
            else:
                Length = len(Buffer) - Offset
            self.AddEmbeddedDriver(Buffer[Offset:Offset + Length])

        #
        # Parse the Payloads that are FMP Capsule Images
        #
        for Index in range(EmbeddedDriverCount, EmbeddedDriverCount + PayloadItemCount):
            Offset = offset_list[Index]
            if Index < (len(offset_list) - 1):
                Length = offset_list[Index + 1] - Offset
            else:
                Length = len(Buffer) - Offset
            FmpCapsuleImageHeader = FmpCapsuleImageHeaderClass()
            FmpCapsuleImageHeader.Decode(Buffer[Offset:Offset + Length])
            self.AddFmpCapsuleImageHeader(FmpCapsuleImageHeader)

        return Result

    def DumpInfo(self) -> None:
        """Prints the object to the console."""
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.Version             = {Version:08X}'.format(Version=self.Version))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.EmbeddedDriverCount = {EmbeddedDriverCount:08X}'.format(
            EmbeddedDriverCount=self.EmbeddedDriverCount))
        for EmbeddedDriver in self._EmbeddedDriverList:
            print('  sizeof (EmbeddedDriver)                                  = {Size:08X}'.format(
                Size=len(EmbeddedDriver)))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.PayloadItemCount    = {PayloadItemCount:08X}'.format(
            PayloadItemCount=self.PayloadItemCount))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.ItemOffsetList      = ')
        for FmpCapsuleImageHeader in self._FmpCapsuleImageHeaderList:
            FmpCapsuleImageHeader.DumpInfo()
