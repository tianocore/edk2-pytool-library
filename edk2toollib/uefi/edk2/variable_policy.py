# @file
# Module contains helper classes and functions to work with Variable Policy structures
# and substructures.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import uuid
import struct
from edk2toollib.uefi.uefi_multi_phase import EfiVariableAttributes


class VariableLockOnVarStatePolicy(object):
    # typedef struct {
    #     EFI_GUID Namespace;
    #     UINT8    Value;
    #     UINT8    Reserved;
    #     // CHAR16   Name[];           // Variable Length Field
    # } VARIABLE_LOCK_ON_VAR_STATE_POLICY;
    _HdrStructFormat = "<16sBB"
    _HdrStructSize = struct.calcsize(_HdrStructFormat)

    def __init__(self):
        self.Namespace = uuid.UUID(bytes=b'\x00' * 16)
        self.Value = 0
        self.Name = None

    def __str__(self):
        return "VARIABLE_LOCK_ON_VAR_STATE_POLICY(%s, %d, %s)" % (self.Namespace, self.Value, self.Name)

    def decode(self, buffer):
        """
        load this object from a bytes buffer

        return any remaining buffer
        """
        (_namespace, self.Value, _) = struct.unpack(
            self._HdrStructFormat, buffer[:self._HdrStructSize])

        self.Namespace = uuid.UUID(bytes_le=_namespace)

        # Scan the rest of the buffer for a \x00\x00 to terminate the string.
        buffer = buffer[self._HdrStructSize:]
        if len(buffer) < 4:
            raise ValueError("Buffer too short!")

        string_end = None
        for i in range(0, len(buffer), 2):
            if buffer[i] == 0 and buffer[i + 1] == 0:
                string_end = i + 2
                break

        if string_end is None:
            raise ValueError("String end not detected!")

        self.Name = buffer[:string_end].decode('utf-16').strip('\x00')

        return buffer[string_end:]


