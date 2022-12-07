## @file
# Module that encodes and decodes a EFI_FIRMWARE_IMAGE_AUTHENTICATION with
# certificate data and payload data.
#
# Copyright (c) 2018 - 2019, Intel Corporation. All rights reserved.<BR>
# Copyright (c) Microsoft Corporation
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

"""Module for encoding and decoding EFI_FIRMWARE_IMAGE_AUTHENTICATION with certificate data and payload data."""

import struct

from edk2toollib.uefi.wincert import WinCertUefiGuid
from edk2toollib.uefi.edk2.fmp_payload_header import FmpPayloadHeaderClass


class FmpAuthHeaderClass (object):
    r"""An object representing an EFI_FIRMWARE_IMAGE_AUTHENTICATION.

    Can parse or produce an EFI_FIRMWARE_IMAGE_AUTHENTICATION structure/byte buffer.

    Attributes:
        MonotonicCount (int):       It is included in the signature of AuthInfo. It is used to ensure freshness/no
                                    replay. It is incremented during each firmware image operation.
        AuthInfo (WinCertUefiGuid): Provides the authorization for the firmware image operations.
        Payload (str):              string representing payload as bytes (i.e. b'\x01\x00\x03')
        FmpPayloadHeader (FmpPayloadHeaderClass): Header for the payload

    ```
    typedef struct {
        UINT64                                  MonotonicCount;
        WIN_CERTIFICATE_UEFI_GUID               AuthInfo;
    } EFI_FIRMWARE_IMAGE_AUTHENTICATION;
    ```
    """
    _MonotonicCountFormat = '<Q'
    _MonotonicCountSize = struct.calcsize(_MonotonicCountFormat)

    def __init__(self):
        """Inits an empty object."""
        self.MonotonicCount = 0
        self.AuthInfo = WinCertUefiGuid()
        self.Payload = b''
        self.FmpPayloadHeader = None

    def Encode(self):
        r"""Serializes the Auth header + AuthInfo + Payload/FmpPayloadHeader.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        FmpAuthHeader = struct.pack(
            self._MonotonicCountFormat,
            self.MonotonicCount
        )

        if self.FmpPayloadHeader is not None:
            return FmpAuthHeader + self.AuthInfo.Encode() + self.FmpPayloadHeader.Encode()
        else:
            return FmpAuthHeader + self.AuthInfo.Encode() + self.Payload

    def Decode(self, Buffer):
        """Loads data into the Object by parsing a buffer.

        Args:
            Buffer (obj): Buffer containing the data

        Returns:
            (str): string of binary representing the payload

        Raises:
            (ValueError): Invalid Buffer
        """
        if len(Buffer) < self._MonotonicCountSize:
            raise ValueError
        (MonotonicCount,) = struct.unpack(
            self._MonotonicCountFormat,
            Buffer[:self._MonotonicCountSize]
        )
        self.MonotonicCount = MonotonicCount

        self.Payload = self.AuthInfo.Decode(Buffer[self._MonotonicCountSize:])
        if len(self.Payload) > 0:
            self.FmpPayloadHeader = FmpPayloadHeaderClass()
            self.FmpPayloadHeader.Decode(self.Payload)
        return self.Payload

    def IsSigned(self, Buffer):
        """Parses the buffer and returns if the Cert is signed or not.

        Returns:
            (bool): True if signed
            (bool): False if invalid buffer
            (bool): False if not signed
        """
        if len(Buffer) < self._MonotonicCountSize:
            return False

        auth_info = WinCertUefiGuid(Buffer[self._MonotonicCountSize:])
        if auth_info.CertType != WinCertUefiGuid._EFI_CERT_TYPE_PKCS7_GUID.bytes_le:
            return False
        return True

    def DumpInfo(self):
        """Prints object to console."""
        print('EFI_FIRMWARE_IMAGE_AUTHENTICATION.MonotonicCount                = {MonotonicCount:016X}'
              .format(MonotonicCount=self.MonotonicCount))
        self.AuthInfo.DumpInfo()
        print('sizeof (Payload)                                                = {Size:08X}'
              .format(Size=len(self.Payload)))
        if self.FmpPayloadHeader is not None:
            self.FmpPayloadHeader.DumpInfo()
