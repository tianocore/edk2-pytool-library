# @file wincert.py
# Code to work with UEFI WinCert data
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

"""Module for working with UEFI WinCert data."""


import io
import struct
import uuid
from edk2toollib.utility_functions import PrintByteList


class WinCertPkcs1(object):
    """Object representing a WinCertPkcs1 struct.

    Certificate which encapsulates the RSASSA_PKCS1-v1_5 digital signature.

    Attributes:
        Hdr_dwLength (int):         The length of the entire certificate, including the length of the header, in bytes.
        Hdr_wRevision (int):        The certificate type. See WIN_CERT_TYPE_xxx for the UEFI certificate types. The UEFI
                                    specification reserves the range of certificate type values from 0x0EF0 to 0x0EFF.
        Hdr_wCertificateType (int): The following is the actual certificate. The format of the certificate depends on
                                    wCertificateType.
        HashAlgorithm (uuid.UUID):  The Guid representing the hash algorithm for the Cert.
        CertData (memoryview):      The actual Cert.

    The WIN_CERTIFICATE_UEFI_PKCS1_15 structure is derived from
    WIN_CERTIFICATE and encapsulate the information needed to
    implement the RSASSA-PKCS1-v1_5 digital signature algorithm as
    specified in RFC2437.
    typedef struct {
        WIN_CERTIFICATE Hdr;
        EFI_GUID        HashAlgorithm;
        UINT8 Signature[];
    } WIN_CERTIFICATE_EFI_PKCS1_15;

    The WIN_CERTIFICATE structure is part of the PE/COFF specification.
    typedef struct {
        UINT32  dwLength;
        UINT16  wRevision;
        UINT16  wCertificateType;
        UINT8 bCertificate[ANYSIZE_ARRAY];
    } WIN_CERTIFICATE;
    """
    STATIC_STRUCT_SIZE = (4 + 2 + 2 + 16)
    EFI_HASH_SHA256 = uuid.UUID("{51AA59DE-FDF2-4EA3-BC63-875FB7842EE9}")  # EFI_HASH_SHA256 guid defined by UEFI spec

    def __init__(self, filestream=None):
        """Inits the object."""
        if (filestream is None):
            self.Hdr_dwLength = WinCertPkcs1.STATIC_STRUCT_SIZE
            self.Hdr_wRevision = WinCert.REVISION
            self.Hdr_wCertificateType = WinCert.WIN_CERT_TYPE_EFI_PKCS115
            self.HashAlgorithm = None
            self.CertData = None
        else:
            self.PopulateFromFileStream(filestream)

    def AddCertData(self, fs):
        """Adds the Cert Data to the struct.

        Raises:
            (Exception): Invalid Cert Data
            (Exception): Missing Hash Algorithm
        """
        if (self.CertData is not None):
            raise Exception("Cert Data not 0")
        if (self.HashAlgorithm is None):
            raise Exception("You must set the Hash Algorithm first")
        self.CertData = fs.read()
        self.Hdr_dwLength = self.Hdr_dwLength + len(self.CertData)

    def PopulateFromFileStream(self, fs):
        """Populates the struct from a filestream.

        Args:
            fs (obj): An open file

        Raises:
            (Exception): Invalid stream
            (Exception): Invalid stream size
        """
        if (fs is None):
            raise Exception("Invalid File stream")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if ((end - offset) < WinCertPkcs1.STATIC_STRUCT_SIZE):  # size of the static header data
            raise Exception("Invalid file stream size")

        self.Hdr_dwLength = struct.unpack("=I", fs.read(4))[0]
        self.Hdr_wRevision = struct.unpack("=H", fs.read(2))[0]
        self.Hdr_wCertificateType = struct.unpack("=H", fs.read(2))[0]
        self.HashAlgorithm = uuid.UUID(bytes_le=fs.read(16))
        self.CertData = None

        if ((end - fs.tell()) < 1):
            raise Exception("Invalid File stream. No data for signature cert data")

        if ((end - fs.tell()) < (self.Hdr_dwLength - WinCertPkcs1.STATIC_STRUCT_SIZE)):
            raise Exception("Invalid file stream size")

        self.CertData = memoryview(fs.read(self.Hdr_dwLength - WinCertPkcs1.STATIC_STRUCT_SIZE))

    def Print(self):
        """Prints the struct to the console."""
        print("WinCertPKCS115")
        print("  Hdr_dwLength:         0x%X" % self.Hdr_dwLength)
        print("  Hdr_wRevision:        0x%X" % self.Hdr_wRevision)
        print("  Hdr_wCertificateType: 0x%X" % self.Hdr_wCertificateType)
        print("  Hash Guid:            %s" % str(self.HashAlgorithm))
        print("  CertData:             ")
        cdl = self.CertData.tolist()
        PrintByteList(cdl)

    def Write(self, fs):
        r"""Serializes the object.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        fs.write(struct.pack("=I", self.Hdr_dwLength))
        fs.write(struct.pack("=H", self.Hdr_wRevision))
        fs.write(struct.pack("=H", self.Hdr_wCertificateType))
        fs.write(self.HashAlgorithm.bytes_le)
        fs.write(self.CertData)


class WinCertUefiGuid(object):
    """Object representing a Certificate which encapsulates a GUID-specific digital signature.

    Attributes:
        Hdr_dwLength (int):         The length of the entire certificate, including the length of the header, in bytes.
        Hdr_wRevision (int):        The certificate type. See WIN_CERT_TYPE_xxx for the UEFI certificate types. The UEFI
                                    specification reserves the range of certificate type values from 0x0EF0 to 0x0EFF.
        Hdr_wCertificateType (int): The following is the actual certificate. The format of the certificate depends on
                                    wCertificateType.
        CertData (memoryview):      The actual Cert.

    typedef struct {
        WIN_CERTIFICATE   Hdr;
        EFI_GUID          CertType;
        UINT8            CertData[1];
    } WIN_CERTIFICATE_UEFI_GUID;

    The WIN_CERTIFICATE structure is part of the PE/COFF specification.
    typedef struct {
        UINT32  dwLength;
        UINT16  wRevision;
        UINT16  wCertificateType;
        UINT8 bCertificate[ANYSIZE_ARRAY];
    } WIN_CERTIFICATE;
    """

    _StructFormat = '<IHH16s'
    _StructSize = struct.calcsize(_StructFormat)

    _EFI_CERT_TYPE_PKCS7_GUID = uuid.UUID('4aafd29d-68df-49ee-8aa9-347d375665a7')

    # Preserved for back compat.
    STATIC_STRUCT_SIZE = _StructSize
    PKCS7Guid = _EFI_CERT_TYPE_PKCS7_GUID

    def __init__(self, in_data=None):
        """Inits the object."""
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
        r"""Serializes the object.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')

        Raises:
            (ValueError): Invalid Revision
            (ValueError): Invalid Cert Type
        """
        if self.Hdr_wRevision != WinCert.REVISION:
            raise ValueError
        if self.Hdr_wCertificateType != WinCert.WIN_CERT_TYPE_EFI_GUID:
            raise ValueError
        if self.CertType != self._EFI_CERT_TYPE_PKCS7_GUID:
            raise ValueError
        self.Hdr_dwLength = self._StructSize + len(self.CertData)

        WinCertHeader = struct.pack(
            self._StructFormat,
            self.Hdr_dwLength,
            self.Hdr_wRevision,
            self.Hdr_wCertificateType,
            self.CertType.bytes_le
        )

        return WinCertHeader + self.CertData

    def Decode(self, Buffer):
        """Loads the struct with values from a buffer.

        Args:
            Buffer (obj): Buffer containing serialized data

        Returns:
            (obj): Any remaining buffer

        Raises:
            (ValueError): Invalid Buffer
            (ValueError): Invalid dw length
            (ValueError): Invalid Revision
            (ValueError): Invalid Cert Type
        """
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
        """Adds the Cert Data to the struct.

        Args:
            in_data (obj): Data to read.
        """
        # Account for back compat. Behave differently for file streams.
        if hasattr(in_data, 'seek'):
            self.CertData = in_data.read()
        else:
            self.CertData = in_data

        self.Hdr_dwLength = self.Hdr_dwLength + len(self.CertData)

    def PopulateFromFileStream(self, fs):
        """Un-serialized from a filestream.

        Args:
            fs (obj): Already opened file

        Raises:
            (ValueError): Invalid fs
            (ValueError): Invalid size
        """
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
        """Prints struct to console."""
        self.DumpInfo()

    def DumpInfo(self):
        """Prints struct to console."""
        print('WIN_CERTIFICATE.dwLength         = {dwLength:08X}'
              .format(dwLength=self.Hdr_dwLength))
        print('WIN_CERTIFICATE.wRevision        = {wRevision:04X}'
              .format(wRevision=self.Hdr_wRevision))
        print('WIN_CERTIFICATE.wCertificateType = {wCertificateType:04X}'
              .format(wCertificateType=self.Hdr_wCertificateType))
        print('WIN_CERTIFICATE_UEFI_GUID.CertType             = {Guid}'
              .format(Guid=str(self.CertType).upper()))
        print('sizeof (WIN_CERTIFICATE_UEFI_GUID.CertData)    = {Size:08X}'
              .format(Size=len(self.CertData)))

    def Write(self, fs):
        """Writes the struct to a filestream."""
        fs.write(self.Encode())


class WinCert(object):
    """Object for generating a WinCert."""
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
        """Generates a specific Cert Type depending on parsed Hdr_wCertificationType from the fs.

        Args:
            fs (obj): filestream

        Returns:
            (WinCertUefiGuid): if Hdr_wCertificationType == WIN_CERT_TYPE_EFI_GUID
            (WinCertPkcs1): if Hdr_wCertificationType == WIN_CERT_TYPE_EFI_PKCS115
        Raises:
            (Exception): Invalid fs
            (Exception): Invalid fs size
        """
        if (fs is None):
            raise Exception("Invalid File stream")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if ((end - offset) < WinCert.STATIC_STRUCT_SIZE):  # size of the static header data
            raise Exception("Invalid file stream size")
        # 1 read len
        # 2 read revision
        # 3 read cert type
        fs.seek(4, 1)  # seeking past Hdr_dwLength
        fs.seek(2, 1)  # seeking past Hdr_wRevision
        Hdr_wCertificateType = struct.unpack("=H", fs.read(2))[0]

        fs.seek(offset)

        if (Hdr_wCertificateType == WinCert.WIN_CERT_TYPE_EFI_GUID):
            return WinCertUefiGuid(fs)
        elif (Hdr_wCertificateType == WinCert.WIN_CERT_TYPE_EFI_PKCS115):
            return WinCertPkcs1(fs)
        else:
            return None
