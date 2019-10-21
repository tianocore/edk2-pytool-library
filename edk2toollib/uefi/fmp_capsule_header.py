## @file
# Module that encodes and decodes a EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER with
# a payload.
#
# Copyright (c) 2018 - 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
FmpCapsuleHeader
'''

import struct
import uuid
from edk2toollib.uefi.fmp_auth_header import FmpAuthHeaderClass


class FmpCapsuleImageHeaderClass (object):
    # typedef struct {
    #   UINT32   Version;
    #
    #   ///
    #   /// Used to identify device firmware targeted by this update. This guid is matched by
    #   /// system firmware against ImageTypeId field within a EFI_FIRMWARE_IMAGE_DESCRIPTOR
    #   ///
    #   EFI_GUID UpdateImageTypeId;
    #
    #   ///
    #   /// Passed as ImageIndex in call to EFI_FIRMWARE_MANAGEMENT_PROTOCOL.SetImage ()
    #   ///
    #   UINT8    UpdateImageIndex;
    #   UINT8    reserved_bytes[3];
    #
    #   ///
    #   /// Size of the binary update image which immediately follows this structure
    #   ///
    #   UINT32   UpdateImageSize;
    #
    #   ///
    #   /// Size of the VendorCode bytes which optionally immediately follow binary update image in the capsule
    #   ///
    #   UINT32   UpdateVendorCodeSize;
    #
    #   ///
    #   /// The HardwareInstance to target with this update. If value is zero it means match all
    #   /// HardwareInstances. This field allows update software to target only a single device in
    #   /// cases where there are more than one device with the same ImageTypeId GUID.
    #   /// This header is outside the signed data of the Authentication Info structure and
    #   /// therefore can be modified without changing the Auth data.
    #   ///
    #   UINT64   UpdateHardwareInstance;
    # } EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER;
    #
    #  #define EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER_INIT_VERSION 0x00000002

    _StructFormat = '<I16sB3BIIQ'  # spell-checker: disable-line
    _StructSize = struct.calcsize(_StructFormat)

    EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER_INIT_VERSION = 0x00000002

    def __init__(self):
        self.Version = self.EFI_FIRMWARE_MANAGEMENT_CAPSULE_IMAGE_HEADER_INIT_VERSION
        self.UpdateImageTypeId = uuid.UUID('00000000-0000-0000-0000-000000000000')
        self.UpdateImageIndex = 0
        self.UpdateImageSize = 0
        self.UpdateVendorCodeSize = 0
        self.UpdateHardwareInstance = 0x0000000000000000
        self.Payload = b''
        self.VendorCodeBytes = b''
        self.FmpAuthHeader = None

    def Encode(self):
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

    def Decode(self, Buffer):
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

    def DumpInfo(self):
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
    # typedef struct {
    #   UINT32 Version;
    #
    #   ///
    #   /// The number of drivers included in the capsule and the number of corresponding
    #   /// offsets stored in ItemOffsetList array.
    #   ///
    #   UINT16 EmbeddedDriverCount;
    #
    #   ///
    #   /// The number of payload items included in the capsule and the number of
    #   /// corresponding offsets stored in the ItemOffsetList array.
    #   ///
    #   UINT16 PayloadItemCount;
    #
    #   ///
    #   /// Variable length array of dimension [EmbeddedDriverCount + PayloadItemCount]
    #   /// containing offsets of each of the drivers and payload items contained within the capsule
    #   ///
    #   // UINT64 ItemOffsetList[];
    # } EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER;
    #
    #  #define EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER_INIT_VERSION       0x00000001
    _StructFormat = '<IHH'
    _StructSize = struct.calcsize(_StructFormat)

    _ItemOffsetFormat = '<Q'
    _ItemOffsetSize = struct.calcsize(_ItemOffsetFormat)

    EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER_INIT_VERSION = 0x00000001

    def __init__(self):
        self.Version = self.EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER_INIT_VERSION
        self.EmbeddedDriverCount = 0
        self.PayloadItemCount = 0
        self._ItemOffsetList = []
        self._EmbeddedDriverList = []
        self._FmpCapsuleImageHeaderList = []

    def AddEmbeddedDriver(self, EmbeddedDriver):
        self._EmbeddedDriverList.append(EmbeddedDriver)

    def GetEmbeddedDriver(self, Index):
        return self._EmbeddedDriverList[Index]

    def AddFmpCapsuleImageHeader(self, FmpCapsuleHeader):
        self._FmpCapsuleImageHeaderList.append(FmpCapsuleHeader)

    def GetFmpCapsuleImageHeader(self, Index):
        return self._FmpCapsuleImageHeaderList[Index]

    def Encode(self):
        self.EmbeddedDriverCount = len(self._EmbeddedDriverList)
        self.PayloadItemCount = len(self._FmpCapsuleImageHeaderList)

        FmpCapsuleHeader = struct.pack(
            self._StructFormat,
            self.Version,
            self.EmbeddedDriverCount,
            self.PayloadItemCount
        )

        FmpCapsuleData = b''
        Offset = self._StructSize + (self.EmbeddedDriverCount + self.PayloadItemCount) * self._ItemOffsetSize
        for EmbeddedDriver in self._EmbeddedDriverList:
            FmpCapsuleData = FmpCapsuleData + EmbeddedDriver
            self._ItemOffsetList.append(Offset)
            Offset = Offset + len(EmbeddedDriver)
        for FmpCapsuleImageHeader in self._FmpCapsuleImageHeaderList:
            FmpCapsuleImage = FmpCapsuleImageHeader.Encode()
            FmpCapsuleData = FmpCapsuleData + FmpCapsuleImage
            self._ItemOffsetList.append(Offset)
            Offset = Offset + len(FmpCapsuleImage)

        for Offset in self._ItemOffsetList:
            FmpCapsuleHeader = FmpCapsuleHeader + struct.pack(self._ItemOffsetFormat, Offset)

        return FmpCapsuleHeader + FmpCapsuleData

    def Decode(self, Buffer):
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
        self._ItemOffsetList = []
        self._EmbeddedDriverList = []
        self._FmpCapsuleImageHeaderList = []

        #
        # Parse the ItemOffsetList values
        #
        Offset = self._StructSize
        for Index in range(0, EmbeddedDriverCount + PayloadItemCount):
            ItemOffset = struct.unpack(self._ItemOffsetFormat, Buffer[Offset:Offset + self._ItemOffsetSize])[0]
            if ItemOffset >= len(Buffer):
                raise ValueError
            self._ItemOffsetList.append(ItemOffset)
            Offset = Offset + self._ItemOffsetSize
        Result = Buffer[Offset:]

        #
        # Parse the EmbeddedDrivers
        #
        for Index in range(0, EmbeddedDriverCount):
            Offset = self._ItemOffsetList[Index]
            if Index < (len(self._ItemOffsetList) - 1):
                Length = self._ItemOffsetList[Index + 1] - Offset
            else:
                Length = len(Buffer) - Offset
            self.AddEmbeddedDriver(Buffer[Offset:Offset + Length])

        #
        # Parse the Payloads that are FMP Capsule Images
        #
        for Index in range(EmbeddedDriverCount, EmbeddedDriverCount + PayloadItemCount):
            Offset = self._ItemOffsetList[Index]
            if Index < (len(self._ItemOffsetList) - 1):
                Length = self._ItemOffsetList[Index + 1] - Offset
            else:
                Length = len(Buffer) - Offset
            FmpCapsuleImageHeader = FmpCapsuleImageHeaderClass()
            FmpCapsuleImageHeader.Decode(Buffer[Offset:Offset + Length])
            self.AddFmpCapsuleImageHeader(FmpCapsuleImageHeader)

        return Result

    def DumpInfo(self):
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.Version             = {Version:08X}'.format(Version=self.Version))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.EmbeddedDriverCount = {EmbeddedDriverCount:08X}'.format(
            EmbeddedDriverCount=self.EmbeddedDriverCount))
        for EmbeddedDriver in self._EmbeddedDriverList:
            print('  sizeof (EmbeddedDriver)                                  = {Size:08X}'.format(
                Size=len(EmbeddedDriver)))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.PayloadItemCount    = {PayloadItemCount:08X}'.format(
            PayloadItemCount=self.PayloadItemCount))
        print('EFI_FIRMWARE_MANAGEMENT_CAPSULE_HEADER.ItemOffsetList      = ')
        for Offset in self._ItemOffsetList:
            print('  {Offset:016X}'.format(Offset=Offset))
        for FmpCapsuleImageHeader in self._FmpCapsuleImageHeaderList:
            FmpCapsuleImageHeader.DumpInfo()
