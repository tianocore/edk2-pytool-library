# @file wincert.py
# Code to work with UEFI WinCert data
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##


import io
import struct
import uuid
from edk2toollib.utility_functions import PrintByteList


class WinCertPkcs1(object):
    # ///
    # /// Certificate which encapsulates the RSASSA_PKCS1-v1_5 digital signature.
    # ///
    # /// The WIN_CERTIFICATE_UEFI_PKCS1_15 structure is derived from
    # /// WIN_CERTIFICATE and encapsulate the information needed to
    # /// implement the RSASSA-PKCS1-v1_5 digital signature algorithm as
    # /// specified in RFC2437.
    # ///
    # typedef struct {
    #   ///
    #   /// This is the standard WIN_CERTIFICATE header, where
    #   /// wCertificateType is set to WIN_CERT_TYPE_UEFI_PKCS1_15.
    #   ///
    #   WIN_CERTIFICATE Hdr;
    #   ///
    #   /// This is the hashing algorithm which was performed on the
    #   /// UEFI executable when creating the digital signature.
    #   ///
    #   EFI_GUID        HashAlgorithm;
    #   ///
    #   /// The following is the actual digital signature. The
    #   /// size of the signature is the same size as the key
    #   /// (1024-bit key is 128 bytes) and can be determined by
    #   /// subtracting the length of the other parts of this header
    #   /// from the total length of the certificate as found in
    #   /// Hdr.dwLength.
    #   ///
    #   /// UINT8 Signature[];
    #   ///
    # } WIN_CERTIFICATE_EFI_PKCS1_15;
    #
    # ///
    # /// The WIN_CERTIFICATE structure is part of the PE/COFF specification.
    # ///
    # typedef struct {
    #   ///
    #   /// The length of the entire certificate,
    #   /// including the length of the header, in bytes.
    #   ///
    #   UINT32  dwLength;
    #   ///
    #   /// The revision level of the WIN_CERTIFICATE
    #   /// structure. The current revision level is 0x0200.
    #   ///
    #   UINT16  wRevision;
    #   ///
    #   /// The certificate type. See WIN_CERT_TYPE_xxx for the UEFI
    #   /// certificate types. The UEFI specification reserves the range of
    #   /// certificate type values from 0x0EF0 to 0x0EFF.
    #   ///
    #   UINT16  wCertificateType;
    #   ///
    #   /// The following is the actual certificate. The format of
    #   /// the certificate depends on wCertificateType.
    #   ///
    #   /// UINT8 bCertificate[ANYSIZE_ARRAY];
    #   ///
    # } WIN_CERTIFICATE;

    STATIC_STRUCT_SIZE = (4 + 2 + 2 + 16)
    EFI_HASH_SHA256 = uuid.UUID("{51AA59DE-FDF2-4EA3-BC63-875FB7842EE9}")  # EFI_HASH_SHA256 guid defined by UEFI spec

    def __init__(self, filestream=None):
        if(filestream is None):
            self.Hdr_dwLength = WinCertPkcs1.STATIC_STRUCT_SIZE
            self.Hdr_wRevision = WinCert.REVISION
            self.Hdr_wCertificateType = WinCert.WIN_CERT_TYPE_EFI_PKCS115
            self.HashAlgorithm = None
            self.CertData = None
        else:
            self.PopulateFromFileStream(filestream)

    def AddCertData(self, fs):
        if(self.CertData is not None):
            raise Exception("Cert Data not 0")
        if(self.HashAlgorithm is None):
            raise Exception("You must set the Hash Algorithm first")
        self.CertData = fs.read()
        self.Hdr_dwLength = self.Hdr_dwLength + len(self.CertData)
    #
    # Method to un-serialize from a filestream
    #

    def PopulateFromFileStream(self, fs):
        if(fs is None):
            raise Exception("Invalid File stream")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if((end - offset) < WinCertPkcs1.STATIC_STRUCT_SIZE):  # size of the static header data
            raise Exception("Invalid file stream size")

        self.Hdr_dwLength = struct.unpack("=I", fs.read(4))[0]
        self.Hdr_wRevision = struct.unpack("=H", fs.read(2))[0]
        self.Hdr_wCertificateType = struct.unpack("=H", fs.read(2))[0]
        self.HashAlgorithm = uuid.UUID(bytes_le=fs.read(16))
        self.CertData = None

        if((end - fs.tell()) < 1):
            raise Exception("Invalid File stream. No data for signature cert data")

        if((end - fs.tell()) < (self.Hdr_dwLength - WinCertPkcs1.STATIC_STRUCT_SIZE)):
            raise Exception("Invalid file stream size")

        self.CertData = memoryview(fs.read(self.Hdr_dwLength - WinCertPkcs1.STATIC_STRUCT_SIZE))

    def Print(self):
        print("WinCertPKCS115")
        print("  Hdr_dwLength:         0x%X" % self.Hdr_dwLength)
        print("  Hdr_wRevision:        0x%X" % self.Hdr_wRevision)
        print("  Hdr_wCertificateType: 0x%X" % self.Hdr_wCertificateType)
        print("  Hash Guid:            %s" % str(self.HashAlgorithm))
        print("  CertData:             ")
        cdl = self.CertData.tolist()
        PrintByteList(cdl)

    def Write(self, fs):
        fs.write(struct.pack("=I", self.Hdr_dwLength))
        fs.write(struct.pack("=H", self.Hdr_wRevision))
        fs.write(struct.pack("=H", self.Hdr_wCertificateType))
        fs.write(self.HashAlgorithm.bytes_le)
        fs.write(self.CertData)


