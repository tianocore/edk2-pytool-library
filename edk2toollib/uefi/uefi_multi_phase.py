# @file
# Module contains defintions and structures from the UefiMultiPhase header file.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import struct

EFI_VARIABLE_NON_VOLATILE = 0x00000001
EFI_VARIABLE_BOOTSERVICE_ACCESS = 0x00000002
EFI_VARIABLE_RUNTIME_ACCESS = 0x00000004
EFI_VARIABLE_HARDWARE_ERROR_RECORD = 0x00000008
EFI_VARIABLE_AUTHENTICATED_WRITE_ACCESS = 0x00000010
EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS = 0x00000020
EFI_VARIABLE_APPEND_WRITE = 0x00000040


class EfiVariableAttributes(object):
    # UINT32
    _StructFormat = "<I"
    _StructSize = struct.calcsize(_StructFormat)

    STRING_MAP = {
        EFI_VARIABLE_APPEND_WRITE: "EFI_VARIABLE_APPEND_WRITE",
        EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS: "EFI_VARIABLE_TIME_BASED_AUTHENTICATED_WRITE_ACCESS",
        EFI_VARIABLE_AUTHENTICATED_WRITE_ACCESS: "EFI_VARIABLE_AUTHENTICATED_WRITE_ACCESS",
        EFI_VARIABLE_HARDWARE_ERROR_RECORD: "EFI_VARIABLE_HARDWARE_ERROR_RECORD",
        EFI_VARIABLE_RUNTIME_ACCESS: "EFI_VARIABLE_RUNTIME_ACCESS",
        EFI_VARIABLE_BOOTSERVICE_ACCESS: "EFI_VARIABLE_BOOTSERVICE_ACCESS",
        EFI_VARIABLE_NON_VOLATILE: "EFI_VARIABLE_NON_VOLATILE",
    }

    def __init__(self, attributes=0x0000_0000):
        self.Attributes = attributes

    def __str__(self):
        result = []
        for key in EfiVariableAttributes.STRING_MAP:
            if self.Attributes & key:
                result.append(EfiVariableAttributes.STRING_MAP[key])
        return ",".join(result)
