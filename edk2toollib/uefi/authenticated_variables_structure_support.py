##
# UEFI Authenticated Variable Structure Support Library
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module containing Authenticated Variable Structure definitions based on UEFI specification (2.7).

Each object can be created and or populated from a file stream.
Each object can be written to a filesteam as binary and printed to the console in text.
"""
import logging
import datetime
import struct
import hashlib
import uuid
import io
import sys

from typing import BinaryIO, List
from operator import attrgetter

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import pkcs7, Encoding
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.x509.base import Certificate

from pyasn1.codec.der.decoder import decode as der_decode
from pyasn1.codec.der.encoder import encode as der_encode
from pyasn1_modules import rfc2315

from edk2toollib.uefi.wincert import WinCert, WinCertUefiGuid
from edk2toollib.utility_functions import PrintByteList
from edk2toollib.uefi.uefi_multi_phase import EfiVariableAttributes


# spell-checker: ignore decodefs, createfs, deduplicated, deduplication

# UEFI global Variable Namespace
EfiGlobalVarNamespaceUuid = uuid.UUID('8BE4DF61-93CA-11d2-AA0D-00E098032B8C')
Sha256Oid = [0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01]


class EfiSignatureDataEfiCertX509(object):
    """An object representing a EFI_SIGNATURE_DATA Structure for X509 Certs."""
    STATIC_STRUCT_SIZE = 16
    FIXED_SIZE = False

    def __init__(self,
                 decodefs: BinaryIO = None,
                 decodesize=0,
                 createfs: BinaryIO = None,
                 cert: bytes = None,
                 sigowner: uuid.UUID = None):
        """Inits the object.

        Args:
            decodefs (BinaryIO): a filestream object of binary content that is the structure encoded
            decodesize (int):number of bytes to decode as the EFI_SIGNATURE_DATA object (guid + x509 data)
            createfs (BinaryIO): a filestream object that is the DER encoded x509 cert
            cert (bytes): the x509 certificate to initialize this object
            sigowner (uuid.UUID): the uuid object of the signature owner guid

        Raises:
            (Exception): Invalid FileStream size
            (Exception): Invalid Parameters
        """
        if (decodefs is not None):
            self.PopulateFromFileStream(decodefs, decodesize)
        elif (createfs is not None):
            # create a new one
            self.SignatureOwner = sigowner
            # should be 0 but maybe this filestream has other things at the head
            start = createfs.tell()
            createfs.seek(0, 2)
            end = createfs.tell()
            createfs.seek(start)
            self.SignatureDataSize = end - start
            if (self.SignatureDataSize < 0):
                raise Exception("Create File Stream has invalid size")
            self.SignatureData = (createfs.read(self.SignatureDataSize))
        elif (cert is not None):
            self.SignatureOwner = sigowner
            self.SignatureDataSize = len(cert)
            self.SignatureData = cert

        else:
            raise Exception("Invalid Parameters - Not Supported")

    def __lt__(self, other):
        """Less-than comparison for sorting. Looks at SignatureData only, not SignatureOwner."""
        return self.SignatureData < other.SignatureData

    def PopulateFromFileStream(self, fs: BinaryIO, decodesize):
        """Loads an object from a filestream.

        Args:
            fs (BinaryIO): filestream
            decodesize (int): amount to decode.

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid Decode Size
        """
        if (fs is None):
            raise Exception("Invalid File Steam")

        if (decodesize == 0):
            raise Exception("Invalid Decode Size")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if ((end - offset) < EfiSignatureDataEfiCertX509.STATIC_STRUCT_SIZE):  # size of the  guid
            raise Exception("Invalid file stream size")

        if ((end - offset) < decodesize):  # size requested is too big
            raise Exception("Invalid file stream size vs decodesize")

        self.SignatureOwner = uuid.UUID(bytes_le=fs.read(16))

        # read remaining decode size for x509 data
        self.SignatureDataSize = decodesize - \
            EfiSignatureDataEfiCertX509.STATIC_STRUCT_SIZE
        self.SignatureData = fs.read(self.SignatureDataSize)

    def Print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        if not compact:
            outfs.write("EfiSignatureData - EfiSignatureDataEfiCertX509\n")
            outfs.write(f"  Signature Owner:      {str(self.SignatureOwner)}\n")
            outfs.write("  Signature Data: \n")
            if (self.SignatureData is None):
                outfs.write("    NONE\n")
            else:
                sdl = self.SignatureData
                if (self.SignatureDataSize != len(sdl)):
                    raise Exception(
                        "Invalid Signature Data Size vs Length of data")
                PrintByteList(sdl)
        else:
            s = "ESD:EFI_CERT_X509,"
            s += f"{str(self.SignatureOwner)},"
            if (self.SignatureData is None):
                s += 'NONE'
            else:
                sdl = self.SignatureData
                for index in range(len(sdl)):
                    s += f'{sdl[index]:02X}'
            outfs.write(s)
            outfs.write("\n")

    def Write(self, fs):
        """Write the object to the filestream.

        Args:
            fs (BinaryIO): filestream

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid object
        """
        if (fs is None):
            raise Exception("Invalid File Output Stream")
        if (self.SignatureData is None):
            raise Exception("Invalid object")

        fs.write(self.SignatureOwner.bytes_le)
        fs.write(self.SignatureData)

    def GetBytes(self) -> bytes:
        """Return bytes array produced by Write()."""
        with io.BytesIO() as fs:
            self.Write(fs)
            return fs.getvalue()

    def GetTotalSize(self):
        """Returns the total size of the object."""
        return EfiSignatureDataEfiCertX509.STATIC_STRUCT_SIZE + self.SignatureDataSize


class EfiSignatureDataEfiCertSha256(object):
    """An object representing a EFI_SIGNATURE_DATA Structure for Sha256 Certs."""
    STATIC_STRUCT_SIZE = 16 + hashlib.sha256().digest_size  # has guid and array
    FIXED_SIZE = True

    def __init__(self,
                 decodefs: BinaryIO = None,
                 createfs: BinaryIO = None,
                 digest: bytes = None,
                 sigowner: uuid = None):
        """Inits the object.

        Args:
            decodefs (BinaryIO): a filestream object of binary content that is the structure encoded
            createfs (BinaryIO): a filestream object that is the DER encoded x509 cert
            digest (bytes): a bytes object that contains the hash value for new signature data
            sigowner (uuid.UUID): the uuid object of the signature owner guid

        Raises:
            (Exception): Invalid FileStream size
            (Exception): Invalid Parameters
        """
        if (decodefs is not None):
            self.PopulateFromFileStream(decodefs)
        elif (createfs is not None):
            # create a new one
            self.SignatureOwner = sigowner
            self.SignatureData = (hashlib.sha256(createfs.read()).digest())
        elif (digest is not None):
            digest_length = len(digest)
            if (digest_length != hashlib.sha256().digest_size):
                raise Exception("Invalid digest length (found / expected): (%d / %d)",
                                digest_length, hashlib.sha256().digest_size)
            self.SignatureOwner = sigowner
            self.SignatureData = digest
        else:
            raise Exception("Invalid Parameters - Not Supported")

    def PopulateFromFileStream(self, fs):
        """Loads an object from a filestream.

        Args:
            fs (BinaryIO): filestream

        Raises:
            (Exception): Invalid filestream
        """
        if (fs is None):
            raise Exception("Invalid File Steam")

        # only populate from file stream those parts that are complete in the file stream
        offset = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(offset)

        if ((end - offset) < EfiSignatureDataEfiCertSha256.STATIC_STRUCT_SIZE):  # size of the  data
            raise Exception("Invalid file stream size")

        self.SignatureOwner = uuid.UUID(bytes_le=fs.read(16))

        self.SignatureData = fs.read(hashlib.sha256().digest_size)

    def Print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        if not compact:
            outfs.write("EfiSignatureData - EfiSignatureDataEfiCertSha256\n")
            outfs.write(f"  Signature Owner:      {str(self.SignatureOwner)}\n")
            outfs.write("  Signature Data: ")
            if (self.SignatureData is None):
                outfs.write(" NONE\n")
            else:
                sdl = self.SignatureData
                for index in range(len(sdl)):
                    outfs.write(f"{sdl[index]:02X}")
                outfs.write("\n")
        else:
            s = 'ESD:EFI_CERT_SHA256,'
            s += f"{str(self.SignatureOwner)},"
            if (self.SignatureData is None):
                s += 'NONE'
            else:
                sdl = self.SignatureData
                for index in range(len(sdl)):
                    s += f"{sdl[index]:02X}"
            outfs.write(s)
            outfs.write("\n")

    def Write(self, fs):
        """Write the object to the filestream.

        Args:
            fs (BinaryIO): filestream

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid object
        """
        if (fs is None):
            raise Exception("Invalid File Output Stream")
        if (self.SignatureData is None):
            raise Exception("Invalid object")

        fs.write(self.SignatureOwner.bytes_le)
        fs.write(self.SignatureData)

    def GetBytes(self) -> bytes:
        """Return bytes array produced by Write()."""
        with io.BytesIO() as fs:
            self.Write(fs)
            return fs.getvalue()

    def GetTotalSize(self):
        """Returns the total size of the object."""
        return EfiSignatureDataEfiCertSha256.STATIC_STRUCT_SIZE


class EfiSignatureHeader(object):  # noqa
    def __init__(self, fs, header_size):  # noqa
        raise Exception("Not Implemented")


class EfiSignatureDataFactory(object):
    """Factory class for generating an EFI Signature struct."""
    EFI_CERT_SHA256_GUID = uuid.UUID('c1c41626-504c-4092-aca9-41f936934328')
    # EFI_CERT_RSA2048_GUID = uuid.UUID("0x3c5766e8, 0x269c, 0x4e34, 0xaa, 0x14, 0xed, 0x77, 0x6e, 0x85, 0xb3, 0xb6")
    # EFI_CERT_RSA2048_SHA256_GUID = uuid.UUID("0xe2b36190, 0x879b, 0x4a3d, 0xad, 0x8d, 0xf2, 0xe7, 0xbb, 0xa3, 0x27, 0x84")  # noqa: E501
    # EFI_CERT_SHA1_GUID = uuid.UUID("0x826ca512, 0xcf10, 0x4ac9, 0xb1, 0x87, 0xbe, 0x1, 0x49, 0x66, 0x31, 0xbd")
    # EFI_CERT_RSA2048_SHA1_GUID = uuid.UUID("0x67f8444f, 0x8743, 0x48f1, 0xa3, 0x28, 0x1e, 0xaa, 0xb8, 0x73, 0x60, 0x80")    # noqa: E501
    EFI_CERT_X509_GUID = uuid.UUID("a5c059a1-94e4-4aa7-87b5-ab155c2bf072")
    # EFI_CERT_SHA224_GUID = uuid.UUID("0xb6e5233, 0xa65c, 0x44c9, 0x94, 0x7, 0xd9, 0xab, 0x83, 0xbf, 0xc8, 0xbd")
    # EFI_CERT_SHA384_GUID = uuid.UUID("0xff3e5307, 0x9fd0, 0x48c9, 0x85, 0xf1, 0x8a, 0xd5, 0x6c, 0x70, 0x1e, 0x1")
    # EFI_CERT_SHA512_GUID = uuid.UUID("0x93e0fae, 0xa6c4, 0x4f50, 0x9f, 0x1b, 0xd4, 0x1e, 0x2b, 0x89, 0xc1, 0x9a")
    EFI_CERT_X509_SHA256_GUID = uuid.UUID(
        "3bd2a492-96c0-4079-b420-fcf98ef103ed")
    # EFI_CERT_X509_SHA384_GUID = uuid.UUID("0x7076876e, 0x80c2, 0x4ee6, 0xaa, 0xd2, 0x28, 0xb3, 0x49, 0xa6, 0x86, 0x5b")     # noqa: E501
    # EFI_CERT_X509_SHA512_GUID = uuid.UUID("0x446dbf63, 0x2502, 0x4cda, 0xbc, 0xfa, 0x24, 0x65, 0xd2, 0xb0, 0xfe, 0x9d")     # noqa: E501
    # EFI_CERT_TYPE_PKCS7_GUID = uuid.UUID("0x4aafd29d, 0x68df, 0x49ee, 0x8a, 0xa9, 0x34, 0x7d, 0x37, 0x56, 0x65, 0xa7")

    @staticmethod
    def Factory(fs: BinaryIO, type, size):
        """This method is a factory for creating the correct Efi Signature Data object from the filestream.

        Uses a Filestream of an existing auth payload.

        Args:
            fs (BinaryIO): filestream to read
            type (uuid.UUID): Guid of the type
            size (int): decodesize for x509, struct size for Sha256
        """
        if (fs is None):
            raise Exception("Invalid File stream")

        if (type == EfiSignatureDataFactory.EFI_CERT_SHA256_GUID):
            if (size != EfiSignatureDataEfiCertSha256.STATIC_STRUCT_SIZE):
                raise Exception("Invalid Size 0x%x" % size)
            return EfiSignatureDataEfiCertSha256(decodefs=fs)

        elif (type == EfiSignatureDataFactory.EFI_CERT_X509_GUID):
            return EfiSignatureDataEfiCertX509(decodefs=fs, decodesize=size)

        else:
            logging.error("GuidType Value: %s" % type)
            raise Exception("Not Supported")
            return None

    @staticmethod
    def Create(type, ContentFileStream, sigowner):
        """Create a new EFI Sginature Data Object.

        Args:
            type (uuid.UUID): Guid of the type
            ContentFileStream (BinaryIO): filestream to read
            sigowner (uuid.UUID): the uuid object of the signature owner guid
        """
        if (ContentFileStream is None):
            raise Exception("Invalid Content File Stream")

        if (type == EfiSignatureDataFactory.EFI_CERT_SHA256_GUID):
            return EfiSignatureDataEfiCertSha256(createfs=ContentFileStream, sigowner=sigowner)
        elif (type == EfiSignatureDataFactory.EFI_CERT_X509_GUID):
            return EfiSignatureDataEfiCertX509(createfs=ContentFileStream, sigowner=sigowner)
        else:
            raise Exception("Not Supported")


class EfiSignatureList(object):
    """An object representing a EFI_SIGNATURE_LIST."""
    STATIC_STRUCT_SIZE = 16 + 4 + 4 + 4

    def __init__(self, filestream: BinaryIO = None, typeguid: uuid.UUID = None):
        """Inits the object.

        Args:
            filestream (:obj:`BinaryIO`, optional): a filestream object of binary content that is the structure encoded
            typeguid (:obj:`uuid.UUID`, optional): type guid
        """
        if (filestream is None):

            # Type of the signature. GUID signature types are defined in below.
            self.SignatureType = typeguid

            # Total size of the signature list, including this header.
            self.SignatureListSize = EfiSignatureList.STATIC_STRUCT_SIZE

            # Size of the signature header which precedes the array of signatures.
            self.SignatureHeaderSize = -1

            # Size of each signature.
            self.SignatureSize = 0

            # Header before the array of signatures. The format of this header is specified by the SignatureType.
            self.SignatureHeader = None

            # An array of signatures. Each signature is SignatureSize bytes in length.
            self.SignatureData_List = None

        else:
            self.PopulateFromFileStream(filestream)

    def PopulateFromFileStream(self, fs: BinaryIO):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid filestream size
            (Exception): Invalid siglist
            (Exception): Invalid parsing
        """
        if (fs is None):
            raise Exception("Invalid File Steam")

        # only populate from file stream those parts that are complete in the file stream
        start = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(start)

        if ((end - start) < EfiSignatureList.STATIC_STRUCT_SIZE):  # size of the static header data
            raise Exception("Invalid file stream size")

        self.SignatureType = uuid.UUID(bytes_le=fs.read(16))
        self.SignatureListSize = struct.unpack("<I", fs.read(4))[0]
        self.SignatureHeaderSize = struct.unpack("<I", fs.read(4))[0]
        self.SignatureSize = struct.unpack("<I", fs.read(4))[0]

        # check the total size of this is within the File
        if ((end - start) < self.SignatureListSize):
            logging.debug(f"SignatureListSize {self.SignatureListSize:0x}")
            logging.debug(f"End - Start is {(end - start):0x}")
            raise Exception(
                "Invalid File Stream.  Not enough file content to cover the Sig List Size")

        # check that structure is built correctly and there is room within the structure total size to read the header
        if ((self.SignatureListSize - (fs.tell() - start)) < self.SignatureHeaderSize):
            raise Exception("Invalid Sig List.  Sizes not correct.  "
                            "SignatureHeaderSize extends beyond end of structure")

        # Signature Header is allowed to be nothing (size 0)
        self.SignatureHeader = None
        if (self.SignatureHeaderSize > 0):
            self.SignatureHeader = EfiSignatureHeader(
                fs, self.SignatureHeaderSize)

        if (((self.SignatureListSize - (fs.tell() - start)) % self.SignatureSize) != 0):
            raise Exception(
                "Invalid Sig List.  Signature Data Array is not a valid size")

        self.SignatureData_List = []
        while ((start + self.SignatureListSize) > fs.tell()):
            # double check that everything is adding up correctly.
            if ((start + self.SignatureListSize - fs.tell() - self.SignatureSize) < 0):
                raise Exception(
                    "Invalid Signature List Processing.  Signature Data not correctly parsed!!")
            a = EfiSignatureDataFactory.Factory(
                fs, self.SignatureType, self.SignatureSize)
            self.SignatureData_List.append(a)

    def Print(self, compact: bool = False, outfs=sys.stdout):
        """Prints to the console."""
        if not compact:
            outfs.write("EfiSignatureList\n")
            outfs.write(f"  Signature Type:        {str(self.SignatureType)}\n")
            outfs.write(f"  Signature List Size:   {self.SignatureListSize:0x}\n")
            outfs.write(f"  Signature Header Size: {self.SignatureHeaderSize:0x}\n")
            outfs.write(f"  Signature Size:       {self.SignatureSize:0x}\n")
            if (self.SignatureHeader is not None):
                self.SignatureHeader.Print(compact=compact)
            else:
                outfs.write("  Signature Header:      NONE\n")
        else:
            csv = "ESL:"
            csv += f"{str(self.SignatureType)}"
            csv += f",{self.SignatureListSize:0x}"
            csv += f",{self.SignatureHeaderSize:0x}"
            csv += f",{self.SignatureSize:0x}"
            if (self.SignatureHeader is not None):
                csv += self.SignatureHeader.Print(compact=compact)
            else:
                csv += ",NONE"
            outfs.write(csv)
            outfs.write('\n')

        if (self.SignatureData_List is not None):
            for a in self.SignatureData_List:
                a.Print(compact=compact)

    def Write(self, fs):
        """Serializes the object and writes it to a filestream.

        Raises:
            (Exception): Invalid filestream
            (Exception): Uninitialized Sig header
        """
        if (fs is None):
            raise Exception("Invalid File Output Stream")
        if ((self.SignatureHeader is None) and (self.SignatureHeaderSize == -1)):
            raise Exception("Invalid object.  Uninitialized Sig Header")

        fs.write(self.SignatureType.bytes_le)
        fs.write(struct.pack("<I", self.SignatureListSize))
        fs.write(struct.pack("<I", self.SignatureHeaderSize))
        fs.write(struct.pack("<I", self.SignatureSize))
        if (self.SignatureHeader is not None):
            self.SignatureHeader.Write(fs)

        if (self.SignatureData_List is not None):
            for a in self.SignatureData_List:
                a.Write(fs)

    def GetBytes(self) -> bytes:
        """Return bytes array produced by Write()."""
        with io.BytesIO() as fs:
            self.Write(fs)
            return fs.getvalue()

    def AddSignatureHeader(self, SigHeader, SigSize=0):
        """Adds the Signature Header.

        Raises:
            (Exception): Signature header already set
        """
        if (self.SignatureHeader is not None):
            raise Exception("Signature Header already set")

        if (self.SignatureHeaderSize != -1):
            raise Exception("Signature Header already set (size)")

        if (self.SignatureSize != 0):
            raise Exception("Signature Size already set")

        if (self.SignatureData_List is not None):
            raise Exception("Signature Data List is already initialized")

        self.SignatureHeader = SigHeader
        if (SigHeader is None):
            self.SignatureHeaderSize = 0
            self.SignatureSize = SigSize
        else:
            self.SignatureHeaderSize = SigHeader.GetTotalSize()
            self.SignatureSize = SigHeader.GetSizeOfSignatureDataEntry()
            self.SignatureListSize += self.SignatureHeaderSize

    def AddSignatureData(self, SigDataObject):
        """Adds the Signature Data.

        Raises:
            (Exception): Signature size does not match Sig Data Object size
        """
        if (self.SignatureSize == 0):
            raise Exception(
                "Before adding Signature Data you must have set the Signature Size")

        if (self.SignatureSize != SigDataObject.GetTotalSize()):
            raise Exception("Can't add Signature Data of different size")

        if (self.SignatureData_List is None):
            self.SignatureData_List = []

        self.SignatureData_List.append(SigDataObject)
        self.SignatureListSize += self.SignatureSize

    def MergeSignatureList(self, esl):
        """Add the EfiSignatureData entries within the supplied EfiSignatureList to the current object.

        No sorting or deduplication is performed, the EfiSignatureData elements are simply appended
        """
        if not isinstance(esl, EfiSignatureList):
            raise Exception(
                "Parameter 1 'esl' must be of type EfiSignatureList")

        if (self.SignatureType != esl.SignatureType):
            raise Exception("Signature Types must match")

        if (self.SignatureHeaderSize > 0
           or esl.SignatureHeaderSize > 0):
            raise Exception("Merge does not support Signature Headers")
        self.SignatureHeaderSize = 0

        if (esl.SignatureListSize == EfiSignatureList.STATIC_STRUCT_SIZE):
            # supplied EfiSignatureList is empty, return
            return

        FixedSizeData = esl.SignatureData_List[0].FIXED_SIZE
        if not FixedSizeData:
            raise Exception(
                "Can only merge EfiSignatureLists with fixed-size data elements")

        if (self.SignatureData_List is None):
            self.SignatureData_List = []
            self.SignatureSize = esl.SignatureSize

        self.SignatureData_List += esl.SignatureData_List
        self.SignatureListSize += esl.SignatureListSize - \
            EfiSignatureList.STATIC_STRUCT_SIZE

    def SortBySignatureDataValue(self, deduplicate: bool = True):
        """Sort self's SignatureData_List by SignatureData values (ignores SigOwner) & optionally deduplicate.

        When deduplicate is true, remove duplicate SignatureData values from self and return them in an
        EfiSignatureList.  This EfiSignatureList of duplicates is itself not deduplicated.

        When deduplicate is false, returns an empty EfiSignatureList (has 0 Data elements)
        """
        # initialize the duplicate list, an EFI_SIGNATURE_LIST with no signature data entries
        dupes = EfiSignatureList(typeguid=self.SignatureType)
        dupes.SignatureListSize = EfiSignatureList.STATIC_STRUCT_SIZE
        dupes.SignatureHeaderSize = self.SignatureHeaderSize
        dupes.SignatureHeader = self.SignatureHeader
        dupes.SignatureSize = 0
        dupes.SignatureData_List = []

        # if nothing to sort, return the empty dupe list
        if (self.SignatureData_List is None
           or len(self.SignatureData_List) == 1):
            return dupes

        self.SignatureData_List.sort(key=attrgetter('SignatureData'))

        if (deduplicate is False):
            return dupes  # return empty dupe list without performing deduplicate

        # perform deduplicate on self
        last = len(self.SignatureData_List) - 1  # index of the last item
        for i in range(last - 1, -1, -1):
            if self.SignatureData_List[last].SignatureData == self.SignatureData_List[i].SignatureData:
                dupes.SignatureData_List.insert(
                    0, self.SignatureData_List[last])
                dupes.SignatureListSize += self.SignatureSize
                del self.SignatureData_List[last]
                self.SignatureListSize -= self.SignatureSize
                last = i
            else:
                last = i

        # only initialize dupes.SignatureSize if duplicate elements are present
        if (len(dupes.SignatureData_List) > 0):
            dupes.SignatureSize = self.SignatureSize

        return dupes