class WinCertUefiGuid(object):
    # ///
    # /// Certificate which encapsulates a GUID-specific digital signature
    # ///
    # typedef struct {
    #   ///
    #   /// This is the standard WIN_CERTIFICATE header, where
    #   /// wCertificateType is set to WIN_CERT_TYPE_EFI_GUID.
    #   ///
    #   WIN_CERTIFICATE   Hdr;
    #   ///
    #   /// This is the unique id which determines the
    #   /// format of the CertData. .
    #   ///
    #   EFI_GUID          CertType;
    #   ///
    #   /// The following is the certificate data. The format of
    #   /// the data is determined by the CertType.
    #   /// If CertType is EFI_CERT_TYPE_RSA2048_SHA256_GUID,
    #   /// the CertData will be EFI_CERT_BLOCK_RSA_2048_SHA256 structure.
    #   ///
    #   UINT8            CertData[1];
    # } WIN_CERTIFICATE_UEFI_GUID;
    #
    # ///
    # /// The WIN_CERTIFICATE structure is part of the PE/COFF specification.
    # ///
    # typedef struct {
    #   ///
    #   /// The length of the entire certificate,
    #   /// including the length of the header, in bytes.
    #   ///
    #   UINT32  dwLength;
    #   ///
    #   /// The revision level of the WIN_CERTIFICATE
    #   /// structure. The current revision level is 0x0200.
    #   ///
    #   UINT16  wRevision;
    #   ///
    #   /// The certificate type. See WIN_CERT_TYPE_xxx for the UEFI
    #   /// certificate types. The UEFI specification reserves the range of
    #   /// certificate type values from 0x0EF0 to 0x0EFF.
    #   ///
    #   UINT16  wCertificateType;
    #   ///
    #   /// The following is the actual certificate. The format of
    #   /// the certificate depends on wCertificateType.
    #   ///
    #   /// UINT8 bCertificate[ANYSIZE_ARRAY];
    #   ///
    # } WIN_CERTIFICATE;

    _StructFormat = '<IHH16s'
    _StructSize = struct.calcsize(_StructFormat)

    _EFI_CERT_TYPE_PKCS7_GUID = uuid.UUID('4aafd29d-68df-49ee-8aa9-347d375665a7')

    # Preserved for back compat.
    STATIC_STRUCT_SIZE = _StructSize
    PKCS7Guid = _EFI_CERT_TYPE_PKCS7_GUID

    def __init__(self, in_data=None):
        self.Hdr_dwLength = self._StructSize
        self.Hdr_wRevision = WinCert.REVISION
        self.Hdr_wCertificateType = WinCert.WIN_CERT_TYPE_EFI_GUID
        self.CertType = self._EFI_CERT_TYPE_PKCS7_GUID
        self.CertData = b''

        if in_data is not None:
            # Account for back compat. Behave differently for file streams.
            if hasattr(in_data, 'seek'):
                self.PopulateFromFileStream(in_data)
            else:
                self.Decode(in_data)

    def Encode(self):
        if self.Hdr_wRevision != self._WIN_CERT_REVISION:
            raise ValueError
        if self.Hdr_wCertificateType != self._WIN_CERT_TYPE_EFI_GUID:
            raise ValueError
        if self.CertType != self._EFI_CERT_TYPE_PKCS7_GUID:
            raise ValueError
        self.Hdr_dwLength = self._StructSize + len(self.CertData)

        WinCertHeader = struct.pack(
            self._StructFormat,
            self.dwLength,
            self.wRevision,
            self.wCertificateType,
            self.CertType.bytes_le
        )

        return WinCertHeader + self.CertData

    def Decode(self, Buffer):
        if len(Buffer) < self._StructSize:
            raise ValueError
        (dwLength, wRevision, wCertificateType, CertType) = struct.unpack(
            self._StructFormat,
            Buffer[0:self._StructSize]
        )
        if dwLength < self._StructSize:
            raise ValueError
        if wRevision != WinCert.REVISION:
            raise ValueError
        if wCertificateType != WinCert.WIN_CERT_TYPE_EFI_GUID:
            raise ValueError
        if CertType != self._EFI_CERT_TYPE_PKCS7_GUID.bytes_le:
            raise ValueError
        self.Hdr_dwLength = dwLength
        self.Hdr_wRevision = wRevision
        self.Hdr_wCertificateType = wCertificateType
        self.CertType = uuid.UUID(bytes_le=CertType)
        self.CertData = Buffer[self._StructSize:self.Hdr_dwLength]

        # Return the remaining buffer, if any exists.
        return Buffer[self.Hdr_dwLength:]

    def AddCertData(self, in_data):
        # Account for back compat. Behave differently for file streams.
        if hasattr(in_data, 'seek'):
            self.CertData = in_data.read()
        else:
            self.CertData = in_data

        self.Hdr_dwLength = self.Hdr_dwLength + len(self.CertData)

    #
    # Method to un-serialize from a filestream
    #

    def PopulateFromFileStream(self, fs):
        if fs is None:
            raise ValueError

        # Determine the end of the stream.
        current = fs.tell()
        end = fs.seek(0, io.SEEK_END)
        fs.seek(current)

        # Make sure that we can at least parse the size field.
        field_string = "<I"
        field_size = struct.calcsize(field_string)
        if (end - current) < field_size:
            raise ValueError

        # Parse the size field.
        (buffer_size,) = struct.unpack(field_string, fs.read(field_size))

        if (end - current) < buffer_size:
            raise ValueError

        fs.seek(current)
        object_buffer = fs.read(buffer_size)

        return self.Decode(object_buffer)

    def Print(self):
        self.DumpInfo()

    def DumpInfo(self):
        print('EFI_FIRMWARE_IMAGE_AUTHENTICATION.AuthInfo.Hdr.dwLength         = {dwLength:08X}'
              .format(dwLength=self.Hdr_dwLength))
        print('EFI_FIRMWARE_IMAGE_AUTHENTICATION.AuthInfo.Hdr.wRevision        = {wRevision:04X}'
              .format(wRevision=self.Hdr_wRevision))
        print('EFI_FIRMWARE_IMAGE_AUTHENTICATION.AuthInfo.Hdr.wCertificateType = {wCertificateType:04X}'
              .format(wCertificateType=self.Hdr_wCertificateType))
        print('EFI_FIRMWARE_IMAGE_AUTHENTICATION.AuthInfo.CertType             = {Guid}'
              .format(Guid=str(self.CertType).upper()))
        print('sizeof (EFI_FIRMWARE_IMAGE_AUTHENTICATION.AuthInfo.CertData)    = {Size:08X}'
              .format(Size=len(self.CertData)))

    def Write(self, fs):
        fs.write(self.Encode)


