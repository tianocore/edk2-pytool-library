# @file
# Module contains helper classes for working with Fault Tolerant Working block content
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import struct
import uuid
import sys

#
# UEFI GUIDs
#
EdkiiWorkingBlockSignatureGuid = uuid.UUID(fields=(0x9E58292B, 0x7C68, 0x497D, 0xA0, 0xCE, 0x6500FD9F1B95))

#
# The EDKII Fault tolerant working block header.
# The header is immediately followed by the write queue data.
#
# typedef struct {
#   EFI_GUID  Signature;
#   UINT32    Crc;
#   UINT8     WorkingBlockValid : 1;
#   UINT8     WorkingBlockInvalid : 1;
#   UINT8     Reserved : 6;
#   UINT8     Reserved3[3];
#   UINT64    WriteQueueSize;
# } EFI_FAULT_TOLERANT_WORKING_BLOCK_HEADER;


class EfiFtwWorkingBlockHeader(object):
    def __init__(self):
        self.StructString = "=16sLBBBBQ"  # spell-checker: disable-line
        self.Signature = None
        self.Crc = None
        self.WorkingBlockValidFields = None
        self.Reserved1 = None
        self.Reserved2 = None
        self.Reserved3 = None
        self.WriteQueueSize = None

    def load_from_file(self, file):
        # This function assumes that the file has been seeked
        # to the correct starting location.
        orig_seek = file.tell()
        struct_bytes = file.read(struct.calcsize(self.StructString))
        file.seek(orig_seek)

        # Load this object with the contents of the data.
        (signature_bin, self.Crc, self.WorkingBlockValidFields, self.Reserved1, self.Reserved2, self.Reserved3,
         self.WriteQueueSize) = struct.unpack(self.StructString, struct_bytes)

        # Update the GUID to be a UUID object.
        if sys.byteorder == 'big':
            self.Signature = uuid.UUID(bytes=signature_bin)
        else:
            self.Signature = uuid.UUID(bytes_le=signature_bin)

        # Check that signature is valid
        if self.Signature != EdkiiWorkingBlockSignatureGuid:
            raise Exception("FTW Working Block Header has unknown signature: %s" % self.Signature)

        return self

    def serialize(self):
        signature_bin = self.Signature.bytes if sys.byteorder == 'big' else self.Signature.bytes_le
        return struct.pack(self.StructString, signature_bin, self.Crc, self.WorkingBlockValidFields,
                           self.Reserved1, self.Reserved2, self.Reserved3, self.WriteQueueSize)

#
# EFI Fault tolerant block update write queue entry.
#
# typedef struct {
#   UINT8     HeaderAllocated : 1;
#   UINT8     WritesAllocated : 1;
#   UINT8     Complete : 1;
#   UINT8     Reserved : 5;
#   EFI_GUID  CallerId;
#   UINT64    NumberOfWrites;
#   UINT64    PrivateDataSize;
# } EFI_FAULT_TOLERANT_WRITE_HEADER;


class EfiFtwWriteHeader(object):
    def __init__(self):
        self.StructString = "=BBBB16sLQQ"
        self.StatusBits = None
        self.ReservedByte1 = None
        self.ReservedByte2 = None
        self.ReservedByte3 = None
        self.CallerId = None
        self.ReservedUint32 = None
        self.NumberOfWrites = None
        self.PrivateDataSize = None

    def load_from_file(self, file):
        # This function assumes that the file has been seeked
        # to the correct starting location.
        orig_seek = file.tell()
        struct_bytes = file.read(struct.calcsize(self.StructString))
        file.seek(orig_seek)

        # Load this object with the contents of the data.
        (self.StatusBits, self.ReservedByte1, self.ReservedByte2, self.ReservedByte3, self.CallerId,
         self.ReservedUint32, self.NumberOfWrites, self.PrivateDataSize) = struct.unpack(self.StructString,
                                                                                         struct_bytes)

        return self

    def serialize(self):
        return struct.pack(self.StructString, self.StatusBits, self.ReservedByte1, self.ReservedByte2,
                           self.ReservedByte3, self.CallerId, self.ReservedUint32, self.NumberOfWrites,
                           self.PrivateDataSize)

#
# EFI Fault tolerant block update write queue record.
#
# typedef struct {
#   UINT8   BootBlockUpdate : 1;
#   UINT8   SpareComplete : 1;
#   UINT8   DestinationComplete : 1;
#   UINT8   Reserved : 5;
#   EFI_LBA Lba;
#   UINT64  Offset;
#   UINT64  Length;
#   INT64   RelativeOffset;
# } EFI_FAULT_TOLERANT_WRITE_RECORD;


class EfiFtwWriteRecord(object):
    def __init__(self):
        self.StructString = "=BBBBLQQQQ"  # spell-checker: disable-line
        self.StatusBits = None
        self.ReservedByte1 = None
        self.ReservedByte2 = None
        self.ReservedByte3 = None
        self.ReservedUint32 = None
        self.Lba = None
        self.Offset = None
        self.Length = None
        self.RelativeOffset = None

    def load_from_file(self, file):
        # This function assumes that the file has been seeked
        # to the correct starting location.
        orig_seek = file.tell()
        struct_bytes = file.read(struct.calcsize(self.StructString))
        file.seek(orig_seek)

        # Load this object with the contents of the data.
        (self.StatusBits, self.ReservedByte1, self.ReservedByte2, self.ReservedByte3, self.ReservedUint32, self.Lba,
         self.Offset, self.Length, self.RelativeOffset) = struct.unpack(self.StructString, struct_bytes)

        return self

    def serialize(self):
        return struct.pack(self.StructString, self.StatusBits, self.ReservedByte1, self.ReservedByte2,
                           self.ReservedByte3, self.ReservedUint32, self.Lba, self.Offset, self.Length,
                           self.RelativeOffset)