class EfiSignatureDatabase(object):
    """Concatenation of EFI_SIGNATURE_LISTs, as is returned from UEFI GetVariable() on PK, KEK, db, & dbx.

    Useful for parsing and building the contents of the Secure Boot variables
    """

    def __init__(self, filestream: BinaryIO = None, EslList: List[EfiSignatureList] = None):
        """Inits an Efi Signature Database object.

        Args:
            filestream (:obj:`BinaryIO`, optional): Inits the object with this stream
            EslList (:obj:`list[EfiSignatureList]`, optional): Inits the object with this list
        """
        if filestream:
            self.EslList = []
            self.PopulateFromFileStream(filestream)
        else:
            self.EslList = [] if EslList is None else EslList

    def PopulateFromFileStream(self, fs: BinaryIO):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid filestream size
        """
        if (fs is None):
            raise Exception("Invalid File Stream")
        self.EslList = []
        begin = fs.tell()
        fs.seek(0, io.SEEK_END)
        end = fs.tell()  # end is offset after last byte
        fs.seek(begin)
        while (fs.tell() != end):
            Esl = EfiSignatureList(fs)
            self.EslList.append(Esl)

    def Print(self, compact: bool = False):
        """Prints to the console."""
        for Esl in self.EslList:
            Esl.Print(compact=compact)

    def Write(self, fs):
        """Serializes the object and writes it to a filestream.

        Raises:
            (Exception): Invalid filestream
        """
        if (fs is None):
            raise Exception("Invalid File Output Stream")
        for Esl in self.EslList:
            Esl.Write(fs)

    def GetBytes(self) -> bytes:
        """Return bytes array produced by Write()."""
        with io.BytesIO() as fs:
            self.Write(fs)
            return fs.getvalue()

    def GetCanonicalAndDupes(self):
        """Compute and return a tuple containing both a canonicalized database & a database of duplicates.

        Returns:
            (Tuple[EfiSignatureDatabase, EfiSignatureDatabase]): (canonical, duplicates)

        !!! note
            canonical is an EfiSignatureDatabase where EfiSignatureLists are merged (where possible),
                deduplicated, & sorted, and the EfiSignatureData elements are also deduplicated & sorted
            duplicates is an EfiSignatureDatabase with EfiSignatureLists containing any duplicated
                EfiSignatureData entries (only the data contents are checked for effective equality,
                signature owner is ignored)
        """
        # First group EFI_SIGNATURE_LISTS by type, merging them where possible

        sha256esl = None
        x509eslList = None

        for Esl in self.EslList:
            if (Esl.SignatureData_List is None):  # discard empty EfiSignatureLists
                continue
            if (Esl.SignatureType == EfiSignatureDataFactory.EFI_CERT_SHA256_GUID):
                if (sha256esl is None):
                    sha256esl = Esl  # initialize it
                else:
                    sha256esl.MergeSignatureList(Esl)
            elif (Esl.SignatureType == EfiSignatureDataFactory.EFI_CERT_X509_GUID):
                if (x509eslList is None):
                    x509eslList = [Esl]  # initialize it
                else:
                    x509eslList.append(Esl)
            else:
                raise Exception("Unsupported signature type %s",
                                Esl.SignatureType)

        # for each type, sort and de-duplicate, and then populate the respective databases
        # note the ordering of this section is the prescribed canonical order
        # first 1 EfiSignatureList for SHA256 hashes, EfiSignatureData elements sorted ascending
        # followed by EfiSignatureLists for each x509 certificate, sorted ascending by data content

        canonicalDb = EfiSignatureDatabase()
        duplicatesDb = EfiSignatureDatabase()

        if (sha256esl is not None):
            dupes = sha256esl.SortBySignatureDataValue(deduplicate=True)
            canonicalDb.EslList.append(sha256esl)
            duplicatesDb.EslList.append(dupes)

        if (x509eslList is not None):
            x509eslList.sort(key=attrgetter('SignatureData_List'))
            for esl in x509eslList:
                if not canonicalDb.EslList:
                    canonicalDb.EslList.append(esl)
                elif esl == canonicalDb.EslList[-1]:
                    duplicatesDb.EslList.append(esl)
                else:
                    canonicalDb.EslList.append(esl)

        return (canonicalDb, duplicatesDb)

    def GetCanonical(self):
        """Return a canonicalized EfiSignatureDatabase, see GetCanonicalAndDupes() for more details."""
        (canonical, dupes) = self.GetCanonicalAndDupes()
        return canonical

    def GetDuplicates(self):
        """Return an EfiSignatureDatabase of duplicates, see GetCanonicalAndDupes() for more details."""
        (canonical, dupes) = self.GetCanonicalAndDupes()
        return dupes


class EfiTime(object):
    """Object representing an EFI_TIME."""
    _StructFormat = '<H6BLh2B'
    _StructSize = struct.calcsize(_StructFormat)

    def __init__(self, Time=datetime.datetime.now(), decodefs=None):
        """Inits an EFI_TIME object.

        Args:
            Time (:obj:`datetime`, optional): Inits object with specified date (if decodefs not set)
            decodefs (:obj:`BinaryIO`, optional): Inits the object with this stream
        """
        if (decodefs is None):
            self.Time = Time
        else:
            self.PopulateFromFileStream(decodefs)

    def PopulateFromFileStream(self, fs):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (Exception): Invalid filestream
            (Exception): Invalid filestream size
        """
        if (fs is None):
            raise Exception("Invalid File Steam")

        # only populate from file stream those parts that are complete in the file stream
        start = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(start)

        if ((end - start) < EfiTime._StructSize):  # size of the static structure data
            raise Exception("Invalid file stream size")
        (
            Year,
            Month,
            Day,
            Hour,
            Minute,
            Second,
            _,  # Pad1
            NanoSecond,
            TimeZone,
            Daylight,
            _   # Pad2
        ) = struct.unpack(EfiTime._StructFormat, fs.read(EfiTime._StructSize))

        self.Time = datetime.datetime(
            Year, Month, Day, Hour, Minute, Second, int(NanoSecond / 1000))
        logging.debug("Timezone value is: 0x%x" % TimeZone)
        logging.debug("Daylight value is: 0x%X" % Daylight)

    def Print(self, outfs=sys.stdout):
        """Prints to the console."""
        outfs.write("\nEfiTime: %s\n" % datetime.datetime.strftime(
            self.Time, "%A, %B %d, %Y %I:%M%p"))

    def Encode(self):
        """Get's time as packed EfiTime structure."""
        return struct.pack(
            EfiTime._StructFormat,
            self.Time.year,
            self.Time.month,
            self.Time.day,
            self.Time.hour,
            self.Time.minute,
            self.Time.second,
            0,  # Pad1
            0,  # Nano Seconds
            0,  # Daylight
            0,  # TimeZone
            0   # Pad2
        )

    def Write(self, fs):
        """Serializes the object and writes it to a filestream.

        Raises:
            (Exception): Invalid filestream
        """
        if (fs is None):
            raise Exception("Invalid File Output Stream")

        fs.write(self.Encode())

    def __str__(self):
        """String representation of EFI_TIME."""
        return datetime.datetime.strftime(self.Time, "%A, %B %d, %Y %I:%M%p")


