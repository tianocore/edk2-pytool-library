# @file
# Python implementation of UEFI C types
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Python implementation of UEFI C types"""

from typing import TypeAlias
import ctypes

# These depend on 32 bit vs 64 bit, but assuming 64
EFI_PHYSICAL_ADDRESS: TypeAlias = ctypes.c_uint64
UINTN: TypeAlias = ctypes.c_uint64
UINT8: TypeAlias = ctypes.c_uint8