class WinCert(object):
    STATIC_STRUCT_SIZE = 8
    # WIN_CERTIFICATE.wCertificateTypes UEFI Spec defined
    WIN_CERT_TYPE_NONE = 0x0000
    WIN_CERT_TYPE_PKCS_SIGNED_DATA = 0x0002
    WIN_CERT_TYPE_EFI_PKCS115 = 0x0EF0
    WIN_CERT_TYPE_EFI_GUID = 0x0EF1
    # Revision
    REVISION = 0x200

    #
    # this method is a factory
    #
    @staticmethod
    def Factory(fs):
        if(fs is None):
            raise Exception("Invalid File stream")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if((end - offset) < WinCert.STATIC_STRUCT_SIZE):  # size of the static header data
            raise Exception("Invalid file stream size")
        # 1 read len
        # 2 read revision
        # 3 read cert type
        fs.seek(4, 1)  # seeking past Hdr_dwLength
        fs.seek(2, 1)  # seeking past Hdr_wRevision
        Hdr_wCertificateType = struct.unpack("=H", fs.read(2))[0]

        fs.seek(offset)

        if(Hdr_wCertificateType == WinCert.WIN_CERT_TYPE_EFI_GUID):
            return WinCertUefiGuid(fs)
        elif(Hdr_wCertificateType == WinCert.WIN_CERT_TYPE_EFI_PKCS115):
            return WinCertPkcs1(fs)
        else:
            return None
