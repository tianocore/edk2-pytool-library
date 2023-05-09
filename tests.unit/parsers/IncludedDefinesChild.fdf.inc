## @file
# Test FDF containing simple definitions and conditionals
#
# Copyright (c) Microsoft Corporation.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
##


DEFINE INTERNAL_VALUE   = 104
DEFINE EXTRA_BLOCK_SIZE = 0x00001000

!if $(TARGET) == "TEST4"
DEFINE AM_I_YOU    = FALSE
!endif
