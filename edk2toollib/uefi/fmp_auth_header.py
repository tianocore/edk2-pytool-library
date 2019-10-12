## @file
# Module that encodes and decodes a EFI_FIRMWARE_IMAGE_AUTHENTICATION with
# certificate data and payload data.
#
# Copyright (c) 2018 - 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

'''
FmpAuthHeader
'''

import struct

from edk2toollib.uefi.wincert import WinCertUefiGuid


class FmpAuthHeaderClass (object):
    # ///
    # /// Image Attribute -Authentication Required
    # ///
    # typedef struct {
    #   ///
    #   /// It is included in the signature of AuthInfo. It is used to ensure freshness/no replay.
    #   /// It is incremented during each firmware image operation.
    #   ///
    #   UINT64                                  MonotonicCount;
    #   ///
    #   /// Provides the authorization for the firmware image operations. It is a signature across
    #   /// the image data and the Monotonic Count value. Caller uses the private key that is
    #   /// associated with a public key that has been provisioned via the key exchange.
    #   /// Because this is defined as a signature, WIN_CERTIFICATE_UEFI_GUID.CertType must
    #   /// be EFI_CERT_TYPE_PKCS7_GUID.
    #   ///
    #   WIN_CERTIFICATE_UEFI_GUID               AuthInfo;
    # } EFI_FIRMWARE_IMAGE_AUTHENTICATION;

    _MonotonicCountFormat = '<Q'
    _MonotonicCountSize = struct.calcsize(_MonotonicCountFormat)

    def __init__(self):
        self._Valid = False
        self.MonotonicCount = 0
        self.AuthInfo = WinCertUefiGuid()
        self.Payload = b''

    def Encode(self):
        FmpAuthHeader = struct.pack(
            self._MonotonicCountFormat,
            self.MonotonicCount
        )
        self._Valid = True

        return FmpAuthHeader + self.AuthInfo.Encode() + self.Payload

    def Decode(self, Buffer):
        if len(Buffer) < self._MonotonicCountSize:
            raise ValueError
        (MonotonicCount,) = struct.unpack(
            self._MonotonicCountFormat,
            Buffer[:self._MonotonicCountSize]
        )
        self.MonotonicCount = MonotonicCount

        self.Payload = self.AuthInfo.Decode(Buffer[self._MonotonicCountSize:])
        self._Valid = True

        return self.Payload

    def IsSigned(self, Buffer):
        if len(Buffer) < self._MonotonicCountSize:
            return False

        auth_info = WinCertUefiGuid(Buffer[self._MonotonicCountSize:])
        if auth_info.CertType != WinCertUefiGuid._EFI_CERT_TYPE_PKCS7_GUID.bytes_le:
            return False
        return True

    def DumpInfo(self):
        if not self._Valid:
            raise ValueError
        print('EFI_FIRMWARE_IMAGE_AUTHENTICATION.MonotonicCount                = {MonotonicCount:016X}'
              .format(MonotonicCount=self.MonotonicCount))
        self.AuthInfo.DumpInfo()
        print('sizeof (Payload)                                                = {Size:08X}'
              .format(Size=len(self.Payload)))