class VariablePolicyEntry(object):
    # typedef struct {
    #     UINT32   Version;
    #     UINT16   Size;
    #     UINT16   OffsetToName;
    #     EFI_GUID Namespace;
    #     UINT32   MinSize;
    #     UINT32   MaxSize;
    #     UINT32   AttributesMustHave;
    #     UINT32   AttributesCantHave;
    #     UINT8    LockPolicyType;
    #     UINT8    Reserved[3];
    #     // UINT8    LockPolicy[];     // Variable Length Field
    #     // CHAR16   Name[]            // Variable Length Field
    # } VARIABLE_POLICY_ENTRY;
    _HdrStructFormat = "<IHH16sIIIIB3s"             # spell-checker:disable-line
    _HdrStructSize = struct.calcsize(_HdrStructFormat)

    ENTRY_REVISION = 0x0001_0000

    NO_MIN_SIZE = 0
    NO_MAX_SIZE = 0xFFFF_FFFF
    NO_MUST_ATTR = 0
    NO_CANT_ATTR = 0

    TYPE_NO_LOCK = 0
    TYPE_LOCK_NOW = 1
    TYPE_LOCK_ON_CREATE = 2
    TYPE_LOCK_ON_VAR_STATE = 3

    LOCK_POLICY_STRING_MAP = {
        TYPE_NO_LOCK: "NONE",
        TYPE_LOCK_NOW: "NOW",
        TYPE_LOCK_ON_CREATE: "ON_CREATE",
        TYPE_LOCK_ON_VAR_STATE: "ON_VAR_STATE",
    }

    def __init__(self):
        self.Version = VariablePolicyEntry.ENTRY_REVISION
        self.Size = VariablePolicyEntry._HdrStructSize
        self.OffsetToName = self.Size
        self.Namespace = uuid.UUID(bytes=b'\x00' * 16)
        self.MinSize = VariablePolicyEntry.NO_MIN_SIZE
        self.MaxSize = VariablePolicyEntry.NO_MAX_SIZE
        self.AttributesMustHave = VariablePolicyEntry.NO_MUST_ATTR
        self.AttributesCantHave = VariablePolicyEntry.NO_CANT_ATTR
        self.LockPolicyType = VariablePolicyEntry.TYPE_NO_LOCK
        self.LockPolicy = None
        self.Name = None

    def __str__(self):
        result = "VARIABLE_POLICY_ENTRY(%s, %s)\n" % (self.Namespace, self.Name)

        if self.LockPolicyType in (VariablePolicyEntry.TYPE_NO_LOCK,
                                   VariablePolicyEntry.TYPE_LOCK_NOW,
                                   VariablePolicyEntry.TYPE_LOCK_ON_CREATE):
            result += "\tLock        = %s\n" % VariablePolicyEntry.LOCK_POLICY_STRING_MAP[self.LockPolicyType]
        elif self.LockPolicyType is VariablePolicyEntry.TYPE_LOCK_ON_VAR_STATE:
            result += "\tLock        = %s\n" % self.LockPolicy

        result += "\tMin = 0x%08X, Max = 0x%08X, Must = 0x%08X, Cant = 0x%08X\n" % (
            self.MinSize, self.MaxSize, self.AttributesMustHave, self.AttributesCantHave)

        return result

    @staticmethod
    def csv_header():
        """returns a list containing the names of the ordered columns that are produced by csv_row()"""
        return ['Namespace', 'Name', 'LockPolicyType', 'VarStateNamespace', 'VarStateName',
                'VarStateValue', 'MinSize', 'MaxSize', 'AttributesMustHave', 'AttributesCantHave']

    def csv_row(self, guid_xref: dict = None):
        """
        returns a list containing the elements of this structure (in the same order as the csv_header)
        ready to be written to a csv file

        guid_xref - a dictionary of GUID/name substitutions where the key is a uuid object
                    and the value is a string
        """
        if guid_xref is None:
            guid_xref = {}

        result = [guid_xref.get(self.Namespace, self.Namespace),
                  self.Name, VariablePolicyEntry.LOCK_POLICY_STRING_MAP[self.LockPolicyType]]

        if self.LockPolicyType in (VariablePolicyEntry.TYPE_NO_LOCK,
                                   VariablePolicyEntry.TYPE_LOCK_NOW,
                                   VariablePolicyEntry.TYPE_LOCK_ON_CREATE):
            result += ['N/A', 'N/A', 'N/A']
        elif self.LockPolicyType is VariablePolicyEntry.TYPE_LOCK_ON_VAR_STATE:
            result += [guid_xref.get(self.LockPolicy.Namespace, self.LockPolicy.Namespace),
                       self.LockPolicy.Name, self.LockPolicy.Value]

        result += ["0x%08X" % self.MinSize,
                   "0x%08X" % self.MaxSize,
                   str(EfiVariableAttributes(self.AttributesMustHave)),
                   str(EfiVariableAttributes(self.AttributesCantHave))]

        return result

    def decode(self, buffer):
        """
        load this object from a bytes buffer

        return any remaining buffer
        """
        (self.Version, self.Size, self.OffsetToName, _namespace,
            self.MinSize, self.MaxSize, self.AttributesMustHave,
            self.AttributesCantHave, self.LockPolicyType, _) = struct.unpack(
                self._HdrStructFormat, buffer[:self._HdrStructSize])

        if self.Version != VariablePolicyEntry.ENTRY_REVISION:
            raise ValueError("Unknown structure version!")
        if self.LockPolicyType not in VariablePolicyEntry.LOCK_POLICY_STRING_MAP:
            raise ValueError("Unknown LockPolicyType!")

        self.Namespace = uuid.UUID(bytes_le=_namespace)

        if self.OffsetToName != self.Size:
            self.Name = buffer[self.OffsetToName:self.Size].decode('utf-16').strip('\x00')

        if self.LockPolicyType == VariablePolicyEntry.TYPE_LOCK_ON_VAR_STATE:
            self.LockPolicy = VariableLockOnVarStatePolicy()
            self.LockPolicy.decode(buffer[self._HdrStructSize:self.OffsetToName])

        return buffer[self.Size:]
