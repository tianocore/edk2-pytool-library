## @file
# Test FDF containing simple definitions and conditionals
#
# Copyright (c) Microsoft Corporation.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
##


DEFINE CONDITIONAL_VALUE = 121

!if $(TARGET) == "TEST4"
DEFINE AM_I_YOU    = FALSE
!endif