class EfiVariableAuthentication2(object):
    """An object representing a EFI_VARIABLE_AUTHENTICATION_2."""

    def __init__(self, Time=datetime.datetime.now(), decodefs=None):
        """Inits an EFI_VARIABLE_AUTHENTICATION_2 object.

        Args:
            Time (:obj:`datetime`, optional): Inits object with specified date (if decodefs not set)
            decodefs (:obj:`BinaryIO`, optional): Inits the object with this stream
        """
        if decodefs:
            self.PopulateFromFileStream(decodefs)
            return

        self.Time = EfiTime(Time=Time)
        self.AuthInfo = WinCertUefiGuid()
        self.Payload = None
        self.PayloadSize = 0

        # Most variables do not have a sig list
        self.SigListPayload = None

    def Encode(self, outfs=None):
        """Encodes a new variable into a binary representation.

        Args:
            outfs (BinaryIO): [default: None] write's to a file stream if provided

        :return: buffer - binary representation of the variable
        """
        buffer = self.Time.Encode() + self.AuthInfo.Encode()

        if self.Payload:
            buffer += self.Payload

        if outfs:
            outfs.write(buffer)

        return buffer

    def PopulateFromFileStream(self, fs):
        """Decodes a filestream and generates the structure.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (Exception): Invalid filestream
        """
        if (fs is None):
            raise Exception("Invalid File Steam")
        self.Time = EfiTime(decodefs=fs)
        self.AuthInfo = WinCert.Factory(fs)
        self.Payload = None
        self.SigListPayload = None

        self.SetPayload(fs)

    def Print(self, outfs=sys.stdout):
        """Prints to the console."""
        outfs.write("EFiVariableAuthentication2\n")
        self.Time.Print(outfs)
        self.AuthInfo.Print(outfs)

        outfs.write("\n-------------------- VARIABLE PAYLOAD --------------------\n")
        if self.SigListPayload is not None:
            self.SigListPayload.Print()

        elif self.Payload is not None:
            outfs.write("Raw Data: \n")
            sdl = self.Payload.tolist()
            if (self.PayloadSize != len(sdl)):
                raise Exception("Invalid Payload Data Size vs Length of data")
            PrintByteList(sdl)

    def Write(self, fs) -> None:
        """Serializes the object and writes it to a filestream.

        Raises:
            (Exception): Invalid filestream
        """
        if (fs is None):
            raise Exception("Invalid File Output Stream")

        self.Time.Write(fs)
        self.AuthInfo.Write(fs)
        if (self.Payload is not None):
            fs.write(self.Payload)

    def SetPayload(self, fs, signature_list=False) -> None:
        """Decodes a filestream and generates the payload.

        Args:
            fs (BinaryIO): filestream to load from

        Raises:
            (Exception): Invalid filestream
        """
        if (fs is None):
            raise Exception("Invalid File Input Stream")

        # Find the payload size
        start = fs.tell()
        fs.seek(0, 2)
        end = fs.tell()
        fs.seek(start)
        self.PayloadSize = end - start
        if (self.PayloadSize == 0):
            logging.debug(
                "No Payload for this EfiVariableAuthenticated2 Object")
            return

        if signature_list:
            # Variables with the GUID EFI_IMAGE_SECURITY_DATABASE_GUID are formatted as EFI_SIGNATURE_LIST
            try:
                self.SigListPayload = EfiSignatureList(fs)
            except Exception as e:
                logging.debug(
                    "Exception Trying to parse SigList Payload.  \n%s" % str(e))

        # reset the file pointer
        fs.seek(start)
        self.Payload = memoryview(fs.read(self.PayloadSize))


