# @file __init__.py
# The core classes and methods used to interact with the database portion of edk2-pytool-library
# This prevents needing to do deeply nested imports and can simply `from edk2toollib.database import``
##
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Core classes and methods used to interact with the database module inside edk2-pytool-library."""

from tinydb import Query, where  # noqa: F401
from tinyrecord import transaction  # noqa: F401

from .edk2_db import AdvancedQuery, Edk2DB, TableGenerator  # noqa: F401
