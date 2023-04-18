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
import sys

from warnings import warn

from edk2toollib.utility_functions import hexdump

from pyasn1.codec.der.decoder import decode as der_decode
from pyasn1_modules import rfc2315


class WinCertPkcs1(object):
    """Object representing a WinCertPkcs1 struct.

    Certificate which encapsulates the RSASSA_PKCS1-v1_5 digital signature.

    Attributes:
        Hdr_dwLength (int):         The length of the entire certificate, including the length of the header, in bytes.
        Hdr_wRevision (int):        The certificate type. See WIN_CERT_TYPE_xxx for the UEFI certificate types. The UEFI
                                    specification reserves the range of certificate type values from 0x0EF0 to 0x0EFF.
        Hdr_wCertificateType (int): The following is the actual certificate. The format of the certificate depends on
                                    wCertificateType.
        hash_algorithm (uuid.UUID):  The Guid representing the hash algorithm for the Cert.
        cert_data (memoryview):      The actual Cert.

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
        if filestream is None:
            self.Hdr_dwLength = WinCertPkcs1.STATIC_STRUCT_SIZE
            self.Hdr_wRevision = WinCert.REVISION
            self.Hdr_wCertificateType = WinCert.WIN_CERT_TYPE_EFI_PKCS115
            self.hash_algorithm = None
            self.cert_data = None
        else:
            self.decode(filestream)

    def add_cert_data(self, fs):
        """Adds the Cert Data to the struct.

        Args:
            fs (io.BytesIO): filestream representing bytes

        Raises:
            (ValueError): Invalid Cert Data
            (ValueError): Missing Hash Algorithm
        """
        if self.cert_data is not None:
            raise ValueError("Certificate data already set")

        if self.hash_algorithm is None:
            raise ValueError("You must set the Hash Algorithm first")

        self.cert_data = memoryview(fs.read())
        self.Hdr_dwLength = self.Hdr_dwLength + len(self.cert_data)

    def AddCertData(self, fs):
        """Adds the Cert Data to the struct.

        Raises:
            (ValueError): Invalid Cert Data
            (ValueError): Missing Hash Algorithm
        """
        warn("AddCertData is deprecated, use add_cert_data instead", DeprecationWarning, 2)
        self.add_cert_data(fs)

    def set_hash_algorithm(self, hash_algorithm: uuid.UUID):
        """Sets the hash algoritm for the wincert
        
        Args:
            hash_algorithm (uuid.UUID): The Guid representing the hash algorithm for the Cert.
        """
        self.hash_algorithm = hash_algorithm

    def decode(self, fs):
        """Populates the struct from a filestream.

        Args:
            fs (obj): An open file

        Raises:
            (ValueError): Invalid stream
            (ValueError): Invalid stream size
        """
        if (fs is None):
            raise ValueError("Invalid File stream")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if ((end - offset) < WinCertPkcs1.STATIC_STRUCT_SIZE):  # size of the static header data
            raise ValueError("Invalid file stream size")

        self.Hdr_dwLength = struct.unpack("=I", fs.read(4))[0]
        self.Hdr_wRevision = struct.unpack("=H", fs.read(2))[0]
        self.Hdr_wCertificateType = struct.unpack("=H", fs.read(2))[0]
        self.hash_algorithm = uuid.UUID(bytes_le=fs.read(16))
        self.cert_data = None

        if ((end - fs.tell()) < 1):
            raise ValueError("Invalid File stream. No data for signature cert data")

        if ((end - fs.tell()) < (self.Hdr_dwLength - WinCertPkcs1.STATIC_STRUCT_SIZE)):
            raise ValueError("Invalid file stream size")

        self.cert_data = memoryview(fs.read(self.Hdr_dwLength - WinCertPkcs1.STATIC_STRUCT_SIZE))

    def PopulateFromFileStream(self, fs):
        """Populates the struct from a filestream.

        Args:
            fs (obj): an open file

        Raises:
            (ValueError): Invalid stream
            (ValueError): Invalid stream size
        """
        warn("PopulateFromFileStream is deprecated, use decode instead", DeprecationWarning, 2)
        return self.decode(fs)

    def print(self, out_fs=sys.stdout):
        """Prints the struct to the console."""
        out_fs.write("\n-------------------- WinCertPKCS115 ---------------------\n")
        out_fs.write(f"  Hdr_dwLength:         0x{self.Hdr_dwLength:0X}\n")
        out_fs.write(f"  Hdr_wRevision:        0x{self.Hdr_wRevision:0X}\n")
        out_fs.write(f"  Hdr_wCertificateType: 0x{self.Hdr_wCertificateType:0X}\n")
        out_fs.write(f"  Hash Guid:            {str(self.hash_algorithm)}\n")
        out_fs.write("  cert_data:             \n")
        cdl = self.cert_data.tolist()
        hexdump(cdl, out_fs=out_fs)

    def Print(self, out_fs=sys.stdout):
        """Prints the struct to the console."""
        warn("Print is deprecated, use print instead", DeprecationWarning, 2)
        self.print(out_fs)

    def encode(self):
        r"""Serializes the object.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """
        output = b""
        
        output += struct.pack("=I", self.Hdr_dwLength)
        output += struct.pack("=H", self.Hdr_wRevision)
        output += struct.pack("=H", self.Hdr_wCertificateType)
        output += self.hash_algorithm.bytes_le
        output += self.cert_data

        return output
    
    def write(self, fs):
        """Writes an serialized object to a filestream

            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')

        """
        fs.write(self.encode())

    def Write(self, fs):
        r"""Serializes the object.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')
        """    
        warn("Write is deprecated, use encode instead", DeprecationWarning, 2)
        self.write(fs)


class WinCertUefiGuid(object):
    """Object representing a Certificate which encapsulates a GUID-specific digital signature.

    Attributes:
        Hdr_dwLength (int):         The length of the entire certificate, including the length of the header, in bytes.
        Hdr_wRevision (int):        The certificate type. See WIN_CERT_TYPE_xxx for the UEFI certificate types. The UEFI
                                    specification reserves the range of certificate type values from 0x0EF0 to 0x0EFF.
        Hdr_wCertificateType (int): The following is the actual certificate. The format of the certificate depends on
                                    wCertificateType.
        cert_data (memoryview):      The actual Cert.

    typedef struct {
        WIN_CERTIFICATE   Hdr;
        EFI_GUID          cert_type;
        UINT8            cert_data[1];
    } WIN_CERTIFICATE_UEFI_GUID;

    The WIN_CERTIFICATE structure is part of the PE/COFF specification.
    typedef struct {
        UINT32  dwLength;
        UINT16  wRevision;
        UINT16  wCertificateType;
        UINT8 bCertificate[ANYSIZE_ARRAY];
    } WIN_CERTIFICATE;
    """

    _StructFormat = '<L2H16s'
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
        self.cert_type = self._EFI_CERT_TYPE_PKCS7_GUID
        self.cert_data = b''

        if in_data is not None:
            self.decode(in_data)

    def get_length(self):
        """returns the length of the WinCertUefiGuid and it's data"""
        return self.Hdr_dwLength

    def Encode(self):
        r"""Serializes the object.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')

        Raises:
            (ValueError): Invalid Revision
            (ValueError): Invalid Cert Type
        """
        warn("Encode is deprecated, use encode instead", DeprecationWarning, 2)
        return self.encode()
   
    def encode(self):
        r"""Serializes the object.

        Returns:
            (str): string representing packed data as bytes (i.e. b'\x01\x00\x03')

        Raises:
            (ValueError): Invalid Revision
            (ValueError): Invalid Cert Type
        """
        if self.Hdr_wRevision != WinCert.REVISION:
            raise ValueError("Invalid revision")
        if self.Hdr_wCertificateType != WinCert.WIN_CERT_TYPE_EFI_GUID:
            raise ValueError("Invalid win_certificate type (WIN_CERT_TYPE_EFI_GUID)")
        if self.cert_type != self._EFI_CERT_TYPE_PKCS7_GUID:
            raise ValueError("Invalid certificate type (EFI_CERT_TYPE_PKCS7_GUID)")
        self.Hdr_dwLength = self._StructSize + len(self.cert_data)

        win_cert_header = struct.pack(
            self._StructFormat,
            self.Hdr_dwLength,
            self.Hdr_wRevision,
            self.Hdr_wCertificateType,
            self.cert_type.bytes_le
        )

        return win_cert_header + self.cert_data

    def Decode(self, Buffer):
        """Loads the struct with values from a buffer.

        Args:
            Buffer (filestream | bytes): Buffer containing serialized data

        Returns:
            (obj): Any remaining buffer

        Raises:
            (ValueError): Invalid Buffer
            (ValueError): Invalid dwlength
            (ValueError): Invalid Revision
            (ValueError): Invalid Cert Type
        """
        warn("Decode is deprecated, use decode instead", DeprecationWarning, 2)
        return self.decode(Buffer)
    
    def decode(self, in_data):
        """Loads the struct with values from a buffer.

        Args:
            Buffer (filestream | bytes): Buffer containing serialized data

        Returns:
            (obj): Any remaining buffer

        Raises:
            (ValueError): Invalid buffer
            (ValueError): Invalid dwLength
            (ValueError): Invalid Revision
            (ValueError): Invalid Cert Type
            (ValueError): Invalid datatype provided

        """
        if hasattr(in_data, 'seek'):  # Filestream like object
            return self._from_filestream(in_data)
        elif hasattr(in_data, 'decode'):  # Bytes like object
            return self._from_buffer(in_data)
        else:
            raise ValueError(f"Invalid datatype provided: {type(in_data)}, data may only be of type filestream or bytes")

    def _from_buffer(self, buffer):
        """Loads the struct with values from a buffer.

        Args:
            Buffer (obj): Buffer containing serialized data

        Returns:
            (obj): Any remaining buffer

        Raises:
            (ValueError): Invalid buffer
            (ValueError): Invalid dwLength
            (ValueError): Invalid Revision
            (ValueError): Invalid Cert Type
        """
        if len(buffer) < self._StructSize:
            raise ValueError
        (dwLength, wRevision, wCertificateType, cert_type) = struct.unpack(
            self._StructFormat,
            buffer[0:self._StructSize]
        )
        if dwLength < self._StructSize:
            raise ValueError
        if wRevision != WinCert.REVISION:
            raise ValueError
        if wCertificateType != WinCert.WIN_CERT_TYPE_EFI_GUID:
            raise ValueError
        if cert_type != self._EFI_CERT_TYPE_PKCS7_GUID.bytes_le:
            raise ValueError
        self.Hdr_dwLength = dwLength
        self.Hdr_wRevision = wRevision
        self.Hdr_wCertificateType = wCertificateType
        self.cert_type = uuid.UUID(bytes_le=cert_type)
        self.cert_data = buffer[self._StructSize:self.Hdr_dwLength]

        # Return the remaining buffer, if any exists.
        return buffer[self.Hdr_dwLength:]

    def _from_filestream(self, fs):
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

        return self._from_buffer(object_buffer)
    
    def AddCertData(self, in_data):
        """Adds the Cert Data to the struct.

        Args:
            in_data (obj): Data to read.
        """
        warn("AddCertData is deprecated, use add_cert_data instead", DeprecationWarning, 2)
        return self.add_cert_data(in_data)

    def add_cert_data(self, in_data):
        """Adds the Cert Data to the struct.

        Args:
            in_data (obj): Data to read.
        """

        # if the data is already set, let's subtract it from the length before adding the new data
        if self.cert_data is not None:
            self.Hdr_dwLength -= len(self.cert_data)

        # Account for back compat. Behave differently for file streams.
        if hasattr(in_data, 'seek'):
            self.cert_data = in_data.read()
        elif hasattr(in_data, 'decode'):
            self.cert_data = in_data
        else:
            raise ValueError(f"Invalid datatype provided: {type(in_data)}, data may only be of type filestream or bytes")

        self.Hdr_dwLength = self.Hdr_dwLength + len(self.cert_data)

    def PopulateFromFileStream(self, fs):
        """Un-serialized from a filestream.

        Args:
            fs (obj): Already opened file

        Raises:
            (ValueError): Invalid fs
            (ValueError): Invalid size
        """
        warn("PopulateFromFileStream is deprecated, use decode instead", DeprecationWarning, 2)
        return self.decode(fs)

    def get_certificate(self):
        """Returns certificate data, if certificate data exists."""
        return self.cert_data

    def GetCertificate(self):
        """Returns certificate data, if certificate data exists."""
        warn("GetCertificate is deprecated, use get_certificate instead", DeprecationWarning, 2)
        return self.get_certificate()

    def print(self, outfs=sys.stdout):
        """Prints struct to console."""
        self.dump_info(outfs)

    def Print(self, outfs=sys.stdout):
        """Prints struct to console."""
        warn("Print() is deprecated, use print() instead.", DeprecationWarning, 2)
        self.dump_info(outfs)

    def dump_info(self, outfs=sys.stdout):
        """Prints struct to a file stream."""
        outfs.write("\n-------------------- WIN_CERTIFICATE ---------------------\n")
        outfs.write(f"WIN_CERTIFICATE.dwLength         = {self.Hdr_dwLength:08X}\n")
        outfs.write(f"WIN_CERTIFICATE.wRevision        = {self.Hdr_wRevision:04X}\n")
        outfs.write(f"WIN_CERTIFICATE.wCertificateType = {self.Hdr_wCertificateType:04X}\n")
        outfs.write(f"WIN_CERTIFICATE_UEFI_GUID.cert_type             = {str(self.cert_type).upper()}\n")
        outfs.write(f"sizeof (WIN_CERTIFICATE_UEFI_GUID.cert_data)    = {len(self.cert_data):08X}\n")

        outfs.write("\n------------------- CERTIFICATE DATA ---------------------\n")
        
        # Technically the signature could be wrapped in a ContentInfo
        
        try:
            content_info, _ = der_decode(self.cert_data, asn1Spec=rfc2315.ContentInfo())

            outfs.write(str(content_info))
        except Exception:
            # But usually its not
            try:
                signed_data, _ = der_decode(self.cert_data, asn1Spec=rfc2315.SignedData())

                outfs.write(str(signed_data))
            except Exception as exc:
                raise ValueError("Unable to decode cert_data") from exc

    def DumpInfo(self, outfs=sys.stdout):
        """Prints struct to a file stream."""
        warn("DumpInfo is deprecated, use dump_info instead", DeprecationWarning, 2)
        self.dump_info(outfs)

    def write(self, fs):
        """Writes the struct to a filestream."""
        fs.write(self.encode())

    def Write(self, fs):
        """Writes the struct to a filestream."""
        warn("Write is deprecated, use write instead", DeprecationWarning, 2)
        fs.write(self.encode())

    def __str__(self):
        """Returns the object as a string"""
        string_repr = ""
        with io.StringIO() as f:
            self.print(f)
            f.seek(0)
            string_repr = f.read()

        return string_repr



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

    @staticmethod
    def factory(fs):
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
        warn("Factory is deprecated, use factory instead", DeprecationWarning, 2)
        return WinCert.factory(fs)