class EfiVariableAuthentication2Builder(object):
    """Builds EfiVariableAuthentication2 variables."""

    def __init__(self, name, guid, attributes, payload=None, efi_time=datetime.datetime.now()):
        """Builds a EfiVariableAuthentication2 structure.

        Args:
            name: Name of the UEFI Variable
            guid: Guid of the namespace the UEFI variable belongs to
            attributes: Attributes of the UEFI variable
            payload (fs, or bytearray): binary payload to be signed and used as the value of the variable
            efi_time (datetime): EFI time of the datetime object

        """
        self.signature = b""

        # the authenticated variable to be returned
        self.authenticated_variable = EfiVariableAuthentication2(Time=efi_time)

        # Start setting up the builder
        self.signature_builder = pkcs7.PKCS7SignatureBuilder()

        efi_attributes = EfiVariableAttributes(attributes)

        # if it's a string, convert it to a uuid type
        if isinstance(guid, str):
            guid = uuid.UUID(guid)

        # if it's still not a uuid lets warn the caller
        if not isinstance(guid, uuid.UUID):
            raise ValueError(f"guid is not the correct type: {type(guid)}")

        # This is the digest being signed that all signer's must sign
        self.digest_without_payload = name.encode('utf_16_le') + \
            guid.bytes_le + efi_attributes.encode() + self.authenticated_variable.Time.Encode()

        # Allow a caller to swap out the payload
        self.digest = self.digest_without_payload

        self.update_payload(payload)

    def get_digest(self) -> bytearray:
        """Returns the Digest to be signed."""
        return self.digest

    def get_signature(self) -> bytearray:
        """Returns the Signature of the digest (PKCS#7 ContentInfo or SignedData structure)."""
        return self.signature

    def update_payload(self, payload) -> None:
        """Updates the autheticated variables payload and ultimately the digest.

        Args:
            payload: byte array or byte file stream of variable data

        Returns:
            None
        """
        # if provided with a payload, the serialized payload must be added to the Digest to be signed
        if not payload:
            logging.info("Empty payload")
            return

        # convert the payload to a file stream for SetPayload
        if not hasattr(payload, 'seek'):
            payload = io.BytesIO(payload)

        # Get the starting position and the length
        start = payload.tell()

        self.digest = self.digest_without_payload + payload.read()

        # before we pass it to SetPayload lets make sure we put the position back
        payload.seek(start)

        self.authenticated_variable.SetPayload(payload)

    def sign(self, signing_certificate: Certificate, signing_private_key: RSAPrivateKey, additional_certificates=[],
             **kwargs) -> None:
        """Signs an authenticated variable.

        Args:
            signing_certificate: x.509 format public key
            signing_private_key: x.509 format private key
            additional_certificates: list of x.509 format public keys to include

        Keyword Arguments:
            hash_algorithm: accepts cryptography.hazmat.primitives.hashes types to specify the hash_algorithm
            omit_content_info: enabled by default, allows to include the  content info asn.1 structure
            digest: uses the digest produced by EFiVariableAuthentication2.New() by default, otherwise may specify a
                 new digest to sign

        :return: pkcs#7 signature (content_info structure may be ommited unless otherwised specified)
        """
        hash_algorithm = kwargs.get("hash_algorithm", SHA256())
        digest = kwargs.get("digest", self.digest)
        indent = kwargs.get("indent", " " * 4)

        # Set up the databuffer that will be signed
        self.signature_builder = self.signature_builder.set_data(digest)

        logging.info("")
        logging.info("Signing with Certificate: ")
        logging.info("%sIssuer: %s", indent, signing_certificate.issuer)
        logging.info("%sSubject: %s", indent, signing_certificate.subject)

        self.signature_builder = self.signature_builder.add_signer(
            signing_certificate, signing_private_key, hash_algorithm)

        for i, cert in enumerate(additional_certificates):
            indents = indent * i
            logging.info("")
            logging.info("%sAdding Additional Certificate: ", indents)
            logging.info("%sIssuer: %s", indents, cert.certificate.issuer)
            logging.info("%sSubject: %s", indents, cert.certificate.subject)

            # Add the certificate for verifcation
            self.signature_builder = self.signature_builder.add_certificate(cert.certificate)

    def finalize(self, omit_content_info=True) -> EfiVariableAuthentication2:
        """Finalizes the signature and returns a EfiVariableAuthentication2.

        Args:
            omit_content_info: omits the asn.1 content info structure
                By specification this should be supported (and the SignedData structure) but this
                has been broken in tianocore for some time now
                
        Returns:
            EfiVariableAuthentication2
        """
        # Set the options for the pkcs7 signature:
        #   - The signature is detached
        #   - Do not convert LF to CRLF in the file (windows format)
        #   - Remove the attributes section from the pkcs7 structure
        options = [pkcs7.PKCS7Options.DetachedSignature,
                   pkcs7.PKCS7Options.Binary, pkcs7.PKCS7Options.NoAttributes]

        # The signature is enclosed in a asn1 content info structure
        self.signature = self.signature_builder.sign(Encoding.DER, options)

        # Up until recently including the content info section (on tianocore edk2 based implementations)
        # will cause UEFI to return `SECURITY_VIOLATION``
        if omit_content_info:
            content_info, _ = der_decode(
                self.signature, asn1Spec=rfc2315.ContentInfo())

            content_type = content_info.getComponentByName('contentType')
            if content_type != rfc2315.signedData:
                raise ValueError("This wasn't a signed data structure?")

            # Remove the contentInfo section and just return the sign data
            signed_data, _ = der_decode(content_info.getComponentByName(
                'content'), asn1Spec=rfc2315.SignedData())

            self.signature = der_encode(signed_data)

        self.authenticated_variable.AuthInfo.AddCertData(self.signature)

        return self.authenticated_variable


'''
THESE ARE NOT SUPPORTED IN THE TOOL

```
typedef struct {
  ///
  /// The SHA256 hash of an X.509 certificate's To-Be-Signed contents.
  ///
  EFI_SHA256_HASH     ToBeSignedHash;
  ///
  /// The time that the certificate shall be considered to be revoked.
  ///
  EFI_TIME            TimeOfRevocation;
} EFI_CERT_X509_SHA256;
```

```
typedef struct {
  ///
  /// The SHA384 hash of an X.509 certificate's To-Be-Signed contents.
  ///
  EFI_SHA384_HASH     ToBeSignedHash;
  ///
  /// The time that the certificate shall be considered to be revoked.
  ///
  EFI_TIME            TimeOfRevocation;
} EFI_CERT_X509_SHA384;
```

```
typedef struct {
  ///
  /// The SHA512 hash of an X.509 certificate's To-Be-Signed contents.
  ///
  EFI_SHA512_HASH     ToBeSignedHash;
  ///
  /// The time that the certificate shall be considered to be revoked.
  ///
  EFI_TIME            TimeOfRevocation;
} EFI_CERT_X509_SHA512;
```
'''
