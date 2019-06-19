# @file
# Module contains helper classes and functions to work with UEFI FFs.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import uuid
import struct
import sys

#
# EFI_FFS_FILE_HEADER
#
# typedef struct {
#   EFI_GUID                Name;
#   EFI_FFS_INTEGRITY_CHECK IntegrityCheck;
#   EFI_FV_FILETYPE         Type;
#   EFI_FFS_FILE_ATTRIBUTES Attributes;
#   UINT8                   Size[3];
#   EFI_FFS_FILE_STATE      State;
# } EFI_FFS_FILE_HEADER;


class EfiFirmwareFileSystemHeader(object):
    def __init__(self):
        self.StructString = "=16sHBBBBBB"
        self.FileSystemGuid = None
        self.Size0 = None
        self.Size1 = None
        self.Size2 = None
        self.Attributes = None
        self.Type = None
        self.State = None

    def get_size(self):
        return self.Size0 + (self.Size1 << 8) + (self.Size2 << 16)

    def load_from_file(self, file):
        orig_seek = file.tell()
        struct_bytes = file.read(struct.calcsize(self.StructString))
        file.seek(orig_seek)

        # Load this object with the contents of the data.
        (self.FileSystemGuid, self.Checksum, self.Type, self.Attributes, self.Size0, self.Size1,
            self.Size2, self.State) = struct.unpack(self.StructString, struct_bytes)

        # Update the GUID to be a UUID object.
        if sys.byteorder == 'big':
            self.FileSystemGuid = uuid.UUID(bytes=self.FileSystemGuid)
        else:
            self.FileSystemGuid = uuid.UUID(bytes_le=self.FileSystemGuid)

        return self

    def serialize(self):
        file_system_guid_bin = self.FileSystemGuid.bytes if sys.byteorder == 'big' else self.FileSystemGuid.bytes_le
        return struct.pack(self.StructString, file_system_guid_bin, self.Checksum,
                           self.Type, self.Attributes, self.Size0, self.Size1, self.Size2, self.State)
